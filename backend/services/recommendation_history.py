"""
Recommendation History Cache - v1.0.0

Tracks recent flower recommendations to enable diversity penalties.
Uses SQLite for persistence across requests.

The diversity penalty reduces the match_score of frequently recommended flowers
to encourage variety in recommendations.

Penalty formula: penalty = min(0.5, count * 0.05)
- 5 recommendations in 24h = -0.25 to score
- 10+ recommendations = max -0.5 penalty
"""

import sqlite3
import os
import threading
from datetime import datetime, timedelta
from typing import Optional


class RecommendationHistoryCache:
    """SQLite cache for tracking recent flower recommendations."""

    def __init__(self, db_path: str = None, max_history_hours: int = 24):
        """
        Initialize the recommendation history cache.

        Args:
            db_path: Path to SQLite database. Defaults to backend/recommendation_history.db
            max_history_hours: Hours to keep history before cleanup. Default 24.
        """
        if db_path is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(backend_dir, "recommendation_history.db")
        self.db_path = db_path
        self.max_history_hours = max_history_hours
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Create database connection with optimized settings."""
        return sqlite3.connect(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
        )

    def _init_db(self):
        """Create history table if not exists and enable WAL mode."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    flower_id TEXT NOT NULL,
                    emotion TEXT,
                    recommended_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_flower_time
                ON recommendation_history(flower_id, recommended_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recommended_at
                ON recommendation_history(recommended_at)
            """)
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")

    def record_recommendation(
        self,
        flower_id: str,
        session_id: str = None,
        emotion: str = None
    ) -> None:
        """
        Record a flower recommendation.

        Args:
            flower_id: The ID of the recommended flower
            session_id: Optional session identifier for tracking user sessions
            emotion: Optional emotion context for the recommendation
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO recommendation_history (session_id, flower_id, emotion, recommended_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, flower_id.lower(), emotion, datetime.utcnow().isoformat())
            )
            conn.commit()

    def get_recent_counts(self, hours: int = 24) -> dict[str, int]:
        """
        Get count of each flower recommended in last N hours.

        Args:
            hours: Number of hours to look back. Default 24.

        Returns:
            Dict mapping flower_id to recommendation count
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT flower_id, COUNT(*) as count
                FROM recommendation_history
                WHERE recommended_at > ?
                GROUP BY flower_id
                """,
                (cutoff.isoformat(),)
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def calculate_diversity_penalty(
        self,
        flower_id: str,
        hours: int = 24,
        base_penalty: float = 0.15,
        max_penalty: float = 0.7
    ) -> float:
        """
        Calculate diversity penalty based on recent recommendation frequency.

        The penalty increases linearly with the number of recent recommendations,
        capped at max_penalty to prevent complete suppression of good matches.

        Args:
            flower_id: The flower to check
            hours: Hours to look back for history. Default 24.
            base_penalty: Penalty per recommendation. Default 0.15 (3x stronger).
            max_penalty: Maximum penalty cap. Default 0.7.

        Returns:
            Penalty value (0.0-0.7) to subtract from match_score
        """
        counts = self.get_recent_counts(hours)
        count = counts.get(flower_id.lower(), 0)
        return min(max_penalty, count * base_penalty)

    def get_diversity_adjusted_score(
        self,
        flower_id: str,
        original_score: float,
        hours: int = 24
    ) -> float:
        """
        Get the diversity-adjusted match score for a flower.

        Args:
            flower_id: The flower ID
            original_score: Original match score (0.0-1.0)
            hours: Hours to look back. Default 24.

        Returns:
            Adjusted score (minimum 0.1 to keep flower viable)
        """
        penalty = self.calculate_diversity_penalty(flower_id, hours)
        return max(0.1, original_score - penalty)

    def clear_old_entries(self) -> int:
        """
        Remove entries older than max_history_hours.

        Returns:
            Number of deleted entries
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.max_history_hours)
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM recommendation_history WHERE recommended_at < ?",
                (cutoff.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> dict:
        """Get recommendation history statistics."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute(
                "SELECT COUNT(*) as count FROM recommendation_history"
            ).fetchone()["count"]

            top_flowers = conn.execute("""
                SELECT flower_id, COUNT(*) as count
                FROM recommendation_history
                WHERE recommended_at > ?
                GROUP BY flower_id
                ORDER BY count DESC
                LIMIT 10
            """, ((datetime.utcnow() - timedelta(hours=24)).isoformat(),)).fetchall()

            return {
                "total_entries": total,
                "top_flowers_24h": [
                    {"flower_id": row["flower_id"], "count": row["count"]}
                    for row in top_flowers
                ]
            }


# Singleton instance (Thread-Safe)
_cache: Optional[RecommendationHistoryCache] = None
_cache_lock = threading.Lock()


def get_recommendation_history() -> RecommendationHistoryCache:
    """
    Get or create the global recommendation history cache instance.

    Uses double-checked locking for thread safety.
    """
    global _cache
    if _cache is None:
        with _cache_lock:
            if _cache is None:
                _cache = RecommendationHistoryCache()
    return _cache


def reset_recommendation_history() -> None:
    """Reset recommendation history singleton (for testing). Thread-safe."""
    global _cache
    with _cache_lock:
        _cache = None
