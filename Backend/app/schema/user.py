# ============================================================================
# User Schemas (Pydantic) - סכמות קלט/פלט למשתמשים ומדורים
# ============================================================================
# קובץ זה מגדיר את כל המודלים (DTOs) של Pydantic לולידציה וסריאליזציה.
# הם משמשים ל:
#   1. ולידציה של קלט מהלקוח (request body)
#   2. פורמט התשובה ללקוח (response_model)
#   3. אובייקטי העברה פנימיים בין השכבות
#
# המנהג ConfigDict:
#   - extra="forbid" -> חוסם שדות נוספים בקלט (מניעת הזרקה)
#   - from_attributes=True -> מאפשר המרה של ORM objects ל-Pydantic
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

    model_config = ConfigDict(use_enum_values=True)  # שומר את הערך הטקסטואלי ולא את האובייקט


# --- GroupInCreate - קלט ליצירת מדור ---
class GroupInCreate(BaseModel):
    name: str  # שם המדור החדש
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- GroupInUpdate - קלט לעדכון מדור ---
class GroupInUpdate(BaseModel):
    name: Optional[str] = None  # אופציונלי - אפשר לעדכן רק את מה שרלוונטי

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- MemberAccessOutput - פלט רמת גישה של חבר ---
# מייצג את הרמה של כל משתמש בתוך מדור מסוים
class MemberAccessOutput(BaseModel):
    user_id: UUID                          # UUID של המשתמש
    access_level: MemberGroupAccessLevel   # רמת הגישה שלו במדור

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- GroupOutput - פלט של מדור מלא ---
# זה מה שחוזר ללקוח כששואלים מידע על מדור
class GroupOutput(BaseModel):
    UUID: UUID                                                                     # מזהה המדור
    name: str                                                                      # שם המדור
    members: Optional[List[UUID]] = Field(default_factory=list)                    # רשימת UUIDs של החברים
    meetings: Optional[List[str]] = Field(default_factory=list)                    # רשימת מספרי הפגישות המשויכות
    member_access_levels: Optional[List[MemberAccessOutput]] = Field(default_factory=list)  # רמות גישה לכל חבר


    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserInCreate - קלט ליצירת משתמש (עם תפקיד) ---
class UserInCreate(BaseModel):
    s_id: str                                              # מזהה משתמש (כמו מספר עובד)
    username: str                                          # שם תצוגה
    password: str                                          # סיסמה (תוצפן לפני שמירה)
    role: UserRole                                         # תפקיד (super_admin/admin/agent)
    group_ids: Optional[List[UUID]] = Field(default_factory=list)  # מדורים לשיוך (אופציונלי)
    responsible_access_level: Optional[str] = None
    can_audio: bool = False
    can_video: bool = False

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserInCreateNoRole - קלט לעדכון משתמש (role אופציונלי) ---
class UserInCreateNoRole(BaseModel):
    s_id: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    group_ids: Optional[List[UUID]] = Field(default_factory=list)
    responsible_access_level: Optional[str] = None
    can_audio: Optional[bool] = None
    can_video: Optional[bool] = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- UserOutput - פלט של משתמש ---
# זה מה שחוזר ללקוח - לעולם לא כולל סיסמה!
class UserOutput(BaseModel):
    UUID: UUID
    s_id: str
    username: str
    role: UserRole
    responsible_access_level: Optional[str] = None
    can_audio: bool = False
    can_video: bool = False
    groups: Optional[List[UUID]] = Field(default_factory=list)  # רשימת UUIDs של המדורים

    # ולידטור מותאם אישית - ממיר אובייקטי Group ל-UUID בלבד
    # נדרש כי SQLAlchemy מחזיר אובייקטים מלאים ולא UUIDs
    @field_validator('groups', mode='before')
    @classmethod
    def extract_group_uuids(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [getattr(group, 'UUID', group) for group in v]
        return v

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- BoolOutput - תשובה בווליאנית פשוטה ---
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
    responsible_access_level: Optional[str] = None
    can_audio: bool = False
    can_video: bool = False

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
# חוזר ללקוח אחרי login מוצלח


# --- UserWithToken - משתמש מלא + טוקן ---
# מרחיב את UserOutput ומוסיף טוקן
class UserWithToken(UserOutput):
    token: str

    model_config = ConfigDict(extra="forbid", from_attributes=True)


