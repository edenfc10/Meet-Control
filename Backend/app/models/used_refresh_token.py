
from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SqlEnum, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


class UsedRefreshToken(Base):
    __tablename__ = "used_refresh_tokens"
    __mapper_args__ = {"confirm_deleted_rows": False}
    jti = Column(String, primary_key=True, index=True)
    user_uuid = Column(String, index=True)
    expires_at = Column(Integer)