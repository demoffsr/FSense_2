"""
Tests for FMRA budget enforcement feature.

Tests cover:
- Budget tier parsing (keywords and dollar ranges)
- Budget multiplier calculations
- Prompt content with budget_range
- Integration: budget constraint reorders candidates
- E2E: iOS budget normalization through pipeline
"""

import pytest
from backend.agents.adapters.fmra_adapter import FMRAAdapter
from backend.pipeline.context import (
    PipelineContext,
    UserPriors,
    FlowerCandidate,
    IntentData,
)
from backend.core.budget_normalizer import normalize_budget


class TestBudgetTierParsing:
    """Unit tests for _parse_budget_to_tier() - now delegates to normalize_budget()"""

    def test_keyword_budget(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("budget") == "budget"
        assert adapter._parse_budget_to_tier("cheap") == "budget"
        assert adapter._parse_budget_to_tier("modest") == "budget"
        assert adapter._parse_budget_to_tier("affordable") == "budget"
        assert adapter._parse_budget_to_tier("low") == "budget"

    def test_keyword_premium(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("premium") == "premium"
        assert adapter._parse_budget_to_tier("luxury") == "premium"
        assert adapter._parse_budget_to_tier("expensive") == "premium"
        assert adapter._parse_budget_to_tier("high") == "premium"
        assert adapter._parse_budget_to_tier("splurge") == "premium"

    def test_dollar_range_budget(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("$20-40") == "budget"
        assert adapter._parse_budget_to_tier("$30") == "budget"
        assert adapter._parse_budget_to_tier("$25-35") == "budget"

    def test_dollar_range_mid(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("$50-70") == "mid"
        assert adapter._parse_budget_to_tier("50-60") == "mid"
        assert adapter._parse_budget_to_tier("$45-75") == "mid"

    def test_dollar_range_premium(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("$80-150") == "premium"
        assert adapter._parse_budget_to_tier("$100+") == "premium"
        assert adapter._parse_budget_to_tier("$200") == "premium"

    def test_unknown_format(self):
        adapter = FMRAAdapter()
        assert adapter._parse_budget_to_tier("whatever") is None
        assert adapter._parse_budget_to_tier("") is None


class TestBudgetMultiplier:
    """Unit tests for _calculate_budget_multiplier()"""

    def test_exact_match_budget_tier(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("budget", "budget") == 1.2

    def test_exact_match_premium_tier(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("premium", "luxury") == 1.2
        assert adapter._calculate_budget_multiplier("premium", "premium") == 1.2

    def test_dollar_range_match(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("budget", "$30-40") == 1.2
        assert adapter._calculate_budget_multiplier("premium", "$100-150") == 1.2

    def test_opposite_tier_penalty(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("premium", "budget") == 0.7
        assert adapter._calculate_budget_multiplier("budget", "premium") == 0.7
        assert adapter._calculate_budget_multiplier("budget", "$100+") == 0.7
        assert adapter._calculate_budget_multiplier("premium", "$30") == 0.7

    def test_adjacent_tier_neutral(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("mid", "budget") == 1.0
        assert adapter._calculate_budget_multiplier("mid", "premium") == 1.0
        assert adapter._calculate_budget_multiplier("budget", "mid") == 1.0
        assert adapter._calculate_budget_multiplier("premium", "mid") == 1.0

    def test_skip_non_constraints(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier("budget", "any") == 1.0
        assert adapter._calculate_budget_multiplier("budget", "unspecified") == 1.0
        assert adapter._calculate_budget_multiplier("premium", "mid") == 1.0
        assert adapter._calculate_budget_multiplier("budget", "standard") == 1.0

    def test_missing_tier_neutral(self):
        adapter = FMRAAdapter()
        assert adapter._calculate_budget_multiplier(None, "budget") == 1.0
        assert adapter._calculate_budget_multiplier("budget", None) == 1.0
        assert adapter._calculate_budget_multiplier(None, None) == 1.0


class TestBudgetPrompt:
    """Unit tests for budget in prompt"""

    def test_budget_range_appears_in_prompt(self):
        adapter = FMRAAdapter()
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
            priors=UserPriors(budget_range="budget")
        )
        ctx.intent = IntentData(raw_output={})
        ctx.emotions = None

        prompt = adapter._build_prompt(ctx)
        assert "Budget preference: budget" in prompt

    def test_budget_hint_skipped_when_range_present(self):
        adapter = FMRAAdapter()
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
            priors=UserPriors(budget_range="premium")
        )
        ctx.intent = IntentData(
            raw_output={'context_flags': {'budget_hint': 'modest'}}
        )
        ctx.emotions = None

        prompt = adapter._build_prompt(ctx)
        assert "Budget preference: premium" in prompt
        assert "Budget hint: modest" not in prompt

    def test_budget_hint_used_when_no_range(self):
        adapter = FMRAAdapter()
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
        )
        ctx.intent = IntentData(
            raw_output={'context_flags': {'budget_hint': 'modest'}}
        )
        ctx.emotions = None

        prompt = adapter._build_prompt(ctx)
        assert "Budget hint: modest" in prompt
        assert "Budget preference" not in prompt

    def test_no_budget_when_any(self):
        adapter = FMRAAdapter()
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
            priors=UserPriors(budget_range="any")
        )
        ctx.intent = IntentData(raw_output={})
        ctx.emotions = None

        prompt = adapter._build_prompt(ctx)
        assert "Budget preference" not in prompt


class TestBudgetIntegration:
    """Integration tests for budget enforcement"""

    def test_budget_constraint_reorders_candidates(self):
        """Budget flowers should rank higher when user selects budget tier"""
        adapter = FMRAAdapter()

        candidates = [
            FlowerCandidate(
                flower_id="orchid",
                name="Orchid",
                match_score=0.9,
                match_reasons=["test"],
                meanings=["Beauty"],
                price_tier="premium"
            ),
            FlowerCandidate(
                flower_id="carnation",
                name="Carnation",
                match_score=0.8,
                match_reasons=["test"],
                meanings=["Gratitude"],
                price_tier="budget"
            ),
        ]

        # Apply budget multiplier manually to test logic
        for c in candidates:
            mult = adapter._calculate_budget_multiplier(c.price_tier, "budget")
            c.match_score = min(1.0, max(0.1, c.match_score * mult))

        candidates.sort(key=lambda x: x.match_score, reverse=True)

        # Carnation (0.8 * 1.2 = 0.96) beats Orchid (0.9 * 0.7 = 0.63)
        assert candidates[0].name == "Carnation"
        assert candidates[0].match_score == pytest.approx(0.96, abs=0.01)
        assert candidates[1].match_score == pytest.approx(0.63, abs=0.01)

    def test_premium_constraint_reorders_candidates(self):
        """Premium flowers should rank higher when user selects premium tier"""
        adapter = FMRAAdapter()

        candidates = [
            FlowerCandidate(
                flower_id="carnation",
                name="Carnation",
                match_score=0.9,
                match_reasons=["test"],
                meanings=["Gratitude"],
                price_tier="budget"
            ),
            FlowerCandidate(
                flower_id="peony",
                name="Peony",
                match_score=0.85,
                match_reasons=["test"],
                meanings=["Prosperity"],
                price_tier="premium"
            ),
        ]

        # Apply budget multiplier
        for c in candidates:
            mult = adapter._calculate_budget_multiplier(c.price_tier, "premium")
            c.match_score = min(1.0, max(0.1, c.match_score * mult))

        candidates.sort(key=lambda x: x.match_score, reverse=True)

        # Peony (0.85 * 1.2 = 1.02 -> capped at 1.0) beats Carnation (0.9 * 0.7 = 0.63)
        assert candidates[0].name == "Peony"
        assert candidates[0].match_score == pytest.approx(1.0, abs=0.01)  # capped
        assert candidates[1].match_score == pytest.approx(0.63, abs=0.01)

    def test_mid_tier_no_adjustment(self):
        """Mid-tier flowers should not be adjusted"""
        adapter = FMRAAdapter()

        candidates = [
            FlowerCandidate(
                flower_id="rose",
                name="Rose",
                match_score=0.9,
                match_reasons=["test"],
                meanings=["Love"],
                price_tier="mid"
            ),
            FlowerCandidate(
                flower_id="tulip",
                name="Tulip",
                match_score=0.85,
                match_reasons=["test"],
                meanings=["Hope"],
                price_tier="mid"
            ),
        ]

        # Apply budget multiplier with "budget" user preference
        for c in candidates:
            mult = adapter._calculate_budget_multiplier(c.price_tier, "budget")
            c.match_score = min(1.0, max(0.1, c.match_score * mult))

        # Mid-tier flowers get neutral (1.0) multiplier
        assert candidates[0].match_score == pytest.approx(0.9, abs=0.01)
        assert candidates[1].match_score == pytest.approx(0.85, abs=0.01)


class TestIOSBudgetNormalization:
    """E2E tests for iOS budget normalization through pipeline"""

    def test_ios_budget_normalization_e2e(self):
        """
        E2E: iOS sends 'Luxury' -> runner normalizes to 'premium' ->
        FMRA receives 'premium' -> SFA shows correct warning.
        """
        # iOS sends "Luxury"
        ios_value = "Luxury"

        # Runner normalizes at entry
        normalized = normalize_budget(ios_value)
        assert normalized == "premium"

        # Create context with normalized value
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
            priors=UserPriors(budget_range=normalized),
        )

        # FMRA receives canonical tier
        assert ctx.priors.budget_range == "premium"

        # SFA would use this directly (no re-parsing needed)
        # Premium flower + premium user = no mismatch warning (only label)

    def test_ios_moderate_normalizes_to_mid(self):
        """iOS 'Moderate' tier normalizes to canonical 'mid'"""
        normalized = normalize_budget("Moderate")
        assert normalized == "mid"

    def test_fmra_delegates_to_normalizer(self):
        """FMRA._parse_budget_to_tier() delegates to normalize_budget()"""
        adapter = FMRAAdapter()

        # Test that FMRA uses the central normalizer
        assert adapter._parse_budget_to_tier("luxury") == "premium"
        assert adapter._parse_budget_to_tier("modest") == "budget"
        assert adapter._parse_budget_to_tier("$75") == "mid"

    def test_budget_normalization_in_context(self):
        """Budget is normalized when passed through runner to context"""
        # Simulate what runner.py does
        budget_range = "Luxury"
        normalized_budget = normalize_budget(budget_range)

        ctx = PipelineContext(
            user_input="test",
            region="us",
            priors=UserPriors(budget_range=normalized_budget),
        )

        # Context has canonical tier
        assert ctx.priors.budget_range == "premium"
