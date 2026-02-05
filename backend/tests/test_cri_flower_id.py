"""Tests for CRI flower ID resolution."""

import pytest
from unittest.mock import MagicMock, patch
from backend.agents.adapters.cri_adapter import CRIAdapter
from backend.pipeline.context import PipelineContext, CandidatesData, FlowerCandidate


class TestCRIFlowerIdResolution:
    """Tests for _resolve_flower_id helper."""

    def test_matches_flower_name_to_correct_candidate(self):
        """Should match flower_name against candidate names, not just [0]."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[
                FlowerCandidate(flower_id="red_rose", name="Red Rose"),
                FlowerCandidate(flower_id="white_lily", name="White Lily"),
            ]
        )

        # Should find White Lily, not just return first candidate
        result = adapter._resolve_flower_id("White Lily", ctx)
        assert result == "white_lily"

    def test_case_insensitive_matching(self):
        """Should match regardless of case."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="red_rose", name="Red Rose")]
        )

        result = adapter._resolve_flower_id("RED ROSE", ctx)
        assert result == "red_rose"

    def test_ignores_unknown_candidate_id(self):
        """Should not use 'unknown' as flower_id."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="unknown", name="Red Rose")]
        )

        with patch('backend.agents.adapters.cri_adapter.FlowerKnowledgeBase') as mock_kb:
            mock_kb.resolve_flower_id.return_value = "red_rose"
            result = adapter._resolve_flower_id("Red Rose", ctx)

        assert result == "red_rose"
        mock_kb.resolve_flower_id.assert_called_once_with("Red Rose")

    def test_fallback_to_knowledge_base(self):
        """Should use FlowerKnowledgeBase when no candidate match."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="red_rose", name="Red Rose")]
        )

        with patch('backend.agents.adapters.cri_adapter.FlowerKnowledgeBase') as mock_kb:
            mock_kb.resolve_flower_id.return_value = "white_lily"
            # Ask for flower not in candidates
            result = adapter._resolve_flower_id("White Lily", ctx)

        assert result == "white_lily"

    def test_returns_none_when_unresolved(self):
        """Should return None when resolution fails."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = None

        with patch('backend.agents.adapters.cri_adapter.FlowerKnowledgeBase') as mock_kb:
            mock_kb.resolve_flower_id.return_value = None
            result = adapter._resolve_flower_id("Unknown Flower", ctx)

        assert result is None

    def test_handles_knowledge_base_exception(self):
        """Should catch exceptions from FlowerKnowledgeBase."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = None

        with patch('backend.agents.adapters.cri_adapter.FlowerKnowledgeBase') as mock_kb:
            mock_kb.resolve_flower_id.side_effect = Exception("DB error")
            result = adapter._resolve_flower_id("Rose", ctx)

        assert result is None  # Graceful degradation

    def test_empty_candidates_list(self):
        """Should handle empty candidates list gracefully."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(candidates=[])

        with patch('backend.agents.adapters.cri_adapter.FlowerKnowledgeBase') as mock_kb:
            mock_kb.resolve_flower_id.return_value = "tulip"
            result = adapter._resolve_flower_id("Tulip", ctx)

        assert result == "tulip"

    def test_strips_whitespace_from_names(self):
        """Should handle whitespace in flower names."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="red_rose", name="  Red Rose  ")]
        )

        result = adapter._resolve_flower_id("Red Rose", ctx)
        assert result == "red_rose"


class TestCRICulturalWarningsIntegration:
    """Integration tests for _check_cultural_warnings with resolved IDs."""

    @patch('backend.agents.adapters.cri_adapter.DATABASE_AVAILABLE', True)
    def test_uses_resolved_id_for_database_lookup(self):
        """Verify resolved ID is passed to get_cultural_warnings."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="chrysanthemum", name="Chrysanthemum")]
        )

        with patch('backend.agents.adapters.cri_adapter.get_cultural_warnings') as mock_get:
            mock_get.return_value = {"is_taboo": True, "taboo_reason": "Funeral flower in Italy"}
            warnings = adapter._check_cultural_warnings("Chrysanthemum", "IT", ctx)

        mock_get.assert_called_once_with("chrysanthemum", "it")
        assert "Funeral flower in Italy" in warnings

    @patch('backend.agents.adapters.cri_adapter.DATABASE_AVAILABLE', True)
    def test_combines_db_and_heuristic_warnings(self):
        """Should combine DB warnings with heuristic warnings."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="yellow_rose", name="Yellow Rose")]
        )

        with patch('backend.agents.adapters.cri_adapter.get_cultural_warnings') as mock_get:
            mock_get.return_value = {"is_taboo": True, "taboo_reason": "DB warning"}
            warnings = adapter._check_cultural_warnings("Yellow Rose", "RU", ctx)

        # Should have both DB warning and heuristic warning
        assert "DB warning" in warnings
        assert any("separation" in w.lower() for w in warnings)

    @patch('backend.agents.adapters.cri_adapter.DATABASE_AVAILABLE', True)
    def test_deduplicates_warnings(self):
        """Should not duplicate warnings from DB and heuristics."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="yellow_rose", name="Yellow Rose")]
        )

        with patch('backend.agents.adapters.cri_adapter.get_cultural_warnings') as mock_get:
            # Same warning from DB as heuristic would produce
            mock_get.return_value = {
                "is_taboo": True,
                "taboo_reason": "Yellow flowers may be associated with separation in Russian culture"
            }
            warnings = adapter._check_cultural_warnings("Yellow Rose", "RU", ctx)

        # Count occurrences of "separation"
        separation_count = sum(1 for w in warnings if "separation" in w.lower())
        assert separation_count == 1  # Not duplicated

    def test_handles_none_region(self):
        """Should return heuristic warnings only when region is None."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="red_rose", name="Red Rose")]
        )

        # Should not crash with None region
        warnings = adapter._check_cultural_warnings("Red Rose", None, ctx)
        assert isinstance(warnings, list)  # Returns list, not crash

    def test_handles_empty_region(self):
        """Should return heuristic warnings only when region is empty string."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="red_rose", name="Red Rose")]
        )

        warnings = adapter._check_cultural_warnings("Red Rose", "", ctx)
        assert isinstance(warnings, list)

    @patch('backend.agents.adapters.cri_adapter.DATABASE_AVAILABLE', True)
    def test_heuristics_run_even_with_no_db_match(self):
        """Should still check heuristics when DB returns nothing."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="yellow_rose", name="Yellow Rose")]
        )

        with patch('backend.agents.adapters.cri_adapter.get_cultural_warnings') as mock_get:
            mock_get.return_value = None  # DB returns nothing
            warnings = adapter._check_cultural_warnings("Yellow Rose", "RU", ctx)

        # Heuristics should still catch this
        assert any("separation" in w.lower() for w in warnings)

    @patch('backend.agents.adapters.cri_adapter.DATABASE_AVAILABLE', False)
    def test_heuristics_only_when_database_unavailable(self):
        """Should use heuristics when database is not available."""
        adapter = CRIAdapter()
        ctx = MagicMock(spec=PipelineContext)
        ctx.candidates = CandidatesData(
            candidates=[FlowerCandidate(flower_id="white_lily", name="White Lily")]
        )

        warnings = adapter._check_cultural_warnings("White Lily", "JP", ctx)

        # Should get heuristic warning about white flowers
        assert any("funeral" in w.lower() for w in warnings)


class TestCRIHeuristicWarnings:
    """Tests for _check_heuristic_warnings method."""

    def test_yellow_flowers_ru(self):
        """Yellow flowers should warn in Russia."""
        adapter = CRIAdapter()
        warnings = adapter._check_heuristic_warnings("Yellow Rose", "RU")
        assert len(warnings) == 1
        assert "separation" in warnings[0].lower()

    def test_white_flowers_jp(self):
        """White flowers should warn in Japan."""
        adapter = CRIAdapter()
        warnings = adapter._check_heuristic_warnings("White Lily", "JP")
        assert len(warnings) == 1
        assert "funeral" in warnings[0].lower()

    def test_white_flowers_cn(self):
        """White flowers should warn in China."""
        adapter = CRIAdapter()
        warnings = adapter._check_heuristic_warnings("White Rose", "CN")
        assert len(warnings) == 1
        assert "funeral" in warnings[0].lower()

    def test_chrysanthemum_eu(self):
        """Chrysanthemums should warn in European countries."""
        adapter = CRIAdapter()
        for region in ("EU", "IT", "FR"):
            warnings = adapter._check_heuristic_warnings("Chrysanthemum", region)
            assert len(warnings) == 1
            assert "funeral" in warnings[0].lower()

    def test_no_warnings_for_safe_combinations(self):
        """Should return empty list for safe flower/region combinations."""
        adapter = CRIAdapter()
        warnings = adapter._check_heuristic_warnings("Red Rose", "US")
        assert warnings == []

    def test_empty_region_no_warnings(self):
        """Should return empty list for empty region."""
        adapter = CRIAdapter()
        warnings = adapter._check_heuristic_warnings("Yellow Rose", "")
        assert warnings == []
