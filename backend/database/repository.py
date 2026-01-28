"""
Database repository layer for image cache.

Provides CRUD operations for ImageCache model.
"""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from backend.database.models import ImageCache

logger = logging.getLogger(__name__)


class ImageCacheRepository:
    """Data access layer for image cache"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_cache_key(self, cache_key: str) -> Optional[ImageCache]:
        """Get cached image by cache key"""
        return self.db.query(ImageCache).filter(
            ImageCache.cache_key == cache_key
        ).first()

    def create(
        self,
        flower_name: str,
        emotion_context: str,
        cache_key: str,
    ) -> ImageCache:
        """Create new cache entry"""
        entry = ImageCache(
            flower_name=flower_name,
            emotion_context=emotion_context,
            cache_key=cache_key,
            status="pending",
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        logger.info(f"Created cache entry: {cache_key}")
        return entry

    def update_status(
        self,
        cache_key: str,
        status: str,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        error_message: Optional[str] = None,
        generation_time_ms: Optional[int] = None,
        prompt_used: Optional[str] = None,
    ) -> Optional[ImageCache]:
        """Update cache entry status"""
        entry = self.get_by_cache_key(cache_key)
        if not entry:
            logger.warning(f"Cache entry not found: {cache_key}")
            return None

        entry.status = status
        entry.updated_at = datetime.utcnow()

        if image_path:
            entry.image_path = image_path
        if image_url:
            entry.image_url = image_url
        if error_message:
            entry.error_message = error_message
        if generation_time_ms:
            entry.generation_time_ms = generation_time_ms
        if prompt_used:
            entry.prompt_used = prompt_used

        if status == "completed":
            entry.completed_at = datetime.utcnow()
        elif status == "failed":
            entry.retry_count += 1

        self.db.commit()
        self.db.refresh(entry)
        logger.info(f"Updated cache entry {cache_key}: status={status}")
        return entry

    def get_stale_pending_entries(self, timeout_minutes: int = 10) -> list[ImageCache]:
        """Get entries stuck in 'generating' status (for cleanup)"""
        threshold = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        return self.db.query(ImageCache).filter(
            ImageCache.status == "generating",
            ImageCache.updated_at < threshold,
        ).all()
