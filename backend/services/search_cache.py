"""
SQLite cache for flower search results.

Caches Yandex/FloristOne API responses to avoid repeated API calls
for the same flower+city+region combination.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List
from backend.schemas.flower_product import ShopCard


class FlowerSearchCache:
    """SQLite cache for flower search results."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in backend directory
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(backend_dir, "flower_search_cache.db")
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create cache table if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    cache_key TEXT PRIMARY KEY,
                    flower_name TEXT,
                    city TEXT,
                    region TEXT,
                    products TEXT,
                    provider TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON search_cache(expires_at)
            """)

    def _normalize(self, text: str) -> str:
        """Normalize text for cache key."""
        return text.lower().strip()

    def _make_key(self, flower_name: str, city: str, region: str) -> str:
        """Create cache key from search parameters."""
        return f"{self._normalize(flower_name)}:{self._normalize(city)}:{region}"

    def get(self, flower_name: str, city: str, region: str) -> Optional[List[ShopCard]]:
        """
        Get cached products if not expired.

        Args:
            flower_name: Name of flower
            city: City for search
            region: Region code (RU, US, etc.)

        Returns:
            List of ShopCard if cache hit, None if miss or expired
        """
        products, _ = self.get_with_metadata(flower_name, city, region)
        return products

    def get_with_metadata(
        self, flower_name: str, city: str, region: str
    ) -> tuple[Optional[List[ShopCard]], Optional[str]]:
        """
        Get cached products with metadata.

        Args:
            flower_name: Name of flower
            city: City for search
            region: Region code (RU, US, etc.)

        Returns:
            Tuple of (products, cached_at_timestamp) or (None, None) if miss/expired
        """
        key = self._make_key(flower_name, city, region)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM search_cache WHERE cache_key = ? AND expires_at > ?",
                (key, datetime.utcnow().isoformat())
            ).fetchone()

            if row:
                # Increment hit count
                conn.execute(
                    "UPDATE search_cache SET hit_count = hit_count + 1 WHERE cache_key = ?",
                    (key,)
                )
                conn.commit()
                products_data = json.loads(row["products"])
                products = [ShopCard(**p) for p in products_data]
                cached_at = row["created_at"]
                return products, cached_at
        return None, None

    def set(
        self,
        flower_name: str,
        city: str,
        region: str,
        products: List[ShopCard],
        provider: str,
        ttl_hours: int = 24
    ):
        """
        Store products in cache.

        Args:
            flower_name: Name of flower
            city: City for search
            region: Region code
            products: List of products to cache
            provider: Provider name (yandex, florist_one, etc.)
            ttl_hours: Time to live in hours (default 24)
        """
        key = self._make_key(flower_name, city, region)
        now = datetime.utcnow()
        expires = now + timedelta(hours=ttl_hours)

        products_json = json.dumps([p.model_dump() for p in products])

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO search_cache
                (cache_key, flower_name, city, region, products, provider, created_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                key, flower_name, city, region, products_json, provider,
                now.isoformat(), expires.isoformat()
            ))
            conn.commit()

    def clear_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of deleted entries
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM search_cache WHERE expires_at < ?",
                (datetime.utcnow().isoformat(),)
            )
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> dict:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            total = conn.execute("SELECT COUNT(*) as count FROM search_cache").fetchone()["count"]
            total_hits = conn.execute("SELECT SUM(hit_count) as hits FROM search_cache").fetchone()["hits"] or 0

            top_queries = conn.execute("""
                SELECT cache_key, hit_count
                FROM search_cache
                ORDER BY hit_count DESC
                LIMIT 10
            """).fetchall()

            return {
                "total_entries": total,
                "total_hits": total_hits,
                "top_queries": [
                    {"key": row["cache_key"], "hits": row["hit_count"]}
                    for row in top_queries
                ]
            }


# Singleton instance
_cache: Optional[FlowerSearchCache] = None


def get_search_cache() -> FlowerSearchCache:
    """Get or create the global search cache instance."""
    global _cache
    if _cache is None:
        _cache = FlowerSearchCache()
    return _cache
