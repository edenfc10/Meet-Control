import os
import time
from sqlalchemy.exc import OperationalError
from app.core.database import Base, _engine
# Ensure all SQLAlchemy models are imported so they are registered in Base.metadata
import app.models.user  # noqa: F401
import app.models.mador  # noqa: F401
import app.models.meeting  # noqa: F401
import app.models.member_mador_access  # noqa: F401
import app.models.events  # noqa: F401 — register SQLAlchemy event listeners



def create_tables(retries=5, delay=3):
    # If RESET_DB is set, drop all existing tables first
    if os.getenv("RESET_DB") in ("1", "true", "True"):
        print("RESET_DB enabled: dropping all tables")
        Base.metadata.drop_all(bind=_engine)

    for i in range(retries):
        try:
            Base.metadata.create_all(bind=_engine)
            print("Tables created successfully")
            break
        except OperationalError:
            print(f"Database not ready, retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        raise Exception("Could not connect to the database")