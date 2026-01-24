"""
CIA Adapter - Context Intensity Agent - v3 (Adapted)

Purpose:
Determines the emotional intensity level appropriate for
the context, considering emotions, relationship, occasion, and cultural factors.

Based on: context_intensity_agent_v3.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, IntensityData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

# Intensity scoring constants
TONE_TARGET = {
    "passionate": 0.85,
    "romantic": 0.80,
    "warm": 0.60,
    "subtle": 0.30,
    "neutral": 0.40,
    "formal": 0.25,
}

RELATION_STAGE_SHIFT = {
    "new": -0.15,
    "early": -0.10,
    "growing": -0.05,
    "established": 0.0,
    "longterm": 0.05,
}

OCCASION_SHIFT = {
    "apology": -0.10,
    "birthday": 0.05,
    "anniversary": 0.15,
    "date": 0.10,
    "get well": -0.20,
    "congratulations": 0.10,
    "thank you": 0.05,
    "general": 0.0,
}

RECIPIENT_SHIFT = {
    "girlfriend": 0.10,
    "wife": 0.15,
    "partner": 0.10,
    "crush": -0.10,
    "friend": -0.10,
    "mother": 0.0,
    "father": 0.0,
    "colleague": -0.15,
}

CULTURE_SHIFT = {
    "RU": -0.05,  # Slightly more reserved
    "US": 0.02,   # Slightly more expressive
    "JP": -0.10,  # More reserved
}

INTENSITY_ANALYSIS_PROMPT = """You are Context Intensity Agent v3 for FSense.
Analyze the context to determine appropriate emotional intensity and output STRICT JSON only.

Consider:
- Emotional state and tone
- Relationship dynamics (type, stage, intimacy)
- Occasion and recipient
- Cultural context

Return JSON with:
- intensity_score: 0.0-1.0 (final calibrated intensity)
- intensity_label: "very_low" | "low" | "balanced" | "high" | "very_high"
- factors: array of strings explaining what influenced the score
- reasoning: brief explanation of the intensity calculation

Intensity scale:
- 0.0-0.2 = very_low (subtle, understated)
- 0.2-0.4 = low (gentle, calm)
- 0.4-0.6 = balanced (appropriate, neutral)
- 0.6-0.8 = high (strong, passionate)
- 0.8-1.0 = very_high (intense, overwhelming)

Example:
{
  "intensity_score": 0.72,
  "intensity_label": "high",
  "factors": ["romantic occasion", "warm emotional tone", "established relationship"],
  "reasoning": "Strong romantic context with warm emotions suggests high intensity"
}"""


class CIAAdapter(BaseAgent):
    """Context Intensity Agent - calculates emotional intensity calibration."""

    name = "CIA"

    def run(self, ctx: PipelineContext) -> None:
        """Calculate appropriate mood intensity based on context with AI refinement."""
        try:
            # Calculate base intensity from emotions
            base_intensity = ctx.emotions.emotion_intensity if ctx.emotions else 0.5

            # Apply heuristic adjustments
            heuristic_intensity = self._calculate_intensity_heuristic(ctx, base_intensity)

            # Refine with AI for better accuracy
            intensity, factors, reasoning = self._refine_with_ai(ctx, heuristic_intensity)

            # Determine label
            label = self._get_intensity_label(intensity)

            ctx.intensity = IntensityData(
                mood_intensity=intensity,
                intensity_label=label,
                intensity_factors=factors,
                raw_output={
                    "base_intensity": base_intensity,
                    "heuristic_intensity": heuristic_intensity,
                    "final_intensity": intensity,
                    "reasoning": reasoning,
                },
            )

            logger.info(f"CIA calculated intensity: {intensity:.2f} ({label}) - AI refined")

            # Console output
            console = get_console_logger()
            console.agent_result("CIA", {
                "Mood Intensity": f"{intensity:.2f}",
                "Intensity Label": label,
                "Factors": factors[:3] if factors else ["emotion_level"],
            })

        except AIClientError as e:
            logger.error(f"CIA AI error: {e}")
            ctx.add_error(f"CIA: {str(e)}")
            self._fallback_intensity(ctx)

        except Exception as e:
            logger.error(f"CIA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"CIA: Unexpected error")
            self._fallback_intensity(ctx)

    def _calculate_intensity_heuristic(self, ctx: PipelineContext, base: float) -> float:
        """Calculate intensity using heuristic rules."""
        score = base

        # Extract context data
        if ctx.intent:
            tone = ctx.intent.raw_output.get("tone", "neutral")
            occasion = ctx.intent.raw_output.get("occasion", "general")
            recipient = ctx.intent.raw_output.get("recipient", "unspecified")

            # Apply tone target
            tone_target = TONE_TARGET.get(tone.lower(), 0.5)
            score = 0.5 * score + 0.5 * tone_target

            # Apply occasion shift
            score += OCCASION_SHIFT.get(occasion.lower(), 0.0)

            # Apply recipient shift
            score += RECIPIENT_SHIFT.get(recipient.lower(), 0.0)

        # Apply relationship adjustments
        if ctx.relationship:
            r_stage = ctx.relationship.raw_output.get("relationship_stage", "established")
            score += RELATION_STAGE_SHIFT.get(r_stage.lower(), 0.0)

            # Adjust based on intimacy
            intimacy = ctx.relationship.intimacy_level
            if intimacy > 0.7:
                score += 0.05
            elif intimacy < 0.3:
                score -= 0.10

        # Apply cultural adjustment
        culture_adj = CULTURE_SHIFT.get(ctx.region.upper(), 0.0)
        score += culture_adj

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def _refine_with_ai(self, ctx: PipelineContext, heuristic_score: float) -> tuple[float, List[str], str]:
        """Refine intensity calculation with AI reasoning."""
        try:
            client = get_ai_client_fast()

            # Build context summary
            emotion_summary = ""
            if ctx.emotions:
                emotion_summary = f"Emotion: {ctx.emotions.primary_emotion}, tone: {ctx.emotions.emotional_tone}, intensity: {ctx.emotions.emotion_intensity:.2f}"

            relationship_summary = ""
            if ctx.relationship:
                rel_data = ctx.relationship.raw_output
                relationship_summary = f"Relationship: {ctx.relationship.relationship_type}, stage: {rel_data.get('relationship_stage', 'unknown')}, tone: {rel_data.get('relationship_tone', 'unknown')}"

            intent_summary = ""
            if ctx.intent:
                intent_data = ctx.intent.raw_output
                intent_summary = f"Intent: {ctx.intent.primary_intent}, recipient: {intent_data.get('recipient', 'unknown')}, occasion: {intent_data.get('occasion', 'unknown')}"

            prompt = f"""Context:
- User message: "{ctx.user_input}"
- Region: {ctx.region.upper()}
- {emotion_summary}
- {relationship_summary}
- {intent_summary}
- Heuristic intensity: {heuristic_score:.2f}

Analyze and calibrate the final emotional intensity for this context."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=INTENSITY_ANALYSIS_PROMPT,
                temperature=0.3,
            )

            intensity = float(response.get("intensity_score", heuristic_score))
            factors = response.get("factors", ["emotional_context"])
            reasoning = response.get("reasoning", "AI-refined intensity calculation")

            # Ensure intensity is in valid range
            intensity = max(0.0, min(1.0, intensity))

            return intensity, factors, reasoning

        except Exception as e:
            logger.warning(f"CIA AI refinement failed, using heuristic: {e}")
            return heuristic_score, ["emotion_level", "heuristic"], "Heuristic-based calculation"

    def _get_intensity_label(self, intensity: float) -> str:
        """Convert intensity score to label."""
        if intensity < 0.2:
            return "very_low"
        elif intensity < 0.4:
            return "low"
        elif intensity < 0.6:
            return "balanced"
        elif intensity < 0.8:
            return "high"
        else:
            return "very_high"

    def _fallback_intensity(self, ctx: PipelineContext) -> None:
        """Provide fallback intensity when calculation fails."""
        intensity = ctx.emotions.emotion_intensity if ctx.emotions else 0.5
        ctx.intensity = IntensityData(
            mood_intensity=intensity,
            intensity_label=self._get_intensity_label(intensity),
            intensity_factors=["fallback"],
            raw_output={"fallback": True},
        )
