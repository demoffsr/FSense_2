"""
Tests for FMRA flower name validation feature.

Tests cover:
- is_valid_flower_name() helper function
- Invalid name detection (blocklist + pattern matching)
- Valid flower name acceptance
- Defensive handling of malformed AI responses
- Feature flag rollback behavior
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.agents.adapters.fmra_adapter import (
    is_valid_flower_name,
    FMRAAdapter,
    FMRA_VALIDATE_FLOWER_NAMES,
)
from backend.pipeline.context import (
    PipelineContext,
    EmotionData,
)


class TestFlowerNameValidation:
    """Test is_valid_flower_name helper (public for testing)."""

    @pytest.mark.parametrize("invalid_name", [
        "Unknown Flower",
        "unknown",
        "N/A",
        "None",
        "null",
        "",
        "   ",
        "Flower Not Found",
        "Error: timeout",
        "placeholder",
        "test",
        "Unknown Species",
        "UNKNOWN",
        "invalid flower",
        "undefined",
        "sample",
        "tbd",
        "flower",
        "FLOWER",
    ])
    def test_rejects_invalid_names(self, invalid_name):
        assert is_valid_flower_name(invalid_name) is False

    @pytest.mark.parametrize("valid_name", [
        "Rose",
        "Red Rose",
        "Fleur de Lis",
        "Bird of Paradise",
        "Baby's Breath",
        "Lily of the Valley",
        "Pink Carnation",
        "White Tulip",
        "Orchid",
        "Sunflower",
        "Peony",
        "Hydrangea",
    ])
    def test_accepts_valid_names(self, valid_name):
        assert is_valid_flower_name(valid_name) is True

    def test_rejects_non_string(self):
        assert is_valid_flower_name(None) is False
        assert is_valid_flower_name(123) is False
        assert is_valid_flower_name(["Rose"]) is False
        assert is_valid_flower_name({"name": "Rose"}) is False
        assert is_valid_flower_name(0.5) is False

    def test_case_insensitive(self):
        assert is_valid_flower_name("UNKNOWN FLOWER") is False
        assert is_valid_flower_name("Unknown flower") is False
        assert is_valid_flower_name("unknown FLOWER") is False
        assert is_valid_flower_name("UnKnOwN fLoWeR") is False

    def test_whitespace_handling(self):
        """Leading/trailing whitespace should be stripped before validation."""
        assert is_valid_flower_name("  Rose  ") is True
        assert is_valid_flower_name("  Unknown Flower  ") is False
        assert is_valid_flower_name("\tTulip\n") is True

    def test_pattern_matching_substring(self):
        """Invalid patterns should match as substrings."""
        assert is_valid_flower_name("My Unknown Flower") is False
        assert is_valid_flower_name("Error getting flower") is False
        assert is_valid_flower_name("Flower not found in database") is False
        assert is_valid_flower_name("Invalid response") is False
        assert is_valid_flower_name("placeholder_flower") is False


class TestFMRACandidatesDefensive:
    """Test _ai_selection_multiple handles malformed AI responses."""

    @pytest.fixture
    def adapter(self):
        return FMRAAdapter()

    @pytest.fixture
    def basic_ctx(self):
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
        )
        ctx.emotions = EmotionData(
            primary_emotion="gratitude",
            emotion_intensity=0.7,
        )
        return ctx

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_null_candidates(self, mock_client, adapter, basic_ctx):
        """AI returns {"candidates": null}."""
        mock_client.return_value.complete_json.return_value = {"candidates": None}

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should return fallback, not crash
        assert len(result) == 1
        assert result[0].match_reasons[-1] == "Context-based fallback"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_string_candidates(self, mock_client, adapter, basic_ctx):
        """AI returns {"candidates": "invalid"}."""
        mock_client.return_value.complete_json.return_value = {"candidates": "some string"}

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should return fallback, not iterate over chars
        assert len(result) == 1
        assert result[0].match_reasons[-1] == "Context-based fallback"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_non_dict_items(self, mock_client, adapter, basic_ctx):
        """AI returns [123, "string", null, {...}]."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                123,
                "string",
                None,
                {"flower_name": "Rose", "match_score": 0.85},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should skip non-dict, keep valid dict
        assert len(result) == 1
        assert result[0].name == "Rose"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_non_string_flower_name(self, mock_client, adapter, basic_ctx):
        """AI returns flower_name as non-string."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                {"flower_name": 123, "match_score": 0.9},
                {"flower_name": ["Rose"], "match_score": 0.85},
                {"flower_name": "Tulip", "match_score": 0.8},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should skip numeric/list flower_name, keep string
        assert len(result) == 1
        assert result[0].name == "Tulip"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_empty_array(self, mock_client, adapter, basic_ctx):
        """AI returns empty candidates array."""
        mock_client.return_value.complete_json.return_value = {"candidates": []}

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should return fallback
        assert len(result) == 1
        assert result[0].match_reasons[-1] == "Context-based fallback"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_handles_missing_candidates_key(self, mock_client, adapter, basic_ctx):
        """AI returns response without candidates key."""
        mock_client.return_value.complete_json.return_value = {"flowers": []}

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should return fallback
        assert len(result) == 1
        assert result[0].match_reasons[-1] == "Context-based fallback"


class TestFMRAValidationIntegration:
    """Integration tests for flower name validation in FMRA."""

    @pytest.fixture
    def adapter(self):
        return FMRAAdapter()

    @pytest.fixture
    def basic_ctx(self):
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
        )
        ctx.emotions = EmotionData(
            primary_emotion="gratitude",
            emotion_intensity=0.7,
        )
        return ctx

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_filters_invalid_ai_response(self, mock_client, adapter, basic_ctx):
        """FMRA should skip invalid flower names from AI."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                {"flower_name": "Unknown Flower", "match_score": 0.9},
                {"flower_name": "Rose", "match_score": 0.85},
                {"flower_name": "", "match_score": 0.8},
                {"flower_name": "N/A", "match_score": 0.75},
                {"flower_name": "Tulip", "match_score": 0.7},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should only keep Rose and Tulip
        assert len(result) == 2
        assert result[0].name == "Rose"
        assert result[1].name == "Tulip"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_all_invalid_returns_fallback(self, mock_client, adapter, basic_ctx):
        """FMRA should use fallback when all AI candidates are invalid."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                {"flower_name": "Unknown Flower", "match_score": 0.9},
                {"flower_name": "N/A", "match_score": 0.85},
                {"flower_name": "Error", "match_score": 0.8},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should return context-aware fallback
        assert len(result) == 1
        assert result[0].match_reasons[-1] == "Context-based fallback"

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    def test_generates_flower_id_from_name(self, mock_client, adapter, basic_ctx):
        """FMRA should generate flower_id when AI provides invalid one."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                {"flower_name": "Red Rose", "flower_id": "unknown_flower", "match_score": 0.85},
                {"flower_name": "White Lily", "flower_id": "", "match_score": 0.8},
                {"flower_name": "Bird of Paradise", "match_score": 0.75},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # Should generate valid flower_ids from names
        assert result[0].flower_id == "red_rose"
        assert result[1].flower_id == "white_lily"
        assert result[2].flower_id == "bird_of_paradise"


class TestFMRAValidationFeatureFlag:
    """Test feature flag for validation rollback."""

    @pytest.fixture
    def adapter(self):
        return FMRAAdapter()

    @pytest.fixture
    def basic_ctx(self):
        ctx = PipelineContext(
            user_input="flowers for mom",
            region="us",
        )
        ctx.emotions = EmotionData(
            primary_emotion="gratitude",
            emotion_intensity=0.7,
        )
        return ctx

    @patch("backend.agents.adapters.fmra_adapter.get_ai_client_fast")
    @patch("backend.agents.adapters.fmra_adapter.FMRA_VALIDATE_FLOWER_NAMES", False)
    def test_validation_disabled_allows_invalid_names(self, mock_client, adapter, basic_ctx):
        """FMRA_VALIDATE_FLOWER_NAMES=false allows all names through."""
        mock_client.return_value.complete_json.return_value = {
            "candidates": [
                {"flower_name": "Unknown Flower", "match_score": 0.9},
            ]
        }

        result = adapter._ai_selection_multiple(basic_ctx)

        # With validation disabled, "Unknown Flower" should pass through
        assert len(result) == 1
        assert result[0].name == "Unknown Flower"
