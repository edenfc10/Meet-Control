# ============================================================================
# MeetingRepository - שכבת גישה לנתוני פגישות
# ============================================================================
# אחראית על כל פעולות ה-DB הקשורות לפגישות:
#   - CRUD מלא (create/read/update/delete)
#   - חיפוש לפי UUID, מספר פגישה, או קבוצה
#   - עדכון לפי UUID או לפי מספר פגישה
# ============================================================================

import uuid
from sqlalchemy import String, cast

from .base import BaseRepository
from app.models.user import User
from app.models.group import Group

from app.schema.user import UserInCreate, UserInCreateNoRole, UserOutput
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput
from app.models.meeting import Meeting, AccessLevel
from app.models.member_group_access import MemberGroupAccess


class MeetingRepository(BaseRepository):

    def create_meeting(self, meeting_data: MeetingInCreate, access_level: AccessLevel) -> MeetingOutput:
        """
        יוצר פגישה חדשה ב-DB לפי סוג הגישה.
        access_level: "audio" | "video" | "blast_dial"
        """
        data = meeting_data.model_dump(exclude_none=True)
        data["accessLevel"] = access_level  # קובע את סוג הפגישה לפי ה-route שקרא לפונקציה

        new_meeting = Meeting(**data)

        self.session.add(new_meeting)
        self.session.commit()
        self.session.refresh(new_meeting)

        return new_meeting
    
    
    def delete_meeting(self, meeting_uuid: str) -> bool:
        """ מוחק פגישה לפי UUID. מחזיר True אם הצליח """
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if meeting:
            self.session.delete(meeting)
            self.session.commit()
            return True
        return False
    
    def get_meeting_by_uuid(self, meeting_uuid: str) -> MeetingOutput:
        """ מוצא פגישה לפי UUID """
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        return meeting

    def user_can_access_meeting(self, user_uuid: str, meeting_uuid: str, user_role: str | None = None) -> bool:
        """
        ×‘×•×“×§ ×”×× ×œ×ž×©×ª×ž×© ×™×© ×’×™×©×” ×œ×¤×’×™×©×”:
        - ×”×ž×©×ª×ž×© ×¦×¨×™×š ×œ×”×™×•×ª ×—×‘×¨ ×‘×œ×¤×—×•×ª ×ž×“×•×¨ ××—×“ ×©×œ ×”×¤×’×™×©×”
        - ×•×‘××•×ª×• ×ž×“×•×¨ ×—×™×™×‘×ª ×œ×”×™×•×ª ×œ×• ×¨×ž×ª ×’×™×©×” ×©×ž×ª××™×ž×” ×œ×¡×•×’ ×”×¤×’×™×©×”
        """
        try:
            normalized_user_uuid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return False

        meeting = self.get_meeting_by_uuid(meeting_uuid=meeting_uuid)
        if not meeting:
            return False

        meeting_level = getattr(meeting.accessLevel, "value", meeting.accessLevel)
        meeting_level = str(meeting_level).lower().strip()
        if meeting_level not in {"audio", "video", "blast_dial"}:
            return False

        meeting_group_uuids = [group.UUID for group in meeting.groups]
        if not meeting_group_uuids:
            return False

        access_row = (
            self.session.query(MemberGroupAccess)
            .filter(
                MemberGroupAccess.member_uuid == normalized_user_uuid,
                MemberGroupAccess.group_uuid.in_(meeting_group_uuids),
                MemberGroupAccess.access_level == meeting_level,
            )
            .first()
        )
        return access_row is not None
    
    def get_all_meetings(self,user_uuid: str,user_role: str | None = None, access_level: AccessLevel | None = None) -> list[MeetingOutput]:
        """ מחזיר את כל הפגישות. אם נשלח access_level — מסנן לפי סוג (audio/video/blast_dial) """
        normalized_role = str(user_role or "").lower().strip()
        if normalized_role in ["admin", "super_admin"]:
            query = self.session.query(Meeting)
            if access_level is not None:
                query = query.filter(Meeting.accessLevel == access_level)
            return query.distinct().all()

        try:
            normalized_user_uuid = uuid.UUID(str(user_uuid))
        except (ValueError, TypeError):
            return []

        query = (
            self.session.query(Meeting)
            .join(Meeting.groups)
            .join(MemberGroupAccess, MemberGroupAccess.group_uuid == Group.UUID)
            .filter(MemberGroupAccess.member_uuid == normalized_user_uuid)
        )

        if access_level is not None:
            access_level_value = str(getattr(access_level, "value", access_level))
            query = query.filter(
                Meeting.accessLevel == access_level,
                cast(MemberGroupAccess.access_level, String) == access_level_value,
            )
        else:
            query = query.filter(
                cast(Meeting.accessLevel, String)
                == cast(MemberGroupAccess.access_level, String)
            )

        return query.distinct().all()
    
    def get_meeting_by_number(self, number: int) -> MeetingOutput:
        """ מוצא פגישה לפי מספר הפגישה (m_number) """
        meeting = self.session.query(Meeting).filter(Meeting.m_number == number).first()
        return meeting
    
    def get_meetings_by_group_uuid(self, group_uuid: str) -> list[str]:
        """ מחזיר רשימת UUIDs של פגישות השייכות לקבוצה """
        group = self.session.query(Group).filter(Group.UUID == group_uuid).first()
        if group:
            return [meeting.UUID for meeting in group.meetings]
        return []
    
    def update_meeting_by_number(self, meeting_number: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        """ מעדכן פגישה לפי מספר - רק שדות שנשלחו """
        meeting = self.session.query(Meeting).filter(Meeting.m_number == meeting_number).first()
        if not meeting:
            return None

        for key, value in meeting_data.model_dump(exclude_none=True).items():
            setattr(meeting, key, value)

        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    def update_meeting_by_uuid(self, meeting_uuid: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        """ מעדכן פגישה לפי UUID - רק שדות שנשלחו """
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if not meeting:
            return None

        for key, value in meeting_data.model_dump(exclude_none=True).items():
            setattr(meeting, key, value)

        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    def update_password_by_uuid(self, meeting_uuid: str, password: str) -> MeetingOutput:
        """ מעדכן את הסיסמה של פגישה לפי UUID """
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if not meeting:
            return None

        meeting.password = password
        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    
