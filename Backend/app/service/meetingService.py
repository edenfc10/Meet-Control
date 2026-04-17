# ============================================================================
# MeetingService - שכבת לוגיקה עסקית לפגישות
# ============================================================================
# השכבה הזו מכילה את כל הלוגיקה העסקית הקשורה לפגישות:
#   - CRUD מלא: יצירה, קריאה, עדכון, מחיקה
#   - חיפוש לפי UUID, מספר, או קבוצה
#   - המרה לפורמט פלט: _to_output ממיר ORM ל-Pydantic
# ============================================================================

from typing import Dict

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
import uuid

# Define AccessLevel type if not imported from elsewhere



class MeetingService:
    def __init__(self, session):
        self.__meetingRepository = MeetingRepository(session=session)  # מופע הרפוזיטורי
        self.session = session

    def _to_output(self, meeting) -> MeetingOutput:
        """ממיר ORM object של פגישה ל-Pydantic MeetingOutput. ממיר את רשימת הקבוצות ל-UUIDs בלבד."""
        return MeetingOutput(
            UUID=meeting.UUID,
            m_number=meeting.m_number,
            accessLevel=meeting.accessLevel,
            password=getattr(meeting, "password", None),
            groups=[m.UUID for m in meeting.groups],
        )

    def create_meeting(self, meeting_data: MeetingInCreate, access_level: AccessLevel) -> MeetingOutput:
        # access_level: "audio" | "video" | "blast_dial"
        return self._to_output(self.__meetingRepository.create_meeting(meeting_data=meeting_data, access_level=access_level))

    def get_all_meetings(self,user_uuid:str, user_role:str, access_level: AccessLevel | None = None) -> list[MeetingOutput]:
        meetings = self.__meetingRepository.get_all_meetings(user_uuid=user_uuid, user_role=user_role, access_level=access_level)
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
    
