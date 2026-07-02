# ============================================================================
# Meeting Models - Hybrid Meeting Management
# ============================================================================
# This file defines the core meeting entities:
#
# 1. AccessLevel Enum - Types of meetings (audio/video/blast_dial)
# 2. Meeting - Central registry of tracked meetings (proxy to CMS data)
#    - PK: (meeting_number, access_level)
#    - Cascade deletes to GroupMeeting and FavoriteMeeting
# 3. GroupMeeting - Links departments to meetings
#    - PK: (meeting_number, access_level, group_uuid)
#    - FK: meetings, groups
#
# Data integrity is enforced via:
#   - Composite primary keys (same meeting_number can exist on audio/video servers)
#   - Composite foreign keys (referential integrity)
#   - Cascade deletes (no orphaned records)
# ============================================================================

from enum import Enum
from datetime import datetime
import uuid

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, ForeignKeyConstraint,
    PrimaryKeyConstraint, Index, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


# --- AccessLevel Enum - Meeting Types ---
class AccessLevel(str, Enum):
    audio = "audio"           # Audio-only meetings
    video = "video"           # Video meetings
    blast_dial = "blast_dial" # Mass dialing (not yet supported)


# ============================================================================
# Meeting Model - Central Registry (NEW)
# ============================================================================
# Represents a meeting tracked in the local system.
# The meeting itself lives in the CMS, but we maintain a local record for:
#   - Linking to departments (via GroupMeeting)
#   - Tracking favorites (via FavoriteMeeting)
#   - Audit trail (created_at, updated_at)
#   - Sync tracking (last_synced for future use)
#
# Composite Primary Key: (meeting_number, access_level)
#   - meeting_number: CMS URI/meeting number (e.g., "5551234567")
#   - access_level: Type of meeting ("audio" or "video")
# ============================================================================
class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        PrimaryKeyConstraint("meeting_number", "access_level", name="pk_meetings"),
    )

    # Composite Primary Key
    meeting_number = Column(String(50), nullable=False, doc="CMS URI (e.g., '5551234567')")
    access_level = Column(String(10), nullable=False, doc="Meeting type: 'audio' or 'video'")

    # CMS Metadata
    cms_id = Column(
        String(100),
        nullable=True,
        index=True,
        doc="CoSpace ID from CMS (for future tracking)"
    )

    # Audit Trail
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="When this meeting was first tracked locally"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp"
    )
    last_synced = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time sync was performed with CMS (for future use)"
    )

    # -----------------------------------------------------------------------
    # Relationships - Cascade Delete Chain
    # -----------------------------------------------------------------------
    # When a Meeting is deleted, all associated records are automatically removed:
    #   Meeting deleted → GroupMeeting deleted → (orphaned)
    #   Meeting deleted → FavoriteMeeting deleted → (orphaned)
    group_links = relationship(
        "GroupMeeting",
        back_populates="meeting",
        cascade="all, delete-orphan",
        foreign_keys="GroupMeeting.meeting_number, GroupMeeting.access_level",
        doc="Departments linked to this meeting"
    )
    favorites = relationship(
        "FavoriteMeeting",
        back_populates="meeting",
        cascade="all, delete-orphan",
        foreign_keys="FavoriteMeeting.meeting_number, FavoriteMeeting.access_level",
        doc="Users who marked this meeting as favorite"
    )

    def __repr__(self):
        return f"<Meeting {self.meeting_number} ({self.access_level})>"


# ============================================================================
# GroupMeeting Model - Department to Meeting Links (UPDATED)
# ============================================================================
# Associates a department (group) with a meeting.
#
# Composite Primary Key: (meeting_number, access_level, group_uuid)
#   - meeting_number: CMS meeting URI
#   - access_level: Type of meeting
#   - group_uuid: Department ID
#
# Composite Foreign Keys:
#   - (meeting_number, access_level) → meetings (CASCADE delete)
#   - (group_uuid) → groups (CASCADE delete)
#
# This ensures:
#   - If a meeting is deleted from CMS → GroupMeeting is automatically removed
#   - If a group is deleted → GroupMeeting is automatically removed
#   - No orphaned records possible
# ============================================================================
class GroupMeeting(Base):
    __tablename__ = "group_meeting"
    __table_args__ = (
        PrimaryKeyConstraint(
            "meeting_number", "access_level", "group_uuid",
            name="pk_group_meeting"
        ),
        ForeignKeyConstraint(
            ["meeting_number", "access_level"],
            ["meetings.meeting_number", "meetings.access_level"],
            ondelete="CASCADE",
            name="fk_group_meeting_meeting"
        ),
        Index("ix_group_meeting_group", "group_uuid"),
    )

    # Composite Primary Key & Foreign Keys
    meeting_number = Column(String(50), nullable=False, doc="CMS meeting URI")
    access_level = Column(String(10), nullable=False, doc="Meeting type ('audio' or 'video')")
    group_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("groups.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Department UUID"
    )

    # Audit Trail (NEW)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="When this association was created"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp"
    )

    # -----------------------------------------------------------------------
    # Relationships
    # -----------------------------------------------------------------------
    group = relationship(
        "Group",
        back_populates="meeting_links",
        doc="The department this meeting is linked to"
    )
    meeting = relationship(
        "Meeting",
        back_populates="group_links",
        foreign_keys=[meeting_number, access_level],
        doc="The meeting being linked"
    )

    def __repr__(self):
        return f"<GroupMeeting {self.meeting_number} → {self.group_uuid}>"
