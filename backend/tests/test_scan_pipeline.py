"""
Scan Pipeline Tests - v1.0

Tests for the flower scan pipeline.
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.pipeline.scan_context import ScanContext, IdentifiedFlower, IdentificationData
from backend.pipeline.scan_orchestrator import run_scan, ScanOrchestrator
from backend.agents.adapters.flower_identification_agent import FlowerIdentificationAgent
from backend.agents.adapters.flower_search_agent import FlowerSearchAgent
from backend.agents.adapters.scan_detail_assembler import ScanDetailAssembler


class TestScanContext:
    """Tests for ScanContext."""

    def test_create_context(self):
        """Test basic context creation."""
        ctx = ScanContext(
            image_base64="test_base64",
            scan_mode="single",
            region="US",
        )
        assert ctx.image_base64 == "test_base64"
        assert ctx.scan_mode == "single"
        assert ctx.region == "US"
        assert ctx.request_id is not None

    def test_has_valid_identification_false_when_empty(self):
        """Test has_valid_identification returns False when no flower."""
        ctx = ScanContext()
        assert ctx.has_valid_identification() is False

    def test_has_valid_identification_true_with_flower(self):
        """Test has_valid_identification returns True with valid flower."""
        ctx = ScanContext()
        ctx.identification.primary_flower = IdentifiedFlower(
            id="test",
            name="Rose",
            confidence=0.9,
        )
        assert ctx.has_valid_identification() is True

    def test_has_valid_identification_false_low_confidence(self):
        """Test has_valid_identification returns False with low confidence."""
        ctx = ScanContext()
        ctx.identification.primary_flower = IdentifiedFlower(
            id="test",
            name="Rose",
            confidence=0.3,  # Below 0.5 threshold
        )
        assert ctx.has_valid_identification() is False


class TestFlowerIdentificationAgent:
    """Tests for FID agent."""

    def test_agent_name(self):
        """Test agent has correct name."""
        agent = FlowerIdentificationAgent()
        assert agent.name == "FID"

    def test_fallback_on_no_image(self):
        """Test agent sets error when no image provided."""
        agent = FlowerIdentificationAgent()
        ctx = ScanContext(image_base64="")
        agent.run(ctx)
        assert len(ctx.errors) > 0
        assert "No image provided" in ctx.errors[0]

    @patch("backend.agents.adapters.flower_identification_agent.get_ai_client")
    def test_parse_single_response(self, mock_client):
        """Test parsing single flower response."""
        mock_ai = MagicMock()
        mock_ai.analyze_image.return_value = {
            "flower": {
                "name": "Red Rose",
                "scientific_name": "Rosa",
                "color": "red",
                "confidence": 0.95,
            },
            "additional_notes": "A beautiful rose"
        }
        mock_client.return_value = mock_ai

        agent = FlowerIdentificationAgent()
        ctx = ScanContext(image_base64="test_image", scan_mode="single")
        agent.run(ctx)

        assert ctx.identification.primary_flower is not None
        assert ctx.identification.primary_flower.name == "Red Rose"
        assert ctx.identification.primary_flower.confidence == 0.95


class TestFlowerSearchAgent:
    """Tests for FSA agent."""

    def test_agent_name(self):
        """Test agent has correct name."""
        agent = FlowerSearchAgent()
        assert agent.name == "FSA"

    def test_fallback_on_no_flower(self):
        """Test agent uses fallback when no flower identified."""
        agent = FlowerSearchAgent()
        ctx = ScanContext()
        agent.run(ctx)
        assert ctx.flower_info.family == "Unknown"


class TestScanDetailAssembler:
    """Tests for SDA agent."""

    def test_agent_name(self):
        """Test agent has correct name."""
        agent = ScanDetailAssembler()
        assert agent.name == "SDA"

    def test_builds_quick_payload(self):
        """Test agent builds quick payload."""
        agent = ScanDetailAssembler()
        ctx = ScanContext()
        ctx.identification.primary_flower = IdentifiedFlower(
            id="test",
            name="Rose",
            scientific_name="Rosa",
            confidence=0.9,
        )
        agent.run(ctx)

        assert ctx.quick_payload is not None
        assert ctx.quick_payload["primaryFlower"]["name"] == "Rose"


class TestScanOrchestrator:
    """Tests for scan orchestrator."""

    def test_orchestrator_creation(self):
        """Test orchestrator creates successfully."""
        orchestrator = ScanOrchestrator()
        assert orchestrator.agent_names == ["FID", "FSA", "SDA"]

    @patch("backend.agents.adapters.flower_identification_agent.get_ai_client")
    @patch("backend.agents.adapters.flower_search_agent.get_ai_client")
    def test_run_scan_success(self, mock_fsa_client, mock_fid_client):
        """Test full scan pipeline execution."""
        # Mock FID response
        mock_fid = MagicMock()
        mock_fid.analyze_image.return_value = {
            "flower": {
                "name": "Tulip",
                "scientific_name": "Tulipa",
                "color": "pink",
                "confidence": 0.92,
            }
        }
        mock_fid_client.return_value = mock_fid

        # Mock FSA response
        mock_fsa = MagicMock()
        mock_fsa.complete_json.return_value = {
            "botanical": {
                "family": "Liliaceae",
                "native_regions": ["Central Asia"],
                "bloom_seasons": ["Spring"],
                "lifespan": "perennial"
            },
            "meanings": ["Love", "Rebirth"],
            "care": {
                "difficulty": "easy",
                "light": "full_sun",
                "water": "moderate",
            },
            "similar_flowers": [
                {"name": "Lily", "scientific_name": "Lilium"}
            ]
        }
        mock_fsa_client.return_value = mock_fsa

        result = run_scan(
            image_base64="fake_base64_image",
            scan_mode="single",
            region="US",
        )

        assert result["success"] is True
        assert result["quick"] is not None
        assert result["quick"]["primaryFlower"]["name"] == "Tulip"
        assert result["detail"] is not None
        assert result["detail"]["botanical"]["family"] == "Liliaceae"


class TestRunScanFunction:
    """Tests for run_scan convenience function."""

    def test_returns_error_on_empty_image(self):
        """Test run_scan returns error for empty image."""
        result = run_scan(
            image_base64="",
            scan_mode="single",
            region="US",
        )
        # Should still return a result structure
        assert "success" in result
        assert "error" in result
