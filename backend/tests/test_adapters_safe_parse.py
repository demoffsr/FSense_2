"""Integration tests for safe_parse_float in adapters.

These tests verify that adapters handle invalid AI responses without crashing.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.agents.adapters.eia_adapter import EIAAdapter
from backend.agents.adapters.cia_adapter import CIAAdapter
from backend.agents.adapters.fmra_adapter import FMRAAdapter
from backend.pipeline.context import PipelineContext, IntentData, EmotionData


class TestEIASafeParseIntegration:
    """Test EIA handles invalid AI responses without crashing."""

    def test_eia_handles_invalid_intensity_string(self):
        """EIA should not crash when AI returns 'high' instead of float."""
        ctx = PipelineContext(user_input="I love my wife", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "romantic_love",
            "emotion_intensity": "high",  # Invalid string!
            "emotion_tone": "passionate",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        # Verify: should not crash, EmotionData created with default intensity
        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.7  # default from safe_parse_float

    def test_eia_handles_nan_intensity(self):
        """EIA should use default when AI returns 'nan'."""
        ctx = PipelineContext(user_input="Thank you", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "gratitude",
            "emotion_intensity": "nan",  # NaN string!
            "emotion_tone": "warm",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.7  # default, not nan

    def test_eia_handles_inf_intensity(self):
        """EIA should use default when AI returns 'inf'."""
        ctx = PipelineContext(user_input="I'm so excited!", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "excitement",
            "emotion_intensity": "inf",  # Infinity!
            "emotion_tone": "celebratory",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.7  # default

    def test_eia_handles_malformed_version_string(self):
        """EIA should use default when AI returns something like '0.7.2'."""
        ctx = PipelineContext(user_input="Thanks for everything", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "gratitude",
            "emotion_intensity": "0.7.2",  # Malformed!
            "emotion_tone": "warm",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.7

    def test_eia_accepts_valid_intensity(self):
        """EIA should work normally with valid float values."""
        ctx = PipelineContext(user_input="I love my wife", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "romantic_love",
            "emotion_intensity": 0.85,  # Valid!
            "emotion_tone": "passionate",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.85

    def test_eia_accepts_string_number(self):
        """EIA should work with string representation of numbers."""
        ctx = PipelineContext(user_input="Happy birthday!", region="us")

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "dominant_emotion": "happiness",
            "emotion_intensity": "0.75",  # String but valid
            "emotion_tone": "celebratory",
        }

        with patch("backend.agents.adapters.eia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = EIAAdapter()
            adapter.run(ctx)

        assert ctx.emotions is not None
        assert ctx.emotions.emotion_intensity == 0.75


class TestCIASafeParseIntegration:
    """Test CIA handles invalid AI responses without crashing."""

    def test_cia_handles_invalid_intensity_score(self):
        """CIA should use heuristic fallback when AI returns invalid score."""
        ctx = PipelineContext(user_input="I love my wife", region="us")
        ctx.emotions = EmotionData(
            primary_emotion="romantic_love",
            emotion_intensity=0.75,
            emotional_tone="passionate"
        )

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "intensity_score": "very_high",  # Invalid string!
            "intensity_label": "high",
            "factors": ["romantic_occasion"],
            "reasoning": "Strong romantic context",
        }

        with patch("backend.agents.adapters.cia_adapter.get_ai_client_fast", return_value=mock_client):
            adapter = CIAAdapter()
            adapter.run(ctx)

        assert ctx.intensity is not None
        # Should fall back to heuristic score, which is based on emotion intensity
        assert 0.0 <= ctx.intensity.mood_intensity <= 1.0


class TestFMRASafeParseIntegration:
    """Test FMRA handles invalid AI responses in loop without crashing."""

    def test_fmra_handles_invalid_match_score_in_ai_selection(self):
        """FMRA should not crash when AI returns invalid match_score in candidates."""
        ctx = PipelineContext(user_input="Flowers for my mom's birthday", region="us")
        ctx.intent = IntentData(primary_intent="flower_request", confidence=0.9)
        ctx.emotions = EmotionData(
            primary_emotion="happiness",
            emotion_intensity=0.7,
            emotional_tone="celebratory"
        )

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "candidates": [
                {
                    "flower_name": "Rose",
                    "flower_id": "rose_001",
                    "match_score": "very high",  # Invalid string!
                    "match_reason": "classic for celebrations",
                    "meanings": ["Love", "Celebration"],
                },
                {
                    "flower_name": "Lily",
                    "flower_id": "lily_001",
                    "match_score": 0.82,  # Valid
                    "match_reason": "elegant choice",
                    "meanings": ["Purity", "Beauty"],
                },
            ]
        }

        with patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast", return_value=mock_client):
            with patch("backend.agents.adapters.fmra_adapter.DATABASE_AVAILABLE", False):
                adapter = FMRAAdapter()
                adapter.run(ctx)

        # Should not crash, should have candidates
        assert ctx.candidates is not None
        assert len(ctx.candidates.candidates) >= 1
        # First candidate should have default match_score (0.85)
        first_candidate = ctx.candidates.candidates[0]
        assert first_candidate.match_score == 0.85  # default

    def test_fmra_handles_nan_match_score(self):
        """FMRA should use default when AI returns 'nan' for match_score."""
        ctx = PipelineContext(user_input="Flowers for a friend", region="us")
        ctx.intent = IntentData(primary_intent="flower_request", confidence=0.9)
        ctx.emotions = EmotionData(
            primary_emotion="friendship",
            emotion_intensity=0.6,
            emotional_tone="warm"
        )

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "candidates": [
                {
                    "flower_name": "Sunflower",
                    "flower_id": "sunflower_001",
                    "match_score": "nan",  # NaN!
                    "match_reason": "cheerful and friendly",
                    "meanings": ["Happiness", "Friendship"],
                },
            ]
        }

        with patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast", return_value=mock_client):
            with patch("backend.agents.adapters.fmra_adapter.DATABASE_AVAILABLE", False):
                adapter = FMRAAdapter()
                adapter.run(ctx)

        assert ctx.candidates is not None
        assert len(ctx.candidates.candidates) >= 1
        assert ctx.candidates.candidates[0].match_score == 0.85  # default

    def test_fmra_accepts_valid_match_scores(self):
        """FMRA should work normally with valid float values."""
        ctx = PipelineContext(user_input="Thank you flowers", region="us")
        ctx.intent = IntentData(primary_intent="flower_request", confidence=0.9)
        ctx.emotions = EmotionData(
            primary_emotion="gratitude",
            emotion_intensity=0.65,
            emotional_tone="warm"
        )

        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "candidates": [
                {
                    "flower_name": "Pink Rose",
                    "flower_id": "pink_rose",
                    "match_score": 0.92,  # Valid!
                    "match_reason": "gratitude symbol",
                    "meanings": ["Gratitude", "Appreciation"],
                },
            ]
        }

        with patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast", return_value=mock_client):
            with patch("backend.agents.adapters.fmra_adapter.DATABASE_AVAILABLE", False):
                adapter = FMRAAdapter()
                adapter.run(ctx)

        assert ctx.candidates is not None
        assert ctx.candidates.candidates[0].match_score == 0.92
