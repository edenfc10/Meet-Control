from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SqlEnum, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    agent = "agent"

user_mador_association = Table(
    "user_mador_association",
    Base.metadata,
    Column("user_id", PostgresUUID(as_uuid=True), ForeignKey("users.UUID", ondelete="CASCADE"), primary_key=True),
    Column("mador_id", PostgresUUID(as_uuid=True), ForeignKey("madors.UUID", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    s_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    password = Column(String(250), nullable=False)
    role = Column(SqlEnum(UserRole), nullable=False, default=UserRole.agent)

    madors = relationship("Mador", secondary="user_mador_association", back_populates="members")
    mador_access_levels = relationship("MemberMadorAccess", back_populates="member", cascade="all, delete-orphan")




