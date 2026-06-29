# ============================================================================
# MeetingService - שכבת לוגיקה עסקית לפגישות
# ============================================================================
# השכבה הזו מכילה את כל הלוגיקה העסקית הקשורה לפגישות:
#   - CRUD מלא: יצירה, קריאה, עדכון, מחיקה
#   - חיפוש לפי UUID, מספר, או קבוצה
#   - המרה לפורמט פלט: _to_output ממיר ORM ל-Pydantic
# ============================================================================

from typing import Dict, List

from sqlalchemy import String

from app.models.user import User
from app.repository.groupRepo import GroupRepository
from app.repository.meetingRepo import MeetingRepository
from app.schema.user import GroupInCreate, GroupOutput, UserInCreateNoRole , UserOutput, UserInCreate, UserInLogin, UserWithToken
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput
from app.schema.user import GroupInCreate, GroupOutput, UserInCreateNoRole , UserOutput, UserInCreate, UserInLogin, UserWithToken
from app.security.hashHelper import HashHelp
from app.security.auth import AuthHand
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.meeting import Meeting, AccessLevel
from app.service.cms import CMS
from logger import LoggerManager
import uuid

# Define AccessLevel type if not imported from elsewhere



class MeetingService:
    def __init__(self, session):
        self.__meetingRepository = MeetingRepository(session=session)  # מופע הרפוזיטורי
        self.session = session

    def _to_output(self, meeting) -> MeetingOutput:
        """ממיר ORM object של פגישה ל-Pydantic MeetingOutput. ממיר את רשימת הקבוצות ל-UUIDs בלבד."""
        meeting_level = str(getattr(meeting.accessLevel, "value", meeting.accessLevel)).lower()
        users_seen = set()
        for group in meeting.groups:
            for member_access in group.member_access_levels:
                access_val = str(getattr(member_access.access_level, "value", member_access.access_level)).lower()
                if access_val == meeting_level:
                    users_seen.add(str(member_access.member_uuid))
        return MeetingOutput(
            UUID=meeting.UUID,
            m_number=meeting.m_number,
            name=meeting.name,
            accessLevel=meeting.accessLevel,
            password=getattr(meeting, "password", None),
            groups=[m.UUID for m in meeting.groups],
            participant_count=len(users_seen),
        )

    def create_meeting(self, meeting_data: MeetingInCreate, access_level: AccessLevel) -> MeetingOutput:
        # access_level: "audio" | "video" | "blast_dial"
        return self._to_output(self.__meetingRepository.create_meeting(meeting_data=meeting_data, access_level=access_level))

    def get_all_meetings(self, user_uuid: str, user_role: str, access_level: AccessLevel | None = None, responsible_access_level: str | None = None) -> list[MeetingOutput]:
        meetings = self.__meetingRepository.get_all_meetings(user_uuid=user_uuid, user_role=user_role, access_level=access_level, responsible_access_level=responsible_access_level)
        # אם access_level נשלח — מסנן לפי סוג; אחרת מחזיר הכול
        return [self._to_output(m) for m in meetings]
    
    def get_meeting_by_uuid(self, meeting_uuid: str) -> MeetingOutput:
        meeting = self.__meetingRepository.get_meeting_by_uuid(meeting_uuid=meeting_uuid)
        if meeting:
            return self._to_output(meeting)
        raise HTTPException(status_code=400, detail="Meeting is not available")

    def get_meeting_by_uuid_for_user(self, meeting_uuid: str, user_uuid: str, user_role: str) -> MeetingOutput:
        """
        מחזיר פגישה בודדת לפי המשתמש המחובר:
        - admin/super_admin: גישה מלאה
        - agent/viewer: רק אם יש גישה לפי קבוצה + access level
        """
        meeting = self.__meetingRepository.get_meeting_by_uuid(meeting_uuid=meeting_uuid)
        if not meeting:
            raise HTTPException(status_code=400, detail="Meeting is not available")

        if user_role in ("admin", "super_admin"):
            return self._to_output(meeting)

        can_access = self.__meetingRepository.user_can_access_meeting(
            user_uuid=user_uuid,
            meeting_uuid=meeting_uuid,
            user_role=user_role,
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="You are not allowed to access this meeting")

        return self._to_output(meeting)
    
    def delete_meeting(self, meeting_uuid: str) -> bool:
        if self.__meetingRepository.delete_meeting(meeting_uuid=meeting_uuid):
            return True
        raise HTTPException(status_code=400, detail="Meeting is not available")
    
    def update_password_by_uuid(self, meeting_uuid: str, password: str, user_uuid: str, user_role: str) -> MeetingOutput:
        normalized_role = str(user_role or "").lower().strip()

        if normalized_role not in ("admin", "super_admin"):
            can_access = self.__meetingRepository.user_can_access_meeting(
                user_uuid=user_uuid,
                meeting_uuid=meeting_uuid,
                user_role=normalized_role,
            )
            if not can_access:
                raise HTTPException(status_code=403, detail="You are not allowed to update this meeting password")

        meeting = self.__meetingRepository.update_password_by_uuid(meeting_uuid=meeting_uuid, password=password)
        if meeting:
            return self._to_output(meeting)
        raise HTTPException(status_code=400, detail="Meeting is not available")
    
    def update_meeting_by_uuid(self, meeting_uuid: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        meeting = self.__meetingRepository.update_meeting_by_uuid(meeting_uuid=meeting_uuid, meeting_data=meeting_data)
        if meeting:
            return self._to_output(meeting)
        raise HTTPException(status_code=400, detail="Meeting is not available")
    
    def get_meeting_by_number(self, number: int) -> MeetingOutput:
        meeting = self.__meetingRepository.get_meeting_by_number(number=number)
        if meeting:
            return self._to_output(meeting)
        raise HTTPException(status_code=400, detail="Meeting is not available")
    
    def get_meetings_by_group_uuid(self, group_uuid: str) -> list[str]:
        meetings = self.__meetingRepository.get_meetings_by_group_uuid(group_uuid=group_uuid)
        if meetings is not None:
            return meetings
        raise HTTPException(status_code=400, detail="Group is not available")
    
    def update_meeting_by_number(self, meeting_number: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        meeting = self.__meetingRepository.update_meeting_by_number(meeting_number=meeting_number, meeting_data=meeting_data)
        if meeting:
            return self._to_output(meeting)
        raise HTTPException(status_code=400, detail="Meeting is not available")

    def get_active_meetings(self) -> Dict:
        """
        מחזיר סטטיסטיקה של פגישות פעילות (live) מה-CMS.
        שואל את שני שרתי ה-CMS (audio ו-video) ומרכיב את התוצאות.
        אם ה-CMS לא זמין, מחזיר אפסים עם הודעת אזהרה.
        """
        stats = {
            "audio": {"meetings": 0, "participants": 0},
            "video": {"meetings": 0, "participants": 0},
            "blast_dial": {"meetings": 0, "participants": 0},
            "unknown": {"meetings": 0, "participants": 0},
        }

        all_calls = []
        warnings = []

        # Query audio CMS
        try:
            cms_audio = CMS(cms_type="audio")
            audio_calls = cms_audio.get_active_calls()
            all_calls.extend(audio_calls)
        except Exception as error:
            LoggerManager.get_logger().warning("Audio CMS unavailable for live stats. Error: %s", str(error))
            warnings.append("Audio CMS server is unreachable")

        # Query video CMS
        try:
            cms_video = CMS(cms_type="video")
            video_calls = cms_video.get_active_calls()
            all_calls.extend(video_calls)
        except Exception as error:
            LoggerManager.get_logger().warning("Video CMS unavailable for live stats. Error: %s", str(error))
            warnings.append("Video CMS server is unreachable")

        if not all_calls:
            return {
                "total_active": 0,
                "by_type": stats,
                "warning": "; ".join(warnings) if warnings else "No active calls found",
            }

        total_active = 0

        for call in all_calls:
            call_id = call.get("id") or call.get("callId") or call.get("@id")
            if not call_id:
                continue
            call_name = str(call.get("name", ""))
            meeting_type = self._resolve_meeting_type(call_name)

            # Only handle audio and video — blast_dial and unknown are skipped
            if meeting_type not in ("audio", "video"):
                continue

            try:
                cms = CMS(cms_type=meeting_type)
                participants = cms.get_call_participants(call_id)
                participant_count = len(participants)
            except Exception:
                participant_count = 0
            stats[meeting_type]["meetings"] += 1
            stats[meeting_type]["participants"] += participant_count
            total_active += 1

        return {"total_active": total_active, "by_type": stats}

    def _resolve_meeting_type(self, m_number: str) -> str:
        """
        מזהה את סוג הפגישה לפי DB או לפי קידומת המספר.
        """
        meeting = self.session.query(Meeting).filter(Meeting.m_number == str(m_number)).first()
        if meeting:
            mt_type = str(getattr(meeting.accessLevel, "value", meeting.accessLevel)).lower()
            if mt_type in {"audio", "video"}:
                return mt_type

        prefix = m_number[:2] if m_number.isdigit() and len(m_number) >= 2 else ""
        if prefix == "89":
            return "audio"
        if prefix == "77":
            return "video"
        return "unknown"
    
