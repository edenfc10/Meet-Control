# ============================================================================
# User Model - מודל המשתמש
# ============================================================================
# מודל המשתמש במערכת.
# כולל: תפקידי משתמש (roles), קשרים עם פגישות וקבוצות.
#
# Permission Hierarchy (היררכיית הרשאות):
#   super_admin > admin > agent
#   - super_admin: יוצר ומנהל כל המערכת
#   - admin: מנהל - יכול לנהל agents ופגישות
#   - agent: סוכן - יכול להתחבר לפגישות
# ============================================================================

from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SqlEnum, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


# --- UserRole Enum - תפקידי המשתמש ---
# הEnum יורש מ-str כדי שהערך יישמר כטקסט בDB ויהיה קל להשוות.
class UserRole(str, Enum):
    super_admin = "super_admin"  # יוצר ומנהל כל המערכת
    admin = "admin"  # מנהל - יכול לנהל agents ופגישות
    agent = "agent"  # סוכן - יכול להתחבר לפגישות


# --- User Model - מודל המשתמש ---
class User(Base):
    __tablename__ = "users"

    # מזהה משתמש ייחודי - נוצר אוטומטית
    UUID = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # מזהה משתמש (כמו מספר עובד) - חייב להיות ייחודי
    s_id = Column(String(50), unique=True, nullable=False, index=True)
    # שם המשתמש
    username = Column(String(50), nullable=False)
    # סיסמה מוצפנת (Argon2 hash)
    password = Column(String(250), nullable=False)

    responsible_access_level = Column(String(20), nullable=True)
    # תפקיד המשתמש - ברירת מחדל: agent
    role = Column(SqlEnum(UserRole), nullable=False, default=UserRole.agent)

    # --- Relationships (קשרים) ---
    # רמות הגישה של המשתמש לכל מדור (audio/video/blast_dial/voice)
    group_access_levels = relationship(
        "MemberGroupAccess", back_populates="member", cascade="all, delete-orphan"
    )
    meeting_statuses = relationship(
        "MeetingParticipantStatus", back_populates="user", cascade="all, delete-orphan"
    )
