"""Tests for _preserved_context in VIA clarification payload."""
import dataclasses
import pytest
from unittest.mock import patch, MagicMock

from backend.pipeline.orchestrator import PipelineOrchestrator
from backend.pipeline.context import (
    PipelineContext,
    UserPriors,
    VisionAnalysisData,
    DetectedFlower,
)


class TestBuildClarificationPayload:
    """Unit tests for _build_clarification_payload preserved context."""

    @pytest.fixture
    def orchestrator(self):
        return PipelineOrchestrator()

    def _make_ctx(
        self,
        budget_range=None,
        region="us",
        user_input="What flower is this?",
    ):
        """Create a PipelineContext with VIA clarification data."""
        ctx = PipelineContext(
            user_input=user_input,
            region=region,
            priors=UserPriors(budget_range=budget_range),
        )
        ctx.vision = VisionAnalysisData(
            main_flower=DetectedFlower(name="Rose", color="red", confidence=0.5),
            secondary_flowers=[
                DetectedFlower(name="Lily", color="white", confidence=0.4),
            ],
            needs_clarification=True,
            clarification_message="Multiple flowers detected. Which one?",
            bouquet_description="A mixed bouquet",
        )
        return ctx

    def test_preserved_context_contains_full_priors(self, orchestrator):
        """_preserved_context['priors'] is a dict with all UserPriors fields."""
        ctx = self._make_ctx(budget_range="premium")
        payload = orchestrator._build_clarification_payload(ctx)

        preserved = payload["_preserved_context"]
        priors = preserved["priors"]

        # All UserPriors fields present
        expected_fields = {f.name for f in dataclasses.fields(UserPriors)}
        assert set(priors.keys()) == expected_fields
        assert priors["budget_range"] == "premium"

    def test_preserved_context_with_none_budget(self, orchestrator):
        """None budget is preserved; region defaults to 'us'."""
        ctx = self._make_ctx(budget_range=None)
        payload = orchestrator._build_clarification_payload(ctx)

        preserved = payload["_preserved_context"]
        assert preserved["priors"]["budget_range"] is None
        assert preserved["region"] == "us"

    @pytest.mark.parametrize("tier", ["budget", "mid", "premium", "any"])
    def test_preserved_context_all_budget_tiers(self, orchestrator, tier):
        """Each canonical budget tier is preserved exactly."""
        ctx = self._make_ctx(budget_range=tier)
        payload = orchestrator._build_clarification_payload(ctx)

        assert payload["_preserved_context"]["priors"]["budget_range"] == tier

    def test_preserved_context_includes_region_and_user_input(self, orchestrator):
        """Region and user_input are preserved in _preserved_context."""
        ctx = self._make_ctx(region="jp", user_input="What flower is this?")
        payload = orchestrator._build_clarification_payload(ctx)

        preserved = payload["_preserved_context"]
        assert preserved["region"] == "jp"
        assert preserved["user_input"] == "What flower is this?"

    def test_clarification_payload_original_keys_unchanged(self, orchestrator):
        """All original keys remain in the clarification payload."""
        ctx = self._make_ctx()
        payload = orchestrator._build_clarification_payload(ctx)

        required_keys = {
            "type", "message", "options", "bouquet_description",
            "request_id", "pipeline_version",
        }
        assert required_keys.issubset(set(payload.keys()))
        assert payload["type"] == "clarification"


class TestOrchestratorClarificationIntegration:
    """Integration tests: orchestrator.run() with VIA clarification."""

    def test_orchestrator_early_exit_preserves_context(self):
        """VIA clarification triggers early exit with preserved context."""
        orchestrator = PipelineOrchestrator()

        ctx = PipelineContext(
            user_input="What flower is this?",
            region="jp",
            priors=UserPriors(budget_range="mid"),
            image_base64="fake_base64_data",
        )

        # Mock VIA to set needs_clarification=True
        def mock_via_run(via_ctx):
            via_ctx.vision = VisionAnalysisData(
                main_flower=DetectedFlower(name="Tulip", color="yellow", confidence=0.4),
                secondary_flowers=[
                    DetectedFlower(name="Daisy", color="white", confidence=0.3),
                ],
                needs_clarification=True,
                clarification_message="I see multiple flowers.",
                bouquet_description="A spring bouquet",
            )

        with patch.object(orchestrator._via, 'run', side_effect=mock_via_run):
            result_ctx = orchestrator.run(ctx)

        # Pipeline stopped early — no FIA/EIA data
        assert result_ctx.intent.primary_intent == ""
        assert result_ctx.emotions.primary_emotion == ""

        # Clarification payload has preserved context
        payload = result_ctx.ui_payload
        assert payload is not None
        assert payload["type"] == "clarification"

        preserved = payload["_preserved_context"]
        assert preserved["priors"]["budget_range"] == "mid"
        assert preserved["region"] == "jp"
        assert preserved["user_input"] == "What flower is this?"

    def test_run_flower_chat_clarification_preserves_budget(self):
        """run_flower_chat returns clarification with preserved budget (normalized)."""
        from backend.pipeline.runner import run_flower_chat

        def mock_orchestrator_run(self, ctx):
            # Simulate VIA clarification
            ctx.vision = VisionAnalysisData(
                main_flower=DetectedFlower(name="Rose", confidence=0.4),
                needs_clarification=True,
                clarification_message="Which flower?",
            )
            ctx.ui_payload = self._build_clarification_payload(ctx)
            return ctx

        with patch.object(PipelineOrchestrator, 'run', mock_orchestrator_run):
            result = run_flower_chat(
                prompt="What flower is this?",
                region="US",
                image_base64="fake_image",
                budget_range="Luxury",
            )

        assert result["success"] is True
        data = result["data"]
        assert data["type"] == "clarification"

        preserved = data["_preserved_context"]
        # "Luxury" normalizes to "premium"
        assert preserved["priors"]["budget_range"] == "premium"

    def test_run_flower_chat_v2_clarification_preserves_budget(self):
        """run_flower_chat_v2 returns clarification with preserved budget.

        Since v2 delegates to run_flower_chat for FLOWER_REQUEST intent,
        we can patch run_flower_chat directly to simulate VIA clarification.
        """
        from backend.pipeline.runner import run_flower_chat_v2
        from backend.schemas.chat_response import IntentType

        mock_classification = MagicMock()
        mock_classification.intent = IntentType.FLOWER_REQUEST
        mock_classification.confidence = 0.9
        mock_classification.extracted_flower = None
        mock_classification.clarification_type = None

        mock_classifier_cls = MagicMock()
        mock_classifier_cls.return_value.classify.return_value = mock_classification

        # Simulate run_flower_chat returning a clarification payload
        fake_clarification = {
            "success": True,
            "data": {
                "type": "clarification",
                "message": "Which flower?",
                "options": [],
                "bouquet_description": "",
                "request_id": "test-123",
                "pipeline_version": "0.3.0",
                "_preserved_context": {
                    "priors": {"budget_range": "mid", "relationship_type": None,
                               "occasion": None, "recipient_info": None,
                               "color_preferences": [], "cultural_context": None},
                    "region": "us",
                    "user_input": "What flower is this?",
                },
            },
        }

        with patch(
            'backend.agents.adapters.intent_classifier_agent.IntentClassifierAgent',
            mock_classifier_cls,
        ), patch(
            'backend.pipeline.runner.run_flower_chat',
            return_value=fake_clarification,
        ):
            result = run_flower_chat_v2(
                prompt="What flower is this?",
                region="US",
                image_base64="fake_image",
                budget_range="mid",
            )

        assert result["success"] is True
        assert result["type"] == "recommendation"
        data = result["data"]
        assert data["type"] == "clarification"

        preserved = data["_preserved_context"]
        assert preserved["priors"]["budget_range"] == "mid"
