# ============================================================================
# Database Initialization - אתחול בסיס הנתונים
# ============================================================================
# קובץ זה רץ בעליית האפליקציה (lifespan ב-main.py).
# תפקידים:
#   1. אם RESET_DB מוגדר - מוחק את כל הטבלאות ויוצר מחדש (לא מוחק כל data!)
#   2. יוצר את כל הטבלאות החסרות (create_all)
#   3. מנסה retry אם ה-DB עדיין לא מוכן
#
# הערה: חיייבים לייבא את כל המודלים כאן כדי שהם יהיו רשומים ב-Base.metadata!
# ============================================================================

import os
import time
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.core.database import Base, _engine
# ייבוא כל המודלים - חייב כדי שיהיו רשומים ב-Base.metadata לפני create_all
import app.models.user  # noqa: F401
import app.models.group  # noqa: F401
import app.models.meeting  # noqa: F401
import app.models.member_group_access  # noqa: F401
import app.models.favorite_meeting  # noqa: F401
import app.models.server  # noqa: F401



def create_tables(retries=5, delay=3):
    """
    יוצר את כל הטבלאות ב-DB.
    אם RESET_DB=1 מוגדר - מוחק הכל תחילה.
    מנסה מחדש אם ה-DB לא מוכן (Docker startup).
    """
    if os.getenv("USE_ALEMBIC") in ("1", "true", "True"):
        print("USE_ALEMBIC enabled: schema is managed by Alembic migrations")
        return

    # If RESET_DB is set, drop all existing tables first
    if os.getenv("RESET_DB") in ("1", "true", "True"):
        print("RESET_DB enabled: dropping all tables")
        Base.metadata.drop_all(bind=_engine)

    for i in range(retries):
        try:
            Base.metadata.create_all(bind=_engine)
            # Lightweight compatibility migration for existing environments.
            with _engine.connect() as conn:
                conn.execute(text("ALTER TABLE meetings ADD COLUMN IF NOT EXISTS password VARCHAR(120)"))
                conn.commit()
            print("Tables created successfully")
            break
        except OperationalError:
            print(f"Database not ready, retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        raise Exception("Could not connect to the database")
