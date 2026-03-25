from enum import Enum
import uuid
from sqlalchemy import Column, Integer, String, Enum as SqlEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID



class Mador(Base):
    __tablename__ = "madors"

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), nullable=False)
    
    members = relationship("User", secondary="user_mador_association", back_populates="madors")
    meetings = relationship("Meeting", secondary="meeting_mador_association", back_populates="madors")
    member_access_levels = relationship("MemberMadorAccess", back_populates="mador", cascade="all, delete-orphan")


