# ============================================================================
# UserService - ×©×›×‘×ª ×œ×•×’×™×§×” ×¢×¡×§×™×ª ×œ×ž×©×ª×ž×©×™×
# ============================================================================
# ×”×©×›×‘×” ×”×–×• ×ž×›×™×œ×” ××ª ×›×œ ×”×œ×•×’×™×§×” ×”×¢×¡×§×™×ª ×©×§×©×•×¨×” ×œ×ž×©×ª×ž×©×™×:
#   - ×”×ª×—×‘×¨×•×ª (login): ××™×ž×•×ª ×¡×™×¡×ž×”, ×™×¦×™×¨×ª JWT
#   - יצירת משתמש: הצפנת סיסמה, הגדרת תפקיד
#   - ×ž×—×™×§×ª ×ž×©×ª×ž×©: ×‘×“×™×§×•×ª ×”×¨×©××•×ª (×ž×™ ×™×›×•×œ ×œ×ž×—×•×§ ×ž×™)
#   - שליפת פגישות מדור לפי רמת גישה של המשתמש
#
# Pattern: Service Layer
#   הService מתווך בין הRouter (הAPI) לבין הRepository (הDB).
#   ×ž×•×¡×™×£ ×œ×•×’×™×§×” ×¢×¡×§×™×ª ×›×ž×• ×”×¦×¤× ×ª ×¡×™×¡×ž××•×ª, ×‘×“×™×§×•×ª ×”×¨×©××•×ª, ×•×¤×•×¨×ž×˜ ×¤×œ×˜.
# ============================================================================

from datetime import datetime, timedelta, timezone
from typing import Dict

from sqlalchemy import String

from app.models.user import User
from app.repository.userRepo import UserRepository
from app.schema.user import (
    AccessTokenData,
    RefreshTokenData,
    UserInCreateNoRole,
    UserOutput,
    UserInLogin,
    UserLoginOutput
)
from app.security.hashHelper import HashHelp
from app.security.auth import AuthHand, REFRESH_TOKEN_EXPIRE_DAYS, ACCESS_TOKEN_EXPIRE_MINUTES
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid


class UserService:
    def __init__(self, session):
        self.__userRepository = UserRepository(
            session=session
        )  # יוצר מופע של הרפוזיטורי
        self.session = session

    def login(self, login_details: UserInLogin) -> UserLoginOutput:
        """
        תהליך התחברות:
        1. ×‘×•×“×§ ×× ×”×ž×©×ª×ž×© ×§×™×™× ×œ×¤×™ s_id
        2. משווה סיסמה מול hash בDB (Argon2)
        3. ×™×•×¦×™×¨ JWT token ×¢× ×¤×¨×˜×™ ×”×ž×©×ª×ž×©
        4. מחזיר token + role
        """
        user = self.__userRepository.get_user_by_s_id(s_id=login_details.s_id)
        if not user:  # ×‘×“×™×§×” ×× ×”×ž×©×ª×ž×© ×§×™×™× ×‘DB
            raise HTTPException(status_code=400, detail="Please create an Account")

        # ×”×©×•×•××ª ×”×¡×™×¡×ž×” ×ž×•×œ ×”hash ×”×©×ž×•×¨ ×‘DB
        if HashHelp.verify_password(
            plain_password=login_details.password, hashed_password=user.password
        ):
            # ×™×¦×™×¨×ª ×˜×•×§×Ÿ JWT ×¢× ×¤×¨×˜×™ ×”×ž×©×ª×ž×© (UUID, role, s_id)
          
            access_token = AuthHand.generate_access_token(uuid=str(user.UUID), role=user.role, s_id=user.s_id)
            refresh_token = AuthHand.generate_refresh_token(uuid=str(user.UUID), session=self.session)

            if access_token and refresh_token:
                return UserLoginOutput(
                    access_token=access_token, refresh_token=refresh_token, role=user.role
                )  # החזרת הטוקן והתפקיד
            raise HTTPException(status_code=500, detail="Unable to process request")
        raise HTTPException(status_code=401, detail="Please check your Credentials")

    def _role_value(self, role) -> str:
        """×¢×•×–×¨ - ×ž×—×–×™×¨ ××ª ×”×¢×¨×š ×”×˜×§×¡×˜×•××œ×™ ×©×œ ×ª×¤×§×™×“ (×‘×™×Ÿ ×× ×–×” Enum ××• string)"""
        return getattr(role, "value", role)

    def get_all_users(
        self, current_user_role: str, current_user_uuid: str | None = None
    ) -> list[UserOutput]:
        """
        ×ž×—×–×™×¨ ××ª ×›×œ ×”×ž×©×ª×ž×©×™×.
        ×× ×”×ž×©×ª×ž×© ×”× ×•×›×—×™ ×œ× super_admin - ×ž×¡×ª×™×¨ ×¡×•×¤×¨×™× ×ž×”×¨×©×™×ž×”.
        """
        if current_user_role == "viewer" and current_user_uuid:
            users = self.__userRepository.get_users_in_same_groups(
                user_uuid=current_user_uuid
            )
        else:
            users = self.__userRepository.get_all_users()
        if current_user_role != "super_admin":
            users = [
                user for user in users if self._role_value(user.role) != "super_admin"
            ]
        return [UserOutput.model_validate(user, from_attributes=True) for user in users]

    def get_user_by_s_id(self, s_id: str) -> User:
        user = self.__userRepository.get_user_by_s_id(s_id=s_id)
        if user:
            return user
        raise HTTPException(status_code=400, detail="User is not available")
    
    def get_user_by_uuid(self, uuid: str) -> User:
        user = self.__userRepository.get_user_by_uuid(uuid=uuid)
        if user:
            return user
        raise HTTPException(status_code=400, detail="User is not available")
    
    def get_user_by_s_id_for_requester(
        self, s_id: str, requester_role: str, requester_uuid: str
    ) -> User:
        """
        ×ž×—×–×™×¨ ×ž×©×ª×ž×© ×œ×¤×™ s_id, ×¢× ×”×’×‘×œ×ª viewer:
        viewer ×™×›×•×œ ×œ×¦×¤×•×ª ×¨×§ ×‘×ž×©×ª×ž×©×™× ×©×—×•×œ×§×™× ××™×ª×• ×ž×“×•×¨.
        """
        user = self.get_user_by_s_id(s_id=s_id)

        if requester_role == "viewer":
            group_users = self.__userRepository.get_users_in_same_groups(
                user_uuid=requester_uuid
            )
            allowed_ids = {str(u.UUID) for u in group_users}
            if str(user.UUID) not in allowed_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Viewer can only access users in the same group",
                )

        return user
    
    def update_details_on_user(self, user_uuid: str, update_data: UserInCreateNoRole) -> UserOutput:
        """עדכון פרטי משתמש - ללא שינוי תפקיד. הסיסמה מוצפנת לפני שמירה"""
        hashed_password = HashHelp.get_password_hash(plain_password=update_data.password)
        update_data.password = hashed_password
        user = self.__userRepository.update_details_on_user(user_uuid=user_uuid, update_data=update_data)
        if user:
            return UserOutput(
                UUID=user.UUID,
                s_id=user.s_id,
                username=user.username,
                role=user.role,
                groups=[m.group_uuid for m in user.group_access_levels],
            )
        raise HTTPException(status_code=400, detail="User is not available")

    def delete_user(
        self, user_id: str, current_user_role: str, current_user_s_id: str
    ) -> bool:
        """
        ×ž×•×—×§ ×ž×©×ª×ž×© ×¢× ×‘×“×™×§×•×ª ×”×¨×©××•×ª:
        - ×¨×§ admin ××• super_admin ×™×›×•×œ×™× ×œ×ž×—×•×§
        - ×œ× × ×™×ª×Ÿ ×œ×ž×—×•×§ ××ª ×¢×¦×ž×š
        - admin ×œ× ×™×›×•×œ ×œ×ž×—×•×§ super_admin
        """
        if current_user_role not in ("admin", "super_admin"):
            raise HTTPException(
                status_code=403, detail="Only admin or super_admin can delete users"
            )

        target_user = self.__userRepository.get_user_by_s_id(s_id=user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        if target_user.s_id == current_user_s_id:
            raise HTTPException(
                status_code=400, detail="You cannot delete your own user"
            )

        target_role = self._role_value(target_user.role)
        if current_user_role == "admin" and target_role == "super_admin":
            raise HTTPException(
                status_code=403, detail="Admin cannot delete super_admin users"
            )

        return self.__userRepository.delete_user(user_id=user_id)

    def create_agent_user(self, user_data: UserInCreateNoRole) -> UserOutput:
        """יוצר משתמש סוג agent - הסיסמה מוצפנת לפני שמירה"""
        hashed_password = HashHelp.get_password_hash(plain_password=user_data.password)
        user_data.password = hashed_password
        user = self.__userRepository.create_agent_user(user_data=user_data)
        user = UserOutput(
            UUID=user.UUID,
            s_id=user.s_id,
            username=user.username,
            role=user.role,
            groups=[m.group_uuid for m in user.group_access_levels],
        )
        return user

    def create_admin_user(self, user_data: UserInCreateNoRole) -> UserOutput:
        """יוצר משתמש סוג admin - הסיסמה מוצפנת לפני שמירה"""
        hashed_password = HashHelp.get_password_hash(plain_password=user_data.password)
        user_data.password = hashed_password
        user = self.__userRepository.create_admin_user(user_data=user_data)
        user = UserOutput(
            UUID=user.UUID,
            s_id=user.s_id,
            username=user.username,
            role=user.role,
            groups=[m.group_uuid for m in user.group_access_levels],
        )
        return user

    def create_viewer_user(self, user_data: UserInCreateNoRole) -> UserOutput:
        """יוצר משתמש סוג viewer - הסיסמה מוצפנת לפני שמירה"""
        hashed_password = HashHelp.get_password_hash(plain_password=user_data.password)
        user_data.password = hashed_password
        user = self.__userRepository.create_viewer_user(user_data=user_data)
        user = UserOutput(
            UUID=user.UUID,
            s_id=user.s_id,
            username=user.username,
            role=user.role,
            groups=[m.group_uuid for m in user.group_access_levels],
        )
        return user

    def get_group_meetings_by_user_uuid(
        self, user_uuid: str, group_uuid: str
    ) -> list[str]:
        """
        ×ž×—×–×™×¨ ×¨×©×™×ž×ª ×¤×’×™×©×•×ª ×©×ž×©×ª×ž×© ×¨×©××™ ×œ×¨××•×ª ×‘×ž×“×•×¨.
        מסתמך על רמת הגישה מטבלת member_group_access.
        """
        meetings = self.__userRepository.get_group_meetings_by_user_uuid(
            user_uuid=user_uuid, group_uuid=group_uuid
        )
        if meetings is not None:
            return meetings
        else:
            raise HTTPException(
                status_code=400, detail="User or Group is not available"
            )
