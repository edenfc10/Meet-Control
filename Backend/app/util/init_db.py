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


# ============================================================================
# Migration: מעבר לניהול פגישות ב-CMS בלבד
# ============================================================================
# הפגישות עברו להיות מנוהלות אך ורק ב-CMS. ה-DB המקומי שומר רק overlay
# לפי מספר פגישה (שיוך מדור + מועדפים). המיגרציה:
#   1. מגבה את הטבלאות הישנות (_bak_*) לפני כל שינוי הרסני
#   2. מעבירה שיוכי מדור ומועדפים מ-UUID למספר פגישה
#   3. מוחקת את meetings / meeting_participant_status / meeting_group_association
# אידמפוטנטי: אם טבלת meetings כבר נמחקה, לא עושה כלום.
# ============================================================================
_MIGRATE_TO_CMS_MEETINGS = """
DO $$
BEGIN
  IF to_regclass('public.meetings') IS NULL THEN
    RETURN;  -- כבר עברנו למודל החדש
  END IF;

  -- 1. גיבויים (רק אם לא קיימים כבר)
  IF to_regclass('public._bak_meetings') IS NULL THEN
    EXECUTE 'CREATE TABLE _bak_meetings AS SELECT * FROM meetings';
  END IF;
  IF to_regclass('public.meeting_group_association') IS NOT NULL
     AND to_regclass('public._bak_meeting_group_association') IS NULL THEN
    EXECUTE 'CREATE TABLE _bak_meeting_group_association AS SELECT * FROM meeting_group_association';
  END IF;
  IF to_regclass('public._bak_favorite_meetings') IS NULL THEN
    EXECUTE 'CREATE TABLE _bak_favorite_meetings AS SELECT * FROM favorite_meetings';
  END IF;

  -- 2a. העברת שיוכי מדור->פגישה ל-(מספר + סוג)
  IF to_regclass('public.meeting_group_association') IS NOT NULL THEN
    INSERT INTO group_meeting (meeting_number, access_level, group_uuid)
      SELECT m.m_number, m."accessLevel"::text, a.group_id
      FROM meeting_group_association a
      JOIN meetings m ON m."UUID" = a.meeting_id
      WHERE m.m_number IS NOT NULL AND m."accessLevel"::text IN ('audio', 'video')
      ON CONFLICT (meeting_number, access_level) DO NOTHING;
  END IF;

  -- 2b. העברת מועדפים ל-(מספר + סוג)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'favorite_meetings' AND column_name = 'meeting_number'
  ) THEN
    ALTER TABLE favorite_meetings ADD COLUMN meeting_number VARCHAR(15);
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'favorite_meetings' AND column_name = 'access_level'
  ) THEN
    ALTER TABLE favorite_meetings ADD COLUMN access_level VARCHAR(10);
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'favorite_meetings' AND column_name = 'meeting_uuid'
  ) THEN
    UPDATE favorite_meetings f
      SET meeting_number = m.m_number, access_level = m."accessLevel"::text
      FROM meetings m
      WHERE m."UUID" = f.meeting_uuid AND f.meeting_number IS NULL;
    DELETE FROM favorite_meetings WHERE meeting_number IS NULL OR access_level NOT IN ('audio', 'video');

    IF EXISTS (
      SELECT 1 FROM information_schema.table_constraints
      WHERE constraint_name = 'uq_favorite_member_meeting' AND table_name = 'favorite_meetings'
    ) THEN
      ALTER TABLE favorite_meetings DROP CONSTRAINT uq_favorite_member_meeting;
    END IF;

    ALTER TABLE favorite_meetings DROP COLUMN meeting_uuid;
    ALTER TABLE favorite_meetings ALTER COLUMN meeting_number SET NOT NULL;
    ALTER TABLE favorite_meetings ALTER COLUMN access_level SET NOT NULL;
    ALTER TABLE favorite_meetings
      ADD CONSTRAINT uq_favorite_member_meeting UNIQUE (member_uuid, meeting_number, access_level);
  END IF;

  -- 3. מחיקת הטבלאות הישנות
  DROP TABLE IF EXISTS meeting_participant_status;
  DROP TABLE IF EXISTS meeting_group_association;
  DROP TABLE IF EXISTS meetings;
END
$$;
"""



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
            # מיגרציה למודל "פגישות ב-CMS בלבד" (אידמפוטנטי, מגבה לפני מחיקה)
            with _engine.connect() as conn:
                conn.execute(text(_MIGRATE_TO_CMS_MEETINGS))
                conn.commit()
            print("Tables created successfully")
            break
        except OperationalError:
            print(f"Database not ready, retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        raise Exception("Could not connect to the database")
