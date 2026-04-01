"""
Supabase Storage Service - v1.0.0

Handles file uploads to Supabase Storage bucket.
Used for storing generated flower images.
"""

import logging
import os
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Bucket configuration
BUCKET_NAME = "flower-images"


class StorageService:
    """
    Service for uploading files to Supabase Storage.

    Falls back to local storage if Supabase is not configured.
    """

    def __init__(self):
        self._client = None
        self._supabase_url = os.getenv("SUPABASE_URL", "")
        self._supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self._local_dir = Path(__file__).parent.parent / "static" / "images"
        self._local_dir.mkdir(parents=True, exist_ok=True)

    def _get_client(self):
        """Lazy initialization of Supabase client."""
        if self._client is None:
            if not self._supabase_url or not self._supabase_key:
                logger.warning("Supabase credentials not configured, using local storage")
                return None

            try:
                from supabase import create_client
                self._client = create_client(self._supabase_url, self._supabase_key)
                logger.info("Supabase Storage client initialized")
            except ImportError:
                logger.error("supabase package not installed")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                return None

        return self._client

    def upload_image(
        self,
        image_data: bytes,
        filename: str,
        content_type: str = "image/png",
    ) -> Tuple[Optional[str], bool]:
        """
        Upload image to Supabase Storage.

        Args:
            image_data: Image bytes
            filename: Target filename (e.g., "abc123.png")
            content_type: MIME type

        Returns:
            (public_url, is_supabase) tuple
            - public_url: URL to access the image
            - is_supabase: True if uploaded to Supabase, False if local
        """
        client = self._get_client()

        if client:
            return self._upload_to_supabase(client, image_data, filename, content_type)
        else:
            return self._save_locally(image_data, filename)

    def _upload_to_supabase(
        self,
        client,
        image_data: bytes,
        filename: str,
        content_type: str,
    ) -> Tuple[Optional[str], bool]:
        """Upload to Supabase Storage."""
        try:
            # Upload file
            result = client.storage.from_(BUCKET_NAME).upload(
                path=filename,
                file=image_data,
                file_options={"content-type": content_type, "upsert": "true"},
            )

            # Get public URL
            public_url = client.storage.from_(BUCKET_NAME).get_public_url(filename)

            logger.info(f"Uploaded to Supabase Storage: {filename}")
            return (public_url, True)

        except Exception as e:
            logger.error(f"Supabase upload failed: {e}, falling back to local")
            return self._save_locally(image_data, filename)

    def _save_locally(
        self,
        image_data: bytes,
        filename: str,
    ) -> Tuple[Optional[str], bool]:
        """Save to local filesystem (fallback)."""
        try:
            file_path = self._local_dir / filename
            with open(file_path, "wb") as f:
                f.write(image_data)

            # Return relative URL for FastAPI static serving
            local_url = f"/static/images/{filename}"
            logger.info(f"Saved locally: {filename}")
            return (local_url, False)

        except Exception as e:
            logger.error(f"Local save failed: {e}")
            return (None, False)

    def delete_image(self, filename: str) -> bool:
        """
        Delete image from storage.

        Args:
            filename: Filename to delete

        Returns:
            True if deleted successfully
        """
        client = self._get_client()

        if client:
            try:
                client.storage.from_(BUCKET_NAME).remove([filename])
                logger.info(f"Deleted from Supabase: {filename}")
                return True
            except Exception as e:
                logger.error(f"Supabase delete failed: {e}")
                return False
        else:
            # Delete locally
            try:
                file_path = self._local_dir / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted locally: {filename}")
                return True
            except Exception as e:
                logger.error(f"Local delete failed: {e}")
                return False

    def get_public_url(self, filename: str) -> Optional[str]:
        """
        Get public URL for an image.

        Args:
            filename: Image filename

        Returns:
            Public URL or None
        """
        client = self._get_client()

        if client:
            try:
                return client.storage.from_(BUCKET_NAME).get_public_url(filename)
            except Exception as e:
                logger.error(f"Failed to get public URL: {e}")
                return None
        else:
            return f"/static/images/{filename}"

    def is_supabase_configured(self) -> bool:
        """Check if Supabase Storage is properly configured."""
        return bool(self._supabase_url and self._supabase_key)


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
