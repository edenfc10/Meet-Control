# ============================================================================
# MemberGroupAccess Model - רמת גישה של חבר למדור
# ============================================================================
# טבלה זו מגדירה איזו רמת גישה יש לכל משתמש בכל מדור.
# זה מאפשר שליטה פרטנית: משתמש א' יכול לראות רק פגישות אודיו במדור מסוים,
# אבל משתמש ב' יכול לראות גם וידאו באותו מדור.
#
# Composite Primary Key (מפתח מורכב):
#   (member_uuid, group_uuid, access_level)
#   -> בפועל נשמרת רשומה אחת לכל שיוך (מחליפים את הקודם בכל עדכון)
#
# הזרימה:
#   1. Admin מוסיף agent למדור עם רמת גישה (audio/video/blast_dial/voice)
#   2. הרמה נשמרת בטבלה הזו
#   3. כשהagent נכנס לדף הפגישות, הfrontend בודק את הרמה ומציג בהתאם
# ============================================================================

from enum import Enum
from datetime import datetime

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- MemberGroupAccessLevel Enum - רמות גישה אפשריות ---
# voice = גישה לקולית בלבד
# audio = גישה לפגישות אודיו
# video = גישה לפגישות וידאו
# blast_dial = גישה לחיוג המוני
class MemberGroupAccessLevel(str, Enum):
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"


# --- MemberGroupAccess Model - טבלת הרשאות חבר-מדור ---
class MemberGroupAccess(Base):
    __tablename__ = "member_group_access"

    # UUID של המשתמש (FK לטבלת users)
    member_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    # UUID של המדור (FK לטבלת groups)
    group_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("groups.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    # רמת הגישה שמוגדרת למשתמש הזה במדור הזה
    access_level = Column(SqlEnum(MemberGroupAccessLevel), primary_key=True)

    # --- Relationships (קשרים) ---
    # Audit Trail (OPTIONAL - for compliance and debugging)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="When this access was granted"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp"
    )

    # --- Relationships ---
    member = relationship(
        "User", back_populates="group_access_levels"
    )
    group = relationship(
        "Group", back_populates="member_access_levels"
    )
