"""
Florist One Provider - Flower search for US/Canada.

Uses Florist One API (floristone.com/api) to search for flower products.
"""

import hashlib
import logging
from typing import List, ClassVar, Optional

import httpx

from backend.core.settings import get_settings
from backend.schemas.flower_product import ShopCard
from backend.services.providers.base import (
    BaseFlowerProvider,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderError,
)

logger = logging.getLogger(__name__)


class FloristOneProvider(BaseFlowerProvider):
    """
    Florist One API provider for US/Canada.

    Uses Florist One API to get flower products with affiliate links.
    Requires separate API keys for US and Canada.
    """

    name: ClassVar[str] = "floristone"
    supported_regions: ClassVar[List[str]] = ["US", "CA"]

    # Florist One API endpoint
    API_BASE_URL = "https://www.floristone.com/api/rest/flowershop"

    # Product categories for flower search
    FLOWER_CATEGORIES = [
        "roses",
        "mixed",
        "tulips",
        "lilies",
        "orchids",
        "sunflowers",
        "carnations",
    ]

    def __init__(self):
        self.settings = get_settings()

    async def search(
        self,
        flower_name: str,
        city: str,
        max_results: int = 10,
    ) -> List[ShopCard]:
        """
        Search for flower products using Florist One API.

        Args:
            flower_name: Flower name in English (e.g., "roses", "tulips")
            city: US/Canada city name (e.g., "New York", "Toronto")
            max_results: Maximum products to return

        Returns:
            List of ShopCard with flower products
        """
        # Determine region based on city (simple heuristic)
        region = self._detect_region(city)

        # Get appropriate API key
        api_key = self._get_api_key(region)
        if not api_key:
            logger.warning(f"Florist One API key not configured for {region}")
            raise ProviderAuthError(self.name, f"API key not configured for {region}")

        # Fetch products
        products = await self._fetch_products(api_key, flower_name, city, region, max_results)

        return products

    def _detect_region(self, city: str) -> str:
        """Detect region (US or CA) based on city name."""
        # Canadian cities
        canadian_cities = {
            "toronto", "vancouver", "montreal", "calgary", "ottawa",
            "edmonton", "winnipeg", "quebec", "hamilton", "kitchener",
            "london", "victoria", "halifax", "saskatoon", "regina",
        }

        city_lower = city.lower().strip()

        # Check if city is in Canada
        for ca_city in canadian_cities:
            if ca_city in city_lower:
                return "CA"

        # Default to US
        return "US"

    def _get_api_key(self, region: str) -> Optional[str]:
        """Get API key for region."""
        if region == "CA":
            return self.settings.florist_one_api_key_ca or self.settings.florist_one_api_key
        return self.settings.florist_one_api_key

    async def _fetch_products(
        self,
        api_key: str,
        flower_name: str,
        city: str,
        region: str,
        max_results: int,
    ) -> List[ShopCard]:
        """Fetch products from Florist One API."""
        products = []

        # Determine category based on flower name
        category = self._match_category(flower_name)

        # Build API URL
        # Florist One API: GET /flowershop/getproducts
        url = f"{self.API_BASE_URL}/getproducts"

        params = {
            "apikey": api_key,
            "category": category,
            "maxresults": max_results,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)

                if response.status_code == 401:
                    raise ProviderAuthError(self.name, "Invalid API key")

                if response.status_code == 429:
                    raise ProviderError(self.name, "Rate limit exceeded")

                response.raise_for_status()

                data = response.json()

                # Parse products from response
                if "products" in data:
                    for item in data["products"][:max_results]:
                        product = self._parse_product(item, city, region)
                        if product:
                            products.append(product)

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name, "Request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"Florist One API error: {e}")
            raise ProviderError(self.name, f"API error: {e.response.status_code}")

        return products

    def _match_category(self, flower_name: str) -> str:
        """Match flower name to API category."""
        flower_lower = flower_name.lower()

        # Direct category match
        for category in self.FLOWER_CATEGORIES:
            if category in flower_lower or flower_lower in category:
                return category

        # Keyword mapping
        keyword_map = {
            "rose": "roses",
            "tulip": "tulips",
            "lily": "lilies",
            "orchid": "orchids",
            "sunflower": "sunflowers",
            "carnation": "carnations",
            "daisy": "mixed",
            "bouquet": "mixed",
        }

        for keyword, category in keyword_map.items():
            if keyword in flower_lower:
                return category

        # Default to mixed
        return "mixed"

    def _parse_product(self, item: dict, city: str, region: str) -> Optional[ShopCard]:
        """Parse product item from API response."""
        try:
            name = item.get("name") or item.get("productname", "")
            if not name:
                return None

            # Get price
            price_value = None
            price_str = ""

            if "price" in item:
                price_value = float(item["price"])
                currency_symbol = "$" if region == "US" else "CA$"
                price_str = f"{currency_symbol}{price_value:.2f}"

            # Get image URL
            image_url = item.get("imageurl") or item.get("image")

            # Build buy URL (affiliate link)
            product_id = item.get("productid") or item.get("id", "")
            buy_url = item.get("url") or f"https://www.floristone.com/flowers/{product_id}"

            # Generate unique ID
            unique_id = hashlib.md5(f"{name}|{product_id}".encode()).hexdigest()[:16]

            return ShopCard(
                product_id=unique_id,
                name=name,
                price=price_str,
                price_value=price_value,
                currency="USD" if region == "US" else "CAD",
                image_url=image_url,
                vendor="Florist One",
                buy_url=buy_url,
                city=city,
            )

        except Exception as e:
            logger.debug(f"Failed to parse product: {e}")
            return None
