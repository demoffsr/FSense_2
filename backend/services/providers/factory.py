"""
Provider Factory - Select appropriate provider based on region.
"""

import logging
from typing import Dict, Optional

from backend.services.providers.base import BaseFlowerProvider
from backend.services.providers.yandex_provider import YandexFlowerProvider
from backend.services.providers.florist_one_provider import FloristOneProvider
from backend.services.providers.fallback_provider import FallbackProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """
    Factory for selecting flower search provider by region.

    Providers are registered on module load and selected
    based on the user's region.
    """

    _providers: Dict[str, BaseFlowerProvider] = {}
    _fallback: Optional[BaseFlowerProvider] = None

    @classmethod
    def register(cls, provider: BaseFlowerProvider) -> None:
        """
        Register a provider for its supported regions.

        Args:
            provider: Provider instance to register
        """
        for region in provider.supported_regions:
            region_upper = region.upper()
            cls._providers[region_upper] = provider
            logger.debug(f"Registered {provider.name} for region {region_upper}")

    @classmethod
    def set_fallback(cls, provider: BaseFlowerProvider) -> None:
        """
        Set the fallback provider for unsupported regions.

        Args:
            provider: Fallback provider instance
        """
        cls._fallback = provider
        logger.debug(f"Set fallback provider: {provider.name}")

    @classmethod
    def get_provider(cls, region: str) -> BaseFlowerProvider:
        """
        Get appropriate provider for region.

        Args:
            region: Region code (e.g., "US", "CA", "RU")

        Returns:
            Provider for the region, or fallback if not found
        """
        region_upper = region.upper()

        if region_upper in cls._providers:
            provider = cls._providers[region_upper]
            logger.debug(f"Using {provider.name} for region {region_upper}")
            return provider

        logger.warning(f"No provider for region {region_upper}, using fallback")
        return cls._fallback or FallbackProvider()

    @classmethod
    def list_providers(cls) -> Dict[str, str]:
        """
        List all registered providers.

        Returns:
            Dict mapping region codes to provider names
        """
        return {
            region: provider.name
            for region, provider in cls._providers.items()
        }

    @classmethod
    def reset(cls) -> None:
        """Reset all registrations (for testing)."""
        cls._providers.clear()
        cls._fallback = None


# Register providers on module load
def _register_providers():
    """Register all available providers."""
    try:
        ProviderFactory.register(YandexFlowerProvider())
    except Exception as e:
        logger.warning(f"Failed to register Yandex provider: {e}")

    try:
        ProviderFactory.register(FloristOneProvider())
    except Exception as e:
        logger.warning(f"Failed to register Florist One provider: {e}")

    # Set fallback
    ProviderFactory.set_fallback(FallbackProvider())


# Auto-register on import
_register_providers()
