# ============================================================================
# Protected Router - × ×ª×™×‘×™× ×ž×•×’× ×™× ×©×“×•×¨×©×™× JWT
# ============================================================================
# × ×ª×™×‘×™×:
#   GET /protected/me - ×ž×—×–×™×¨ ××ª ×¤×¨×˜×™ ×”×ž×©×ª×ž×© ×”×ž×—×•×‘×¨ (×œ×¤×™ ×”×˜×•×§×Ÿ)
#
# פונקצית get_current_user:
#   - ×ž×¤×¢× ×—×ª ××ª ×”×˜×•×§×Ÿ JWT ×ž×”-Authorization header
#   - ×ž×•×¦××ª ××ª ×”×ž×©×ª×ž×© ×ž×”DB ×œ×¤×™ ×”-s_id ×©×‘×˜×•×§×Ÿ
#   - ×ž×—×–×™×¨×” UserOutput ×¢× ×›×œ ×”×¤×¨×˜×™×
#   - ×–×” ×ž×” ×©×”×¤×¨×•× ×˜×× ×“ ×§×•×¨× ×œ×• ×‘×›×œ ×˜×¢×™× ×ª ×“×£ ×›×“×™ ×œ×“×¢×ª ×ž×™ ×”×ž×©×ª×ž×©
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

validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])

protectRouter = APIRouter()


@protectRouter.get("/me")
def get_protected_data(user: UserOutput = Depends(validator)):
    return {"message": "This is a protected route", "user": user}
