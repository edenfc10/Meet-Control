from enum import Enum

from sqlalchemy import Column, Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MemberMadorAccessLevel(str, Enum):
    voice = "voice"
    audio = "audio"
    video = "video"
    blast_dial = "blast_dial"
    

class MemberMadorAccess(Base):
    __tablename__ = "member_mador_access"

    member_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    mador_uuid = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("madors.UUID", ondelete="CASCADE"),
        primary_key=True,
    )
    access_level = Column(SqlEnum(MemberMadorAccessLevel), primary_key=True)

    member = relationship("User", back_populates="mador_access_levels")
    mador = relationship("Mador", back_populates="member_access_levels")
