import uuid

from .base import BaseRepository
from app.models.user import User
from app.models.mador import Mador
from app.schema.user import UserInCreate, UserInCreateNoRole



class UserRepository(BaseRepository):
    def create_user(self, user_data: UserInCreate):
        data = user_data.model_dump(exclude_none=True)
        mador_ids = data.pop("mador_ids", None)

        new_user = User(**data)
        self.session.add(new_user)

        if mador_ids:
            madors = self.session.query(Mador).filter(Mador.UUID.in_(mador_ids)).all()
            new_user.madors.extend(madors)

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
    
    def user_exist_by_username(self, username: str) -> bool:
        user = self.session.query(User).filter_by(username=username).first()
        return bool(user)

    def get_user_by_username(self, username: str) -> User:
        return self.session.query(User).filter_by(username=username).first()

    def get_user_by_s_id(self, s_id: str) -> User:
        user = self.session.query(User).filter_by(s_id=s_id).first()
        return user

    def get_all_users(self) -> list[User]:
        users = self.session.query(User).all()
        return users

    def delete_user(self, user_id: str) -> bool:
        user = self.session.query(User).filter_by(s_id=user_id).first()
        if user:
            self.session.delete(user)
            self.session.commit()
            return True
    
        return False
