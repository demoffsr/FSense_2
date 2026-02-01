"""
Base Flower Provider - Abstract base class for flower search providers.
"""

from abc import ABC, abstractmethod
from typing import List, ClassVar

from backend.schemas.flower_product import ShopCard


class BaseFlowerProvider(ABC):
    """
    Abstract base class for flower search providers.

    Each provider implements search for specific regions and uses
    different APIs/sources to find flower products.
    """

    # Provider name for logging/response
    name: ClassVar[str] = "base"

    # List of supported region codes (e.g., ["US", "CA"])
    supported_regions: ClassVar[List[str]] = []

    @abstractmethod
    async def search(
        self,
        flower_name: str,
        city: str,
        max_results: int = 10,
    ) -> List[ShopCard]:
        """
        Search for flower products.

        Args:
            flower_name: Name of flower to search (e.g., "roses", "розы")
            city: City for delivery/search (e.g., "New York", "Москва")
            max_results: Maximum number of products to return

        Returns:
            List of ShopCard with product information
        """
        pass

    def supports_region(self, region: str) -> bool:
        """Check if this provider supports the given region."""
        return region.upper() in [r.upper() for r in self.supported_regions]


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, provider: str, message: str):
        self.provider = provider
        self.message = message
        super().__init__(f"[{provider}] {message}")


class ProviderAuthError(ProviderError):
    """Raised when API authentication fails."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when API rate limit is exceeded."""
    pass


class ProviderTimeoutError(ProviderError):
    """Raised when API request times out."""
    pass
