import uuid

from sqlalchemy import Column, DateTime, Enum as SqlEnum, String, Boolean, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.core.database import Base
from app.models.meeting import AccessLevel


class Server(Base):
    __tablename__ = "servers"

    UUID = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    server_name = Column(String(120), nullable=False)
    ip_address = Column(String(45), nullable=False)
    port = Column(Integer, default=8443, nullable=False)  # פורט השרת (בדרך כלל 8443)
    username = Column(String(120), nullable=False)
    password = Column(String(255), nullable=False)
    accessLevel = Column(SqlEnum(AccessLevel), nullable=False, index=True)
    
    # שדות חדשים לניהול CMS
    is_active = Column(Boolean, default=True, nullable=False)  # האם השרת פעיל
    is_primary = Column(Boolean, default=False, nullable=False)  # האם זה השרת הראשי
    hierarchy_order = Column(Integer, default=0, nullable=False)  # סדר היררכיה (0=ראשון, 1=שני, וכו')
    connection_status = Column(String(20), default="disconnected", nullable=False)  # connected/disconnected/error
    last_connection_test = Column(DateTime(timezone=True), nullable=True)  # זמן בדיקה אחרונה
    connection_error = Column(Text, nullable=True)  # פרטי שגיאת חיבור אחרונה
    server_version = Column(String(50), nullable=True)  # גרסת השרת
    system_info = Column(Text, nullable=True)  # מידע מערכת (JSON)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())