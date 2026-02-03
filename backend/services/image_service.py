"""
High-level image service for managing generation and caching.

Orchestrates image generation, database caching, and status management.

Features:
- Retry logic with exponential backoff
- Generation timeout
- Stale entry cleanup
- Concurrent generation limiting
"""

import logging
from typing import Optional, Tuple, List
import hashlib
import time
import threading
from datetime import datetime, timedelta

from backend.database.connection import get_db
from backend.database.repository import ImageCacheRepository
from backend.services.image_generator import ImageGenerator, ImageGenerationError

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 30
GENERATION_TIMEOUT_SECONDS = 120  # 2 minutes
STALE_ENTRY_TIMEOUT_MINUTES = 5
MAX_CONCURRENT_GENERATIONS = 3

# Global semaphore for limiting concurrent generations
_generation_semaphore = threading.Semaphore(MAX_CONCURRENT_GENERATIONS)
_active_generations = 0
_generations_lock = threading.Lock()


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
        Generate image synchronously (called by background task).

        Features:
        - Retry with exponential backoff (max 3 attempts)
        - Concurrency limiting via semaphore
        - Timeout protection
        - Stale entry cleanup

        Args:
            flower_name: Name of the flower
            emotion_context: Emotional context
            cache_key: Cache key
        """
        global _active_generations

        # Try to acquire semaphore (limits concurrent generations)
        if not _generation_semaphore.acquire(timeout=GENERATION_TIMEOUT_SECONDS):
            logger.warning(f"Generation timeout waiting for semaphore: {cache_key}")
            with get_db() as db:
                repo = ImageCacheRepository(db)
                repo.update_status(
                    cache_key=cache_key,
                    status="failed",
                    error_message="Generation queue timeout",
                )
            return

        try:
            with _generations_lock:
                _active_generations += 1
                logger.info(f"Active generations: {_active_generations}/{MAX_CONCURRENT_GENERATIONS}")

            # Mark as generating
            with get_db() as db:
                repo = ImageCacheRepository(db)
                repo.update_status(cache_key, "generating")

            # Retry loop with exponential backoff
            last_error = None
            for attempt in range(1, MAX_RETRIES + 1):
                start_time = time.time()

                try:
                    logger.info(f"Generation attempt {attempt}/{MAX_RETRIES} for {flower_name} ({emotion_context})")

                    image_path, image_url = self.generator.generate_image(
                        flower_name=flower_name,
                        emotion_context=emotion_context,
                        cache_key=cache_key,
                    )

                    generation_time_ms = int((time.time() - start_time) * 1000)

                    # Success - mark as completed
                    with get_db() as db:
                        repo = ImageCacheRepository(db)
                        repo.update_status(
                            cache_key=cache_key,
                            status="completed",
                            image_path=image_path,
                            image_url=image_url,
                            generation_time_ms=generation_time_ms,
                        )

                    logger.info(f"Image generation completed: {cache_key} in {generation_time_ms}ms (attempt {attempt})")
                    return  # Success!

                except ImageGenerationError as e:
                    last_error = e
                    logger.warning(f"Generation attempt {attempt} failed: {e}")

                    if attempt < MAX_RETRIES:
                        # Calculate backoff with exponential increase
                        backoff = min(INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1)), MAX_BACKOFF_SECONDS)
                        logger.info(f"Retrying in {backoff}s...")
                        time.sleep(backoff)

            # All retries exhausted
            with get_db() as db:
                repo = ImageCacheRepository(db)
                repo.update_status(
                    cache_key=cache_key,
                    status="failed",
                    error_message=f"Failed after {MAX_RETRIES} attempts: {last_error}",
                )

            logger.error(f"Image generation failed after {MAX_RETRIES} attempts: {cache_key}")

        finally:
            # Always release semaphore
            _generation_semaphore.release()
            with _generations_lock:
                _active_generations -= 1

    def cleanup_stale_entries(self) -> int:
        """
        Clean up stale pending/generating entries.

        Entries stuck in 'pending' or 'generating' for more than
        STALE_ENTRY_TIMEOUT_MINUTES are marked as failed.

        Returns:
            Number of entries cleaned up
        """
        cleaned = 0

        with get_db() as db:
            repo = ImageCacheRepository(db)

            # Get stale entries
            stale = repo.get_stale_pending_entries(timeout_minutes=STALE_ENTRY_TIMEOUT_MINUTES)

            for entry in stale:
                repo.update_status(
                    cache_key=entry.cache_key,
                    status="failed",
                    error_message=f"Timed out after {STALE_ENTRY_TIMEOUT_MINUTES} minutes",
                )
                cleaned += 1
                logger.warning(f"Cleaned up stale entry: {entry.cache_key}")

        if cleaned:
            logger.info(f"Cleaned up {cleaned} stale image generation entries")

        return cleaned

    @staticmethod
    def get_generation_stats() -> dict:
        """Get current generation statistics."""
        global _active_generations
        with _generations_lock:
            return {
                "active_generations": _active_generations,
                "max_concurrent": MAX_CONCURRENT_GENERATIONS,
                "available_slots": MAX_CONCURRENT_GENERATIONS - _active_generations,
            }


# ═══════════════════════════════════════════════════════════════════════════════
# PRE-WARMING CACHE
# ═══════════════════════════════════════════════════════════════════════════════

# Popular flowers for pre-caching
POPULAR_FLOWERS = [
    "Rose",
    "Red Rose",
    "White Rose",
    "Pink Rose",
    "Tulip",
    "Lily",
    "White Lily",
    "Orchid",
    "Sunflower",
    "Peony",
    "Carnation",
    "Chrysanthemum",
    "Lavender",
    "Daisy",
    "Hydrangea",
]

# Popular emotional contexts for pre-caching
POPULAR_EMOTIONS = [
    "love",
    "romantic love",
    "apology",
    "gratitude",
    "thank you",
    "celebration",
    "congratulations",
    "sympathy",
    "condolence",
    "friendship",
    "birthday",
    "anniversary",
    "wedding",
    "get well",
    "new baby",
]


def pre_warm_cache(
    flowers: Optional[List[str]] = None,
    emotions: Optional[List[str]] = None,
    max_generations: int = 10,
) -> dict:
    """
    Pre-generate images for popular flower/emotion combinations.

    This function creates cache entries for common combinations
    and schedules background generation. Useful for reducing
    latency for the most common use cases.

    Args:
        flowers: List of flower names (defaults to POPULAR_FLOWERS)
        emotions: List of emotion contexts (defaults to POPULAR_EMOTIONS)
        max_generations: Maximum number of new generations to trigger

    Returns:
        Dict with counts: {"checked": int, "cached": int, "scheduled": int}
    """
    flowers = flowers or POPULAR_FLOWERS[:7]  # Top 7 flowers
    emotions = emotions or POPULAR_EMOTIONS[:5]  # Top 5 emotions

    service = ImageService()
    stats = {
        "checked": 0,
        "cached": 0,
        "scheduled": 0,
    }

    # Import here to avoid circular dependency
    from backend.main import add_background_task

    for flower in flowers:
        for emotion in emotions:
            stats["checked"] += 1

            cache_key, image_url, status = service.get_or_create_entry(flower, emotion)

            if status == "completed":
                stats["cached"] += 1
                logger.debug(f"Pre-warm cache HIT: {flower} ({emotion})")

            elif status == "pending" and stats["scheduled"] < max_generations:
                # Schedule background generation
                add_background_task(
                    service.generate_image_sync,
                    flower,
                    emotion,
                    cache_key,
                )
                stats["scheduled"] += 1
                logger.info(f"Pre-warm scheduled: {flower} ({emotion})")

            # Stop if we've scheduled enough
            if stats["scheduled"] >= max_generations:
                logger.info(f"Pre-warm limit reached: {max_generations} generations scheduled")
                break

        if stats["scheduled"] >= max_generations:
            break

    logger.info(
        f"Pre-warm complete: checked={stats['checked']}, "
        f"cached={stats['cached']}, scheduled={stats['scheduled']}"
    )

    return stats
