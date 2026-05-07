# ============================================================================
# User Model - מודל המשתמש
# ============================================================================
# ×§×•×‘×¥ ×–×” ×ž×’×“×™×¨ ××ª ×ž×•×“×œ ×”×ž×©×ª×ž×© (User) ×‘×ž×¡×“ ×”× ×ª×•× ×™×.
# ×›×•×œ×œ: ×ª×¤×§×™×“×™× (roles), ×˜×‘×œ×ª ×§×©×¨ ×‘×™×Ÿ ×ž×©×ª×ž×©×™× ×œ×ž×“×•×¨×™×,
# ×•××ª ×›×œ ×”×©×“×•×ª ×©×œ ×”×ž×©×ª×ž×© ×‘DB.
#
# Permission Hierarchy (×”×™×¨×¨×›×™×™×ª ×”×¨×©××•×ª):
#   super_admin > admin > agent
#   - super_admin: ×’×™×©×” ×ž×œ××” - × ×™×”×•×œ ×›×œ ×”×ž×©×ª×ž×©×™×, ×ž×“×•×¨×™× ×•×¤×’×™×©×•×ª
#   - admin: ×™×›×•×œ ×œ×™×¦×•×¨ agents, ×œ× ×”×œ ×ž×“×•×¨×™× ×•×¤×’×™×©×•×ª
#   - agent: ×¦×¤×™×™×” ×‘×œ×‘×“ - ×¨×•××” ×¨×§ ××ª ×”×¤×’×™×©×•×ª ×œ×¤×™ ×”×ž×“×•×¨×™× ×•×”×’×™×©×” ×©×œ×•
# ============================================================================

from enum import Enum
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Enum as SqlEnum, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


# --- UserRole Enum - תפקידי המשתמש ---
# ×›×œ ×ž×©×ª×ž×© ×—×™×™×‘ ×œ×”×™×•×ª ××—×“ ×ž-3 ×”×ª×¤×§×™×“×™× ×”××œ×”.
# הEnum יורש מ-str כדי שהערך יישמר כטקסט בDB ויהיה קל להשוות.
class UserRole(str, Enum):
    super_admin = "super_admin"  # ×ž× ×”×œ ×¢×œ - ×©×œ×™×˜×” ×ž×œ××” ×¢×œ ×”×ž×¢×¨×›×ª
    admin = "admin"  # מנהל - יכול לנהל agents ופגישות
    agent = "agent"  # ×¡×•×›×Ÿ - ×¦×¤×™×™×” ×‘×œ×‘×“ ×œ×¤×™ ×”×¨×©××•×ª
    viewer = "viewer"  # ×¦×•×¤×” - ×¦×¤×™×™×” ×‘×¡×™×¡×™×ª ×œ×¤×™ ×”×¨×©××•×ª ×ž×“×•×¨


# --- User Model - ×˜×‘×œ×ª ×”×ž×©×ª×ž×©×™× ---
class User(Base):
    __tablename__ = "users"

    # ×ž×–×”×” ×™×™×—×•×“×™ ××•× ×™×‘×¨×¡×œ×™ - × ×•×¦×¨ ××•×˜×•×ž×˜×™×ª
    UUID = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # מזהה משתמש (כמו מספר עובד) - חייב להיות ייחודי
    s_id = Column(String(50), unique=True, nullable=False, index=True)
    # ×©× ×”×ž×©×ª×ž×© ×œ×ª×¦×•×’×”
    username = Column(String(50), nullable=False)
    # ×¡×™×¡×ž×” ×ž×•×¦×¤× ×ª (Argon2 hash) - ×œ×¢×•×œ× ×œ× × ×©×ž×¨×ª ×›×˜×§×¡×˜ ×¨×’×™×œ
    password = Column(String(250), nullable=False)
    # תפקיד המשתמש - ברירת מחדל: agent
    role = Column(SqlEnum(UserRole), nullable=False, default=UserRole.agent)

    # --- Relationships (קשרים) ---
    # Use group_access_levels for user-group relationships with access level
    # רמות הגישה של המשתמש לכל מדור (audio/video/blast_dial/voice)
    # Note: Disabled back_populates to avoid circular import issues
    group_access_levels = relationship(
        "MemberGroupAccess", cascade="all, delete-orphan"
    )
