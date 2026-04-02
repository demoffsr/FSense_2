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
        # Version 0.4.0 - multi-candidate + diversity support
        assert result["data"]["pipeline_version"] == "0.4.0"


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

        # VIA added in v0.3.0 for vision/image analysis
        expected_order = [
            "VIA", "FIA", "EIA", "RIL", "FMRA", "CIA",
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
        
        # Should have timing records for all agents
        assert len(ctx.timings) == 10
        
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


# ═══════════════════════════════════════════════════════════════════════════════
# RUN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
