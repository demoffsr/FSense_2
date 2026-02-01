"""
Flower Product Schema - for "Find Flowers" feature

Defines product card data from flower shop search results.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ShopCard(BaseModel):
    """Product card for flower shop search results."""

    product_id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    price: str = Field(..., description="Formatted price (e.g., '$49.99', '2500 ₽')")
    price_value: Optional[float] = Field(None, description="Numeric price for sorting")
    currency: str = Field(default="USD", description="Currency code: USD, CAD, RUB")
    image_url: Optional[str] = Field(None, description="Product image URL")
    vendor: str = Field(..., description="Store/vendor name")
    buy_url: str = Field(..., description="Direct link to purchase")
    city: Optional[str] = Field(None, description="City where product is available")


# Alias for backward compatibility
FlowerProduct = ShopCard


class FlowerSearchRequest(BaseModel):
    """Request body for flower product search."""

    flower_name: str = Field(..., description="Flower name to search")
    city: str = Field(..., description="City for delivery/search")
    region: str = Field(default="US", description="Geographic region: US, CA, RU")
    max_results: int = Field(default=10, ge=1, le=20, description="Max products to return")
    skip_cache: bool = Field(default=False, description="Bypass cache and force fresh search")


class FlowerSearchResponse(BaseModel):
    """Response for flower product search."""

    success: bool = True
    query: str = Field(..., description="Search query used")
    provider: str = Field(default="unknown", description="Provider used: yandex, floristone, fallback")
    products: List[ShopCard] = Field(default_factory=list)
    error: Optional[str] = None
    cached_at: Optional[str] = Field(default=None, description="ISO timestamp when results were cached")
