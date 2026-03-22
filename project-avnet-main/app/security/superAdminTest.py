import jwt
from dotenv import load_dotenv
import time
import os
import logging

from app.core.database import get_db  # יוצרת חיבור לDB באמצעות הספרייה הבאה 
from app.security.hashHelper import HashHelp

logger = logging.getLogger(__name__)

load_dotenv()  # Loads from current working directory or parent directories

#קריאת המשתנים מהקובץ ENV
SUPER_ADMIN_USERNAME = os.getenv("SUPER_ADMIN_USERNAME")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD")


class SuperAdminTest(object):

    @staticmethod 
    def create_super_admin():
        from app.repository.userRepo import UserRepository
        from app.schema.user import UserInCreate

        user_repo = UserRepository(session=next(get_db()))
        if not user_repo.get_user_by_s_id(SUPER_ADMIN_USERNAME):
            logger.info(f"Creating super admin user: {SUPER_ADMIN_USERNAME}")
            super_admin_data = UserInCreate(
                username=SUPER_ADMIN_USERNAME,
                password=HashHelp.get_password_hash(SUPER_ADMIN_PASSWORD),
                role="super_admin",
                s_id=SUPER_ADMIN_USERNAME,
                mador_ids=[]
            )
            user_repo.create_user(super_admin_data)
            logger.info(f"Super admin created successfully")
        else:
            logger.info(f"Super admin {SUPER_ADMIN_USERNAME} already exists")

    
