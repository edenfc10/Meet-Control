# ============================================================================
# FavoriteMeeting Model - User Favorites (UPDATED)
# ============================================================================
# Stores user-marked favorite meetings in the local database.
# Acts as a cache/local store for frequently-accessed meetings.
#
# Primary Key: UUID (record identifier)
# Composite Natural Key: (member_uuid, meeting_number, access_level)
#   - Ensures user can't favorite the same meeting twice
#
# Foreign Keys:
#   - member_uuid → users.UUID (CASCADE delete)
#   - (meeting_number, access_level) → meetings (CASCADE delete)
#
# Cascade Delete Behavior:
#   - If user is deleted → favorite is removed (via member_uuid FK)
#   - If meeting is deleted → favorite is removed (via composite FK)
#   - Result: No orphaned favorites possible
# ============================================================================

import uuid

from sqlalchemy import (
    Column, DateTime, ForeignKey, String, UniqueConstraint,
    ForeignKeyConstraint, func, Index
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class FavoriteMeeting(Base):
    __tablename__ = "favorite_meetings"
    __table_args__ = (
        UniqueConstraint(
            "member_uuid", "meeting_number", "access_level",
            name="uq_favorite_member_meeting"
        ),
        ForeignKeyConstraint(
            ["meeting_number", "access_level"],
            ["meetings.meeting_number", "meetings.access_level"],
            ondelete="CASCADE",
            name="fk_favorite_meeting_meeting"
        ),
        Index("ix_favorite_member", "member_uuid"),
        Index("ix_favorite_created", "created_at"),
    )

    # Record Identifier
    UUID = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique record ID"
    )

    # Foreign Keys
    member_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who favorited this meeting"
    )

    # Meeting Reference (Composite FK to meetings table)
    # Together these form a natural key that uniquely identifies the meeting
    meeting_number = Column(
        String(50),
        nullable=False,
        index=True,
        doc="CMS meeting URI (e.g., '5551234567')"
    )
    access_level = Column(
        String(10),
        nullable=False,
        doc="Meeting type: 'audio' or 'video'"
    )

    # Audit Trail
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="When this meeting was added to favorites"
    )

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------
    member = relationship(
        "User",
        doc="The user who marked this as favorite"
    )
    meeting = relationship(
        "Meeting",
        back_populates="favorites",
        foreign_keys=[meeting_number, access_level],
        doc="The meeting that is favorited"
    )

    def __repr__(self):
        return f"<FavoriteMeeting user={self.member_uuid} meeting={self.meeting_number}>"
