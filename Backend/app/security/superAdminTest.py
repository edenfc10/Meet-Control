# ============================================================================
# Super Admin Bootstrap - יצירת מנהל על בהפעלה ראשונה
# ============================================================================
# קובץ זה רץ בעליית האפליקציה (lifespan ב-main.py).
# יוצר משתמש super_admin ראשוני אם הוא לא קיים.
# פרטי החיבור נלקחים ממשתני סביבה (.env):
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

# קריאת פרטי הסופר אדמין ממשתני הסביבה
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")


class SuperAdminTest(object):

    @staticmethod 
    def create_super_admin():
        """
        יוצר משתמש super_admin אם הוא לא קיים.
        רץ פעם אחת בעליית האפליקציה.
        משתמש ב-_session_factory ישירות (לא FastAPI Depends).
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

    

