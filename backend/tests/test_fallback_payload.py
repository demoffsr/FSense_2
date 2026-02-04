"""
Tests for SFA Fallback Payload Builder

Tests the _build_fallback_payload() function in runner.py that constructs
a minimal FlowerCardPayload when SFA fails but FMRA has candidates.
"""

import pytest
from unittest.mock import patch

from backend.pipeline.context import (
    PipelineContext,
    CandidatesData,
    FlowerCandidate,
    RisksData,
)
from backend.pipeline.runner import _build_fallback_payload, FALLBACK_PAYLOAD_ENABLED
from backend.schemas.flower_card_payload import FlowerCardPayload


class TestFallbackPayloadHappyPath:
    """Tests for successful fallback payload generation."""

    def test_happy_path_full_context(self):
        """Full context with valid flower data returns valid payload."""
        ctx = PipelineContext(
            user_input="Test message",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="rose_001",
                        name="Red Rose",
                        match_score=0.95,
                        meanings=["Love", "Passion", "Romance", "Beauty"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.header.flower_id == "rose_001"
        assert payload.header.name == "Red Rose"
        assert payload.meaning.meanings == ["Love", "Passion", "Romance", "Beauty"]
        assert payload.request_id == ctx.request_id
        assert payload.pipeline_version == "0.5.7"

    def test_schema_validation_passes(self):
        """Returned payload passes Pydantic validation."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="lily_001",
                        name="White Lily",
                        meanings=["Purity", "Innocence"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        # Should not raise ValidationError
        validated = FlowerCardPayload.model_validate(payload.model_dump())
        assert validated.header.flower_id == "lily_001"

    def test_by_alias_output_produces_camelcase(self):
        """model_dump(by_alias=True) produces camelCase keys for iOS."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="tulip_001",
                        name="Yellow Tulip",
                        meanings=["Friendship"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)
        payload_dict = payload.model_dump(by_alias=True)

        # Check header uses camelCase
        assert "flowerId" in payload_dict["header"]
        assert "flower_id" not in payload_dict["header"]
        assert "imageUrl" in payload_dict["header"]
        assert "imageAsset" in payload_dict["header"]


class TestFallbackPayloadEdgeCases:
    """Tests for edge cases and missing data."""

    def test_empty_candidates_list_returns_none(self):
        """Empty candidates list returns None."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(candidates=[]),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is None

    def test_none_candidates_returns_none(self):
        """Default CandidatesData (empty) returns None."""
        ctx = PipelineContext(user_input="Test")
        # ctx.candidates is default CandidatesData with empty candidates list

        payload = _build_fallback_payload(ctx)

        assert payload is None

    def test_missing_flower_id_uses_placeholder(self):
        """Missing flower_id uses 'unknown' placeholder."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="",  # Empty
                        name="Mystery Flower",
                        meanings=["Unknown"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.header.flower_id == "unknown"
        assert payload.header.name == "Mystery Flower"

    def test_missing_flower_name_uses_placeholder(self):
        """Missing flower name uses 'Flower' placeholder."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="mystery_001",
                        name="",  # Empty
                        meanings=["Beautiful"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.header.flower_id == "mystery_001"
        assert payload.header.name == "Flower"

    def test_none_flower_id_uses_placeholder(self):
        """None flower_id uses 'unknown' placeholder."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id=None,  # type: ignore - testing None handling
                        name="Test Flower",
                        meanings=["Test"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.header.flower_id == "unknown"

    def test_empty_meanings_list_uses_defaults(self):
        """Empty meanings list uses default values."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="rose_001",
                        name="Rose",
                        meanings=[],  # Empty
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.meaning.meanings == ["Beauty", "Emotion", "Care"]

    def test_meanings_truncated_to_four(self):
        """Meanings list truncated to 4 items (schema max is 5)."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="rose_001",
                        name="Rose",
                        meanings=["A", "B", "C", "D", "E", "F"],  # 6 items
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert len(payload.meaning.meanings) == 4
        assert payload.meaning.meanings == ["A", "B", "C", "D"]


class TestFallbackPayloadRiskLevels:
    """Tests for RFFA risk level integration."""

    def test_rffa_high_risk_elevated_in_payload(self):
        """High risk from RFFA reflects in payload."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="lily_001",
                        name="Lily",
                        meanings=["Sympathy"],
                    )
                ]
            ),
            risks=RisksData(
                overall_risk_level="high",
                fit_assessment="Not appropriate for casual gifting.",
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.gifting.emotional_risk.level == "high"
        assert payload.gifting.emotional_risk.description == "Not appropriate for casual gifting."
        assert payload.gifting.suitability.level == "moderate"

    def test_rffa_medium_risk_moderate_in_payload(self):
        """Medium risk from RFFA reflects as moderate in payload."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="orchid_001",
                        name="Orchid",
                        meanings=["Elegance"],
                    )
                ]
            ),
            risks=RisksData(
                overall_risk_level="medium",
                fit_assessment="Consider the relationship context.",
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.gifting.emotional_risk.level == "moderate"
        assert payload.gifting.emotional_risk.description == "Consider the relationship context."

    def test_rffa_low_risk_default_in_payload(self):
        """Low risk from RFFA uses defaults."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="daisy_001",
                        name="Daisy",
                        meanings=["Innocence"],
                    )
                ]
            ),
            risks=RisksData(overall_risk_level="low"),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.gifting.emotional_risk.level == "low"
        assert payload.gifting.suitability.level == "good"

    def test_concurrent_failures_sfa_and_rffa(self):
        """Both SFA and RFFA failed (default risks) - still works."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="sunflower_001",
                        name="Sunflower",
                        meanings=["Happiness", "Joy"],
                    )
                ]
            ),
            # risks is default RisksData with overall_risk_level="low"
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.gifting.emotional_risk.level == "low"
        assert payload.gifting.suitability.level == "good"


class TestFallbackPayloadFeatureFlag:
    """Tests for feature flag behavior."""

    def test_feature_flag_disabled_returns_none(self, monkeypatch):
        """Feature flag disabled returns None."""
        # Need to reload the module to pick up the env var change
        monkeypatch.setenv("FALLBACK_PAYLOAD_ENABLED", "false")

        # Import fresh to get the new flag value
        import importlib
        from backend.pipeline import runner as runner_module

        importlib.reload(runner_module)

        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="rose_001",
                        name="Rose",
                        meanings=["Love"],
                    )
                ]
            ),
        )

        payload = runner_module._build_fallback_payload(ctx)

        assert payload is None

        # Reload again to restore default
        monkeypatch.setenv("FALLBACK_PAYLOAD_ENABLED", "true")
        importlib.reload(runner_module)

    def test_feature_flag_enabled_returns_payload(self, monkeypatch):
        """Feature flag explicitly enabled returns payload."""
        monkeypatch.setenv("FALLBACK_PAYLOAD_ENABLED", "true")

        import importlib
        from backend.pipeline import runner as runner_module

        importlib.reload(runner_module)

        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="rose_001",
                        name="Rose",
                        meanings=["Love"],
                    )
                ]
            ),
        )

        payload = runner_module._build_fallback_payload(ctx)

        assert payload is not None


class TestFallbackPayloadIntegration:
    """Integration tests for fallback in runner functions."""

    def test_run_flower_chat_uses_fallback_on_sfa_failure(self, monkeypatch):
        """run_flower_chat returns fallback when SFA fails but FMRA succeeds."""
        from backend.pipeline.context import CandidatesData, FlowerCandidate

        # Mock orchestrator to return context with candidates but no ui_payload
        def mock_run(self, ctx):
            ctx.candidates = CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="mock_rose",
                        name="Mock Rose",
                        meanings=["Test", "Mock"],
                    )
                ]
            )
            ctx.ui_payload = None  # SFA failed
            return ctx

        monkeypatch.setattr(
            "backend.pipeline.runner.PipelineOrchestrator.run", mock_run
        )
        monkeypatch.setattr(
            "backend.pipeline.runner.get_settings",
            lambda: type("Settings", (), {"openai_api_key": "test"})(),
        )

        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("Test prompt", region="US")

        assert result["success"] is True
        assert result["data"]["_fallback"] is True
        assert result["data"]["header"]["flowerId"] == "mock_rose"

    def test_run_pipeline_uses_fallback_on_sfa_failure(self, monkeypatch):
        """run_pipeline returns fallback when SFA fails but FMRA succeeds."""
        from backend.pipeline.context import CandidatesData, FlowerCandidate

        def mock_run(self, ctx):
            ctx.candidates = CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="mock_tulip",
                        name="Mock Tulip",
                        meanings=["Spring"],
                    )
                ]
            )
            ctx.ui_payload = None
            return ctx

        monkeypatch.setattr(
            "backend.pipeline.runner.PipelineOrchestrator.run", mock_run
        )

        from backend.pipeline.runner import run_pipeline

        result = run_pipeline("Test prompt")

        assert result.get("error") is not True
        assert result["_fallback"] is True
        assert result["header"]["flowerId"] == "mock_tulip"


class TestFallbackPayloadContent:
    """Tests for specific content in fallback payload."""

    def test_suggested_questions_include_flower_name(self):
        """Suggested questions are personalized with flower name."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="peony_001",
                        name="Peony",
                        meanings=["Prosperity"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert "Peony" in payload.ask_ai.suggested_questions[0]

    def test_mood_intensity_uses_default(self):
        """Mood intensity uses project default (0.4)."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="iris_001",
                        name="Iris",
                        meanings=["Wisdom"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert payload.meaning.mood_intensity.value == 0.4
        assert payload.meaning.mood_intensity.label == "Balanced"

    def test_why_this_flower_text_includes_name(self):
        """Why this flower text includes flower name."""
        ctx = PipelineContext(
            user_input="Test",
            candidates=CandidatesData(
                candidates=[
                    FlowerCandidate(
                        flower_id="carnation_001",
                        name="Carnation",
                        meanings=["Fascination"],
                    )
                ]
            ),
        )

        payload = _build_fallback_payload(ctx)

        assert payload is not None
        assert "Carnation" in payload.meaning.why_this_flower.text
