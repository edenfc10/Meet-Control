from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.repository.meetingRepo import MeetingRepository
from app.schema.user import MeetingOutput, MeetingBase
from fastapi import HTTPException


class MeetingService:
    def __init__(self, session):
        self.__meetingRepository = MeetingRepository(session=session)

    def create_meeting(self, meeting_data: MeetingBase, mador_id: UUID) -> MeetingOutput:
        try:
            meeting = self.__meetingRepository.create_meeting(
                meeting_id=meeting_data.meeting_id,
                mador_id=mador_id,
            )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Meeting ID already exists")

        if not meeting:
            raise HTTPException(status_code=404, detail="Mador not found")

        return MeetingOutput.model_validate(meeting, from_attributes=True)

    def get_meetings_by_mador(self, mador_id: UUID) -> list[MeetingOutput]:
        meetings = self.__meetingRepository.get_meetings_by_mador(mador_id=mador_id)
        return [MeetingOutput.model_validate(m, from_attributes=True) for m in meetings]