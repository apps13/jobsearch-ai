"""
Database engine, session factory, and the FastAPI dependency that hands a
short-lived session to each request.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a session and guarantee it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
