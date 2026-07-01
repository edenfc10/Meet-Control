import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base


class FavoriteMeeting(Base):
    __tablename__ = "favorite_meetings"
    __table_args__ = (
        UniqueConstraint("member_uuid", "meeting_number", "access_level", name="uq_favorite_member_meeting"),
    )

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    member_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # מזהה הפגישה: (מספר + סוג) — הפגישה עצמה חיה ב-CMS, לא ב-DB
    meeting_number = Column(String(15), nullable=False, index=True)
    access_level = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
