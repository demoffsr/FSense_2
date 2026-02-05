"""Tests for VIA confidence parsing with warning logging."""
import math
import pytest
from unittest.mock import patch
from backend.agents.adapters.via_adapter import VIAAdapter


class TestVIAConfidenceParsing:
    """Test _safe_parse_confidence method."""

    @pytest.fixture
    def adapter(self):
        return VIAAdapter()

    # === Valid values (no warning) ===

    def test_valid_confidence(self, adapter):
        """Valid confidence values pass through."""
        assert adapter._safe_parse_confidence(0.95) == 0.95
        assert adapter._safe_parse_confidence(0.0) == 0.0
        assert adapter._safe_parse_confidence(1.0) == 1.0
        assert adapter._safe_parse_confidence("0.85") == 0.85

    def test_integer_zero_no_warning(self, adapter):
        """Integer 0 is valid, no warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(0)
            assert result == 0.0
            mock_logger.warning.assert_not_called()

    def test_valid_confidence_no_warning(self, adapter):
        """Valid confidence values don't trigger warnings."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            adapter._safe_parse_confidence(0.7)
            mock_logger.warning.assert_not_called()

    # === Out of range (warning + clamp) ===

    def test_confidence_below_range_clamps_with_warning(self, adapter):
        """Negative confidence clamps to 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(-0.5)
            assert result == 0.0
            mock_logger.warning.assert_called_once()
            assert "outside [0.0, 1.0]" in mock_logger.warning.call_args[0][0]
            assert "clamping to 0.0" in mock_logger.warning.call_args[0][0]

    def test_confidence_above_range_clamps_with_warning(self, adapter):
        """Confidence > 1.0 clamps to 1.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(1.5)
            assert result == 1.0
            mock_logger.warning.assert_called_once()
            assert "outside [0.0, 1.0]" in mock_logger.warning.call_args[0][0]
            assert "clamping to 1.0" in mock_logger.warning.call_args[0][0]

    # === Invalid values (warning + return 0.0) ===

    def test_invalid_string_returns_zero_with_warning(self, adapter):
        """Non-numeric string returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence("high")
            assert result == 0.0
            mock_logger.warning.assert_called_once()
            assert "Invalid confidence value" in mock_logger.warning.call_args[0][0]

    def test_none_returns_zero_with_warning(self, adapter):
        """None returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(None)
            assert result == 0.0
            mock_logger.warning.assert_called_once()

    def test_empty_string_returns_zero_with_warning(self, adapter):
        """Empty string returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence("")
            assert result == 0.0
            mock_logger.warning.assert_called_once()

    # === Non-finite values (warning + return 0.0) ===

    def test_nan_returns_zero_with_warning(self, adapter):
        """NaN returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(float("nan"))
            assert result == 0.0
            mock_logger.warning.assert_called_once()
            assert "Non-finite" in mock_logger.warning.call_args[0][0]

    def test_positive_inf_returns_zero_with_warning(self, adapter):
        """Positive infinity returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(float("inf"))
            assert result == 0.0
            mock_logger.warning.assert_called_once()
            assert "Non-finite" in mock_logger.warning.call_args[0][0]

    def test_negative_inf_returns_zero_with_warning(self, adapter):
        """Negative infinity returns 0.0 with warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._safe_parse_confidence(float("-inf"))
            assert result == 0.0
            mock_logger.warning.assert_called_once()
            assert "Non-finite" in mock_logger.warning.call_args[0][0]


class TestVIAIntegration:
    """Integration tests verifying _parse_detected_flower uses safe confidence parsing."""

    @pytest.fixture
    def adapter(self):
        return VIAAdapter()

    def test_parse_detected_flower_uses_safe_confidence(self, adapter):
        """Integration: _parse_detected_flower uses warning-level confidence parsing."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._parse_detected_flower({
                "name": "Rose",
                "color": "red",
                "confidence": 1.5
            })
            assert result is not None
            assert result.confidence == 1.0  # Clamped
            mock_logger.warning.assert_called_once()

    def test_parse_detected_flower_valid_confidence_no_warning(self, adapter):
        """Integration: valid confidence doesn't trigger warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._parse_detected_flower({
                "name": "Rose",
                "color": "red",
                "confidence": 0.95
            })
            assert result is not None
            assert result.confidence == 0.95
            mock_logger.warning.assert_not_called()

    def test_parse_detected_flower_missing_confidence(self, adapter):
        """Integration: missing confidence key -> .get() returns None -> warning."""
        with patch('backend.agents.adapters.via_adapter.logger') as mock_logger:
            result = adapter._parse_detected_flower({
                "name": "Rose",
                "color": "red"
                # No confidence key
            })
            assert result is not None
            assert result.confidence == 0.0
            mock_logger.warning.assert_called_once()
