"""
Database connection and session management.

Provides SQLAlchemy engine, session factory, and database initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path
import logging

from backend.database.models import Base

logger = logging.getLogger(__name__)

# Database path: backend/data/fsense.db
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "fsense.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with optimizations
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for FastAPI
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize database tables"""
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


@contextmanager
def get_db() -> Session:
    """Database session context manager"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
