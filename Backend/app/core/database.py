# ============================================================================
# Database Configuration - הגדרת חיבור לבסיס הנתונים
# ============================================================================
# קובץ זה מגדיר את החיבור ל-PostgreSQL דרך SQLAlchemy.
# החיבור מתבצע דרך environment variables שמוגדרים ב-docker-compose.
#
# רכיבים עיקריים:
#   - Base: מחלקת בסיס לכל המודלים (Models יורשים ממנה)
#   - _engine: המנוע של SQLAlchemy לחיבור לבסיס הנתונים
#   - _session_factory: יוצר session חדשים לכל בקשה
#   - get_db(): FastAPI Dependency - מספק session לכל endpoint וסוגר אותו
# ============================================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os


# בניית כתובת החיבור ל-PostgreSQL מ-environment variables
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"

# מחלקת בסיס - כל המודלים יורשים ממנה
Base = declarative_base()

# מנוע החיבור לבסיס הנתונים
_engine = create_engine(DB_URL)

# מפעל של sessions - יוצר session חדש לכל קריאה לשרת
_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db():
    """
    FastAPI Dependency - מספק session לכל endpoint.
    משתמש ב-yield כדי שה-session יסגר אוטומטית אחרי הבקשה.
    """
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()