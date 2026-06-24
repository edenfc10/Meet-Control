# ============================================================================
# BaseRepository - מחלקת בסיס לכל הרפוזיטוריות
# ============================================================================
# מספקת session של SQLAlchemy לכל המחלקות היורשות.
# כל repository יורש מהמחלקה הזו ומשתמש ב-session לפעולות DB.
# ה-session נוצר ב-get_db() (database.py) ומוזרק דרך FastAPI Depends.
# ============================================================================

from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session  # סשן DB פעיל לשאילתות וקריאות