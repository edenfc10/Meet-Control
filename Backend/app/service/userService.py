# ============================================================================
# UserService - שכבת לוגיקה עסקית למשתמשים
# ============================================================================
# השכבה הזו מכילה את כל הלוגיקה העסקית שקשורה למשתמשים:
#   - התחברות (login): אימות סיסמה, יצירת JWT
#   - יצירת משתמש: הצפנת סיסמה, הגדרת תפקיד
#   - מחיקת משתמש: בדיקות הרשאות (מי יכול למחוק מי)
#   - שליפת פגישות מדור לפי רמת גישה של המשתמש
#
# Pattern: Service Layer
#   הService מתווך בין הRouter (הAPI) לבין הRepository (הDB).
#   מוסיף לוגיקה עסקית כמו הצפנת סיסמאות, בדיקות הרשאות, ופורמט פלט.
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
        1. בודק אם המשתמש קיים לפי s_id
        2. משווה סיסמה מול hash בDB (Argon2)
        3. יוציר JWT token עם פרטי המשתמש
        4. מחזיר token + role
        """
        user = self.__userRepository.get_user_by_s_id(s_id=login_details.s_id)
        if not user:  # בדיקה אם המשתמש קיים בDB
            raise HTTPException(status_code=400, detail="Please create an Account")

        # השוואת הסיסמה מול הhash השמור בDB
        if HashHelp.verify_password(
            plain_password=login_details.password, hashed_password=user.password
        ):
            # יצירת טוקן JWT עם פרטי המשתמש (UUID, role, s_id)
          
            access_token = AuthHand.generate_access_token(uuid=str(user.UUID), role=user.role, s_id=user.s_id)
            refresh_token = AuthHand.generate_refresh_token(uuid=str(user.UUID), session=self.session)

            if access_token and refresh_token:
                return UserLoginOutput(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    role=user.role,
                    responsible_access_level=getattr(user, "responsible_access_level", None),
                    can_audio=getattr(user, "can_audio", False) or False,
                    can_video=getattr(user, "can_video", False) or False,
                )  # החזרת הטוקן והתפקיד
            raise HTTPException(status_code=500, detail="Unable to process request")
        raise HTTPException(status_code=401, detail="Please check your Credentials")

    def _role_value(self, role) -> str:
        """עוזר - מחזיר את הערך הטקסטואלי של תפקיד (בין אם זה Enum או string)"""
        return getattr(role, "value", role)

    def get_all_users(
        self, current_user_role: str, current_user_uuid: str | None = None
    ) -> list[UserOutput]:
        """
        מחזיר את כל המשתמשים.
        אם המשתמש הנוכחי לא super_admin - מסתיר סופרים מהרשימה.
        """
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
        raise HTTPException(status_code=404, detail="User is not available")
    
    def get_user_by_uuid(self, uuid: str) -> User:
        user = self.__userRepository.get_user_by_uuid(uuid=uuid)
        if user:
            return user
        raise HTTPException(status_code=404, detail="User is not available")
    
    def get_user_by_s_id_for_requester(
        self, s_id: str, requester_role: str, requester_uuid: str
    ) -> User:
        user = self.get_user_by_s_id(s_id=s_id)

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
                responsible_access_level=getattr(user, "responsible_access_level", None),
                can_audio=getattr(user, "can_audio", False) or False,
                can_video=getattr(user, "can_video", False) or False,
                groups=[m.group_uuid for m in user.group_access_levels],
            )
        raise HTTPException(status_code=400, detail="User is not available")

    def delete_user(
        self, user_id: str, current_user_role: str, current_user_s_id: str
    ) -> bool:
        """
        מוחק משתמש עם בדיקות הרשאות:
        - רק admin או super_admin יכולים למחוק
        - לא ניתן למחוק את עצמך
        - admin לא יכול למחוק super_admin
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

    def _derive_responsible_access_level(self, user_data: UserInCreateNoRole) -> str:
        """מוודא שאדמין מוגדר עם סוג פגישה אחד בלבד ומחזיר אותו."""
        access_level = user_data.responsible_access_level
        if access_level:
            access_level = str(access_level).lower().strip()
            if access_level not in ("audio", "video", "blast_dial"):
                raise HTTPException(status_code=400, detail="Invalid responsible access level")
            return access_level

        if user_data.can_audio and user_data.can_video:
            raise HTTPException(status_code=400, detail="Admin can only have one meeting access type")
        if user_data.can_audio:
            return "audio"
        if user_data.can_video:
            return "video"
        raise HTTPException(status_code=400, detail="Admin must have a responsible access level")

    def create_agent_user(self, user_data: UserInCreateNoRole) -> UserOutput:
        """יוצר משתמש סוג agent - הסיסמה מוצפנת לפני שמירה"""
        hashed_password = HashHelp.get_password_hash(plain_password=user_data.password)
        user_data = user_data.model_copy(
            update={
                "password": hashed_password,
                "responsible_access_level": None,
                "can_audio": False,
                "can_video": False,
            }
        )
        user = self.__userRepository.create_agent_user(user_data=user_data)
        return UserOutput.model_validate(user, from_attributes=True)

    def create_admin_user(self, user_data: UserInCreateNoRole) -> UserOutput:
        """יוצר משתמש סוג admin - הסיסמה מוצפנת לפני שמירה"""
        access_level = self._derive_responsible_access_level(user_data)
        hashed_password = HashHelp.get_password_hash(plain_password=user_data.password)
        user_data = user_data.model_copy(
            update={
                "password": hashed_password,
                "responsible_access_level": access_level,
                "can_audio": access_level == "audio",
                "can_video": access_level == "video",
            }
        )
        user = self.__userRepository.create_admin_user(user_data=user_data)
        return UserOutput.model_validate(user, from_attributes=True)

    def get_group_meetings_by_user_uuid(
        self, user_uuid: str, group_uuid: str
    ) -> list[str]:
        """
        מחזיר רשימת פגישות שמשתמש רשאי לראות במדור.
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
