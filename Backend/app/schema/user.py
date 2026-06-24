# ============================================================================
# User Schemas (Pydantic) - ×¡×›×ž×•×ª ×§×œ×˜/×¤×œ×˜ ×œ×ž×©×ª×ž×©×™× ×•×ž×“×•×¨×™×
# ============================================================================
# ×§×•×‘×¥ ×–×” ×ž×’×“×™×¨ ××ª ×›×œ ×”×ž×•×“×œ×™× (DTOs) ×©×œ Pydantic ×œ×•×œ×™×“×¦×™×” ×•×¡×¨×™××œ×™×–×¦×™×”.
# ×”× ×ž×©×ž×©×™× ×œ:
#   1. ולידציה של קלט מהלקוח (request body)
#   2. פורמט התשובה ללקוח (response_model)
#   3. ××•×‘×™×™×§×˜×™ ×”×¢×‘×¨×” ×¤× ×™×ž×™×™× ×‘×™×Ÿ ×”×©×›×‘×•×ª
#
# המנהג ConfigDict:
#   - extra="forbid" -> ×—×•×¡× ×©×“×•×ª × ×•×¡×¤×™× ×‘×§×œ×˜ (×ž× ×™×¢×ª ×”×–×¨×§×”)
#   - from_attributes=True -> ×ž××¤×©×¨ ×”×ž×¨×” ×©×œ ORM objects ×œ-Pydantic
# ============================================================================

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from uuid import UUID
from app.models.member_group_access import MemberGroupAccessLevel


# --- UserRole Enum (שכבת Schema) ---
# שכפול של ה-Enum מהמודל לשימוש ב-Pydantic schemas
class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    agent = "agent"
    viewer = "viewer"

    model_config = ConfigDict(use_enum_values=True)  # ×©×•×ž×¨ ××ª ×”×¢×¨×š ×”×˜×§×¡×˜×•××œ×™ ×•×œ× ××ª ×”××•×‘×™×™×§×˜


# --- GroupInCreate - קלט ליצירת מדור ---
class GroupInCreate(BaseModel):
    name: str  # ×©× ×”×ž×“×•×¨ ×”×—×“×©
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- GroupInUpdate - קלט לעדכון מדור ---
class GroupInUpdate(BaseModel):
    name: Optional[str] = None  # ××•×¤×¦×™×•× ×œ×™ - ××¤×©×¨ ×œ×¢×“×›×Ÿ ×¨×§ ××ª ×ž×” ×©×¨×œ×•×•× ×˜×™

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- MemberAccessOutput - פלט רמת גישה של חבר ---
# ×ž×™×™×¦×’ ××ª ×”×¨×ž×” ×©×œ ×›×œ ×ž×©×ª×ž×© ×‘×ª×•×š ×ž×“×•×¨ ×ž×¡×•×™×
class MemberAccessOutput(BaseModel):
    user_id: UUID                          # UUID של המשתמש
    access_level: MemberGroupAccessLevel   # רמת הגישה שלו במדור

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- GroupOutput - ×¤×œ×˜ ×©×œ ×ž×“×•×¨ ×ž×œ× ---
# ×–×” ×ž×” ×©×—×•×–×¨ ×œ×œ×§×•×— ×›×©×©×•××œ×™× ×ž×™×“×¢ ×¢×œ ×ž×“×•×¨
class GroupOutput(BaseModel):
    UUID: UUID                                                                     # מזהה המדור
    name: str                                                                      # ×©× ×”×ž×“×•×¨
    members: Optional[List[UUID]] = Field(default_factory=list)                    # ×¨×©×™×ž×ª UUIDs ×©×œ ×”×—×‘×¨×™×
    meetings: Optional[List[UUID]] = Field(default_factory=list)                   # רשימת UUIDs של הפגישות
    member_access_levels: Optional[List[MemberAccessOutput]] = Field(default_factory=list)  # רמות גישה לכל חבר


    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserInCreate - ×§×œ×˜ ×œ×™×¦×™×¨×ª ×ž×©×ª×ž×© (×¢× ×ª×¤×§×™×“) ---
class UserInCreate(BaseModel):
    s_id: str                                              # מזהה משתמש (כמו מספר עובד)
    username: str                                          # ×©× ×ª×¦×•×’×”
    password: str                                          # סיסמה (תוצפן לפני שמירה)
    role: UserRole                                         # תפקיד (super_admin/admin/agent)
    group_ids: Optional[List[UUID]] = Field(default_factory=list)  # ×ž×“×•×¨×™× ×œ×©×™×•×š (××•×¤×¦×™×•× ×œ×™)

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserInCreateNoRole - קלט לעדכון משתמש (role אופציונלי) ---
class UserInCreateNoRole(BaseModel):
    s_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    group_ids: Optional[List[UUID]] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserOutput - פלט של משתמש ---
# ×–×” ×ž×” ×©×—×•×–×¨ ×œ×œ×§×•×— - ×œ×¢×•×œ× ×œ× ×›×•×œ×œ ×¡×™×¡×ž×”!
class UserOutput(BaseModel):
    UUID: UUID
    s_id: str
    username: str
    role: UserRole
    groups: Optional[List[UUID]] = Field(default_factory=list)  # ×¨×©×™×ž×ª UUIDs ×©×œ ×”×ž×“×•×¨×™×

    # ×•×œ×™×“×˜×•×¨ ×ž×•×ª×× ××™×©×™×ª - ×ž×ž×™×¨ ××•×‘×™×™×§×˜×™ Group ×œ-UUID ×‘×œ×‘×“
    # × ×“×¨×© ×›×™ SQLAlchemy ×ž×—×–×™×¨ ××•×‘×™×™×§×˜×™× ×ž×œ××™× ×•×œ× UUIDs
    @field_validator('groups', mode='before')
    @classmethod
    def extract_group_uuids(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [getattr(group, 'UUID', group) for group in v]
        return v

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- BoolOutput - ×ª×©×•×‘×” ×‘×•×•×œ×™×× ×™×ª ×¤×©×•×˜×” ---
# משמש לפעולות כמו מחיקה - הצליח/נכשל
class BoolOutput(BaseModel):
    success: bool
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# עדכון הפניות קדימה (forward references) - נדרש ל-Pydantic v2
UserOutput.model_rebuild()


# --- UserInLogin - קלט להתחברות ---
class UserInLogin(BaseModel):
    s_id: str       # מזהה משתמש
    password: str   # סיסמה (תושווה מול hash בDB)
    model_config = ConfigDict(extra="forbid", from_attributes=True)

# --- UserJWTData - מידע שנשמר בתוך הטוקן JWT ---
# המידע הזה מוצפן בתוך ה-payload של הטוקן

class LoginResponse(BaseModel):
    s_id: str
    role: UserRole
    message: str
    
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    
class UserLoginOutput(BaseModel):
    access_token: str
    refresh_token: str
    role: UserRole
    
    model_config = ConfigDict(extra="forbid", from_attributes=True)

class TokenType(str, Enum):
    access = "access"
    refresh = "refresh"

class AccessTokenData(BaseModel):
    UUID: str
    role: UserRole
    s_id: str
    iat: int
    exp: int
    type: TokenType
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    
class RefreshTokenData(BaseModel):
    UUID: str
    jti: str = Field(default_factory=lambda: str(UUID.uuid4()))  # מזהה ייחודי לטוקן
    iat: int
    exp: int
    type: TokenType
    model_config = ConfigDict(extra="forbid", from_attributes=True)

# --- UserToken - תשובת התחברות ---
# ×—×•×–×¨ ×œ×œ×§×•×— ××—×¨×™ login ×ž×•×¦×œ×—


# --- UserWithToken - ×ž×©×ª×ž×© ×ž×œ× + ×˜×•×§×Ÿ ---
# ×ž×¨×—×™×‘ ××ª UserOutput ×•×ž×•×¡×™×£ ×˜×•×§×Ÿ
class UserWithToken(UserOutput):
    token: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)

