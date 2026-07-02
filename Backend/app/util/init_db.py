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
# Migration: Transition to CMS-only Meeting Management (Legacy - Now Disabled)
# ============================================================================
# This migration was used to transition from UUID-based meetings to number-based
# meetings with the new hybrid schema. It is now disabled since we start with
# the new schema from the beginning.
# ============================================================================
_MIGRATE_TO_CMS_MEETINGS = """
DO $$
BEGIN
  -- Migration disabled: New schema starts with meetings by number, not UUID
  -- If old meetings table exists (UUID-based), perform legacy migration
  IF to_regclass('public.meetings') IS NOT NULL THEN
    -- Check if this is the old meetings table (has UUID column)
    IF EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name = 'meetings' AND column_name = 'UUID'
    ) THEN
      -- This is the old schema, perform migration
      RAISE NOTICE 'Migrating from old UUID-based meetings table to new number-based schema';

      -- Backup old tables
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

      -- Migrate group_meeting associations
      IF to_regclass('public.meeting_group_association') IS NOT NULL THEN
        INSERT INTO group_meeting (meeting_number, access_level, group_uuid)
          SELECT m.m_number, m."accessLevel"::text, a.group_id
          FROM meeting_group_association a
          JOIN meetings m ON m."UUID" = a.meeting_id
          WHERE m.m_number IS NOT NULL AND m."accessLevel"::text IN ('audio', 'video')
          ON CONFLICT (meeting_number, access_level) DO NOTHING;
      END IF;

      -- Drop old tables
      DROP TABLE IF EXISTS meeting_participant_status;
      DROP TABLE IF EXISTS meeting_group_association;
      DROP TABLE IF EXISTS meetings;

      RAISE NOTICE 'Migration complete: Old UUID-based meetings removed';
    ELSE
      -- New schema is already in place
      RAISE NOTICE 'New meetings table detected: Migration skipped (already using number-based schema)';
    END IF;
  ELSE
    RAISE NOTICE 'No old meetings table found: Starting with new schema';
  END IF;
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
