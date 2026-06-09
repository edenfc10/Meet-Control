# ============================================================================
# Hash Helper - הצפנת ואימות סיסמאות
# ============================================================================
# משתמש באלגוריתם Argon2 - אחד האלגוריתמים המומלצים ביותר להצפנת סיסמאות.
# תפקידים:
#   - verify_password: משווה סיסמה רגילה ל-hash שמור בDB
#   - get_password_hash: מצפין סיסמה רגילה ל-hash לשמירה בDB
# ============================================================================

from passlib.context import CryptContext

# הגדרת אלגוריתם ההצפנה
pwd_context = CryptContext(schemes=["argon2"], deprecated=["auto"])

class HashHelp(object):

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        """ משווה סיסמה רגילה ל-hash ששמור בDB. מחזיר True/False """
        return pwd_context.verify(plain_password, hashed_password)
        
    @staticmethod
    def get_password_hash(plain_password: str):
        """ מצפין סיסמה רגילה ל-Argon2 hash לשמירה בDB """
        return pwd_context.hash(plain_password)
