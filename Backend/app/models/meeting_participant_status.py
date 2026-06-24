# ============================================================================
# MeetingParticipantStatus Model - סטטוס משתתף בוועידה
# ============================================================================
# טבלה זו שומרת את הסטטוס הנוכחי של כל משתמש בכל ועידה.
# נוצרת בפעם הראשונה שמבצעים Mute או Kick למשתמש.
#
# PK: (meeting_uuid, user_uuid)
# ============================================================================

import uuid
from sqlalchemy import Column, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class MeetingParticipantStatus(Base):
    __tablename__ = "meeting_participant_status"

    # UUID של הוועידה (FK לטבלת meetings)
    meeting_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("meetings.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    # UUID של המשתמש (FK לטבלת users)
    user_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    # האם המשתמש מושתק
    is_muted = Column(Boolean, nullable=False, default=False)
    # האם המשתמש הוסר מהשיחה (kicked)
    is_kicked = Column(Boolean, nullable=False, default=False)

    # --- Relationships ---
    meeting = relationship("Meeting", back_populates="participant_statuses")
    user = relationship("User", back_populates="meeting_statuses")
