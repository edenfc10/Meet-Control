# ============================================================================
# JWT Authentication Handler - יצירה ופיענוח טוקנים
# ============================================================================
# מנהל את יצירה ופיענוח של JWT tokens.
# הטוקן מכיל: UUID, תפקיד, s_id, וזמן תפוגה (24 שעות).
# הסוד והאלגוריתם נטענים ממשתני סביבה (.env).
# ============================================================================

from datetime import datetime, timedelta, timezone
import time
from typing import Union
import uuid as uuid_g

from fastapi import Depends
import jwt
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schema.user import AccessTokenData, RefreshTokenData, UserRole
from app.models.used_refresh_token import UsedRefreshToken

load_dotenv()

# קריאת משתני הסביבה לחתימת JWT
JWT_SECRET = os.getenv("JWT_SECRET")      # מפתח סודי לחתימה
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")  # אלגוריתם הצפנה (HS256)


REFRESH_TOKEN_EXPIRE_DAYS = 7
ACCESS_TOKEN_EXPIRE_MINUTES = 15

class AuthHand(object):

    @staticmethod
    def sign_jwt(jwt_data: Union[AccessTokenData, RefreshTokenData]) -> str:
        payload = jwt_data.model_dump()  # המרת Pydantic model ל-dict רגיל
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_jwt(token: str) -> dict | None:
        """ מפענח טוקן JWT ומחזיר את התוכן. מחזיר None אם לא תקין/פג תוקף. """
        try:
            decoded_token = jwt.decode(token ,JWT_SECRET , algorithms=[JWT_ALGORITHM])
            return decoded_token
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        
        except Exception as error:
            # טיפול בשגיאות כלליות (לוג)
            return None
        
    @staticmethod
    def generate_access_token(uuid: str, role: UserRole, s_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "UUID": uuid,
            "role": role,
            "s_id": s_id,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
            "type": "access"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def generate_refresh_token(uuid: str, session: Session) -> str:
        now = datetime.now(timezone.utc)
        
        exp = int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
        
        jti_row = UsedRefreshToken(
            user_uuid=uuid,
            jti=str(uuid_g.uuid4()),  # מזהה ייחודי לטוקן
            expires_at=int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp())
        )
        
        session.add(jti_row)
        session.commit()
        
        payload = {
            "UUID": uuid,
            "jti": jti_row.jti,  # מזהה ייחודי לטוקן
            "iat": int(now.timestamp()),
            "exp": exp,
            "type": "refresh"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)