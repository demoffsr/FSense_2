"""Test SFA handles None mood_intensity gracefully."""
import pytest
from backend.pipeline.context import PipelineContext, IntensityData
from backend.agents.adapters.sfa_adapter import SFAAdapter


class TestSFAMoodIntensityNone:
    """Test SFA defensive handling of None mood_intensity."""

    def test_get_safe_mood_intensity_returns_default_when_none(self):
        """Should return 0.4 when mood_intensity is None."""
        ctx = PipelineContext(user_input="test", region="US")
        ctx.intensity = IntensityData()
        ctx.intensity.mood_intensity = None  # Violate contract

        sfa = SFAAdapter()
        result = sfa._get_safe_mood_intensity(ctx)

        assert result == 0.4  # Preserves original fallback of 25 on UI scale

    def test_get_safe_mood_intensity_returns_default_when_no_intensity(self):
        """Should return 0.4 when ctx.intensity is None."""
        ctx = PipelineContext(user_input="test", region="US")
        ctx.intensity = None

        sfa = SFAAdapter()
        result = sfa._get_safe_mood_intensity(ctx)

        assert result == 0.4

    def test_get_safe_mood_intensity_returns_default_when_no_ctx(self):
        """Should return 0.4 when ctx is None."""
        sfa = SFAAdapter()
        result = sfa._get_safe_mood_intensity(None)

        assert result == 0.4

    def test_get_safe_mood_intensity_returns_actual_value(self):
        """Should return actual value when valid."""
        ctx = PipelineContext(user_input="test", region="US")
        ctx.intensity = IntensityData(mood_intensity=0.8)

        sfa = SFAAdapter()
        result = sfa._get_safe_mood_intensity(ctx)

        assert result == 0.8

    def test_calculate_mood_intensity_ui_converts_correctly(self):
        """Should convert 0.0-1.0 to 15-40 scale."""
        sfa = SFAAdapter()

        assert sfa._calculate_mood_intensity_ui(0.0) == 15
        assert sfa._calculate_mood_intensity_ui(0.4) == 25  # Default yields "Balanced"
        assert sfa._calculate_mood_intensity_ui(0.5) == 27
        assert sfa._calculate_mood_intensity_ui(1.0) == 40

    def test_fallback_preserves_original_behavior(self):
        """When ctx.intensity is None, fallback should yield 25 (not 27)."""
        ctx = PipelineContext(user_input="test", region="US")
        ctx.intensity = None

        sfa = SFAAdapter()
        mood_val = sfa._get_safe_mood_intensity(ctx)
        mood_intensity = sfa._calculate_mood_intensity_ui(mood_val)

        assert mood_intensity == 25  # Original hardcoded default preserved

    def test_default_constant_is_correct(self):
        """DEFAULT_MOOD_INTENSITY should be 0.4 to yield 25 on UI scale."""
        sfa = SFAAdapter()
        assert sfa.DEFAULT_MOOD_INTENSITY == 0.4
        assert sfa._calculate_mood_intensity_ui(sfa.DEFAULT_MOOD_INTENSITY) == 25
