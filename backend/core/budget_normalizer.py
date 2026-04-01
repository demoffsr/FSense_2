"""
Budget terminology normalization utility.

Canonical tiers: "budget", "mid", "premium", "any"
- "any" = user explicitly chose no constraint
- None = couldn't parse input (error state, logged)
"""
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)


def _is_normalize_enabled() -> bool:
    """Check feature flag at runtime (testable)."""
    return os.getenv("BUDGET_NORMALIZE_ENABLED", "true").lower() == "true"


# Lowercase-only alias mapping
BUDGET_ALIASES: dict[str, str] = {
    # Canonical (identity)
    "budget": "budget",
    "mid": "mid",
    "premium": "premium",
    "any": "any",

    # iOS TasteProfile (lowercased)
    "moderate": "mid",
    "luxury": "premium",

    # FIA budget_hint terms
    "modest": "budget",
    "standard": "mid",
    "unspecified": "any",

    # Synonyms
    "cheap": "budget",
    "low": "budget",
    "affordable": "budget",
    "expensive": "premium",
    "high": "premium",
    "splurge": "premium",
}

# Explicit non-constraint terms
NO_CONSTRAINT_TERMS = {"any", "unspecified", "flexible"}


def normalize_budget(budget_str: Optional[str]) -> Optional[str]:
    """
    Normalize budget string to canonical tier.

    Returns:
        "budget", "mid", "premium", "any" - valid canonical tiers
        None - couldn't parse (logged as warning)

    Note: "any" means explicit no-constraint. None means parse failure.
    """
    if not _is_normalize_enabled():
        return budget_str  # Pass through unchanged (rollback mode)

    if not budget_str or not budget_str.strip():
        return None

    budget_lower = budget_str.lower().strip()

    # Check alias mapping first
    if budget_lower in BUDGET_ALIASES:
        return BUDGET_ALIASES[budget_lower]

    # Check for explicit no-constraint
    if budget_lower in NO_CONSTRAINT_TERMS:
        return "any"

    # Dollar range parsing with exclusive upper bounds
    numbers = re.findall(r'\d+', budget_str)
    if numbers:
        max_value = max(int(n) for n in numbers)
        if max_value < 50:
            return "budget"
        elif max_value < 100:
            return "mid"
        else:
            return "premium"

    # Unknown term - log warning and return None (not "any")
    logger.warning(f"Unknown budget term '{budget_str}' could not be normalized")
    return None
