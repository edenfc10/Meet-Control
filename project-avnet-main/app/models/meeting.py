from sqlalchemy import BigInteger, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.core.database import Base


class Meeting(Base):
    __tablename__ = "Meetings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    meeting_id = Column(BigInteger, unique=True, nullable=False, index=True)
    mador_id = Column(PostgresUUID(as_uuid=True), ForeignKey("Madors.UUID"), nullable=False, index=True)
    mador_owner_id = Column(PostgresUUID(as_uuid=True), ForeignKey("Users.UUID"), nullable=False, index=True)

    mador = relationship("Mador", back_populates="meetings")
    mador_owner = relationship("User", foreign_keys=[mador_owner_id], lazy="selectin")