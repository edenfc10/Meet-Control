import jwt
from dotenv import load_dotenv
import time
import os

from app.schema.user import UserJWTData

load_dotenv()  # Loads from current working directory or parent directories

#קריאת המשתנים מהקובץ ENV
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

class AuthHand(object):

    @staticmethod #יצירת טוקן
    def sign_jwt(jwt_data: UserJWTData) -> str:
        payload = {
            "UUID": jwt_data.UUID,
            "role": jwt_data.role,
            "s_id": jwt_data.s_id,
            "expires": time.time() + 60 * 60 * 24  # הטוקן יהיה בתוקף ל-24 שעות
        }

        token = jwt.encode(payload , JWT_SECRET , algorithm = JWT_ALGORITHM) # יצירת הטוקן
        return token
    
    @staticmethod
    def decode_jwt(token:str) -> dict:  #פונקציה לפענוח הטוקן
        try:
            decoded_token = jwt.decode(token ,JWT_SECRET , algorithms=[JWT_ALGORITHM])
            return decoded_token if decoded_token["expires"] >= time.time() else None
        except:
           print("enable to decode the token")
           return None