"""
Database Initialization Script - v1.0.0

Creates and seeds the flower SQLite database from existing Python data.
Run this script once to initialize the database:

    python -m backend.database.init_db

After running, the flowers.db file will be created and used by the application.
"""

import sqlite3
import json
import logging
from pathlib import Path

# Import data from existing module
# Note: This will load data into memory once during initialization
from backend.database.flower_database import (
    FLOWERS_DATA,
    FLOWER_MEANINGS_DATA,
    CULTURAL_CONTEXTS_DATA,
    REGION_NUMBER_RULES_DATA,
    COLOR_MEANINGS_DATA,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "flowers.db"


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables for the flower database."""
    conn.executescript("""
        -- Flowers table
        CREATE TABLE IF NOT EXISTS flowers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_ru TEXT,
            color TEXT,
            category TEXT DEFAULT 'flower',
            availability TEXT DEFAULT 'year_round',
            price_tier TEXT DEFAULT 'mid',
            primary_meanings TEXT,  -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_flower_name ON flowers(name);
        CREATE INDEX IF NOT EXISTS idx_flower_color ON flowers(color);

        -- Flower meanings table
        CREATE TABLE IF NOT EXISTS flower_meanings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flower_id TEXT NOT NULL,
            emotion TEXT NOT NULL,
            occasion TEXT,
            match_score REAL DEFAULT 0.7,
            meaning_en TEXT NOT NULL,
            meaning_ru TEXT,
            phrases TEXT  -- JSON array
        );
        CREATE INDEX IF NOT EXISTS idx_meaning_emotion ON flower_meanings(emotion);
        CREATE INDEX IF NOT EXISTS idx_meaning_flower_emotion ON flower_meanings(flower_id, emotion);

        -- Cultural contexts table
        CREATE TABLE IF NOT EXISTS flower_cultural_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flower_id TEXT NOT NULL,
            region TEXT NOT NULL,
            meaning TEXT,
            is_taboo INTEGER DEFAULT 0,
            taboo_reason TEXT,
            taboo_occasions TEXT,  -- JSON array
            recommended_occasions TEXT  -- JSON array
        );
        CREATE INDEX IF NOT EXISTS idx_cultural_region ON flower_cultural_contexts(region);
        CREATE INDEX IF NOT EXISTS idx_cultural_flower_region ON flower_cultural_contexts(flower_id, region);

        -- Regional number rules table
        CREATE TABLE IF NOT EXISTS region_number_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL UNIQUE,
            avoid_numbers TEXT,  -- JSON array
            prefer_numbers TEXT,  -- JSON array
            notes TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_number_region ON region_number_rules(region);

        -- Color meanings table
        CREATE TABLE IF NOT EXISTS flower_color_meanings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            color TEXT NOT NULL,
            meaning_universal TEXT,
            meaning_ru TEXT,
            emotions TEXT,  -- JSON array
            occasions TEXT  -- JSON array
        );
        CREATE INDEX IF NOT EXISTS idx_color ON flower_color_meanings(color);
    """)
    conn.commit()
    logger.info("Tables created successfully")


def seed_flowers(conn: sqlite3.Connection) -> int:
    """Seed flowers table."""
    cursor = conn.cursor()
    count = 0
    for data in FLOWERS_DATA:
        cursor.execute("""
            INSERT OR REPLACE INTO flowers
            (id, name, name_ru, color, category, availability, price_tier, primary_meanings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("id"),
            data.get("name"),
            data.get("name_ru"),
            data.get("color"),
            data.get("category", "flower"),
            data.get("availability", "year_round"),
            data.get("price_tier", "mid"),
            json.dumps(data.get("primary_meanings")) if data.get("primary_meanings") else None,
        ))
        count += 1
    conn.commit()
    return count


def seed_meanings(conn: sqlite3.Connection) -> int:
    """Seed flower meanings table."""
    cursor = conn.cursor()
    count = 0
    for data in FLOWER_MEANINGS_DATA:
        cursor.execute("""
            INSERT INTO flower_meanings
            (flower_id, emotion, occasion, match_score, meaning_en, meaning_ru, phrases)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("flower_id"),
            data.get("emotion"),
            data.get("occasion"),
            data.get("match_score", 0.7),
            data.get("meaning_en"),
            data.get("meaning_ru"),
            json.dumps(data.get("phrases")) if data.get("phrases") else None,
        ))
        count += 1
    conn.commit()
    return count


def seed_cultural_contexts(conn: sqlite3.Connection) -> int:
    """Seed cultural contexts table."""
    cursor = conn.cursor()
    count = 0
    for data in CULTURAL_CONTEXTS_DATA:
        cursor.execute("""
            INSERT INTO flower_cultural_contexts
            (flower_id, region, meaning, is_taboo, taboo_reason, taboo_occasions, recommended_occasions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("flower_id"),
            data.get("region"),
            data.get("meaning"),
            1 if data.get("is_taboo") else 0,
            data.get("taboo_reason"),
            json.dumps(data.get("taboo_occasions")) if data.get("taboo_occasions") else None,
            json.dumps(data.get("recommended_occasions")) if data.get("recommended_occasions") else None,
        ))
        count += 1
    conn.commit()
    return count


def seed_number_rules(conn: sqlite3.Connection) -> int:
    """Seed regional number rules table."""
    cursor = conn.cursor()
    count = 0
    for data in REGION_NUMBER_RULES_DATA:
        cursor.execute("""
            INSERT OR REPLACE INTO region_number_rules
            (region, avoid_numbers, prefer_numbers, notes)
            VALUES (?, ?, ?, ?)
        """, (
            data.get("region"),
            json.dumps(data.get("avoid_numbers")) if data.get("avoid_numbers") else None,
            json.dumps(data.get("prefer_numbers")) if data.get("prefer_numbers") else None,
            data.get("notes"),
        ))
        count += 1
    conn.commit()
    return count


def seed_color_meanings(conn: sqlite3.Connection) -> int:
    """Seed color meanings table."""
    cursor = conn.cursor()
    count = 0
    for data in COLOR_MEANINGS_DATA:
        cursor.execute("""
            INSERT INTO flower_color_meanings
            (color, meaning_universal, meaning_ru, emotions, occasions)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get("color"),
            data.get("meaning_universal"),
            data.get("meaning_ru"),
            json.dumps(data.get("emotions")) if data.get("emotions") else None,
            json.dumps(data.get("occasions")) if data.get("occasions") else None,
        ))
        count += 1
    conn.commit()
    return count


def init_database(db_path: Path = DB_PATH) -> None:
    """Initialize the flower database with all seed data."""
    logger.info(f"Initializing database at {db_path}")

    # Remove existing database for clean start
    if db_path.exists():
        db_path.unlink()
        logger.info("Removed existing database")

    # Create connection
    conn = sqlite3.connect(str(db_path))

    try:
        # Create tables
        create_tables(conn)

        # Seed data
        flowers_count = seed_flowers(conn)
        logger.info(f"Seeded {flowers_count} flowers")

        meanings_count = seed_meanings(conn)
        logger.info(f"Seeded {meanings_count} flower meanings")

        contexts_count = seed_cultural_contexts(conn)
        logger.info(f"Seeded {contexts_count} cultural contexts")

        rules_count = seed_number_rules(conn)
        logger.info(f"Seeded {rules_count} regional number rules")

        colors_count = seed_color_meanings(conn)
        logger.info(f"Seeded {colors_count} color meanings")

        logger.info(f"Database initialized successfully at {db_path}")
        logger.info(f"File size: {db_path.stat().st_size / 1024:.1f} KB")

    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
