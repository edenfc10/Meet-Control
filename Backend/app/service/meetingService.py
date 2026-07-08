# ============================================================================
# MeetingService - שכבת לוגיקה לפגישות (מבוסס CMS)
# ============================================================================
# הפגישות חיות אך ורק ב-CMS. השירות הזה קורא/כותב ישירות מול ה-CMS,
# ומצרף נתוני overlay מקומיים לפי מספר פגישה:
#   - groups: מדורים משויכים (GroupMeeting)
#   - participant_count: כמות משתמשים מורשים במדורים המשויכים
#
# בקרת גישה ל-agent: רואה רק פגישות שמספרן משויך למדור שיש לו בו הרשאה
# בדרגה התואמת לסוג הפגישה.
# blast_dial לא קיים ב-CMS ולכן לא נתמך (נשאר להמשך).
# ============================================================================

import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import String, cast

from app.models.meeting import AccessLevel, GroupMeeting, Meeting
from app.models.member_group_access import MemberGroupAccess
from app.models.favorite_meeting import FavoriteMeeting
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput
from app.service.cms import CMS, CMSFactory
from logger import LoggerManager

CMS_TYPES = ("audio", "video")


def _clean(value) -> Optional[str]:
    """מנרמל ערך מ-CMS: אלמנט XML ריק מתפרש כ-{} -> None. מחזיר str לא-ריק או None."""
    if value is None or isinstance(value, dict):
        return None
    text = str(value).strip()
    return text or None


class MeetingService:
    def __init__(self, session):
        self.session = session

    # ------------------------------------------------------------------
    # Overlay helpers (נתונים מקומיים לפי מספר פגישה)
    # ------------------------------------------------------------------
    def _groups_for(self, m_number: str, access_level_value: str) -> List:
        """UUIDs של מדורים המשויכים לפגישה (מספר + סוג)."""
        links = self.session.query(GroupMeeting).filter(
            GroupMeeting.meeting_number == str(m_number),
            GroupMeeting.access_level == access_level_value,
        ).all()
        return [link.group_uuid for link in links]

    def _participant_count(self, group_uuids: List, access_level_value: str) -> int:
        if not group_uuids:
            return 0
        rows = self.session.query(MemberGroupAccess).filter(
            MemberGroupAccess.group_uuid.in_(group_uuids),
            cast(MemberGroupAccess.access_level, String) == access_level_value,
        ).all()
        return len({str(r.member_uuid) for r in rows})

    def _accessible_numbers(self, user_uuid: str, access_level_value: str) -> set:
        """מספרי הפגישות שמשתמש רשאי לגשת אליהן ברמת גישה מסוימת."""
        try:
            uid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return set()
        rows = (
            self.session.query(GroupMeeting.meeting_number)
            .join(MemberGroupAccess, MemberGroupAccess.group_uuid == GroupMeeting.group_uuid)
            .filter(
                GroupMeeting.access_level == access_level_value,
                MemberGroupAccess.member_uuid == uid,
                cast(MemberGroupAccess.access_level, String) == access_level_value,
            )
            .all()
        )
        return {row[0] for row in rows}

    def _to_output(self, cs: Dict, access_level_value: str) -> MeetingOutput:
        m_number = _clean(cs.get("callId")) or ""
        group_uuids = self._groups_for(m_number, access_level_value)
        return MeetingOutput(
            id=cs.get("id") or cs.get("@id"),
            m_number=m_number,
            name=_clean(cs.get("name")) or m_number,
            accessLevel=access_level_value,
            password=_clean(cs.get("passcode")),
            groups=group_uuids,
            participant_count=self._participant_count(group_uuids, access_level_value),
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_all_meetings(self, user_uuid: str, user_role: str, access_level: AccessLevel | None = None, responsible_access_level: str | None = None) -> list[MeetingOutput]:
        role = str(user_role or "").lower().strip()

        if access_level is not None:
            av = str(getattr(access_level, "value", access_level)).lower()
            if av not in CMS_TYPES:
                return []  # blast_dial has no CMS backing
            types = [av]
        else:
            types = list(CMS_TYPES)
            if role == "admin":
                from app.models.user import User
                db_user = self.session.query(User).filter(User.UUID == user_uuid).first()
                if db_user:
                    allowed_types = []
                    if getattr(db_user, "can_audio", False):
                        allowed_types.append("audio")
                    if getattr(db_user, "can_video", False):
                        allowed_types.append("video")
                    if allowed_types:
                        types = allowed_types

        is_admin = role in ("admin", "super_admin")
        outputs: list[MeetingOutput] = []
        for t in types:
            allowed = None if is_admin else self._accessible_numbers(user_uuid, t)
            try:
                cospaces = CMSFactory.get(self.session, t).list_cospaces(full_details=True)
            except Exception as error:
                LoggerManager.get_logger().warning("Failed to list %s CoSpaces: %s", t, str(error))
                continue
            for cs in cospaces:
                num = _clean(cs.get("callId"))
                if not num:
                    continue
                if allowed is not None and num not in allowed:
                    continue
                outputs.append(self._to_output(cs, t))
        return outputs

    def _find_cospace(self, number: str):
        """מחזיר (cospace, cms_type) עבור מספר פגישה (callId), או (None, None)."""
        for t in CMS_TYPES:
            try:
                cs = CMSFactory.get(self.session, t).get_cospace_by_call_id(str(number))
            except Exception:
                cs = None
            if cs:
                return cs, t
        return None, None

    def _find_cospace_by_type(self, number: str, cms_type: str):
        """מחזיר cospace ספציפי לפי סוג CMS (audio/video), או None."""
        try:
            return CMSFactory.get(self.session, cms_type).get_cospace_by_call_id(str(number))
        except Exception:
            return None

    def _ensure_meeting_exists(self, meeting_number: str, access_level: str) -> Meeting:
        """Ensure Meeting record exists in local database. Creates if missing."""
        existing = self.session.query(Meeting).filter(
            Meeting.meeting_number == meeting_number,
            Meeting.access_level == access_level
        ).first()
        if existing:
            return existing
        meeting = Meeting(
            meeting_number=meeting_number,
            access_level=access_level,
            cms_id=None
        )
        self.session.add(meeting)
        self.session.commit()
        return meeting

    def get_meeting_by_number(self, number) -> MeetingOutput:
        cs, t = self._find_cospace(number)
        if cs:
            return self._to_output(cs, t)
        raise HTTPException(status_code=404, detail="Meeting is not available")

    def get_meeting_by_number_for_user(self, number, user_uuid: str, user_role: str) -> MeetingOutput:
        cs, t = self._find_cospace(number)
        if not cs:
            raise HTTPException(status_code=404, detail="Meeting is not available")
        role = str(user_role or "").lower().strip()
        if role not in ("admin", "super_admin"):
            if str(number) not in self._accessible_numbers(user_uuid, t):
                raise HTTPException(status_code=403, detail="You are not allowed to access this meeting")
        return self._to_output(cs, t)

    def get_meetings_by_group_uuid(self, group_uuid: str) -> list[str]:
        links = self.session.query(GroupMeeting).filter(
            GroupMeeting.group_uuid == group_uuid
        ).all()
        return [link.meeting_number for link in links]

    def _assert_admin_access(self, user_role: str, user_uuid: str, meeting_type: str):
        """מוודא שאדמין מורשה לסוג הפגישה הזה לפי can_audio/can_video."""
        if user_role != "admin":
            return
        from app.models.user import User
        user = self.session.query(User).filter(User.UUID == user_uuid).first()
        if not user:
            return
        mt = str(meeting_type).lower()
        if mt == "audio" and not getattr(user, "can_audio", False):
            raise HTTPException(status_code=403, detail="Admin not authorized for audio meetings")
        if mt == "video" and not getattr(user, "can_video", False):
            raise HTTPException(status_code=403, detail="Admin not authorized for video meetings")

    # ------------------------------------------------------------------
    # Write (ישירות ל-CMS)
    # ------------------------------------------------------------------
    def create_meeting(self, meeting_data: MeetingInCreate, access_level: AccessLevel) -> MeetingOutput:
        av = str(getattr(access_level, "value", access_level)).lower()
        if av not in CMS_TYPES:
            raise HTTPException(status_code=400, detail="Only audio/video meetings are supported (blast_dial not supported yet)")
        cms = CMSFactory.get(self.session, av)
        if cms.get_cospace_by_call_id(meeting_data.m_number):
            raise ValueError(f"Meeting number {meeting_data.m_number} already exists")
        cms.create_cospace(
            name=meeting_data.name or meeting_data.m_number,
            uri=meeting_data.m_number,
            passcode=meeting_data.password or None,
        )
        LoggerManager.get_logger().info("Created CoSpace on %s CMS: %s", av, meeting_data.m_number)
        cs = cms.get_cospace_by_call_id(meeting_data.m_number) or {
            "callId": meeting_data.m_number, "name": meeting_data.name, "passcode": meeting_data.password,
        }
        return self._to_output(cs, av)

    def delete_meeting(self, number, user_uuid: str = None, user_role: str = None) -> bool:
        cs, t = self._find_cospace(number)
        if cs and user_uuid and user_role:
            self._assert_admin_access(user_role, user_uuid, t)
        if cs:
            try:
                CMSFactory.get(self.session, t).delete_cospace_by_call_id(str(number))
                LoggerManager.get_logger().info("Deleted CoSpace from %s CMS: %s", t, number)
            except Exception as error:
                raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")
        # ניקוי overlay מקומי (שיוכים + מועדפים). אם הסוג ידוע — לפי (מספר+סוג), אחרת כל הסוגים.
        gm_q = self.session.query(GroupMeeting).filter(GroupMeeting.meeting_number == str(number))
        fav_q = self.session.query(FavoriteMeeting).filter(FavoriteMeeting.meeting_number == str(number))
        if t:
            gm_q = gm_q.filter(GroupMeeting.access_level == t)
            fav_q = fav_q.filter(FavoriteMeeting.access_level == t)
        gm_q.delete()
        fav_q.delete()
        self.session.commit()
        return True

    def update_name_by_number(self, number: str, name: str, user_uuid: str, user_role: str, access_level_hint: str = None) -> MeetingOutput:
        if access_level_hint and access_level_hint.lower() in CMS_TYPES:
            t = access_level_hint.lower()
            cs = self._find_cospace_by_type(number, t)
        else:
            cs, t = self._find_cospace(number)
        if not cs:
            raise HTTPException(status_code=404, detail="Meeting is not available")
        role = str(user_role or "").lower().strip()
        self._assert_admin_access(role, user_uuid, t)
        if role not in ("admin", "super_admin"):
            if str(number) not in self._accessible_numbers(user_uuid, t):
                raise HTTPException(status_code=403, detail="You are not allowed to update this meeting name")
        try:
            CMSFactory.get(self.session, t).update_cospace_name_by_call_id(str(number), name)
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")
        cs, _ = self._find_cospace(number)
        return self._to_output(cs or {"callId": str(number)}, t)

    def update_password_by_number(self, number, password: Optional[str], user_uuid: str, user_role: str, access_level_hint: str = None) -> MeetingOutput:
        if access_level_hint and access_level_hint.lower() in CMS_TYPES:
            t = access_level_hint.lower()
            cs = self._find_cospace_by_type(number, t)
        else:
            cs, t = self._find_cospace(number)
        if not cs:
            raise HTTPException(status_code=404, detail="Meeting is not available")
        role = str(user_role or "").lower().strip()
        self._assert_admin_access(role, user_uuid, t)
        if role not in ("admin", "super_admin"):
            if str(number) not in self._accessible_numbers(user_uuid, t):
                raise HTTPException(status_code=403, detail="You are not allowed to update this meeting password")
        try:
            CMSFactory.get(self.session, t).update_cospace_passcode_by_call_id(str(number), password or "")
        except Exception as error:
            raise HTTPException(status_code=502, detail=f"CMS error: {str(error)}")
        cs, _ = self._find_cospace(number)
        return self._to_output(cs or {"callId": str(number)}, t)

    # ------------------------------------------------------------------
    # Live stats (CMS)
    # ------------------------------------------------------------------
    def get_active_meetings(self) -> Dict:
        stats = {
            "audio": {"meetings": 0, "participants": 0},
            "video": {"meetings": 0, "participants": 0},
            "blast_dial": {"meetings": 0, "participants": 0},
            "unknown": {"meetings": 0, "participants": 0},
        }
        all_calls = []
        warnings = []

        for cms_type in CMS_TYPES:
            try:
                all_calls.extend([(c, cms_type) for c in CMSFactory.get(self.session, cms_type).get_active_calls()])
            except Exception as error:
                LoggerManager.get_logger().warning("%s CMS unavailable for live stats: %s", cms_type, str(error))
                warnings.append(f"{cms_type.capitalize()} CMS server is unreachable")

        if not all_calls:
            return {
                "total_active": 0,
                "by_type": stats,
                "warning": "; ".join(warnings) if warnings else "No active calls found",
            }

        total_active = 0
        for call, cms_type in all_calls:
            call_id = call.get("id") or call.get("callId") or call.get("@id")
            if not call_id:
                continue
            try:
                participant_count = len(CMSFactory.get(self.session, cms_type).get_call_participants(call_id))
            except Exception:
                participant_count = 0
            stats[cms_type]["meetings"] += 1
            stats[cms_type]["participants"] += participant_count
            total_active += 1

        return {"total_active": total_active, "by_type": stats}
