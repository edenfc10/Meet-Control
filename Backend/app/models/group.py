# ============================================================================
# Group Model - מודל המדור (קבוצה)
# ============================================================================
# ×ž×“×•×¨ (Group) = ×§×‘×•×¦×”/×™×—×™×“×” ××¨×’×•× ×™×ª.
# ×›×œ ×ž×“×•×¨ ×ž×›×™×œ ×—×‘×¨×™× (Users) ×•×¤×’×™×©×•×ª (Meetings).
# ×–×”×• ××•×‘×™×™×§×˜ ×”×œ×™×‘×” ×©×ž×—×‘×¨ ×‘×™×Ÿ ×ž×©×ª×ž×©×™× ×œ×¤×’×™×©×•×ª.
#
# ×§×©×¨×™×:
#   Group <-> MemberGroupAccess (One-to-Many - user-group relationship with access level)
#   Group <-> Meetings  (Many-to-Many via meeting_group_association)
# ============================================================================

from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


# --- Group Model - ×˜×‘×œ×ª ×”×ž×“×•×¨×™× ---
class Group(Base):
    __tablename__ = "groups"

    # ×ž×–×”×” ×™×™×—×•×“×™ ××•× ×™×‘×¨×¡×œ×™
    UUID = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # ×©× ×”×ž×“×•×¨ (×œ×ž×©×œ: "×ž×“×•×¨ ×ª×§×©×•×‘", "×ž×“×•×¨ ×ž×‘×¦×¢×™×")
    name = Column(String(50), nullable=False)

    # --- Relationships (×§×©×¨×™×) ---
    # ×—×‘×¨×™ ×”×ž×“×•×¨ - ×¨×©×™×ž×ª ×”×ž×©×ª×ž×©×™× ×©×©×™×™×›×™× ×œ×ž×“×•×¨

    # פגישות המדור - שיוכים לפי מספר פגישה (GroupMeeting)
    meeting_links = relationship(
        "GroupMeeting", back_populates="group", cascade="all, delete-orphan"
    )

    @property
    def meeting_numbers(self):
        """רשימת מספרי הפגישות המשויכות למדור."""
        return [link.meeting_number for link in self.meeting_links]
    # ×¨×ž×•×ª ×’×™×©×” - ×ž×’×“×™×¨ ××™×–×• ×¨×ž×ª ×’×™×©×” ×œ×›×œ ×—×‘×¨ ×‘×ž×“×•×¨
    member_access_levels = relationship(
        "MemberGroupAccess", back_populates="group", cascade="all, delete-orphan"
    )
