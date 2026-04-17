# ============================================================================
# Meeting Schemas (Pydantic) - סכמות קלט/פלט לפגישות
# ============================================================================
# ×§×•×‘×¥ ×–×” ×ž×’×“×™×¨ ××ª ×›×œ ×”×¡×›×ž×•×ª ×©×§×©×•×¨×•×ª ×œ×¤×’×™×©×•×ª:
#   - MeetingRole: סוג הפגישה (audio/video/blast_dial)
#   - MeetingInCreate: קלט יצירה
#   - MeetingInUpdate: ×§×œ×˜ ×¢×“×›×•×Ÿ (×›×œ ×”×©×“×•×ª ××•×¤×¦×™×•× ×œ×™×•×ª)
#   - MeetingOutput: תשובה ללקוח
# ============================================================================

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from uuid import UUID


# --- MeetingRole Enum - סוג פגישה ---
# ×ž×’×“×™×¨ ××™×–×• ×¡×•×’ ×¤×’×™×©×” × ×™×ª×Ÿ ×œ×™×¦×•×¨
class MeetingRole(str, Enum):
    audio = "audio"           # ×¤×’×™×©×ª ××•×“×™×•
    video = "video"           # ×¤×’×™×©×ª ×•×™×“××•
    blast_dial = "blast_dial" # חיוג המוני

    model_config = ConfigDict(use_enum_values=True)


# --- MeetingInCreate - קלט ליצירת פגישה חדשה ---
class MeetingInCreate(BaseModel):
    m_number: str                          # מספר הפגישה (למשל "891234")
    accessLevel: MeetingRole               # סוג הפגישה
    password: Optional[str] = None         # סיסמה לפגישה (אופציונלי)


# --- MeetingInUpdate - קלט לעדכון פגישה ---
# ×›×œ ×”×©×“×•×ª ××•×¤×¦×™×•× ×œ×™×•×ª - ×ž××¤×©×¨ ×¢×“×›×•×Ÿ ×—×œ×§×™
class MeetingInUpdate(BaseModel):
    m_number: Optional[str] = None           # ×ž×¡×¤×¨ ×¤×’×™×©×” ×—×“×© (××•×¤×¦×™×•× ×œ×™)
    accessLevel: Optional[MeetingRole] = None  # ×¡×•×’ ×—×“×© (××•×¤×¦×™×•× ×œ×™)
    password: Optional[str] = None           # ×¡×™×¡×ž×” ×—×“×©×” (××•×¤×¦×™×•× ×œ×™)

    model_config = ConfigDict(extra="forbid", from_attributes=True)


# --- MeetingOutput - ×¤×œ×˜ ×¤×’×™×©×” ×ž×œ× ---
# ×–×” ×ž×” ×©×”×œ×§×•×— ×ž×§×‘×œ ×—×–×¨×” ×›×©×©×•××œ ×¢×œ ×¤×’×™×©×”
class MeetingOutput(BaseModel):
    UUID: UUID                                                   # מזהה הפגישה
    m_number: str                                                # מספר הפגישה
    accessLevel: MeetingRole                                     # סוג הפגישה
    password: Optional[str] = None                               # ×¡×™×¡×ž×ª ×”×•×•×¢×™×“×” (×× ×§×™×™×ž×ª)
    groups: Optional[List[UUID]] = Field(default_factory=list)   # ×¨×©×™×ž×ª ×”×ž×“×•×¨×™× ×©×”×¤×’×™×©×” ×©×™×™×›×ª ××œ×™×”×
   

    model_config = ConfigDict(extra="forbid", from_attributes=True)


