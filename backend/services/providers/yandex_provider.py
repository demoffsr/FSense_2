"""
Yandex Cloud Search API Provider - Flower search for Russia.

Uses Yandex Cloud Search API to search for flower shops and products.
Documentation: https://yandex.cloud/en/docs/search-api/
"""

import base64
import hashlib
import logging
import re
from typing import List, ClassVar

import httpx
from lxml import etree

from backend.core.settings import get_settings
from backend.schemas.flower_product import ShopCard
from backend.services.providers.base import (
    BaseFlowerProvider,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderError,
)

logger = logging.getLogger(__name__)


class YandexFlowerProvider(BaseFlowerProvider):
    """
    Yandex Cloud Search API provider for Russia.

    Uses Yandex Cloud Search API to search for flower products in Russian cities.
    Requires YANDEX_CLOUD_API_KEY and YANDEX_CLOUD_FOLDER_ID credentials.
    """

    name: ClassVar[str] = "yandex"
    supported_regions: ClassVar[List[str]] = ["RU"]

    # Yandex Cloud Search API v2 endpoint
    YANDEX_SEARCH_URL = "https://searchapi.api.cloud.yandex.net/v2/web/search"

    # City name -> Yandex region ID mapping (top Russian cities)
    CITY_REGION_MAP = {
        # Moscow and region
        "москва": 213,
        "moscow": 213,
        # Saint Petersburg
        "санкт-петербург": 2,
        "петербург": 2,
        "спб": 2,
        "saint petersburg": 2,
        # Major cities
        "новосибирск": 65,
        "екатеринбург": 54,
        "нижний новгород": 47,
        "казань": 43,
        "челябинск": 56,
        "омск": 66,
        "самара": 51,
        "ростов-на-дону": 39,
        "уфа": 172,
        "красноярск": 62,
        "пермь": 50,
        "воронеж": 193,
        "волгоград": 38,
        "краснодар": 35,
        "саратов": 194,
        "тюмень": 55,
        "тольятти": 240,
        "ижевск": 44,
        "барнаул": 197,
        "ульяновск": 195,
        "иркутск": 63,
        "хабаровск": 76,
        "ярославль": 16,
        "владивосток": 75,
        "махачкала": 28,
        "томск": 67,
        "оренбург": 48,
        "кемерово": 64,
        "новокузнецк": 237,
        "рязань": 11,
        "астрахань": 37,
        "набережные челны": 236,
        "пенза": 49,
        "липецк": 9,
        "тула": 15,
        "киров": 46,
        "чебоксары": 45,
        "калининград": 22,
        "брянск": 191,
        "курск": 8,
        "иваново": 5,
        "магнитогорск": 235,
        "тверь": 14,
        "ставрополь": 36,
        "белгород": 4,
        "сочи": 239,
    }

    # Default region ID (Moscow)
    DEFAULT_REGION_ID = 213

    def __init__(self):
        self.settings = get_settings()

    async def search(
        self,
        flower_name: str,
        city: str,
        max_results: int = 10,
    ) -> List[ShopCard]:
        """
        Search for flower products using Yandex Cloud Search API.

        Args:
            flower_name: Flower name in Russian (e.g., "розы", "тюльпаны")
            city: Russian city name (e.g., "Москва", "Санкт-Петербург")
            max_results: Maximum products to return

        Returns:
            List of ShopCard with flower products
        """
        # Validate credentials
        if not self.settings.yandex_cloud_api_key or not self.settings.yandex_cloud_folder_id:
            logger.warning("Yandex Cloud API credentials not configured")
            raise ProviderAuthError(self.name, "API credentials not configured")

        # Get region ID for city
        region_id = self._get_region_id(city)

        # Build search query
        query = self._build_query(flower_name, city)

        # Make API request
        products = await self._fetch_products(query, region_id, max_results)

        return products

    def _get_region_id(self, city: str) -> int:
        """Get Yandex region ID for city name."""
        city_lower = city.lower().strip()

        # Direct match
        if city_lower in self.CITY_REGION_MAP:
            return self.CITY_REGION_MAP[city_lower]

        # Partial match
        for city_name, region_id in self.CITY_REGION_MAP.items():
            if city_lower in city_name or city_name in city_lower:
                return region_id

        logger.warning(f"Unknown city '{city}', using default region (Moscow)")
        return self.DEFAULT_REGION_ID

    def _build_query(self, flower_name: str, city: str) -> str:
        """Build search query for Yandex."""
        # Search query: "купить букет {flower_name} {city} с доставкой цена"
        return f"купить букет {flower_name} {city} с доставкой цена"

    async def _fetch_products(
        self,
        query: str,
        region_id: int,
        max_results: int,
    ) -> List[ShopCard]:
        """Fetch products from Yandex Cloud Search API v2."""
        headers = {
            "Authorization": f"Api-Key {self.settings.yandex_cloud_api_key}",
            "Content-Type": "application/json",
        }

        # V2 API uses JSON body, returns base64-encoded XML
        body = {
            "query": {
                "searchType": "SEARCH_TYPE_RU",
                "queryText": query,
            },
            "folderId": self.settings.yandex_cloud_folder_id,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.YANDEX_SEARCH_URL,
                    headers=headers,
                    json=body,
                )

                if response.status_code == 401:
                    raise ProviderAuthError(self.name, "Invalid API credentials")
                if response.status_code == 403:
                    raise ProviderAuthError(self.name, "Access denied - check folder permissions")
                if response.status_code == 429:
                    raise ProviderError(self.name, "Rate limit exceeded")

                response.raise_for_status()

                # V2 API returns JSON with base64-encoded XML in rawData
                data = response.json()
                if "rawData" not in data:
                    logger.error("No rawData in Yandex response")
                    return []

                # Decode base64 XML
                xml_content = base64.b64decode(data["rawData"]).decode("utf-8")
                return self._parse_xml_response(xml_content, max_results)

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.name, "Request timed out")
        except httpx.HTTPStatusError as e:
            logger.error(f"Yandex API HTTP error: {e.response.status_code} - {e.response.text}")
            raise ProviderError(self.name, f"API error: {e.response.status_code}")

    def _parse_xml_response(self, xml_content: str, max_results: int) -> List[ShopCard]:
        """Parse Yandex XML response and extract products."""
        products = []

        try:
            root = etree.fromstring(xml_content.encode("utf-8"))

            # Check for errors
            error = root.find(".//error")
            if error is not None:
                error_code = error.get("code", "unknown")
                error_text = error.text or "Unknown error"
                logger.error(f"Yandex API error: {error_code} - {error_text}")
                raise ProviderError(self.name, f"API error: {error_text}")

            # Find all document groups
            groups = root.xpath("//group")

            for group in groups[:max_results]:
                try:
                    product = self._parse_group_xml(group)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Failed to parse group: {e}")
                    continue

        except etree.XMLSyntaxError as e:
            logger.error(f"Failed to parse XML: {e}")

        return products

    def _parse_group_xml(self, group) -> ShopCard | None:
        """Parse a single group element into ShopCard."""
        # Get document
        doc = group.find(".//doc")
        if doc is None:
            return None

        # Extract URL
        url_elem = doc.find("url")
        if url_elem is None or not url_elem.text:
            return None
        buy_url = url_elem.text

        # Extract title
        title_elem = doc.find(".//title")
        name = ""
        if title_elem is not None:
            # Get text content, handling mixed content with <hlword> tags
            name = "".join(title_elem.itertext()).strip()
            # Remove extra whitespace
            name = " ".join(name.split())

        if not name:
            return None

        # Extract domain as vendor
        domain_elem = doc.find("domain")
        vendor = domain_elem.text if domain_elem is not None else "Unknown"

        # Extract snippet for price detection
        snippet = ""
        passages = doc.findall(".//passage")
        for passage in passages:
            if passage is not None:
                passage_text = "".join(passage.itertext())
                snippet += passage_text + " "

        # Also check headline
        headline_elem = doc.find(".//headline")
        if headline_elem is not None:
            snippet += "".join(headline_elem.itertext()) + " "

        # Try to extract price from snippet and title
        price, price_value = self._extract_price(snippet + " " + name)

        # Generate product ID
        product_id = hashlib.md5(f"{name}|{vendor}|{buy_url}".encode()).hexdigest()[:16]

        # Use favicon as image (Yandex Search API doesn't provide product images)
        image_url = None
        if vendor:
            clean_domain = vendor.replace("www.", "")
            image_url = f"https://www.google.com/s2/favicons?sz=128&domain={clean_domain}"

        return ShopCard(
            product_id=product_id,
            name=name[:200],  # Limit name length
            price=price,
            price_value=price_value,
            currency="RUB",
            image_url=image_url,
            vendor=vendor,
            buy_url=buy_url,
            city=None,
        )

    def _extract_price(self, text: str) -> tuple[str, float | None]:
        """Extract price from text."""
        # Common Russian price patterns
        patterns = [
            r"(\d[\d\s]*)\s*(?:руб|₽|р\.?|rub)",  # 2500 руб, 2500₽
            r"(?:от|от\s+)(\d[\d\s]*)\s*(?:руб|₽|р\.?)",  # от 2500 руб
            r"цена[:\s]+(\d[\d\s]*)",  # цена: 2500
            r"(\d{3,})\s*(?:руб|₽|р)",  # 2500р (3+ digits to avoid false matches)
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                price_str = match.group(1).replace(" ", "").replace("\xa0", "")
                try:
                    price_value = float(price_str)
                    # Format with thousands separator
                    formatted = f"{int(price_value):,}".replace(",", " ")
                    return f"{formatted} ₽", price_value
                except ValueError:
                    continue

        return "", None
