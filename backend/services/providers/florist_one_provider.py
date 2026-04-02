"""
Florist One Provider - Flower search for US/Canada.

Uses Florist One API (floristone.com/api) to search for flower products.
API Documentation: https://florist.one/api/documentation/
"""

import hashlib
import logging
from typing import List, ClassVar, Optional
import base64

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

    Uses Florist One REST API with HTTP Basic Authentication.
    API Base: https://www.floristone.com/api/rest/flowershop/
    """

    name: ClassVar[str] = "floristone"
    supported_regions: ClassVar[List[str]] = ["US", "CA"]

    # Florist One API endpoint
    API_BASE_URL = "https://www.floristone.com/api/rest/flowershop"

    # Color keywords for post-fetch filtering
    COLOR_KEYWORDS = {
        "red", "pink", "white", "yellow", "orange", "purple", "blue",
        "lavender", "peach", "coral", "burgundy", "crimson", "blush",
        "mixed", "rainbow", "multicolor", "assorted",
    }

    # Category codes from API documentation
    # Occasions
    OCCASION_CATEGORIES = {
        "bs": "Best Sellers",
        "ao": "Every Day",
        "bd": "Birthday",
        "an": "Anniversary",
        "lr": "Love & Romance",
        "gw": "Get Well",
        "nb": "New Baby",
        "ty": "Thank You",
        "sy": "Funeral and Sympathy",
    }

    # Product types
    PRODUCT_CATEGORIES = {
        "c": "Centerpieces",
        "o": "One Sided Arrangements",
        "v": "Vased Arrangements",
        "r": "Roses",
        "x": "Fruit Baskets",
        "p": "Plants",
        "b": "Balloons",
    }

    # Seasonal
    SEASONAL_CATEGORIES = {
        "cm": "Christmas",
        "ea": "Easter",
        "vd": "Valentines Day",
        "md": "Mothers Day",
    }

    # Flower name to category mapping
    FLOWER_TO_CATEGORY = {
        # Roses
        "rose": "r",
        "roses": "r",
        "red rose": "r",
        "pink rose": "r",
        "white rose": "r",
        "yellow rose": "r",
        # Romance related
        "love": "lr",
        "romance": "lr",
        "romantic": "lr",
        "valentine": "vd",
        # Occasions
        "birthday": "bd",
        "anniversary": "an",
        "get well": "gw",
        "sympathy": "sy",
        "funeral": "sy",
        "condolence": "sy",
        "baby": "nb",
        "thank you": "ty",
        "thanks": "ty",
        "gratitude": "ty",
        "mother": "md",
        "mom": "md",
        "christmas": "cm",
        "easter": "ea",
        # Product types
        "plant": "p",
        "plants": "p",
        "centerpiece": "c",
        "vase": "v",
        "arrangement": "v",
        "basket": "x",
        # Generic flowers - use best sellers or everyday
        "tulip": "ao",
        "tulips": "ao",
        "lily": "ao",
        "lilies": "ao",
        "orchid": "ao",
        "orchids": "ao",
        "sunflower": "ao",
        "sunflowers": "ao",
        "carnation": "ao",
        "carnations": "ao",
        "daisy": "ao",
        "daisies": "ao",
        "peony": "ao",
        "peonies": "ao",
        "hydrangea": "ao",
        "chrysanthemum": "ao",
        "lavender": "ao",
        "iris": "ao",
        "gerbera": "ao",
        "bouquet": "bs",
        "flowers": "bs",
        "mixed": "bs",
    }

    # Canadian cities for region detection
    CANADIAN_CITIES = {
        "toronto", "vancouver", "montreal", "calgary", "ottawa",
        "edmonton", "winnipeg", "quebec", "hamilton", "kitchener",
        "london", "victoria", "halifax", "saskatoon", "regina",
        "mississauga", "brampton", "surrey", "laval", "markham",
    }

    def __init__(self):
        self.settings = get_settings()

    def _extract_filter_keywords(self, flower_name: str) -> set:
        """Extract color/attribute keywords from user input."""
        words = set(flower_name.lower().split())
        return words & self.COLOR_KEYWORDS

    def _filter_products_by_keywords(
        self,
        products: List[ShopCard],
        keywords: set,
        original_name: str,
    ) -> List[ShopCard]:
        """Filter products by matching keywords in name/description."""
        if not keywords:
            return products

        filtered = []
        for product in products:
            name_lower = product.name.lower()
            if any(kw in name_lower for kw in keywords):
                filtered.append(product)

        # Graceful fallback: if no matches, return original
        return filtered if filtered else products

    def _get_auth_header(self) -> str:
        """Generate HTTP Basic Auth header."""
        api_key = self.settings.florist_one_api_key
        api_password = self.settings.florist_one_api_password

        if not api_key or not api_password:
            raise ProviderAuthError(self.name, "API credentials not configured")

        credentials = f"{api_key}:{api_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def search(
        self,
        flower_name: str,
        city: str,
        max_results: int = 10,
    ) -> List[ShopCard]:
        """
        Search for flower products using Florist One API.

        Args:
            flower_name: Flower name or occasion (e.g., "roses", "birthday")
            city: US/Canada city name (e.g., "New York", "Toronto")
            max_results: Maximum products to return

        Returns:
            List of ShopCard with flower products
        """
        # Determine region based on city
        region = self._detect_region(city)

        # Get category for the flower
        category = self._match_category(flower_name)

        # Extract keywords for filtering
        filter_keywords = self._extract_filter_keywords(flower_name)

        # Fetch more products to allow for filtering
        fetch_count = max_results * 3 if filter_keywords else max_results

        logger.info(f"FloristOne search: flower='{flower_name}', city='{city}', "
                    f"region={region}, category={category}, filter_keywords={filter_keywords}")

        # Fetch products
        products = await self._fetch_products(category, fetch_count, city, region)

        # Filter by keywords
        if filter_keywords:
            products = self._filter_products_by_keywords(products, filter_keywords, flower_name)

        # Limit results
        return products[:max_results]

    def _detect_region(self, city: str) -> str:
        """Detect region (US or CA) based on city name."""
        city_lower = city.lower().strip()

        for ca_city in self.CANADIAN_CITIES:
            if ca_city in city_lower:
                return "CA"

        return "US"

    def _match_category(self, flower_name: str) -> str:
        """Match flower name to API category code."""
        flower_lower = flower_name.lower().strip()

        # Direct match
        if flower_lower in self.FLOWER_TO_CATEGORY:
            return self.FLOWER_TO_CATEGORY[flower_lower]

        # Partial match
        for keyword, category in self.FLOWER_TO_CATEGORY.items():
            if keyword in flower_lower or flower_lower in keyword:
                return category

        # Default to best sellers
        return "bs"

    async def _fetch_products(
        self,
        category: str,
        max_results: int,
        city: str,
        region: str,
    ) -> List[ShopCard]:
        """Fetch products from Florist One API."""
        products = []

        url = f"{self.API_BASE_URL}/getproducts"
        params = {
            "category": category,
            "count": max_results,
            "start": 1,
        }

        headers = {
            "Authorization": self._get_auth_header(),
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)

                if response.status_code == 401 or response.status_code == 403:
                    raise ProviderAuthError(self.name, "Invalid API credentials")

                if response.status_code == 429:
                    raise ProviderError(self.name, "Rate limit exceeded")

                response.raise_for_status()

                data = response.json()
                logger.debug(f"FloristOne response: {len(data.get('PRODUCTS', []))} products")

                # Parse products from response
                if "PRODUCTS" in data:
                    for item in data["PRODUCTS"][:max_results]:
                        product = self._parse_product(item, city, region)
                        if product:
                            products.append(product)

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name, "Request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"Florist One API error: {e}")
            raise ProviderError(self.name, f"API error: {e.response.status_code}")

        return products

    def _parse_product(self, item: dict, city: str, region: str) -> Optional[ShopCard]:
        """Parse product item from API response."""
        try:
            # API returns uppercase keys
            name = item.get("NAME", "")
            if not name:
                return None

            # Get product code
            code = item.get("CODE", "")

            # Get price
            price_value = None
            price_str = ""

            if "PRICE" in item:
                price_value = float(item["PRICE"])
                currency_symbol = "$" if region == "US" else "CA$"
                price_str = f"{currency_symbol}{price_value:.2f}"

            # Get image URL (prefer LARGE, fallback to SMALL)
            image_url = item.get("LARGE") or item.get("SMALL") or ""

            # Build buy URL using product code
            # Format: https://www.floristone.com/flowers/viewitem.asp?pid=CODE
            buy_url = f"https://www.floristone.com/flowers/viewitem.asp?pid={code}" if code else ""

            # Get description (truncate if too long)
            description = item.get("DESCRIPTION", "")
            if len(description) > 200:
                description = description[:197] + "..."

            # Get dimensions
            dimensions = item.get("DIMENSION", "")

            # Generate unique ID
            unique_id = hashlib.md5(f"floristone|{code}".encode()).hexdigest()[:16]

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

    async def get_product_by_code(self, code: str, city: str = "") -> Optional[ShopCard]:
        """
        Get a single product by its code.

        Args:
            code: Florist One product code (e.g., "FAA-100")
            city: City for regional pricing

        Returns:
            ShopCard or None if not found
        """
        region = self._detect_region(city) if city else "US"

        url = f"{self.API_BASE_URL}/getproducts"
        params = {"code": code}
        headers = {"Authorization": self._get_auth_header()}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # Single product response has different structure
                if data and "NAME" in data:
                    return self._parse_product(data, city, region)

        except Exception as e:
            logger.error(f"Failed to get product {code}: {e}")

        return None

    async def check_delivery_date(self, zipcode: str, date: Optional[str] = None) -> dict:
        """
        Check delivery availability for a zipcode.

        Args:
            zipcode: US zipcode or Canadian postal code
            date: Optional date in yyyy-mm-dd format to check specific date

        Returns:
            Dict with DATES array or DATE_AVAILABLE boolean
        """
        url = f"{self.API_BASE_URL}/checkdeliverydate"
        params = {"zipcode": zipcode}

        if date:
            params["date"] = date

        headers = {"Authorization": self._get_auth_header()}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Failed to check delivery date: {e}")
            return {"error": str(e)}
