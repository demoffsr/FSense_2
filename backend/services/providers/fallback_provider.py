"""
Fallback Provider - Mock data for unsupported regions.

Returns sample flower products when no real provider is available.
"""

import hashlib
import logging
from typing import List, ClassVar

from backend.schemas.flower_product import ShopCard
from backend.services.providers.base import BaseFlowerProvider

logger = logging.getLogger(__name__)


class FallbackProvider(BaseFlowerProvider):
    """
    Fallback provider with mock data.

    Used when no real provider is available for a region.
    Returns sample products to demonstrate the UI.
    """

    name: ClassVar[str] = "fallback"
    supported_regions: ClassVar[List[str]] = []  # Supports all regions as fallback

    # Sample products for demonstration
    SAMPLE_PRODUCTS = [
        {
            "name": "Classic Red Roses Bouquet",
            "price": "$49.99",
            "price_value": 49.99,
            "vendor": "Sample Florist",
            "image": "https://images.unsplash.com/photo-1518882605630-8eb572299d16?w=400",
        },
        {
            "name": "Mixed Spring Flowers",
            "price": "$39.99",
            "price_value": 39.99,
            "vendor": "Garden Dreams",
            "image": "https://images.unsplash.com/photo-1487530811176-3780de880c2d?w=400",
        },
        {
            "name": "Elegant White Lilies",
            "price": "$54.99",
            "price_value": 54.99,
            "vendor": "Bloom & Co",
            "image": "https://images.unsplash.com/photo-1460039230329-eb070f0da625?w=400",
        },
        {
            "name": "Sunny Sunflower Arrangement",
            "price": "$44.99",
            "price_value": 44.99,
            "vendor": "Sunshine Flowers",
            "image": "https://images.unsplash.com/photo-1551934190-5e98e1e68c72?w=400",
        },
        {
            "name": "Pink Tulips Collection",
            "price": "$35.99",
            "price_value": 35.99,
            "vendor": "Dutch Blooms",
            "image": "https://images.unsplash.com/photo-1520763185298-1b434c919102?w=400",
        },
    ]

    async def search(
        self,
        flower_name: str,
        city: str,
        max_results: int = 10,
    ) -> List[ShopCard]:
        """
        Return mock products for demonstration.

        Args:
            flower_name: Flower name (used for product naming)
            city: City name (included in response)
            max_results: Maximum products to return

        Returns:
            List of sample ShopCard products
        """
        logger.info(f"Using fallback provider for '{flower_name}' in '{city}'")

        products = []

        for i, sample in enumerate(self.SAMPLE_PRODUCTS[:max_results]):
            # Generate unique ID
            product_id = hashlib.md5(
                f"{sample['name']}|{sample['vendor']}|{i}".encode()
            ).hexdigest()[:16]

            product = ShopCard(
                product_id=product_id,
                name=sample["name"],
                price=sample["price"],
                price_value=sample["price_value"],
                currency="USD",
                image_url=sample["image"],
                vendor=sample["vendor"],
                buy_url=f"https://example.com/flowers/{product_id}",
                city=city,
            )
            products.append(product)

        return products

    def supports_region(self, region: str) -> bool:
        """Fallback supports all regions."""
        return True
