"""Tests for budget_normalizer utility."""
import pytest
from unittest.mock import patch
from backend.core.budget_normalizer import normalize_budget, _is_normalize_enabled


class TestNormalizeBudget:
    """Unit tests for normalize_budget()"""

    # Canonical terms unchanged
    def test_canonical_unchanged(self):
        assert normalize_budget("budget") == "budget"
        assert normalize_budget("mid") == "mid"
        assert normalize_budget("premium") == "premium"
        assert normalize_budget("any") == "any"

    # iOS TasteProfile terms
    def test_ios_terms(self):
        assert normalize_budget("Budget") == "budget"
        assert normalize_budget("Moderate") == "mid"
        assert normalize_budget("Premium") == "premium"
        assert normalize_budget("Luxury") == "premium"

    # FIA budget_hint terms
    def test_fia_terms(self):
        assert normalize_budget("modest") == "budget"
        assert normalize_budget("standard") == "mid"
        assert normalize_budget("luxury") == "premium"
        assert normalize_budget("unspecified") == "any"

    # Synonyms
    def test_synonyms(self):
        assert normalize_budget("cheap") == "budget"
        assert normalize_budget("affordable") == "budget"
        assert normalize_budget("expensive") == "premium"
        assert normalize_budget("splurge") == "premium"

    # Dollar ranges with exclusive upper bounds
    def test_dollar_ranges(self):
        assert normalize_budget("$20-40") == "budget"  # max=40 < 50
        assert normalize_budget("$49") == "budget"     # < 50
        assert normalize_budget("$50-70") == "mid"     # max=70 < 100
        assert normalize_budget("$99") == "mid"        # < 100
        assert normalize_budget("$100+") == "premium"  # >= 100
        assert normalize_budget("50-60") == "mid"      # no $ sign

    # Edge case: boundary values
    def test_boundary_values(self):
        assert normalize_budget("$40") == "budget"     # < 50
        assert normalize_budget("$50") == "mid"        # 50 <= x < 100
        assert normalize_budget("$80") == "mid"        # < 100
        assert normalize_budget("$100") == "premium"   # >= 100

    # None/empty handling
    def test_none_empty(self):
        assert normalize_budget(None) is None
        assert normalize_budget("") is None
        assert normalize_budget("   ") is None

    # Case insensitivity
    def test_case_insensitive(self):
        assert normalize_budget("BUDGET") == "budget"
        assert normalize_budget("Premium") == "premium"
        assert normalize_budget("MID") == "mid"

    # Unknown returns None (not "any")
    def test_unknown_returns_none(self):
        assert normalize_budget("foobar") is None
        assert normalize_budget("whatever") is None

    # Malformed inputs - regex extracts digits regardless of surrounding chars
    def test_malformed_inputs(self):
        # "$-50" extracts "50" -> mid (not None!)
        assert normalize_budget("$-50") == "mid"
        # "around 100 dollars" extracts 100 -> premium
        assert normalize_budget("around 100 dollars") == "premium"

    # Feature flag rollback
    def test_feature_flag_disabled(self):
        with patch.dict("os.environ", {"BUDGET_NORMALIZE_ENABLED": "false"}):
            # Passes through unchanged when disabled
            assert normalize_budget("luxury") == "luxury"
            assert normalize_budget("Moderate") == "Moderate"


class TestIntegration:
    """Integration test for full normalization flow."""

    def test_ios_to_canonical_flow(self):
        """Verify iOS term normalizes correctly for FMRA/SFA consumption."""
        # Simulate iOS sending "Luxury"
        ios_budget = "Luxury"
        normalized = normalize_budget(ios_budget)

        # Should be canonical "premium"
        assert normalized == "premium"

        # Should work in SFA warning logic
        # (premium flower + premium user = no mismatch warning)
        assert normalized not in ("budget",)  # Would trigger warning
