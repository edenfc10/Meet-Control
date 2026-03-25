import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.mador import Mador
from app.models.meeting import Meeting

from app.schema.user import MadorInCreate, MadorInUpdate, MadorOutput

from app.models.meeting import AccessLevel as MeetingAccessLevel

class MadorRepository(BaseRepository):
    def create_mador(self, mador_data: MadorInCreate) -> MadorOutput:
        data = mador_data.model_dump(exclude_none=True)

        new_mador = Mador(**data)

        self.session.add(new_mador)
        self.session.commit()
        self.session.refresh(new_mador)

        return new_mador
    
    def get_all_madors(self) -> list[MadorOutput]:
       return self.session.query(Mador).all()
        
    def get_mador_by_uuid(self, mador_uuid: str) -> MadorOutput:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        return mador

    def delete_mador(self, mador_uuid: str) -> bool:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        if mador:
            self.session.delete(mador)
            self.session.commit()
            return True
        return False

    def update_mador(self, mador_uuid: str, mador_data: MadorInUpdate) -> MadorOutput:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        if not mador:
            return None

        for key, value in mador_data.model_dump(exclude_none=True).items():
            setattr(mador, key, value)

        self.session.commit()
        self.session.refresh(mador)
        return mador

    def add_member_to_mador(self, mador_uuid: str, user_s_id: str, access_level: MeetingAccessLevel) -> MadorOutput:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        user = self.session.query(User).filter(User.s_id == user_s_id).first()

        if not mador or not user:
            return None

        mador.members.append(user)
        

        self.session.commit()
        self.session.refresh(mador)
        return mador

    def remove_member_from_mador(self, mador_uuid: str, user_s_id: str) -> MadorOutput:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        user = self.session.query(User).filter(User.s_id == user_s_id).first()

        if not mador or not user:
            return None

        if user in mador.members:
            mador.members.remove(user)
            self.session.commit()
            self.session.refresh(mador)

        return mador

    def add_meeting_to_mador_by_uuid(self, mador_uuid: str, meeting_uuid: str) -> MadorOutput:
        mador = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first()
        meeting = self.session.query(Meeting).filter(Meeting.UUID == meeting_uuid).first()

        if not mador or not meeting:
            return None

        mador.meetings.append(meeting)

        self.session.commit()
        self.session.refresh(mador)
        return mador