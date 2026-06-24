import uuid

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


class FavoriteMeeting(Base):
    __tablename__ = "favorite_meetings"
    __table_args__ = (
        UniqueConstraint("member_uuid", "meeting_uuid", name="uq_favorite_member_meeting"),
    )

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    member_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meeting_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("meetings.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
