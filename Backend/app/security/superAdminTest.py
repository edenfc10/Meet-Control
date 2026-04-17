# ============================================================================
# Super Admin Bootstrap - ×™×¦×™×¨×ª ×ž× ×”×œ ×¢×œ ×‘×”×¤×¢×œ×” ×¨××©×•× ×”
# ============================================================================
# ×§×•×‘×¥ ×–×” ×¨×¥ ×‘×¢×œ×™×™×ª ×”××¤×œ×™×§×¦×™×” (lifespan ×‘-main.py).
# ×™×•×¦×¨ ×ž×©×ª×ž×© super_admin ×¨××©×•× ×™ ×× ×”×•× ×œ× ×§×™×™×.
# ×¤×¨×˜×™ ×”×—×™×‘×•×¨ × ×œ×§×—×™× ×ž×ž×©×ª× ×™ ×¡×‘×™×‘×” (.env):
#   SUPER_ADMIN_USERNAME ו-SUPER_ADMIN_PASSWORD
# ============================================================================

import jwt
from dotenv import load_dotenv
import time
import os
import logging

from app.core.database import _session_factory  # גישה ישירה ל-session factory לשימוש startup
from app.security.hashHelper import HashHelp

logger = logging.getLogger(__name__)

load_dotenv()

# ×§×¨×™××ª ×¤×¨×˜×™ ×”×¡×•×¤×¨ ××“×ž×™×Ÿ ×ž×ž×©×ª× ×™ ×”×¡×‘×™×‘×”
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")


class SuperAdminTest(object):

    @staticmethod 
    def create_super_admin():
        """
        ×™×•×¦×¨ ×ž×©×ª×ž×© super_admin ×× ×”×•× ×œ× ×§×™×™×.
        ×¨×¥ ×¤×¢× ××—×ª ×‘×¢×œ×™×™×ª ×”××¤×œ×™×§×¦×™×”.
        ×ž×©×ª×ž×© ×‘-_session_factory ×™×©×™×¨×•×ª (×œ× FastAPI Depends).
        """
        from app.repository.userRepo import UserRepository
        from app.schema.user import UserInCreate

        session = _session_factory()
        user_repo = UserRepository(session=session)
        if not user_repo.get_user_by_s_id(SUPER_ADMIN_USERNAME):
            logger.info(f"Creating super admin user: {SUPER_ADMIN_USERNAME}")
            super_admin_data = UserInCreate(
                username=SUPER_ADMIN_USERNAME,
                password=HashHelp.get_password_hash(SUPER_ADMIN_PASSWORD),
                role="super_admin",
                s_id=SUPER_ADMIN_USERNAME,
                group_ids=[],
        )
            user_repo.create_user(super_admin_data)
            logger.info(f"Super admin created successfully")
        else:
            logger.info(f"Super admin {SUPER_ADMIN_USERNAME} already exists")

    

