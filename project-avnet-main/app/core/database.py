from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os


DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"

Base = declarative_base()

_engine = create_engine(DB_URL)
_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

def get_db():
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()