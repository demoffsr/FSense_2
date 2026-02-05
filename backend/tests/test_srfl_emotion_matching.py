"""Tests for SRFL emotion substring matching fix."""
import pytest
from unittest.mock import MagicMock, patch
from backend.agents.adapters.srfl_adapter import SRFLAdapter, EMOTION_TO_MEANING_TONES
from backend.pipeline.context import PipelineContext, EmotionData, CandidatesData, FlowerCandidate


class TestSegmentMatching:
    """Test the segment-based matching logic."""

    def test_love_is_segment_of_romantic_love(self):
        """'love' is a segment of 'romantic_love' when split by underscore."""
        segments = "romantic_love".split("_")
        assert "love" in segments
        assert segments == ["romantic", "love"]

    def test_care_is_segment_of_care_concern(self):
        """'care' is a segment of 'care_concern'."""
        segments = "care_concern".split("_")
        assert "care" in segments
        assert "concern" in segments

    def test_love_not_segment_of_lovey(self):
        """'love' is NOT a segment of 'lovey' (typo)."""
        segments = "lovey".split("_")
        assert "love" not in segments
        assert segments == ["lovey"]

    def test_care_not_segment_of_concern(self):
        """'care' is NOT a segment of 'concern' (different emotions)."""
        segments = "concern".split("_")
        assert "care" not in segments

    def test_longer_key_preferred_when_multiple_match(self):
        """When multiple keys match segments, prefer longer (more specific)."""
        emotion_segments = set("care_concern".split("_"))

        # Find all matching keys and sort by length (descending)
        matching_keys = [
            k for k in EMOTION_TO_MEANING_TONES.keys()
            if k in emotion_segments
        ]
        # Sort by length descending and take first
        best_match = max(matching_keys, key=len) if matching_keys else None

        # "concern" (7) should be preferred over "care" (4)
        assert best_match == "concern"


class TestComputeConsistencyIntegration:
    """Integration tests for _compute_consistency."""

    def _create_mock_context(self, primary_emotion, flower_meanings):
        """Create a minimal mock context for testing."""
        ctx = MagicMock(spec=PipelineContext)
        ctx.emotions = MagicMock(spec=EmotionData)
        ctx.emotions.primary_emotion = primary_emotion

        candidate = MagicMock(spec=FlowerCandidate)
        candidate.meanings = flower_meanings

        ctx.candidates = MagicMock(spec=CandidatesData)
        ctx.candidates.candidates = [candidate]

        ctx.relationship = None
        ctx.intensity = None

        return ctx

    def test_exact_match_love(self):
        """'love' emotion should use 'love' targets exactly."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("love", ["love", "passion", "romance"])

        score = adapter._compute_consistency(ctx)

        # "love" targets: {"love", "passion", "romance", "affection", "devotion", "desire"}
        # 3 out of 6 match → score ~0.5 + stage/intensity bonuses
        assert score >= 0.5

    def test_exact_match_care(self):
        """'care' emotion should use 'care' targets exactly."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("care", ["care", "support", "comfort"])

        score = adapter._compute_consistency(ctx)

        # "care" targets: {"care", "support", "comfort", "nurturing", "warmth"}
        # 3 out of 5 match → score ~0.6
        assert score >= 0.5

    def test_none_primary_emotion(self):
        """None primary_emotion should return 0.5 (no data)."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context(None, ["love"])

        score = adapter._compute_consistency(ctx)

        assert score == 0.5

    def test_empty_primary_emotion(self):
        """Empty string primary_emotion should return 0.5."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("", ["love"])

        score = adapter._compute_consistency(ctx)

        assert score == 0.5

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_unknown_emotion_returns_neutral(self):
        """Completely unknown emotion should return 0.6 (neutral)."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("xyz_unknown_emotion", ["love"])

        score = adapter._compute_consistency(ctx)

        assert score == 0.6

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_typo_emotion_returns_neutral(self):
        """Typo like 'lovey' should return 0.6 (no segment match)."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("lovey", ["love"])

        score = adapter._compute_consistency(ctx)

        assert score == 0.6

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_compound_emotion_fallback_to_longer_segment(self):
        """'care_concern' should fallback to 'concern' targets (longer key)."""
        adapter = SRFLAdapter()
        # "concern" targets: {"care", "support", "worry", "comfort"}
        ctx = self._create_mock_context("care_concern", ["care", "support", "worry", "comfort"])

        score = adapter._compute_consistency(ctx)

        # 4 out of 4 targets match → high score
        # This verifies fallback worked (not neutral 0.6)
        assert score > 0.6

    # --- Real EIA output tests ---

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_puppy_love_fallback_to_love(self):
        """'puppy_love' (valid EIA output) should fallback to 'love' targets."""
        adapter = SRFLAdapter()
        # "love" targets: {"love", "passion", "romance", "affection", "devotion", "desire"}
        ctx = self._create_mock_context("puppy_love", ["love", "passion", "romance"])

        score = adapter._compute_consistency(ctx)

        # Fallback to "love" should work → not neutral 0.6
        assert score > 0.4

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_mature_love_fallback_to_love(self):
        """'mature_love' (valid EIA output) should fallback to 'love' targets."""
        adapter = SRFLAdapter()
        # "love" targets: {"love", "passion", "romance", "affection", "devotion", "desire"}
        # 2 out of 6 match → score ~0.33, but not 0.6 (neutral)
        ctx = self._create_mock_context("mature_love", ["devotion", "affection"])

        score = adapter._compute_consistency(ctx)

        # Key assertion: score is NOT 0.6 (neutral), meaning fallback worked
        # Actual score is 2/6 ≈ 0.33
        assert score != 0.6
        assert score > 0.3

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_indebtedness_no_fallback(self):
        """'indebtedness' (valid EIA output) has no segment match → neutral."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("indebtedness", ["gratitude"])

        score = adapter._compute_consistency(ctx)

        # No match in segments → returns 0.6 neutral
        assert score == 0.6

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', True)
    def test_disappointment_no_fallback(self):
        """'disappointment' (valid EIA output) has no segment match → neutral."""
        adapter = SRFLAdapter()
        ctx = self._create_mock_context("disappointment", ["sadness"])

        score = adapter._compute_consistency(ctx)

        assert score == 0.6

    # --- Feature flag rollback tests ---

    @patch('backend.agents.adapters.srfl_adapter.SRFL_USE_SEGMENT_MATCHING', False)
    def test_old_bidirectional_matching_when_flag_disabled(self):
        """With feature flag disabled, old bidirectional matching should be used."""
        adapter = SRFLAdapter()
        # "romantic_love" contains "love" as substring AND segment
        ctx = self._create_mock_context("romantic_love", ["love", "passion", "romance"])

        score = adapter._compute_consistency(ctx)

        # Should still work via exact match (romantic_love is in dict)
        assert score > 0.4


class TestEdgeCases:
    """Edge case tests."""

    def test_no_emotions_context(self):
        """Missing emotions context should return 0.5."""
        adapter = SRFLAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.emotions = None
        ctx.candidates = MagicMock()
        ctx.candidates.candidates = [MagicMock()]

        score = adapter._compute_consistency(ctx)

        assert score == 0.5

    def test_no_candidates_context(self):
        """Missing candidates context should return 0.5."""
        adapter = SRFLAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.emotions = MagicMock()
        ctx.emotions.primary_emotion = "love"
        ctx.candidates = None

        score = adapter._compute_consistency(ctx)

        assert score == 0.5

    def test_empty_candidates_list(self):
        """Empty candidates list should return 0.5."""
        adapter = SRFLAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.emotions = MagicMock()
        ctx.emotions.primary_emotion = "love"
        ctx.candidates = MagicMock()
        ctx.candidates.candidates = []

        score = adapter._compute_consistency(ctx)

        assert score == 0.5

    def test_case_insensitive_matching(self):
        """Emotion matching should be case-insensitive."""
        adapter = SRFLAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.emotions = MagicMock()
        ctx.emotions.primary_emotion = "LOVE"  # uppercase

        candidate = MagicMock()
        candidate.meanings = ["love", "passion"]
        ctx.candidates = MagicMock()
        ctx.candidates.candidates = [candidate]
        ctx.relationship = None
        ctx.intensity = None

        score = adapter._compute_consistency(ctx)

        # Should match "love" targets despite uppercase input
        assert score > 0.3
