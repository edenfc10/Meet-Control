# ============================================================================
# Meeting Schemas (Pydantic) - סכמות קלט/פלט לפגישות
# ============================================================================
#   - MeetingRole: סוג הפגישה (audio/video/blast_dial)
#   - MeetingInCreate: קלט יצירה
#   - MeetingInUpdate: עדכון פגישה
#   - MeetingOutput: תשובה ללקוח
# ============================================================================

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# --- MeetingRole Enum ---
class MeetingRole(str, Enum):
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"

    model_config = ConfigDict(use_enum_values=True)


# --- MeetingInCreate - קלט ליצירת פגישה חדשה ---
class MeetingInCreate(BaseModel):
    m_number: str
    name: str                              # שם הפגישה
    accessLevel: MeetingRole               # סוג הפגישה
    password: Optional[str] = None         # סיסמה לפגישה (אופציונלי)


# --- MeetingInUpdate - קלט לעדכון פגישה ---
class MeetingInUpdate(BaseModel):
    m_number: Optional[str] = None
    name: Optional[str] = None
    accessLevel: Optional[MeetingRole] = None
    password: Optional[str] = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class MeetingPasswordUpdate(BaseModel):
    password: Optional[str] = None

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- MeetingOutput ---
class MeetingOutput(BaseModel):
    UUID: UUID
    m_number: str
    name: Optional[str] = None
    accessLevel: MeetingRole
    password: Optional[str] = None
    groups: Optional[List[UUID]] = Field(default_factory=list)
    participant_count: int = 0
   

    model_config = ConfigDict(extra="forbid", from_attributes=True)


