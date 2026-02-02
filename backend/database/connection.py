"""
Database Connection Management - v1.1.0

Provides connection management for:
1. Flower catalog SQLite database (read-only, flowers.db)
2. App SQLAlchemy database (sessions, image cache, history)
"""

import sqlite3
import os
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DbSession

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FLOWER DATABASE (SQLite - read-only catalog)
# ═══════════════════════════════════════════════════════════════════════════════

_DEFAULT_FLOWER_DB_PATH = Path(__file__).parent / "flowers.db"
FLOWER_DB_PATH = Path(os.getenv("FLOWERS_DB_PATH", str(_DEFAULT_FLOWER_DB_PATH)))


def get_flower_connection() -> sqlite3.Connection:
    """
    Get SQLite connection for flower database with row factory.

    Uses check_same_thread=False for multi-threaded access (read-only safe).
    """
    if not FLOWER_DB_PATH.exists():
        raise FileNotFoundError(
            f"Flower database not found at {FLOWER_DB_PATH}. "
            f"Run 'python -m backend.database.init_db' to initialize."
        )

    conn = sqlite3.connect(str(FLOWER_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_flower_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for flower database connection.

    Usage:
        with get_flower_db() as conn:
            cursor = conn.execute("SELECT * FROM flowers WHERE id = ?", (flower_id,))
            row = cursor.fetchone()
    """
    conn = get_flower_connection()
    try:
        yield conn
    finally:
        conn.close()


def check_flower_db_exists() -> bool:
    """Check if the flower database file exists."""
    return FLOWER_DB_PATH.exists()


def get_flower_db_path() -> Path:
    """Get the flower database file path."""
    return FLOWER_DB_PATH


# Backward compatibility aliases
def check_db_exists() -> bool:
    """Alias for check_flower_db_exists (backward compatibility)."""
    return check_flower_db_exists()


# ═══════════════════════════════════════════════════════════════════════════════
# APP DATABASE (SQLAlchemy - sessions, image cache, conversation history)
# ═══════════════════════════════════════════════════════════════════════════════

_DEFAULT_APP_DB_PATH = Path(__file__).parent / "fsense.db"
APP_DB_PATH = Path(os.getenv("FSENSE_DB_PATH", str(_DEFAULT_APP_DB_PATH)))
APP_DB_URL = f"sqlite:///{APP_DB_PATH}"

# Create engine with check_same_thread=False for multi-threaded FastAPI
_engine = create_engine(
    APP_DB_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# Session factory
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def init_app_db() -> None:
    """
    Initialize app database tables.

    Call this at app startup to ensure tables exist.
    """
    from backend.database.models import Base
    Base.metadata.create_all(bind=_engine)
    logger.info(f"App database initialized at {APP_DB_PATH}")


@contextmanager
def get_db() -> Generator[DbSession, None, None]:
    """
    Context manager for SQLAlchemy database session.

    Usage:
        with get_db() as db:
            repo = ImageCacheRepository(db)
            entry = repo.get_by_cache_key(cache_key)
    """
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_app_db_path() -> Path:
    """Get the app database file path."""
    return APP_DB_PATH
