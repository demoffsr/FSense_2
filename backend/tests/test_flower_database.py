"""Unit tests for flower_database batch functions.

Note: These tests use the actual flower database (SQLite or in-memory fallback).
Ensure DB is seeded before running tests.
"""
import pytest
from backend.database.flower_database import (
    get_flowers_by_emotion,
    get_flowers_by_emotions,
)


class TestGetFlowersByEmotions:
    """Tests for batch emotion query function."""

    def test_empty_list_returns_empty_dict(self):
        """Empty emotions list returns empty dict."""
        result = get_flowers_by_emotions([])
        assert result == {}

    def test_single_emotion_returns_results(self):
        """Single emotion returns tuple of matches."""
        result = get_flowers_by_emotions(["love"], top_n_per=5)
        assert "love" in result
        assert isinstance(result["love"], tuple)
        assert len(result["love"]) <= 5
        assert all("flower_id" in m for m in result["love"])

    def test_multiple_emotions(self):
        """Multiple emotions return separate results."""
        emotions = ["love", "gratitude", "apology"]
        result = get_flowers_by_emotions(emotions, top_n_per=3)

        for emotion in emotions:
            assert emotion in result
            assert isinstance(result[emotion], tuple)
            assert len(result[emotion]) <= 3

    def test_respects_per_emotion_limit(self):
        """Limit applies per emotion, not total."""
        result = get_flowers_by_emotions(["love", "gratitude"], top_n_per=2)

        # Each emotion gets up to 2, not 2 total
        for emotion in ["love", "gratitude"]:
            assert len(result[emotion]) <= 2

    def test_deduplicates_emotions(self):
        """Duplicate emotions are deduplicated."""
        result = get_flowers_by_emotions(["love", "LOVE", "Love"], top_n_per=5)
        assert len(result) == 1
        assert "love" in result

    def test_unknown_emotion_returns_empty(self):
        """Unknown emotions return empty tuple."""
        result = get_flowers_by_emotions(["nonexistent_xyz_emotion"])
        assert result.get("nonexistent_xyz_emotion") == ()

    def test_primary_emotion_gets_different_limit(self):
        """Primary emotion can have different limit."""
        result = get_flowers_by_emotions(
            ["love", "gratitude"],
            top_n_per=2,
            primary_emotion="love",
            primary_top_n=5,
        )

        # Primary gets 5, secondary gets 2
        assert len(result["love"]) <= 5
        assert len(result["gratitude"]) <= 2

    def test_result_structure_has_required_keys(self):
        """Result dicts have expected keys."""
        result = get_flowers_by_emotions(["love"], top_n_per=1)
        if result["love"]:
            match = result["love"][0]
            assert "flower_id" in match
            assert "emotion" in match
            assert "match_score" in match
            assert "meaning_en" in match

    def test_batch_matches_serial_function(self):
        """Batch with one emotion returns same flower_ids as serial function.

        Note: Order may differ due to RANDOM() tiebreaker, so compare sets.
        """
        emotion = "gratitude"
        top_n = 5

        single = get_flowers_by_emotion(emotion, top_n=top_n)
        batch = get_flowers_by_emotions([emotion], top_n_per=top_n)

        single_ids = {m["flower_id"] for m in single}
        batch_ids = {m["flower_id"] for m in batch[emotion]}

        assert single_ids == batch_ids
