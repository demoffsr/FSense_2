"""
Pipeline Smoke Tests - v0.0.1

Basic smoke tests to verify the pipeline is wired correctly.
These tests use mock/placeholder data (no real AI calls in v0.0.1 placeholders).

Run with:
    pytest backend/tests/test_pipeline_smoke.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

# Mock settings before importing pipeline modules
@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings to avoid requiring real API key in tests."""
    with patch("backend.core.settings._load_dotenv"):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key-for-testing"}):
            # Reset settings singleton
            from backend.core import settings
            settings._settings = None
            yield
            settings._settings = None


class TestFlowerChat:
    """Tests for run_flower_chat() - the main iOS entrypoint."""
    
    def test_flower_chat_success(self):
        """Test that run_flower_chat returns success with valid payload."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("I want to apologize sincerely")
        
        # Must return success
        assert result["success"] is True
        assert "data" in result
        
        # Data must contain required fields
        data = result["data"]
        assert "header" in data
        assert "meaning" in data
        assert "gifting" in data
        assert "context" in data
    
    def test_flower_chat_has_header(self):
        """Test that response contains valid header."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("I want to express my love")

        assert result["success"] is True
        header = result["data"]["header"]

        # Uses camelCase serialization (serialization_alias)
        assert "flowerId" in header
        assert "name" in header
        assert header["name"]  # Not empty

    def test_flower_chat_has_alternatives(self):
        """Test that response contains alternatives array."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("I want to apologize")

        assert result["success"] is True
        assert "alternatives" in result["data"]
        alternatives = result["data"]["alternatives"]

        assert isinstance(alternatives, list)
        # May be empty or have up to 4 items
        assert len(alternatives) <= 4

        # If alternatives exist, verify structure
        if alternatives:
            alt = alternatives[0]
            assert "flowerId" in alt
            assert "name" in alt
            assert "confidence" in alt
            assert "briefReason" in alt
            assert 0.0 <= alt["confidence"] <= 1.0
    
    def test_flower_chat_has_meanings(self):
        """Test that response contains meanings."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("Thank you flowers")
        
        assert result["success"] is True
        meaning = result["data"]["meaning"]
        
        assert "meanings" in meaning
        assert isinstance(meaning["meanings"], list)
        assert len(meaning["meanings"]) >= 1
    
    def test_flower_chat_has_gifting_info(self):
        """Test that response contains gifting information."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("Anniversary gift")

        assert result["success"] is True
        gifting = result["data"]["gifting"]

        # GiftingTab uses snake_case (no serialization_alias)
        assert "suitability" in gifting
        assert "emotional_risk" in gifting
        assert "recipient_fits" in gifting
        assert "when_to_gift" in gifting
        assert "when_to_avoid" in gifting
    
    def test_flower_chat_has_context(self):
        """Test that response contains context information."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("Flowers for my mother")
        
        assert result["success"] is True
        context = result["data"]["context"]

        # ContextTab uses snake_case (no serialization_alias)
        assert "summary" in context
        assert "cultural_interpretations" in context
        assert "relationship_contexts" in context
        assert "timing_sensitivities" in context
        assert "common_misinterpretations" in context
    
    def test_flower_chat_empty_prompt_fails(self):
        """Test that empty prompt returns error."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("")
        
        assert result["success"] is False
        assert "error" in result
        assert "empty" in result["error"].lower()
    
    def test_flower_chat_whitespace_prompt_fails(self):
        """Test that whitespace-only prompt returns error."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("   \n\t  ")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_flower_chat_region_normalization(self):
        """Test that region is normalized correctly."""
        from backend.pipeline.runner import run_flower_chat
        
        # Various region formats should work
        for region in ["us", "US", "  us  ", "Us"]:
            result = run_flower_chat("Test flowers", region=region)
            assert result["success"] is True
    
    def test_flower_chat_returns_request_id(self):
        """Test that response contains request_id for tracking."""
        from backend.pipeline.runner import run_flower_chat
        
        result = run_flower_chat("Birthday flowers")
        
        assert result["success"] is True
        assert "request_id" in result["data"]
        assert result["data"]["request_id"]  # Not empty
    
    def test_flower_chat_returns_pipeline_version(self):
        """Test that response contains pipeline version."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("Get well flowers")

        assert result["success"] is True
        # pipeline_version uses snake_case (no serialization_alias)
        assert "pipeline_version" in result["data"]
        # Version 0.5.0 - RIL removed, deterministic relationship inference
        assert result["data"]["pipeline_version"] == "0.5.0"


class TestRelationshipInference:
    """Unit tests for deterministic relationship inference."""

    def test_romantic_recipient(self):
        """Test romantic recipients are correctly identified."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        intent = IntentData(
            primary_intent="Anniversary for girlfriend",
            raw_output={
                "recipient": "girlfriend",
                "relationship_level": "established",
                "tone": "passionate",
                "occasion": "anniversary",
                "context_flags": {"is_first_gift": False},
            }
        )

        rel = infer_relationship_from_intent(intent)

        assert rel.relationship_type == "romantic"
        assert rel.intimacy_level == 0.7
        assert rel.formality_level < 0.3
        assert rel.power_dynamic == "equal"
        assert rel.raw_output["relationship_stage"] == "established"
        assert rel.raw_output["gift_appropriateness"]["romantic_flowers_ok"] is True
        assert rel.raw_output["gift_appropriateness"]["max_intensity"] >= 0.8

    def test_professional_recipient_boss(self):
        """Test professional recipients have correct power dynamic."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        intent = IntentData(
            primary_intent="Thank you for boss",
            raw_output={
                "recipient": "boss",
                "relationship_level": "established",
                "tone": "formal",
                "occasion": "thank_you",
            }
        )

        rel = infer_relationship_from_intent(intent)

        assert rel.relationship_type == "professional"
        assert rel.power_dynamic == "hierarchical_up"
        assert rel.formality_level > 0.7
        assert rel.raw_output["gift_appropriateness"]["romantic_flowers_ok"] is False
        assert "red rose" in rel.raw_output["gift_appropriateness"]["avoid_flowers"]

    def test_familial_recipient_mother(self):
        """Test familial recipients with respectful power dynamic."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        intent = IntentData(
            primary_intent="Birthday for mom",
            raw_output={
                "recipient": "mom",
                "relationship_level": "longterm",
                "tone": "warm",
            }
        )

        rel = infer_relationship_from_intent(intent)

        assert rel.relationship_type == "familial"
        assert rel.power_dynamic == "respectful"
        assert rel.intimacy_level == 0.9
        assert rel.raw_output["relationship_stage"] == "deep"

    def test_unknown_recipient_fallback(self):
        """Unknown recipients should get safe defaults."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        intent = IntentData(
            primary_intent="Gift for the nurse",
            raw_output={
                "recipient": "the nurse",  # Unknown
                "relationship_level": "new",
            }
        )

        rel = infer_relationship_from_intent(intent)

        assert rel.relationship_type == "neutral"
        assert rel.power_dynamic == "equal"
        assert rel.intimacy_level == 0.2  # "new" relationship_level
        assert rel.raw_output["confidence"] == 0.5  # Lower confidence for unknown

    def test_sympathy_occasion_overrides(self):
        """Sympathy occasions should limit intensity and disable romantic."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        intent = IntentData(
            primary_intent="Sympathy for friend",
            raw_output={
                "recipient": "friend",
                "occasion": "sympathy",
            }
        )

        rel = infer_relationship_from_intent(intent)

        appropriateness = rel.raw_output["gift_appropriateness"]
        assert appropriateness["romantic_flowers_ok"] is False
        assert appropriateness["max_intensity"] <= 0.6

    def test_romantic_with_remorse_vs_love_emotions(self):
        """Same recipient with different emotions should affect max_intensity."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        base_raw = {"recipient": "wife", "relationship_level": "longterm"}

        # High-intensity remorse should cap max_intensity
        intent_remorse = IntentData(raw_output={**base_raw, "occasion": "apology"})
        emotion_remorse = {"primary_emotion": "remorse", "emotion_intensity": 0.9}
        rel_remorse = infer_relationship_from_intent(intent_remorse, emotion_remorse)

        # Love/joy should allow full intensity
        intent_love = IntentData(raw_output={**base_raw, "occasion": "anniversary"})
        emotion_love = {"primary_emotion": "love", "emotion_intensity": 0.9}
        rel_love = infer_relationship_from_intent(intent_love, emotion_love)

        # Both should be romantic
        assert rel_remorse.relationship_type == "romantic"
        assert rel_love.relationship_type == "romantic"

        # Remorse should have capped intensity
        assert rel_remorse.raw_output["gift_appropriateness"]["max_intensity"] <= 0.6
        # Love should have higher intensity
        assert rel_love.raw_output["gift_appropriateness"]["max_intensity"] > 0.8

    def test_recipient_aliases(self):
        """Test that common recipient aliases are handled."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        aliases = {
            "gf": "romantic",
            "bf": "romantic",
            "mum": "familial",
            "mama": "familial",
            "bestie": "platonic",
            "co-worker": "professional",
        }

        for alias, expected_type in aliases.items():
            intent = IntentData(raw_output={"recipient": alias})
            rel = infer_relationship_from_intent(intent)
            assert rel.relationship_type == expected_type, f"Failed for {alias}"

    def test_ex_relationships(self):
        """Test ex-relationships are still romantic context."""
        from backend.agents.adapters.relationship_inference import infer_relationship_from_intent
        from backend.pipeline.context import IntentData

        ex_recipients = ["ex-girlfriend", "ex-boyfriend", "ex-wife", "ex-husband", "ex"]

        for recipient in ex_recipients:
            intent = IntentData(raw_output={"recipient": recipient})
            rel = infer_relationship_from_intent(intent)
            assert rel.relationship_type == "romantic", f"Failed for {recipient}"


class TestRelationshipIntegration:
    """Integration tests verifying downstream agents receive correct data."""

    def test_fmra_receives_gift_appropriateness(self):
        """FMRA should receive gift_appropriateness from inference."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("I want to thank my boss")

        # Verify pipeline succeeded
        assert result["success"] is True

    def test_pipeline_without_ril_produces_valid_output(self):
        """Full pipeline should work without RIL agent."""
        from backend.pipeline.runner import run_flower_chat

        result = run_flower_chat("I want to apologize to my wife")

        assert result["success"] is True
        assert result["data"] is not None
        assert "header" in result["data"]

    def test_relationship_data_populated_in_context(self):
        """Verify relationship data is populated after pipeline run."""
        from backend.pipeline.orchestrator import PipelineOrchestrator
        from backend.pipeline.context import PipelineContext

        orchestrator = PipelineOrchestrator()
        ctx = PipelineContext(user_input="Flowers for my girlfriend")

        ctx = orchestrator.run(ctx)

        # Relationship should be populated
        assert ctx.relationship.relationship_type != ""
        assert ctx.relationship.raw_output.get("inference_source") == "deterministic"


class TestPipelineContext:
    """Tests for PipelineContext."""

    def test_context_creation(self):
        """Test that context can be created with defaults."""
        from backend.pipeline.context import PipelineContext
        
        ctx = PipelineContext(user_input="Test")
        
        assert ctx.user_input == "Test"
        assert ctx.request_id  # Auto-generated
        assert ctx.region == "us"  # Default
    
    def test_context_timing(self):
        """Test context timing functionality."""
        from backend.pipeline.context import PipelineContext
        
        ctx = PipelineContext(user_input="Test")
        
        ctx.start_timing("TestAgent")
        ctx.end_timing("TestAgent", status="completed")
        
        assert len(ctx.timings) == 1
        assert ctx.timings[0].agent_name == "TestAgent"
        assert ctx.timings[0].status == "completed"
    
    def test_context_errors(self):
        """Test context error recording."""
        from backend.pipeline.context import PipelineContext
        
        ctx = PipelineContext(user_input="Test")
        
        ctx.add_error("Test error")
        
        assert len(ctx.errors) == 1
        assert "Test error" in ctx.errors[0]


class TestOrchestrator:
    """Tests for PipelineOrchestrator."""

    def test_orchestrator_agent_order(self):
        """Test that orchestrator has correct agent order."""
        from backend.pipeline.orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()

        # RIL removed in v0.5.0 - relationship now inferred deterministically
        expected_order = [
            "VIA", "FIA", "EIA", "FMRA", "CIA",
            "AITB", "RFFA", "CRI", "SRFL", "SFA"
        ]

        assert orchestrator.agent_names == expected_order

    def test_orchestrator_runs_all_agents(self):
        """Test that orchestrator runs all agents."""
        from backend.pipeline.orchestrator import PipelineOrchestrator
        from backend.pipeline.context import PipelineContext

        orchestrator = PipelineOrchestrator()
        ctx = PipelineContext(user_input="Test")

        ctx = orchestrator.run(ctx)

        # Should have timing records for all agents (9, RIL removed)
        assert len(ctx.timings) == 9

        # All should be completed
        for timing in ctx.timings:
            assert timing.status == "completed"


class TestBaseAgent:
    """Tests for BaseAgent interface."""
    
    def test_agent_interface(self):
        """Test that agents conform to BaseAgent interface."""
        from backend.agents.base import BaseAgent
        from backend.agents.adapters.fia_adapter import FIAAdapter
        
        agent = FIAAdapter()
        
        assert isinstance(agent, BaseAgent)
        assert hasattr(agent, "name")
        assert hasattr(agent, "run")
        assert agent.name == "FIA"


class TestSchemas:
    """Tests for Pydantic schemas."""
    
    def test_flower_card_payload_validation(self):
        """Test FlowerCardPayload schema validation."""
        from backend.schemas.flower_card_payload import (
            FlowerCardPayload,
            FlowerHeader,
            MeaningTab,
            SymbolismCard,
            WhyThisFlowerCard,
            MoodIntensity,
            GiftingTab,
            GiftSuitabilityCard,
            EmotionalRiskCard,
            RecipientFitItem,
            GiftingOccasionItem,
            ContextTab,
            ContextSummary,
            CulturalInterpretationItem,
            RelationshipContextItem,
            TimingSensitivityItem,
            CommonMisinterpretationItem,
        )
        
        # Build minimal valid payload
        payload = FlowerCardPayload(
            header=FlowerHeader(
                flower_id="test_001",
                name="Test Flower",
            ),
            meaning=MeaningTab(
                meanings=["Love"],
                symbolism=SymbolismCard(text="Test symbolism"),
                why_this_flower=WhyThisFlowerCard(text="Test reason"),
                mood_intensity=MoodIntensity(value=0.5, label="Balanced"),
            ),
            gifting=GiftingTab(
                suitability=GiftSuitabilityCard(level="good", description="Good"),
                emotional_risk=EmotionalRiskCard(level="low", description="Low"),
                recipient_fits=[RecipientFitItem(recipient_type="Partner", fit_level="good")],
                when_to_gift=[GiftingOccasionItem(occasion="Anniversary", suitability="good")],
                when_to_avoid=[GiftingOccasionItem(occasion="Funeral", suitability="not_recommended")],
            ),
            context=ContextTab(
                summary=ContextSummary(text="Test summary"),
                cultural_interpretations=[CulturalInterpretationItem(
                    emoji="🌍", culture="Universal", interpretation="Love", sentiment="positive"
                )],
                relationship_contexts=[RelationshipContextItem(
                    relationship_type="Partner", appropriateness="appropriate", guidance="Good"
                )],
                timing_sensitivities=[TimingSensitivityItem(
                    timing="Anytime", sensitivity="low", note="Fine"
                )],
                common_misinterpretations=[CommonMisinterpretationItem(
                    misinterpretation="None", clarification="N/A"
                )],
            ),
            request_id="test-123",
        )
        
        # Should serialize without error
        json_data = payload.model_dump(mode="json", by_alias=True)

        assert json_data["header"]["name"] == "Test Flower"
        # pipeline_version doesn't have serialization_alias
        assert json_data["pipeline_version"] == "0.0.2"

        # Alternatives should be empty by default
        assert json_data["alternatives"] == []


class TestFMRAVisionOptimization:
    """Tests for FMRA vision meanings optimization."""

    def test_fmra_vision_uses_db_meanings_skips_ai(self):
        """FMRA should use DB meanings and NOT call AI for known flowers."""
        from backend.agents.adapters.fmra_adapter import FMRAAdapter
        from backend.pipeline.context import PipelineContext, VisionAnalysisData, DetectedFlower

        ctx = PipelineContext(user_input="What is this?")
        ctx.vision = VisionAnalysisData(
            main_flower=DetectedFlower(name="Red Rose", color="red", confidence=0.95)
        )

        mock_flower_data = {
            "id": "red_rose",
            "name": "Red Rose",
            "price_tier": "mid",
            "primary_meanings": ["love", "passion", "romance", "desire"]
        }

        with patch('backend.agents.adapters.fmra_adapter.get_flower_by_id', return_value=mock_flower_data) as mock_db, \
             patch('backend.agents.adapters.fmra_adapter.get_ai_client_fast') as mock_ai:

            adapter = FMRAAdapter()
            candidate = adapter._flower_from_vision(ctx)

            # Verify DB was called
            mock_db.assert_called_once_with("red_rose")

            # CRITICAL: Verify AI was NOT called (the optimization)
            mock_ai.assert_not_called()

            # Verify meanings are from DB (capitalized)
            assert candidate.meanings == ["Love", "Passion", "Romance", "Desire"]
            assert candidate.price_tier == "mid"

    def test_fmra_vision_falls_back_to_ai_when_no_db(self):
        """FMRA should call AI when flower not in DB."""
        from backend.agents.adapters.fmra_adapter import FMRAAdapter
        from backend.pipeline.context import PipelineContext, VisionAnalysisData, DetectedFlower

        ctx = PipelineContext(user_input="What is this?")
        ctx.vision = VisionAnalysisData(
            main_flower=DetectedFlower(name="Exotic Orchid", color="purple", confidence=0.85)
        )

        mock_ai_client = MagicMock()
        mock_ai_client.complete_json.return_value = {"meanings": ["Exotic", "Luxury", "Beauty"]}

        with patch('backend.agents.adapters.fmra_adapter.get_flower_by_id', return_value=None), \
             patch('backend.agents.adapters.fmra_adapter.get_ai_client_fast', return_value=mock_ai_client) as mock_ai:

            adapter = FMRAAdapter()
            # Mock _estimate_price_tier since flower not in DB
            with patch.object(adapter, '_estimate_price_tier', return_value='premium') as mock_estimate:
                candidate = adapter._flower_from_vision(ctx)

                # Verify price estimation was called
                mock_estimate.assert_called_once_with("Exotic Orchid")

            # Verify AI WAS called (fallback)
            mock_ai.assert_called_once()
            mock_ai_client.complete_json.assert_called_once()

            # Verify results
            assert candidate.meanings == ["Exotic", "Luxury", "Beauty"]
            assert candidate.price_tier == "premium"

    def test_fmra_vision_uses_ai_when_db_meanings_empty(self):
        """FMRA should call AI when DB flower has empty meanings."""
        from backend.agents.adapters.fmra_adapter import FMRAAdapter
        from backend.pipeline.context import PipelineContext, VisionAnalysisData, DetectedFlower

        ctx = PipelineContext(user_input="What is this?")
        ctx.vision = VisionAnalysisData(
            main_flower=DetectedFlower(name="Rare Flower", color="white", confidence=0.90)
        )

        # DB has flower but with empty meanings (edge case)
        mock_flower_data = {
            "id": "rare_flower",
            "name": "Rare Flower",
            "price_tier": "premium",
            "primary_meanings": []  # Empty!
        }

        mock_ai_client = MagicMock()
        mock_ai_client.complete_json.return_value = {"meanings": ["Rare", "Unique", "Special"]}

        with patch('backend.agents.adapters.fmra_adapter.get_flower_by_id', return_value=mock_flower_data) as mock_db, \
             patch('backend.agents.adapters.fmra_adapter.get_ai_client_fast', return_value=mock_ai_client) as mock_ai:

            adapter = FMRAAdapter()
            candidate = adapter._flower_from_vision(ctx)

            # Verify DB was called
            mock_db.assert_called_once_with("rare_flower")

            # Verify AI WAS called (fallback due to empty meanings)
            mock_ai.assert_called_once()

            # Verify price_tier from DB, meanings from AI
            assert candidate.price_tier == "premium"
            assert candidate.meanings == ["Rare", "Unique", "Special"]


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
