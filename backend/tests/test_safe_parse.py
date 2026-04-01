"""Unit tests for safe_parse_float utility."""

import pytest
from backend.core.safe_parse import safe_parse_float


class TestSafeParseFloat:
    """Test safe_parse_float function."""

    # Valid inputs
    def test_valid_float_string(self):
        assert safe_parse_float("0.75") == 0.75

    def test_valid_int(self):
        assert safe_parse_float(1) == 1.0

    def test_valid_float(self):
        assert safe_parse_float(0.5) == 0.5

    def test_valid_zero(self):
        assert safe_parse_float(0) == 0.0

    def test_valid_negative_float_clamped(self):
        # Should clamp to min_val (default 0.0)
        assert safe_parse_float(-0.5) == 0.0

    def test_valid_string_with_whitespace(self):
        # float() handles whitespace
        assert safe_parse_float("  0.8  ") == 0.8

    # Invalid inputs → default
    def test_invalid_string_high(self):
        assert safe_parse_float("high", default=0.7) == 0.7

    def test_invalid_string_low(self):
        assert safe_parse_float("low", default=0.3) == 0.3

    def test_malformed_string(self):
        assert safe_parse_float("0.7.2", default=0.5) == 0.5

    def test_none(self):
        assert safe_parse_float(None, default=0.6) == 0.6

    def test_empty_string(self):
        assert safe_parse_float("", default=0.4) == 0.4

    def test_list_input(self):
        assert safe_parse_float([0.5], default=0.3) == 0.3

    def test_dict_input(self):
        assert safe_parse_float({"value": 0.5}, default=0.3) == 0.3

    # NaN and Inf → default
    def test_nan_string(self):
        assert safe_parse_float("nan", default=0.5) == 0.5

    def test_nan_uppercase(self):
        assert safe_parse_float("NaN", default=0.5) == 0.5

    def test_inf_string(self):
        assert safe_parse_float("inf", default=0.5) == 0.5

    def test_inf_uppercase(self):
        assert safe_parse_float("Inf", default=0.5) == 0.5

    def test_negative_inf(self):
        assert safe_parse_float("-inf", default=0.5) == 0.5

    def test_infinity_word(self):
        assert safe_parse_float("infinity", default=0.5) == 0.5

    # Clamping
    def test_clamp_above_max(self):
        assert safe_parse_float(1.5, max_val=1.0) == 1.0

    def test_clamp_below_min(self):
        assert safe_parse_float(-0.5, min_val=0.0) == 0.0

    def test_clamp_custom_range(self):
        # Value 5 should clamp to max_val=10
        assert safe_parse_float(15, min_val=0, max_val=10) == 10.0

    def test_clamp_negative_range(self):
        # Value in range [-1, 1]
        assert safe_parse_float(-0.5, min_val=-1.0, max_val=1.0) == -0.5

    def test_at_boundary_min(self):
        assert safe_parse_float(0.0, min_val=0.0, max_val=1.0) == 0.0

    def test_at_boundary_max(self):
        assert safe_parse_float(1.0, min_val=0.0, max_val=1.0) == 1.0

    # Default values
    def test_default_no_args(self):
        # Default behavior with invalid input
        assert safe_parse_float("invalid") == 0.0

    def test_custom_default(self):
        assert safe_parse_float("invalid", default=0.85) == 0.85

    # Context logging (just verify it doesn't crash)
    def test_context_parameter(self):
        result = safe_parse_float("invalid", default=0.5, context="EIA.emotion_intensity")
        assert result == 0.5

    def test_empty_context(self):
        result = safe_parse_float("invalid", default=0.5, context="")
        assert result == 0.5

    # Edge cases
    def test_scientific_notation(self):
        assert safe_parse_float("1e-2") == 0.01

    def test_negative_zero(self):
        assert safe_parse_float("-0") == 0.0

    def test_very_small_value(self):
        result = safe_parse_float("0.0001", min_val=0.0, max_val=1.0)
        assert result == 0.0001

    def test_integer_string(self):
        assert safe_parse_float("1", max_val=1.0) == 1.0


class TestSafeParseFloatLogging:
    """Test that logging works correctly (using caplog fixture)."""

    def test_logs_warning_on_invalid_value(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            safe_parse_float("high", default=0.7, context="TEST")
        assert "Invalid float value" in caplog.text
        assert "TEST" in caplog.text

    def test_logs_warning_on_nan(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING):
            safe_parse_float("nan", default=0.5, context="TEST")
        assert "Non-finite value" in caplog.text
        assert "TEST" in caplog.text

    def test_logs_debug_on_clamp(self, caplog):
        import logging
        with caplog.at_level(logging.DEBUG):
            safe_parse_float(1.5, max_val=1.0, context="TEST")
        assert "Clamped" in caplog.text
