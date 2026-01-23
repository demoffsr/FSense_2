"""
High-level image service for managing generation and caching.

Orchestrates image generation, database caching, and status management.
"""

import logging
from typing import Optional, Tuple
import hashlib
import time

from backend.database.connection import get_db
from backend.database.repository import ImageCacheRepository
from backend.services.image_generator import ImageGenerator, ImageGenerationError

logger = logging.getLogger(__name__)


class ImageService:
    """
    High-level service for managing image generation and caching
    """

    def __init__(self):
        self.generator = ImageGenerator()

    def get_cache_key(self, flower_name: str, emotion_context: str) -> str:
        """
        Generate deterministic cache key from flower_name + emotion_context

        Examples:
            - get_cache_key("Red Rose", "love") -> "e3b0c442...1a7d6"
            - get_cache_key("White Lily", "sympathy") -> "5e884898...4c0f9"

        Args:
            flower_name: Name of the flower
            emotion_context: Emotional context

        Returns:
            SHA256 hash (64 chars)
        """
        # Normalize inputs
        normalized = f"{flower_name.lower().strip()}|{emotion_context.lower().strip()}"

        # SHA256 hash for uniqueness
        return hashlib.sha256(normalized.encode()).hexdigest()

    def get_or_create_entry(
        self,
        flower_name: str,
        emotion_context: str,
    ) -> Tuple[str, Optional[str], str]:
        """
        Get existing image or create pending entry

        Args:
            flower_name: Name of the flower
            emotion_context: Emotional context

        Returns:
            (cache_key, image_url, status) tuple
            - cache_key: str - for polling
            - image_url: Optional[str] - URL if completed, None otherwise
            - status: str - "pending" | "generating" | "completed" | "failed"
        """
        cache_key = self.get_cache_key(flower_name, emotion_context)

        with get_db() as db:
            repo = ImageCacheRepository(db)
            entry = repo.get_by_cache_key(cache_key)

            if entry:
                # Entry exists
                if entry.status == "completed" and entry.image_url:
                    logger.info(f"Cache HIT: {flower_name} ({emotion_context})")
                    return (cache_key, entry.image_url, "completed")
                else:
                    logger.info(f"Cache entry exists but not ready: {cache_key} status={entry.status}")
                    return (cache_key, None, entry.status)
            else:
                # Create new pending entry
                entry = repo.create(flower_name, emotion_context, cache_key)
                logger.info(f"Cache MISS: {flower_name} ({emotion_context}) - created pending entry")
                return (cache_key, None, "pending")

    def generate_image_sync(
        self,
        flower_name: str,
        emotion_context: str,
        cache_key: str,
    ) -> None:
        """
        Generate image synchronously (called by background task)

        Updates database with generation results.

        Args:
            flower_name: Name of the flower
            emotion_context: Emotional context
            cache_key: Cache key
        """
        start_time = time.time()

        # Mark as generating
        with get_db() as db:
            repo = ImageCacheRepository(db)
            repo.update_status(cache_key, "generating")

        try:
            # Generate image
            logger.info(f"Starting generation for {flower_name} ({emotion_context})")
            image_path, image_url = self.generator.generate_image(
                flower_name=flower_name,
                emotion_context=emotion_context,
                cache_key=cache_key,
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Mark as completed
            with get_db() as db:
                repo = ImageCacheRepository(db)
                repo.update_status(
                    cache_key=cache_key,
                    status="completed",
                    image_path=image_path,
                    image_url=image_url,
                    generation_time_ms=generation_time_ms,
                )

            logger.info(f"Image generation completed: {cache_key} in {generation_time_ms}ms")

        except ImageGenerationError as e:
            # Mark as failed
            with get_db() as db:
                repo = ImageCacheRepository(db)
                repo.update_status(
                    cache_key=cache_key,
                    status="failed",
                    error_message=str(e),
                )

            logger.error(f"Image generation failed: {cache_key} - {e}")
