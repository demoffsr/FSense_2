"""
Tests for flower search providers.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.services.providers.base import BaseFlowerProvider
from backend.services.providers.factory import ProviderFactory
from backend.services.providers.yandex_provider import YandexFlowerProvider
from backend.services.providers.florist_one_provider import FloristOneProvider
from backend.services.providers.fallback_provider import FallbackProvider
from backend.schemas.flower_product import ShopCard


class TestProviderFactory:
    """Tests for ProviderFactory."""

    def test_factory_returns_yandex_for_ru(self):
        """RU region returns Yandex provider."""
        provider = ProviderFactory.get_provider("RU")
        assert provider.name == "yandex"

    def test_factory_returns_florist_one_for_us(self):
        """US region returns Florist One provider."""
        provider = ProviderFactory.get_provider("US")
        assert provider.name == "floristone"

    def test_factory_returns_florist_one_for_ca(self):
        """CA region returns Florist One provider."""
        provider = ProviderFactory.get_provider("CA")
        assert provider.name == "floristone"

    def test_factory_returns_fallback_for_unknown(self):
        """Unknown region returns Fallback provider."""
        provider = ProviderFactory.get_provider("XX")
        assert provider.name == "fallback"

    def test_factory_case_insensitive(self):
        """Region matching is case-insensitive."""
        assert ProviderFactory.get_provider("ru").name == "yandex"
        assert ProviderFactory.get_provider("Ru").name == "yandex"
        assert ProviderFactory.get_provider("RU").name == "yandex"


class TestYandexProvider:
    """Tests for YandexFlowerProvider."""

    def test_supported_regions(self):
        """Yandex supports RU region."""
        provider = YandexFlowerProvider()
        assert provider.supports_region("RU")
        assert not provider.supports_region("US")

    def test_get_region_id_moscow(self):
        """Moscow returns correct region ID."""
        provider = YandexFlowerProvider()
        assert provider._get_region_id("Москва") == 213
        assert provider._get_region_id("moscow") == 213

    def test_get_region_id_spb(self):
        """Saint Petersburg returns correct region ID."""
        provider = YandexFlowerProvider()
        assert provider._get_region_id("Санкт-Петербург") == 2
        assert provider._get_region_id("СПб") == 2

    def test_get_region_id_unknown_defaults_to_moscow(self):
        """Unknown city defaults to Moscow (213)."""
        provider = YandexFlowerProvider()
        assert provider._get_region_id("Неизвестный город") == 213

    def test_build_query(self):
        """Query is built correctly."""
        provider = YandexFlowerProvider()
        query = provider._build_query("розы", "Москва")
        assert "розы" in query
        assert "Москва" in query
        assert "купить" in query

    def test_extract_price_rub(self):
        """Extracts RUB price from text."""
        provider = YandexFlowerProvider()
        price, value = provider._extract_price("Цена: 2500 руб")
        assert value == 2500.0
        assert "₽" in price

    def test_extract_price_symbol(self):
        """Extracts price with ₽ symbol."""
        provider = YandexFlowerProvider()
        price, value = provider._extract_price("Букет роз за 3500₽")
        assert value == 3500.0

    def test_extract_price_no_match(self):
        """Returns None when no price found."""
        provider = YandexFlowerProvider()
        price, value = provider._extract_price("No price here")
        assert value is None
        assert price == ""


class TestFloristOneProvider:
    """Tests for FloristOneProvider."""

    def test_supported_regions(self):
        """Florist One supports US and CA regions."""
        provider = FloristOneProvider()
        assert provider.supports_region("US")
        assert provider.supports_region("CA")
        assert not provider.supports_region("RU")

    def test_match_category(self):
        """Category matching works correctly."""
        provider = FloristOneProvider()
        assert provider._match_category("red roses") == "roses"
        assert provider._match_category("tulips") == "tulips"
        assert provider._match_category("mixed bouquet") == "mixed"

    def test_detect_region(self):
        """Region detection works correctly."""
        provider = FloristOneProvider()
        assert provider._detect_region("New York") == "US"
        assert provider._detect_region("Toronto") == "CA"
        assert provider._detect_region("Vancouver") == "CA"
        assert provider._detect_region("Los Angeles") == "US"


class TestFallbackProvider:
    """Tests for FallbackProvider."""

    def test_name(self):
        """Fallback provider has correct name."""
        provider = FallbackProvider()
        assert provider.name == "fallback"

    def test_supports_all_regions(self):
        """Fallback supports any region."""
        provider = FallbackProvider()
        assert provider.supports_region("XX")
        assert provider.supports_region("ANY")

    def test_search_returns_mock_data(self):
        """Fallback returns mock products."""
        import asyncio
        provider = FallbackProvider()
        products = asyncio.run(provider.search("roses", "New York", max_results=5))
        assert len(products) > 0
        assert all(isinstance(p, ShopCard) for p in products)


class TestShopCard:
    """Tests for ShopCard model."""

    def test_shop_card_creation(self):
        """ShopCard can be created with required fields."""
        card = ShopCard(
            product_id="123",
            name="Red Roses",
            price="$49.99",
            vendor="Test Florist",
            buy_url="https://example.com/roses",
        )
        assert card.product_id == "123"
        assert card.currency == "USD"  # Default

    def test_shop_card_with_optional_fields(self):
        """ShopCard accepts optional fields."""
        card = ShopCard(
            product_id="123",
            name="Red Roses",
            price="2500 ₽",
            price_value=2500.0,
            currency="RUB",
            image_url="https://example.com/image.jpg",
            vendor="Test Florist",
            buy_url="https://example.com/roses",
            city="Москва",
        )
        assert card.city == "Москва"
        assert card.currency == "RUB"
        assert card.price_value == 2500.0
