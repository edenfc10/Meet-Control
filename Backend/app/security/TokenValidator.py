# ============================================================================
# TokenValidator - בודק טוקן והרשאות תפקיד
# ============================================================================
# FastAPI Dependency שמשמש כ-middleware לאימות:
#   1. מפענח את הJWT token מה-header
#   2. בודק שהטוקן תקין ולא פג תוקף
#   3. בודק שהתפקיד של המשתמש מתאים לנתיב
#   4. בודק שהמשתמש עדיין קיים בDB
#
# שימוש:
#   allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
#   @router.get("/endpoint", dependencies=[Depends(allow_admins_only)])
# ============================================================================

import time

from fastapi import Request, HTTPException, Depends
from fastapi import Request, Cookie
from app.models.used_refresh_token import UsedRefreshToken

from app.core.database import get_db
from app.models.user import User
from app.security.auth import AuthHand
from sqlalchemy.orm import Session
from logger import LoggerManager
from typing import Annotated


class TokenValidator:
    """בודק טוקן JWT ומוודא שהתפקיד של המשתמש מורשה"""

    def __init__(self, allowed_roles: list[str], allow_theirs_only: bool = False):
        self.allowed_roles = allowed_roles  # רשימת התפקידים המותרים
        self.allow_theirs_only = allow_theirs_only

    async def __call__(
        self, access_token: str = Cookie(default=None), refresh_token: str = Cookie(default=None), db: Session = Depends(get_db)
    ):
        """נקרא אוטומטית על ידי FastAPI בכל endpoint שמשתמש ב-Depends"""
        
        if not access_token:
            LoggerManager.get_logger().warning("Missing access token")
            raise HTTPException(
                status_code=401, 
                detail="Authentication required. Please login again."
            )

        payload = AuthHand.decode_jwt(access_token)
        
        if not payload:
            LoggerManager.get_logger().warning(
                "Invalid or expired access token: %s", access_token[:20] + "..."
            )
            raise HTTPException(status_code=401, detail="Session expired. Please login again.")

        # בדיקת refresh token אופציונלית - רק אם קיים
        if refresh_token:
            refresh_payload = AuthHand.decode_jwt(refresh_token)
            if not refresh_payload:
                LoggerManager.get_logger().warning("Invalid or expired refresh token")
                raise HTTPException(status_code=401, detail="Session expired. Please login again.")

            jti = refresh_payload.get("jti")
            if not jti:
                LoggerManager.get_logger().error("Refresh token missing JTI")
                raise HTTPException(status_code=401, detail="Invalid session. Please login again.")

            db_session_record = db.query(UsedRefreshToken).filter_by(jti=jti).first()
            if not db_session_record:
                LoggerManager.get_logger().error(f"Access denied: JTI {jti} not found in whitelist")
                raise HTTPException(status_code=401, detail="Session is no longer active. Please login again.")

        # שלב 2: שליפת פרטי המשתמש מהטוקן
        user_role = payload.get("role")
        user_UUID = payload.get("UUID")
        user_s_id = payload.get("s_id")

        # שלב 3: בדיקה שהמשתמש קיים בDB
        user = db.query(User).filter_by(UUID=user_UUID).first()
        if not user:
            LoggerManager.get_logger().warning("User not found in DB: %s", user_UUID)
            raise HTTPException(status_code=404, detail="User not exists")

        # שלב 4: בדיקה שהתפקיד מותר לנתיב הזה
        if user_role not in self.allowed_roles:
            LoggerManager.get_logger().warning(
                "User %s:%s with role %s not allowed to access this endpoint",
                user_s_id,
                user_UUID,
                user_role,
            )
            raise HTTPException(
                status_code=403, detail="You do not have the required permissions"
            )

        return user
