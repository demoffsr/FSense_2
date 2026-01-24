"""
Database connection and session management.

Supports:
- Supabase PostgreSQL (production)
- SQLite (local development fallback)

Provides SQLAlchemy engine, session factory, and database initialization.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from pathlib import Path
import logging
import os

from backend.database.models import Base

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE URL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════


def get_database_url() -> str:
    """
    Get database URL from environment or use SQLite fallback.

    Priority:
    1. DATABASE_URL environment variable (Supabase PostgreSQL)
    2. SQLite fallback for local development
    """
    db_url = os.getenv("DATABASE_URL", "")

    if db_url:
        logger.info("Using PostgreSQL database (Supabase)")
        return db_url
    else:
        # SQLite fallback for local development
        db_dir = Path(__file__).parent.parent / "data"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / "fsense.db"
        logger.info(f"Using SQLite database at {db_path}")
        return f"sqlite:///{db_path}"


def create_db_engine():
    """
    Create SQLAlchemy engine with appropriate settings.

    For Supabase Transaction Pooler:
    - Uses NullPool (connection pooling handled by Supabase)
    - Disables prepared statements (required for pgbouncer)
    """
    db_url = get_database_url()
    is_postgres = db_url.startswith("postgresql")

    if is_postgres:
        # PostgreSQL (Supabase) configuration
        # NullPool because Supabase handles connection pooling
        engine = create_engine(
            db_url,
            poolclass=NullPool,  # Let Supabase handle pooling
            echo=False,
            # Disable prepared statements for pgbouncer transaction mode
            connect_args={
                "options": "-c statement_timeout=30000"  # 30 second timeout
            },
        )
        logger.info("PostgreSQL engine created with NullPool")
    else:
        # SQLite configuration
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False,
        )
        logger.info("SQLite engine created")

    return engine


# Global engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════


def init_database():
    """
    Initialize database tables.

    Creates all tables defined in models.py if they don't exist.
    Safe to call multiple times.
    """
    try:
        Base.metadata.create_all(bind=engine)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()

        db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"
        logger.info(f"Database initialized ({db_type})")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════


@contextmanager
def get_db() -> Session:
    """
    Database session context manager.

    Usage:
        with get_db() as db:
            # use db session
            result = db.query(Model).all()

    Automatically commits on success, rolls back on exception.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_info() -> dict:
    """
    Get database connection information.

    Returns:
        Dictionary with database type and status
    """
    db_url = str(engine.url)
    is_postgres = "postgresql" in db_url

    # Mask password in URL for logging
    if "@" in db_url:
        parts = db_url.split("@")
        masked_url = parts[0].rsplit(":", 1)[0] + ":***@" + parts[1]
    else:
        masked_url = db_url

    return {
        "type": "PostgreSQL (Supabase)" if is_postgres else "SQLite",
        "url": masked_url,
        "connected": check_database_connection(),
    }
