"""
SRFL Adapter - Self-Reflection Layer - v3 (Enhanced)

Purpose:
Performs consistency checks and quality assessment on all preceding agent outputs.
Validates that the pipeline outputs make sense together and identifies gaps.

Version: v3 - Expanded emotion vocabulary, improved string matching
"""

import logging
import re
from typing import List, Set

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, ReflectionData
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

# Emotion-to-meaning mappings for consistency checking (expanded vocabulary)
EMOTION_TO_MEANING_TONES = {
    # Love spectrum
    "love": {"love", "passion", "romance", "affection", "devotion", "desire"},
    "romantic_love": {"love", "passion", "romance", "desire", "devotion", "ardor"},
    "tender_affection": {"affection", "care", "warmth", "tenderness", "gentle"},
    "deep_devotion": {"devotion", "commitment", "loyalty", "dedication", "forever"},
    "affection": {"gentle", "warm", "admiration", "care", "love", "affection"},

    # Gratitude spectrum
    "gratitude": {"gratitude", "appreciation", "respect", "thanks", "thankful"},
    "appreciation": {"appreciation", "recognition", "acknowledgment", "respect"},
    "thankfulness": {"thanks", "grateful", "blessed", "appreciation"},

    # Joy spectrum
    "joy": {"joy", "happiness", "celebration", "bright", "cheerful", "delight"},
    "happiness": {"joy", "happiness", "cheer", "delight", "bright"},
    "excitement": {"excitement", "enthusiasm", "energy", "vibrant", "thrill"},
    "elation": {"joy", "elation", "ecstasy", "thrill", "euphoria"},
    "contentment": {"peace", "contentment", "serenity", "satisfaction"},
    "pride": {"pride", "achievement", "accomplishment", "success"},
    "celebration": {"celebration", "festive", "congratulations", "joy"},

    # Apology/Guilt spectrum
    "remorse": {"forgiveness", "sincerity", "purity", "new beginnings", "peace"},
    "regret": {"apology", "reconciliation", "peace", "forgiveness"},
    "contrition": {"humility", "sincerity", "purity", "forgiveness"},
    "guilt": {"forgiveness", "redemption", "peace", "sincerity"},
    "shame": {"forgiveness", "humility", "redemption"},

    # Sadness/Support spectrum
    "sadness": {"sympathy", "comfort", "solace", "support", "peace"},
    "grief": {"sympathy", "peace", "comfort", "solace", "remembrance"},
    "melancholy": {"comfort", "solace", "peace", "gentle"},
    "longing": {"memory", "remembrance", "nostalgia", "tenderness"},
    "nostalgia": {"memory", "remembrance", "sentimental", "past"},

    # Hope/Support spectrum
    "hope": {"hope", "new beginnings", "optimism", "renewal", "bright"},
    "optimism": {"hope", "optimism", "bright", "future", "positive"},
    "encouragement": {"hope", "strength", "courage", "support", "uplift"},
    "anticipation": {"excitement", "hope", "future", "anticipation"},

    # Compassion/Support spectrum
    "sympathy": {"sympathy", "comfort", "peace", "solace", "support"},
    "compassion": {"care", "support", "healing", "comfort", "empathy"},
    "empathy": {"understanding", "support", "care", "comfort"},
    "care": {"care", "support", "comfort", "nurturing", "warmth"},
    "concern": {"care", "support", "worry", "comfort"},

    # Admiration spectrum
    "admiration": {"respect", "admiration", "esteem", "honor"},
    "respect": {"respect", "honor", "admiration", "dignity"},
    "awe": {"awe", "wonder", "admiration", "amazement"},
    "inspiration": {"inspiration", "motivation", "hope", "uplift"},

    # Calm/Serenity spectrum
    "calm": {"serenity", "peace", "balance", "tranquil", "harmony"},
    "serenity": {"peace", "serenity", "tranquil", "calm"},
    "peace": {"peace", "harmony", "tranquil", "serenity"},
}

RISK_TO_SCORE = {"low": 1.0, "medium": 0.6, "high": 0.2}


class SRFLAdapter(BaseAgent):
    """Self-Reflection Layer - validates pipeline consistency and quality."""

    name = "SRFL"

    def run(self, ctx: PipelineContext) -> None:
        """Perform self-reflection on pipeline outputs."""
        try:
            # Identify gaps
            gaps = self._identify_gaps(ctx)

            # Calculate consistency metrics
            consistency = self._compute_consistency(ctx)
            cultural_safety = self._compute_cultural_safety(ctx)

            # Overall confidence
            confidence = self._aggregate_confidence(consistency, cultural_safety, len(gaps))

            # Generate suggestions
            suggestions = self._generate_suggestions(ctx, consistency, cultural_safety, gaps)

            # Check if pipeline is consistent
            is_consistent = len(gaps) == 0 and consistency > 0.5

            ctx.reflection = ReflectionData(
                confidence_score=confidence,
                consistency_check=is_consistent,
                gaps_identified=gaps,
                suggestions=suggestions,
                raw_output={
                    "consistency_score": consistency,
                    "cultural_safety_score": cultural_safety,
                    "gap_count": len(gaps),
                },
            )

            status_emoji = "✅" if is_consistent else "⚠️"
            logger.info(f"SRFL {status_emoji} confidence: {confidence:.2f}, consistency: {consistency:.2f}, gaps: {len(gaps)}")

            # Console output
            console = get_console_logger()
            console.agent_result("SRFL", {
                "Confidence Score": f"{confidence:.2f}",
                "Consistency Check": "✅ Passed" if is_consistent else "⚠️ Issues detected",
                "Consistency Score": f"{consistency:.2f}",
                "Cultural Safety": f"{cultural_safety:.2f}",
                "Gaps Identified": gaps if gaps else "None",
                "Suggestions": suggestions[:2] if suggestions else "None",
            })

        except Exception as e:
            logger.error(f"SRFL unexpected error: {e}", exc_info=True)
            ctx.add_error(f"SRFL: Unexpected error")
            self._fallback_reflection(ctx)

    def _identify_gaps(self, ctx: PipelineContext) -> List[str]:
        """Identify missing or incomplete data."""
        gaps = []

        if not ctx.intent or not ctx.intent.primary_intent:
            gaps.append("Intent not determined")

        if not ctx.emotions or not ctx.emotions.primary_emotion:
            gaps.append("Emotions not analyzed")

        if not ctx.relationship or not ctx.relationship.relationship_type:
            gaps.append("Relationship context missing")

        if not ctx.candidates or not ctx.candidates.candidates:
            gaps.append("No flower candidates selected")

        if not ctx.intensity or ctx.intensity.mood_intensity is None:
            gaps.append("Intensity not calculated")

        if not ctx.adaptive or not ctx.adaptive.tone:
            gaps.append("Adaptive tone not configured")

        return gaps

    def _compute_consistency(self, ctx: PipelineContext) -> float:
        """Check consistency between emotional context and flower selection."""
        if not ctx.emotions or not ctx.candidates or not ctx.candidates.candidates:
            return 0.5

        # Get primary emotion
        dominant_emotion = ctx.emotions.primary_emotion.lower()

        # Get flower meanings and extract individual words
        candidate = ctx.candidates.candidates[0]
        meanings_text = " ".join(candidate.meanings).lower() if candidate.meanings else ""
        # Use word boundaries to avoid false positives (e.g., "care" in "careful")
        meanings_words = set(re.findall(r'\b\w+\b', meanings_text))

        # Check if emotion matches meanings
        targets = EMOTION_TO_MEANING_TONES.get(dominant_emotion, set())
        if not targets:
            # Unknown emotion - try to find partial match in all emotions
            for emotion_key, emotion_targets in EMOTION_TO_MEANING_TONES.items():
                if dominant_emotion in emotion_key or emotion_key in dominant_emotion:
                    targets = emotion_targets
                    break
            if not targets:
                return 0.6  # Unknown emotion, assume neutral

        # Count hits using word matching
        hits = sum(1 for target in targets if target in meanings_words)
        base_score = hits / max(1, len(targets))

        # Adjust for relationship stage
        stage_bonus = 0.0
        if ctx.relationship:
            stage = ctx.relationship.raw_output.get("relationship_stage", "established").lower()
            intensity_label = ctx.intensity.intensity_label if ctx.intensity else "balanced"

            if stage in ("new", "early") and intensity_label in ("low", "balanced"):
                stage_bonus = 0.1
            elif stage in ("new", "early") and intensity_label == "high":
                stage_bonus = -0.1

        return max(0.0, min(1.0, base_score + stage_bonus))

    def _compute_cultural_safety(self, ctx: PipelineContext) -> float:
        """Calculate cultural safety score based on risks."""
        if not ctx.risks:
            return 0.7

        # Convert risk level to score
        risk_level = ctx.risks.overall_risk_level.lower()
        base_score = RISK_TO_SCORE.get(risk_level, 0.7)

        # Adjust for cultural warnings
        if ctx.cultural_insights:
            warning_count = len(ctx.cultural_insights.warnings)
            penalty = min(0.3, warning_count * 0.1)
            base_score -= penalty

        return max(0.0, min(1.0, base_score))

    def _aggregate_confidence(self, consistency: float, safety: float, gap_count: int) -> float:
        """Calculate overall confidence score."""
        # Base confidence from consistency and safety
        base = 0.45 * consistency + 0.4 * safety

        # Penalty for gaps
        gap_penalty = min(0.4, gap_count * 0.1)

        return max(0.0, min(1.0, base + 0.15 - gap_penalty))

    def _generate_suggestions(
        self,
        ctx: PipelineContext,
        consistency: float,
        safety: float,
        gaps: List[str]
    ) -> List[str]:
        """Generate suggestions for improvement."""
        suggestions = []

        if consistency < 0.5:
            suggestions.append("Consider adjusting flower selection to better match emotional context")

        if safety < 0.6:
            suggestions.append("Review cultural appropriateness of the recommendation")

        if ctx.intensity and ctx.relationship:
            stage = ctx.relationship.raw_output.get("relationship_stage", "established").lower()
            intensity = ctx.intensity.mood_intensity

            if stage in ("new", "early") and intensity > 0.7:
                suggestions.append("Consider lowering intensity for early relationship stage")

        if gaps:
            suggestions.append(f"Fill missing data: {', '.join(gaps)}")

        if not suggestions:
            suggestions.append("Pipeline outputs are consistent and well-aligned")

        return suggestions

    def _fallback_reflection(self, ctx: PipelineContext) -> None:
        """Provide fallback reflection when analysis fails."""
        gaps = []
        if not ctx.candidates or not ctx.candidates.candidates:
            gaps.append("No flower candidates")

        ctx.reflection = ReflectionData(
            confidence_score=0.5,
            consistency_check=False,
            gaps_identified=gaps,
            suggestions=["Fallback mode - manual review recommended"],
            raw_output={"fallback": True},
        )
