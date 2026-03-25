from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SqlEnum, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

class AccessLevel(str, Enum):
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"

meeting_mador_association = Table(
    "meeting_mador_association",
    Base.metadata,
    Column("meeting_id", PostgresUUID(as_uuid=True), ForeignKey("meetings.UUID", ondelete="CASCADE"), primary_key=True),
    Column("mador_id", PostgresUUID(as_uuid=True), ForeignKey("madors.UUID", ondelete="CASCADE"), primary_key=True)
)

class Meeting(Base):
    __tablename__ = "meetings"

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    m_number = Column(String(15), unique=True, nullable=False, index=True)
    accessLevel = Column(SqlEnum(AccessLevel), nullable=False)

    madors = relationship("Mador", secondary="meeting_mador_association", back_populates="meetings")

