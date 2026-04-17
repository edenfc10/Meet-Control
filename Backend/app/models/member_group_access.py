# ============================================================================
# MemberGroupAccess Model - רמת גישה של חבר למדור
# ============================================================================
# ×˜×‘×œ×” ×–×• ×ž×’×“×™×¨×” ××™×–×• ×¨×ž×ª ×’×™×©×” ×™×© ×œ×›×œ ×ž×©×ª×ž×© ×‘×›×œ ×ž×“×•×¨.
# ×–×” ×ž××¤×©×¨ ×©×œ×™×˜×” ×¤×¨×˜× ×™×ª: ×ž×©×ª×ž×© ×' ×™×›×•×œ ×œ×¨××•×ª ×¨×§ ×¤×’×™×©×•×ª ××•×“×™×• ×‘×ž×“×•×¨ ×ž×¡×•×™×,
# ××‘×œ ×ž×©×ª×ž×© ×‘' ×™×›×•×œ ×œ×¨××•×ª ×’× ×•×™×“××• ×‘××•×ª×• ×ž×“×•×¨.
#
# Composite Primary Key (מפתח מורכב):
#   (member_uuid, group_uuid, access_level)
#   -> ×‘×¤×•×¢×œ × ×©×ž×¨×ª ×¨×©×•×ž×” ××—×ª ×œ×›×œ ×©×™×•×š (×ž×—×œ×™×¤×™× ××ª ×”×§×•×“× ×‘×›×œ ×¢×“×›×•×Ÿ)
#
# הזרימה:
#   1. Admin ×ž×•×¡×™×£ agent ×œ×ž×“×•×¨ ×¢× ×¨×ž×ª ×’×™×©×” (audio/video/blast_dial/voice)
#   2. הרמה נשמרת בטבלה הזו
#   3. ×›×©×”agent × ×›× ×¡ ×œ×“×£ ×”×¤×’×™×©×•×ª, ×”frontend ×‘×•×“×§ ××ª ×”×¨×ž×” ×•×ž×¦×™×’ ×‘×”×ª××
# ============================================================================

from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- MemberGroupAccessLevel Enum - ×¨×ž×•×ª ×’×™×©×” ××¤×©×¨×™×•×ª ---
# voice = גישה לקולית בלבד
# audio = ×’×™×©×” ×œ×¤×’×™×©×•×ª ××•×“×™×•
# video = ×’×™×©×” ×œ×¤×’×™×©×•×ª ×•×™×“××•
# blast_dial = גישה לחיוג המוני
class MemberGroupAccessLevel(str, Enum):
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"


# --- MemberGroupAccess Model - ×˜×‘×œ×ª ×”×¨×©××•×ª ×—×‘×¨-×ž×“×•×¨ ---
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

    # --- Relationships (×§×©×¨×™×) ---
    member = relationship(
        "User", back_populates="group_access_levels"
    )  # חזרה למשתמש
    group = relationship(
        "Group", back_populates="member_access_levels"
    )  # חזרה למדור
