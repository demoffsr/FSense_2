"""Tests for emotion capping in relationship inference."""

import pytest
from unittest.mock import patch
from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
from backend.pipeline.context import IntentData


def _make_intent(recipient: str = "wife") -> IntentData:
    """Helper to create IntentData for apology scenario."""
    return IntentData(
        primary_intent="apologize",
        raw_output={"recipient": recipient, "occasion": "apology"},
    )


def _get_max_intensity(result) -> float:
    """Extract max_intensity from RelationshipData.raw_output."""
    return result.raw_output["gift_appropriateness"]["max_intensity"]


class TestEmotionCapping:
    """Test emotion capping logic for guilt-family emotions."""

    def test_capping_with_remorse(self):
        """Remorse with high intensity should cap max_intensity."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "remorse", "emotion_intensity": 0.9},
        )
        assert _get_max_intensity(result) <= 0.6

    def test_capping_with_shame(self):
        """Shame emotion should also trigger capping."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "shame", "emotion_intensity": 0.8},
        )
        assert _get_max_intensity(result) <= 0.6

    def test_capping_with_contrition(self):
        """Contrition emotion should also trigger capping."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "contrition", "emotion_intensity": 0.85},
        )
        assert _get_max_intensity(result) <= 0.6

    def test_capping_with_guilt_defensive(self):
        """Guilt (category name) should still work as defensive catch."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "guilt", "emotion_intensity": 0.75},
        )
        assert _get_max_intensity(result) <= 0.6

    def test_no_capping_below_threshold(self):
        """Low intensity should not trigger capping."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "remorse", "emotion_intensity": 0.5},
        )
        # Should not be capped to 0.6
        assert _get_max_intensity(result) > 0.6

    def test_apologetic_tone_does_not_trigger_capping(self):
        """Apologetic is a tone, not emotion - should NOT cap."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "apologetic", "emotion_intensity": 0.9},
        )
        # "apologetic" intentionally removed from list
        assert _get_max_intensity(result) > 0.6

    def test_none_primary_emotion(self):
        """None primary_emotion should not crash."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": None, "emotion_intensity": 0.9},
        )
        # Should complete without error
        assert result.relationship_type is not None

    def test_zero_intensity_preserved(self):
        """Zero intensity should be preserved, not replaced with default."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "remorse", "emotion_intensity": 0.0},
        )
        # 0.0 < 0.7 threshold, so no capping should occur
        assert _get_max_intensity(result) > 0.6

    def test_empty_emotion_data_dict(self):
        """Empty dict should not crash."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={},
        )
        assert result.relationship_type is not None

    @patch("backend.agents.adapters.relationship_inference.EMOTION_CAPPING_ENABLED", False)
    def test_feature_flag_disabled(self):
        """When disabled, capping should not occur."""
        result = infer_relationship_from_intent(
            _make_intent(),
            emotion_data={"primary_emotion": "remorse", "emotion_intensity": 0.9},
        )
        # Should not be capped
        assert _get_max_intensity(result) > 0.6
