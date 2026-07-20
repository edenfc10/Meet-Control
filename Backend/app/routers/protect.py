# ============================================================================
# Protected Router - נתיבים מוגנים שדורשים JWT
# ============================================================================
# נתיבים:
#   GET /protected/me - מחזיר את פרטי המשתמש המחובר (לפי הטוקן)
#
# פונקצית get_current_user:
#   - מפענחת את הטוקן JWT מה-Authorization header
#   - מוצאת את המשתמש מהDB לפי ה-s_id שבטוקן
#   - מחזירה UserOutput עם כל הפרטים
#   - זה מה שהפרונטאנד קורא לו בכל טעינת דף כדי לדעת מי המשתמש
# ============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import Any
from app.security.auth import AuthHand
from app.service.userService import UserService
from app.core.database import get_db
from app.schema.user import UserOutput


from fastapi import APIRouter
from app.security.TokenValidator import TokenValidator
from app.models.user import User

validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])

protectRouter = APIRouter()


@protectRouter.get("/me")
def get_protected_data(user=Depends(validator)):
    return {"message": "This is a protected route", "user": UserOutput.model_validate(user)}
