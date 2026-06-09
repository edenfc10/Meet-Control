# ============================================================================
# Auth Router - נתיבי אימות (Login)
# ============================================================================
# נתיב אחד בלבד: POST /auth/login
# מקבל מהלקוח s_id + סיסמה, מחזיר JWT token + תפקיד.
# זה הנתיב היחיד שלא דורש אימות - כל שאר הנתיבים דורשים token.
# ============================================================================

import os
from ast import Dict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Cookie, HTTPException
from app.schema.user import UserInLogin
from app.core.database import get_db  # יוצרת חיבור לבסיס הנתונים
from sqlalchemy.orm import Session  # ביצוע פעולות על הDB

from fastapi import Response
from app.security.TokenValidator import TokenValidator
from app.service.userService import UserService
from app.security.auth import (
    AuthHand,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import User
from app.models.used_refresh_token import UsedRefreshToken
from app.schema.user import AccessTokenData, RefreshTokenData
from app.schema.user import LoginResponse

authRouter = APIRouter()  # יצירת Router לנתיבי auth
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])


def _cookie_settings() -> dict:
    cookie_secure_env = os.getenv("COOKIE_SECURE")
    if cookie_secure_env is None:
        app_env = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()
        secure = app_env in {"prod", "production"}
    else:
        secure = cookie_secure_env.lower() == "true"

    return {
        "httponly": True,
        "samesite": "none" if secure else "lax",
        "secure": secure,
        "path": "/",
    }


# --- POST /auth/login ---
# מקבל: { s_id: string, password: string }
# מחזיר: { token: string, role: string }
@authRouter.post("/login", status_code=200)
def login(
    loginDetails: UserInLogin,
    session: Session = Depends(get_db),
    response: Response = LoginResponse,
):
    try:
        result = UserService(session=session).login(login_details=loginDetails)
        cookie_settings = _cookie_settings()
        # Set the JWT token as a cookie
        if (
            response is not None
            and result
            and hasattr(result, "access_token")
            and hasattr(result, "refresh_token")
        ):
            response.set_cookie(
                key="access_token",
                value=result.access_token,
                **cookie_settings,
            )
            response.set_cookie(
                key="refresh_token",
                value=result.refresh_token,
                **cookie_settings,
            )
        return {"message": "Login successful", "role": result.role, "s_id": loginDetails.s_id}
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500, detail="Internal Server Error - Login failed"
        )


@authRouter.post("/logout", status_code=200)
def logout(response: Response, user=Depends(validator)):
    cookie_settings = _cookie_settings()
    # Clear the access_token and refresh_token cookies by setting them to expire in the past
    response.delete_cookie(key="access_token", **cookie_settings)
    response.delete_cookie(key="refresh_token", **cookie_settings)
    return {"detail": "Logged out successfully"}


@authRouter.post("/refresh", status_code=200)
def refresh_access_token(
    response: Response,
    refresh_token: str = Cookie(default=None),
    session: Session = Depends(get_db),
):
    try:
        cookie_settings = _cookie_settings()

        payload = AuthHand.decode_jwt(refresh_token)
        
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        jti = payload.get("jti") if payload else None
        user_uuid = payload.get("UUID")
        
        db_token = session.query(UsedRefreshToken).filter_by(jti=jti).first()
        
        if not db_token:
           session.query(UsedRefreshToken).filter_by(user_uuid=user_uuid).delete()
           session.commit()
           raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = session.query(User).filter_by(UUID=user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not exists")

        new_access_token = AuthHand.generate_access_token(
            uuid=str(user_uuid), role=user.role, s_id=user.s_id
        )
        new_refresh_token = AuthHand.generate_refresh_token(uuid=str(user_uuid), session=session)

        if not new_access_token or not new_refresh_token:
            raise HTTPException(status_code=500, detail="Failed to generate new tokens")
        
        session.delete(db_token)
        session.commit()

        response.set_cookie(
            key="access_token", value=new_access_token, **cookie_settings
        )
        response.set_cookie(
            key="refresh_token", value=new_refresh_token, **cookie_settings
        )

        return {"detail": "Tokens refreshed"}

    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=500, detail="Internal Server Error - Token refresh failed"
        )
