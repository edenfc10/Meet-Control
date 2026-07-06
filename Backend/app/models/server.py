import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SqlEnum, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base
from app.models.meeting import AccessLevel


class Server(Base):
    __tablename__ = "servers"

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    server_name = Column(String(120), nullable=False)
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(120), nullable=False)
    password = Column(String(255), nullable=False)
    accessLevel = Column(SqlEnum(AccessLevel), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())