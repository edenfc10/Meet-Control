# ============================================================================
# Meeting models - זהות הפגישה חיה ב-CMS, לא ב-DB
# ============================================================================
# הפגישות עצמן (שם/מספר/סיסמה) מנוהלות אך ורק בשרת ה-CMS.
# ה-DB המקומי שומר רק נתונים שה-CMS לא מכיר:
#   - GroupMeeting: שיוך מדור<->פגישה לפי מספר פגישה (לא UUID)
#
# AccessLevel נשאר כאן כי הוא בשימוש רחב במערכת (audio/video/blast_dial).
# ============================================================================

from enum import Enum

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


# --- AccessLevel Enum - סוגי פגישות ---
class AccessLevel(str, Enum):
    audio = "audio"           # שיחת אודיו בלבד
    video = "video"           # שיחת וידאו
    blast_dial = "blast_dial" # חיוג המוני


# --- GroupMeeting - שיוך מדור<->פגישה לפי (מספר פגישה + סוג) ---
# מחליף את meeting_group_association הישן (שהיה לפי UUID).
# המזהה הייחודי של פגישה הוא (meeting_number, access_level) — כי אותו מספר
# יכול להתקיים גם בשרת audio וגם בשרת video (שני שרתי CMS נפרדים).
# PK מורכב => כל פגישה משויכת למדור אחד בלבד.
class GroupMeeting(Base):
    __tablename__ = "group_meeting"

    # מספר הפגישה (ה-URI ב-CMS)
    meeting_number = Column(String(15), primary_key=True)
    # סוג הפגישה / השרת: "audio" | "video"
    access_level = Column(String(10), primary_key=True)
    # המדור שהפגישה משויכת אליו
    group_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("groups.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group = relationship("Group", back_populates="meeting_links")
