import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.mador import Mador

from app.schema.user import UserInCreate, UserInCreateNoRole, UserOutput
from app.schema.meeting import MeetingInCreate, MeetingInUpdate, MeetingOutput
from app.models.meeting import Meeting


class MeetingRepository(BaseRepository):
    def create_meeting(self, meeting_data: MeetingInCreate) -> MeetingOutput:
        data = meeting_data.model_dump(exclude_none=True)

        new_meeting = Meeting(**data)

        self.session.add(new_meeting)
        self.session.commit()
        self.session.refresh(new_meeting)

        return new_meeting
    
    
    def delete_meeting(self, meeting_uuid: str) -> bool:
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if meeting:
            self.session.delete(meeting)
            self.session.commit()
            return True
        return False
    
    def get_meeting_by_uuid(self, meeting_uuid: str) -> MeetingOutput:
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        return meeting
    
    def get_all_meetings(self) -> list[MeetingOutput]:
        return self.session.query(Meeting).all()
    
    def get_meeting_by_number(self, number: int) -> MeetingOutput:
        meeting = self.session.query(Meeting).filter(Meeting.m_number == number).first()
        return meeting
    
    def get_meetings_by_mador_uuid(self, mador_uuid: str) -> list[str]:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        if mador:
            return [meeting.UUID for meeting in mador.meetings]
        return []
    
    def update_meeting_by_number(self, meeting_number: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        meeting = self.session.query(Meeting).filter(Meeting.m_number == meeting_number).first()
        if not meeting:
            return None

        for key, value in meeting_data.model_dump(exclude_none=True).items():
            setattr(meeting, key, value)

        self.session.commit()
        self.session.refresh(meeting)
        return meeting
    
    def update_meeting_by_uuid(self, meeting_uuid: str, meeting_data: MeetingInUpdate) -> MeetingOutput:
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()
        if not meeting:
            return None

        for key, value in meeting_data.model_dump(exclude_none=True).items():
            setattr(meeting, key, value)

        self.session.commit()
        self.session.refresh(meeting)
        return meeting