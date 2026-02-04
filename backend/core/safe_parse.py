"""Safe parsing utilities for AI responses."""

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def safe_parse_float(
    value: Any,
    default: float = 0.0,
    min_val: float = 0.0,
    max_val: float = 1.0,
    context: str = "",
) -> float:
    """
    Safely parse a float value with fallback and clamping.

    Handles:
    - Non-numeric strings ("high", "0.7.2") → default
    - None → default
    - NaN, Inf, -Inf → default
    - Out-of-range values → clamped

    Args:
        value: Value to parse (may be string, int, float, or invalid)
        default: Fallback value if parsing fails
        min_val: Minimum allowed value (clamp floor)
        max_val: Maximum allowed value (clamp ceiling)
        context: Optional context for logging (e.g., "EIA.emotion_intensity")

    Returns:
        Parsed and clamped float, or default if parsing fails
    """
    ctx_prefix = f"{context}: " if context else ""

    try:
        result = float(value)

        # Handle NaN and Inf (float() parses these successfully!)
        if not math.isfinite(result):
            logger.warning(f"{ctx_prefix}Non-finite value '{value}', using default {default}")
            return default

        clamped = max(min_val, min(max_val, result))
        if clamped != result:
            logger.debug(f"{ctx_prefix}Clamped {result} to {clamped}")
        return clamped

    except (TypeError, ValueError):
        logger.warning(f"{ctx_prefix}Invalid float value '{value}', using default {default}")
        return default
