import uuid
from .base import BaseRepository
from app.models.meeting import Meeting
from app.models.mador import Mador


class MeetingRepository(BaseRepository):
    def create_meeting(self, meeting_id: int, mador_id) -> Meeting | None:
        mador = self.session.query(Mador).filter_by(UUID=mador_id).first()
        if not mador:
            return None

        meeting = Meeting(
            meeting_id=meeting_id,
            mador_id=mador_id,
            mador_owner_id=mador.creator_id,
        )
        self.session.add(meeting)
        self.session.commit()
        self.session.refresh(meeting)
        return meeting

    def get_meeting_by_id(self, meeting_id) -> Meeting | None:
        return self.session.query(Meeting).filter_by(id=meeting_id).first()

    def get_meetings_by_mador(self, mador_id) -> list[Meeting]:
        return self.session.query(Meeting).filter_by(mador_id=mador_id).all()