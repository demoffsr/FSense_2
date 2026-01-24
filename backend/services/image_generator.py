"""
Image generation service using OpenAI DALL-E 3.

Generates flower images and uploads to Supabase Storage.
Falls back to local storage if Supabase is not configured.
"""

import logging
from pathlib import Path
import time
from typing import Tuple
import requests
from openai import OpenAI
import os

from backend.services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Raised when image generation fails"""
    pass


class ImageGenerator:
    """
    Service for generating flower images using AI (DALL-E 3).

    Uploads generated images to Supabase Storage.
    """

    def __init__(self):
        self.storage = get_storage_service()

        # Initialize OpenAI client (lazy initialization)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set - image generation will fail")

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client"""
        if self.client is None:
            if not self.api_key:
                raise ImageGenerationError("OPENAI_API_KEY not set")
            self.client = OpenAI(api_key=self.api_key)
        return self.client

    def generate_image(
        self,
        flower_name: str,
        emotion_context: str,
        cache_key: str,
    ) -> Tuple[str, str]:
        """
        Generate flower image and upload to Supabase Storage.

        Args:
            flower_name: Name of the flower (e.g., "Red Rose")
            emotion_context: Emotional context (e.g., "love", "apology")
            cache_key: Cache key for filename

        Returns:
            (storage_path, public_url) tuple

        Raises:
            ImageGenerationError: If generation fails
        """
        start_time = time.time()

        try:
            # Build AI prompt
            prompt = self._build_prompt(flower_name, emotion_context)
            logger.info(f"Generating image for {flower_name} ({emotion_context})")

            # Generate image with DALL-E
            image_data = self._call_ai_image_generator(prompt)

            # Upload to Supabase Storage (or local fallback)
            filename = f"{cache_key[:16]}.png"
            public_url, is_supabase = self.storage.upload_image(
                image_data=image_data,
                filename=filename,
                content_type="image/png",
            )

            if not public_url:
                raise ImageGenerationError("Failed to upload image to storage")

            storage_type = "Supabase" if is_supabase else "local"
            generation_time = int((time.time() - start_time) * 1000)
            logger.info(f"Image generated in {generation_time}ms ({storage_type}): {filename}")

            # Return path and URL
            storage_path = f"flower-images/{filename}" if is_supabase else f"static/images/{filename}"
            return (storage_path, public_url)

        except ImageGenerationError:
            raise
        except Exception as e:
            logger.error(f"Image generation failed: {e}", exc_info=True)
            raise ImageGenerationError(f"Failed to generate image: {str(e)}")

    def _build_prompt(self, flower_name: str, emotion_context: str) -> str:
        """
        Build AI image generation prompt

        Uses professional studio photo style for consistency.
        """
        # Extract color from flower name if present
        parts = flower_name.split()
        if len(parts) > 1:
            color = parts[0]
            flower_type = " ".join(parts[1:])
        else:
            color = ""
            flower_type = flower_name

        prompt = (
            f"A professional studio photo of a bouquet of {color} {flower_type}. "
            f"The bouquet is arranged in a consistent modern style, placed in the center of the frame, "
            f"on a dark contrasting background. No text, no watermark, no additional props. "
            f"Soft studio lighting, shallow depth of field, realistic floral texture."
        )

        # Add emotion context for variation
        if emotion_context:
            prompt += f" The composition evokes a sense of {emotion_context}."

        return prompt

    def _call_ai_image_generator(self, prompt: str) -> bytes:
        """
        Call OpenAI DALL-E 3 API to generate image

        Returns:
            Image data as bytes

        Raises:
            ImageGenerationError: If API call fails
        """
        try:
            client = self._get_client()
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="url",
            )

            image_url = response.data[0].url
            logger.info(f"Generated image URL: {image_url}")

            # Download image
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()

            return img_response.content

        except Exception as e:
            logger.error(f"DALL-E API call failed: {e}", exc_info=True)
            raise ImageGenerationError(f"AI image generation failed: {str(e)}")
