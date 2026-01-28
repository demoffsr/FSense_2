"""
Rate Limiter - v1.0.0

In-memory sliding window rate limiter for FastAPI.

Features:
- Per-IP rate limiting
- Configurable requests per minute
- Automatic cleanup of old entries
- Thread-safe implementation
"""

import time
import threading
import logging
from collections import defaultdict
from typing import Optional, Tuple
from dataclasses import dataclass

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_REQUESTS_PER_MINUTE = 30
DEFAULT_BURST_SIZE = 10  # Allow burst of requests
CLEANUP_INTERVAL_SECONDS = 60  # Clean old entries every minute


# ═══════════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    burst_size: int = DEFAULT_BURST_SIZE
    enabled: bool = True


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding window rate limiter.

    Uses a sliding window algorithm to track requests per IP.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def is_allowed(self, identifier: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed for given identifier.

        Args:
            identifier: Unique identifier (e.g., IP address)

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        if not self.config.enabled:
            return (True, self.config.requests_per_minute, 0)

        now = time.time()
        window_start = now - 60  # 1 minute window

        with self._lock:
            # Cleanup old entries periodically
            if now - self._last_cleanup > CLEANUP_INTERVAL_SECONDS:
                self._cleanup_old_entries(window_start)
                self._last_cleanup = now

            # Get requests in current window
            requests = self._requests[identifier]

            # Remove requests outside window
            requests = [t for t in requests if t > window_start]
            self._requests[identifier] = requests

            # Check limit
            current_count = len(requests)
            limit = self.config.requests_per_minute + self.config.burst_size

            if current_count >= limit:
                # Calculate retry after
                if requests:
                    oldest = min(requests)
                    retry_after = int(oldest - window_start + 1)
                else:
                    retry_after = 60

                return (False, 0, retry_after)

            # Allow request
            requests.append(now)
            remaining = limit - len(requests)

            return (True, remaining, 0)

    def _cleanup_old_entries(self, window_start: float) -> None:
        """Remove entries with no recent requests."""
        empty_keys = []
        for key, requests in self._requests.items():
            # Filter old requests
            self._requests[key] = [t for t in requests if t > window_start]
            if not self._requests[key]:
                empty_keys.append(key)

        # Remove empty entries
        for key in empty_keys:
            del self._requests[key]

        if empty_keys:
            logger.debug(f"Rate limiter cleanup: removed {len(empty_keys)} inactive entries")

    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        with self._lock:
            return {
                "active_identifiers": len(self._requests),
                "config": {
                    "requests_per_minute": self.config.requests_per_minute,
                    "burst_size": self.config.burst_size,
                    "enabled": self.config.enabled,
                },
            }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI MIDDLEWARE
# ═══════════════════════════════════════════════════════════════════════════════

# Global rate limiter instance
_rate_limiter: Optional[SlidingWindowRateLimiter] = None


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = SlidingWindowRateLimiter()
    return _rate_limiter


def configure_rate_limiter(
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
    burst_size: int = DEFAULT_BURST_SIZE,
    enabled: bool = True,
) -> SlidingWindowRateLimiter:
    """Configure global rate limiter."""
    global _rate_limiter
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
        enabled=enabled,
    )
    _rate_limiter = SlidingWindowRateLimiter(config)
    logger.info(f"Rate limiter configured: {requests_per_minute} req/min + {burst_size} burst")
    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.

    Handles:
    - X-Forwarded-For header (proxy/load balancer)
    - X-Real-IP header
    - Direct client connection
    """
    # Check X-Forwarded-For (may contain multiple IPs)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP is the client
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client
    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Adds headers to response:
    - X-RateLimit-Limit: Maximum requests per minute
    - X-RateLimit-Remaining: Remaining requests in current window
    - X-RateLimit-Reset: Seconds until rate limit resets
    """

    # Paths to exclude from rate limiting
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/logs",
        "/api/logs/stream",
    }

    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Get rate limiter
        limiter = get_rate_limiter()
        client_ip = get_client_ip(request)

        # Check rate limit
        is_allowed, remaining, retry_after = limiter.is_allowed(client_ip)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(limiter.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after),
                    "Retry-After": str(retry_after),
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limiter.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
