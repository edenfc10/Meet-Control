import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.mador import Mador

from app.schema.user import UserInCreate, UserInCreateNoRole, UserOutput
from app.models.member_mador_access import MemberMadorAccess, MemberMadorAccessLevel


class UserRepository(BaseRepository):
    def create_user(self, user_data: UserInCreate) -> UserOutput:
        data = user_data.model_dump(exclude_none=True)

        mador_ids = data.pop("mador_ids", [])

        new_user = User(**data)

        if mador_ids and len(mador_ids) > 0:
            madors = self.session.query(Mador).filter(Mador.UUID.in_(mador_ids)).all()
            new_user.madors.extend(madors)

        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        return new_user
    
    #TODO: delete later - only for testing
    def create_agent_user(self, user_data: UserInCreateNoRole):
        data = UserInCreate(**user_data.model_dump(), role="agent").model_dump(exclude_none=True)
        return self.create_user(UserInCreate(**data))
    
    def create_admin_user(self, user_data: UserInCreateNoRole):
        data = UserInCreate(**user_data.model_dump(), role="admin").model_dump(exclude_none=True)
        return self.create_user(UserInCreate(**data))
    
    def get_user_by_s_id(self, s_id: str) -> UserOutput:
        user = self.session.query(User).filter_by(s_id=s_id).first()
        return user

    def get_all_users(self) -> list[UserOutput]:
        users = self.session.query(User).all()
        return users

    def delete_user(self, user_id: str) -> bool:
        user = self.session.query(User).filter_by(s_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
    
        return False

    def get_mador_meetings_by_user_uuid(self, user_uuid: str, mador_uuid: str) -> list[str]:
        connections = self.session.query(MemberMadorAccess).filter(MemberMadorAccess.member_uuid == user_uuid, MemberMadorAccess.mador_uuid == mador_uuid).all()
        access_allowed = [conn.access_level for conn in connections]

        meetings = self.session.query(Mador).filter(Mador.UUID == mador_uuid).first().meetings
        return [str(meeting.UUID) for meeting in meetings if meeting.accessLevel in access_allowed]