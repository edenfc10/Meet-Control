# ============================================================================
# Group Model - מודל המדור (קבוצה)
# ============================================================================
# מדור (Group) = קבוצה/יחידה ארגונית.
# כל מדור מכיל חברים (Users) ופגישות (Meetings).
# זהו אובייקט הליבה שמחבר בין משתמשים לפגישות.
#
# קשרים:
#   Group <-> MemberGroupAccess (One-to-Many - user-group relationship with access level)
#   Group <-> Meetings  (Many-to-Many via meeting_group_association)
# ============================================================================

from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


# --- Group Model - טבלת המדורים ---
class Group(Base):
    __tablename__ = "groups"

    # מזהה ייחודי אוניברסלי
    UUID = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # שם המדור (למשל: "מדור תקשוב", "מדור מבצעים")
    name = Column(String(50), nullable=False)

    # --- Relationships (קשרים) ---
    # חברי המדור - רשימת המשתמשים ששייכים למדור

    # פגישות המדור - שיוכים לפי מספר פגישה (GroupMeeting)
    meeting_links = relationship(
        "GroupMeeting",
        back_populates="group",
        cascade="all, delete-orphan",
        doc="Meetings linked to this department; cascade deletes on group removal"
    )

    @property
    def meeting_numbers(self):
        """רשימת מפתחות פגישות בפורמט 'meeting_number:access_level' למניעת כפילויות."""
        return [f"{link.meeting_number}:{link.access_level}" for link in self.meeting_links]
    # רמות גישה - מגדיר איזו רמת גישה לכל חבר במדור
    member_access_levels = relationship(
        "MemberGroupAccess", back_populates="group", cascade="all, delete-orphan"
    )
