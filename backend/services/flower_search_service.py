"""
Flower Search Service - Main service using provider pattern.

Delegates search to appropriate provider based on region:
- YandexProvider for Russia (RU)
- FloristOneProvider for US/Canada (US, CA)
- FallbackProvider for other regions

Includes SQLite caching to avoid repeated API calls.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from backend.schemas.flower_product import FlowerSearchResponse
from backend.services.providers.factory import ProviderFactory
from backend.services.providers.base import ProviderError
from backend.core.log_queue import broadcast_log
from backend.services.search_cache import get_search_cache

logger = logging.getLogger(__name__)


class FlowerSearchError(Exception):
    """Base exception for flower search errors."""
    pass


class FlowerSearchService:
    """
    Main service for searching flower products.

    Uses the provider pattern to delegate searches to
    region-specific providers.
    """

    async def search_products(
        self,
        flower_name: str,
        city: str,
        region: str = "US",
        max_results: int = 10,
        skip_cache: bool = False,
    ) -> FlowerSearchResponse:
        """
        Search for flower products.

        Args:
            flower_name: Name of flower to search
            city: City for delivery/search
            region: Geographic region (US, CA, RU)
            max_results: Maximum products to return
            skip_cache: If True, bypass cache and force fresh search

        Returns:
            FlowerSearchResponse with products from appropriate provider
        """
        query = f"{flower_name} {city}"
        is_yandex = region == "RU"
        cache = get_search_cache()

        # Check cache first (unless skip_cache)
        if not skip_cache:
            cached_products, cached_at = cache.get_with_metadata(flower_name, city, region)
            if cached_products:
                logger.info(f"Cache HIT for '{flower_name}' in '{city}' ({region})")

                # Broadcast cache hit to logs
                if is_yandex:
                    broadcast_log({
                        "type": "yandex_cache_hit",
                        "source": "yandex",
                        "query": flower_name,
                        "city": city,
                        "count": len(cached_products),
                    })

                return FlowerSearchResponse(
                    success=True,
                    query=query,
                    provider="cache",
                    products=cached_products[:max_results],
                    cached_at=cached_at,
                )

        # Get provider for region
        provider = ProviderFactory.get_provider(region)
        start_time = time.time()

        # Broadcast search start for Yandex
        if is_yandex:
            broadcast_log({
                "type": "yandex_search_start",
                "source": "yandex",
                "query": flower_name,
                "city": city,
            })

        try:
            # Search using provider
            products = await provider.search(
                flower_name=flower_name,
                city=city,
                max_results=max_results,
            )

            logger.info(
                f"Provider '{provider.name}' returned {len(products)} products "
                f"for '{flower_name}' in '{city}' ({region})"
            )

            # Broadcast each product for Yandex
            if is_yandex:
                for product in products[:5]:  # Limit to 5 products in logs
                    broadcast_log({
                        "type": "yandex_product",
                        "source": "yandex",
                        "name": product.name,
                        "price": product.price,
                        "vendor": product.vendor or "Unknown",
                    })

                # Broadcast search completion
                elapsed = round(time.time() - start_time, 2)
                broadcast_log({
                    "type": "yandex_search_end",
                    "source": "yandex",
                    "count": len(products),
                    "time": elapsed,
                })
                broadcast_log({
                    "type": "yandex_separator",
                    "source": "yandex",
                })

            # Cache successful results
            now = datetime.utcnow().isoformat()
            if products:
                cache.set(flower_name, city, region, products, provider.name)
                logger.info(f"Cached {len(products)} products for '{flower_name}' in '{city}' ({region})")

            return FlowerSearchResponse(
                success=True,
                query=query,
                provider=provider.name,
                products=products,
                cached_at=now,  # Fresh results cached just now
            )

        except ProviderError as e:
            logger.error(f"Provider error: {e}")

            # Broadcast error for Yandex
            if is_yandex:
                broadcast_log({
                    "type": "yandex_error",
                    "source": "yandex",
                    "error": str(e.message),
                })

            return FlowerSearchResponse(
                success=False,
                query=query,
                provider=provider.name,
                products=[],
                error=str(e.message),
            )

        except Exception as e:
            logger.exception(f"Unexpected error searching flowers: {e}")

            # Broadcast error for Yandex
            if is_yandex:
                broadcast_log({
                    "type": "yandex_error",
                    "source": "yandex",
                    "error": str(e),
                })

            return FlowerSearchResponse(
                success=False,
                query=query,
                provider=provider.name,
                products=[],
                error="Failed to search for flowers. Please try again.",
            )
