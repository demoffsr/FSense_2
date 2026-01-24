"""
AITB Adapter - Adaptive Intelligence & Tone Builder - v2 (Adapted)

Purpose:
Harmonizes emotional tone, intensity, and relationship context to create
a balanced communication style for all text outputs.

Based on: adaptive_intensity_tone_balancer_v2.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, AdaptiveData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

ADAPTIVE_BALANCING_PROMPT = """You are AITB v2 — Reflective Adaptive Harmonizer for FSense.
Your goal is to harmonize emotional tone, relationship context, and intensity to create
the optimal communication style. Output STRICT JSON only.

Analyze the context and determine:
- adjusted_emotion_tone: refined emotional tone (hopeful, tender, warm, joyful, serene, etc.)
- adjusted_intensity: refined intensity level (very_low, low, balanced, high, very_high)
- voice_style: communication style (poetic, conversational, professional, romantic, playful)
- formality: formality level (very_casual, casual, balanced, formal, very_formal)
- personalization_hints: array of hints for personalizing content (e.g., ["emphasize_warmth", "avoid_overly_romantic"])
- adaptive_advice: brief explanation of adjustments made
- confidence_score: 0.0-1.0

Rules:
1. Early or new relationships → avoid high intensity, use more neutral tone
2. Established relationships with warm tone → allow more personal, warm style
3. Apply cultural adjustments (e.g., RU → moderate warmth, US → more expressive)
4. Balance tone and intensity together (don't mix cold tone with high intensity)

Return JSON:
{
  "adjusted_emotion_tone": "hopeful",
  "adjusted_intensity": "balanced",
  "voice_style": "conversational",
  "formality": "casual",
  "personalization_hints": ["emphasize_warmth", "keep_romantic_subtle"],
  "adaptive_advice": "Tone softened to align with early romantic context",
  "confidence_score": 0.84
}"""


class AITBAdapter(BaseAgent):
    """Adaptive Intelligence & Tone Builder - harmonizes communication style."""

    name = "AITB"

    def run(self, ctx: PipelineContext) -> None:
        """Build adaptive tone configuration with AI analysis."""
        try:
            # Use AI to harmonize tone and style
            result = self._harmonize_with_ai(ctx)

            adjusted_tone = result.get("adjusted_emotion_tone", "warm")
            adjusted_intensity = result.get("adjusted_intensity", "balanced")
            voice_style = result.get("voice_style", "conversational")
            formality = result.get("formality", "casual")
            hints = result.get("personalization_hints", [])
            advice = result.get("adaptive_advice", "AI-harmonized tone and style")
            confidence = result.get("confidence_score", 0.85)

            ctx.adaptive = AdaptiveData(
                tone=adjusted_tone,
                voice_style=voice_style,
                formality=formality,
                personalization_hints=hints,
                raw_output={
                    "original_emotion_tone": ctx.emotions.emotional_tone if ctx.emotions else "neutral",
                    "adjusted_emotion_tone": adjusted_tone,
                    "original_intensity": ctx.intensity.intensity_label if ctx.intensity else "balanced",
                    "adjusted_intensity": adjusted_intensity,
                    "adaptive_advice": advice,
                    "confidence_score": confidence,
                },
            )

            logger.info(f"AITB harmonized tone: {adjusted_tone} ({voice_style}, {formality}) - AI")

            # Console output
            console = get_console_logger()
            console.agent_result("AITB", {
                "Adjusted Tone": adjusted_tone,
                "Voice Style": voice_style,
                "Formality": formality,
                "Personalization Hints": hints[:3] if hints else "None",
                "Confidence": f"{confidence:.2f}",
            })

        except AIClientError as e:
            logger.error(f"AITB AI error: {e}")
            ctx.add_error(f"AITB: {str(e)}")
            self._fallback_adaptive(ctx)

        except Exception as e:
            logger.error(f"AITB unexpected error: {e}", exc_info=True)
            ctx.add_error(f"AITB: Unexpected error")
            self._fallback_adaptive(ctx)

    def _harmonize_with_ai(self, ctx: PipelineContext) -> dict:
        """Use AI to harmonize tone and style."""
        try:
            client = get_ai_client_fast()

            # Build context summary
            emotion_summary = ""
            if ctx.emotions:
                emotion_summary = f"Emotion: {ctx.emotions.primary_emotion}, tone: {ctx.emotions.emotional_tone}, intensity: {ctx.emotions.emotion_intensity:.2f}"

            intensity_summary = ""
            if ctx.intensity:
                intensity_summary = f"Intensity: {ctx.intensity.intensity_label} ({ctx.intensity.mood_intensity:.2f})"

            relationship_summary = ""
            if ctx.relationship:
                rel_data = ctx.relationship.raw_output
                relationship_summary = f"Relationship: {ctx.relationship.relationship_type}, stage: {rel_data.get('relationship_stage', 'unknown')}"

            prompt = f"""Context:
- User message: "{ctx.user_input}"
- Region: {ctx.region.upper()}
- {emotion_summary}
- {intensity_summary}
- {relationship_summary}

Harmonize the tone and communication style for this context."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=ADAPTIVE_BALANCING_PROMPT,
                temperature=0.4,
            )

            return response

        except Exception as e:
            logger.warning(f"AITB AI harmonization failed, using fallback: {e}")
            # Fallback to heuristic
            return {
                "adjusted_emotion_tone": "warm",
                "adjusted_intensity": "balanced",
                "voice_style": "conversational",
                "formality": "casual",
                "personalization_hints": ["keep_balanced"],
                "adaptive_advice": "Fallback harmonization",
                "confidence_score": 0.6,
            }

    def _adjust_tone_heuristic(self, emotion_tone: str, intensity: str, stage: str) -> str:
        """Adjust tone based on heuristics (deprecated - now using AI)."""
        tone_map = {
            "passionate": "warm" if stage in ("new", "early") else "passionate",
            "romantic": "tender" if stage in ("new", "early") else "romantic",
            "warm": "warm",
            "neutral": "warm",
            "formal": "professional",
        }
        return tone_map.get(emotion_tone.lower(), emotion_tone)

    def _determine_voice_style(self, emotion_tone: str, stage: str) -> str:
        """Determine voice style."""
        if emotion_tone.lower() in ("passionate", "romantic"):
            return "romantic" if stage not in ("new", "early") else "conversational"
        elif emotion_tone.lower() in ("formal", "professional"):
            return "professional"
        return "conversational"

    def _determine_formality(self, ctx: PipelineContext) -> str:
        """Determine formality level."""
        if ctx.relationship:
            if ctx.relationship.formality_level > 0.7:
                return "formal"
            elif ctx.relationship.formality_level < 0.3:
                return "very_casual"
        return "casual"

    def _generate_hints(self, emotion_tone: str, intensity: str, stage: str) -> List[str]:
        """Generate personalization hints."""
        hints = []
        if stage in ("new", "early"):
            hints.append("keep_tone_gentle")
            hints.append("avoid_overly_romantic")
        if intensity in ("high", "very_high"):
            hints.append("emphasize_emotion")
        if emotion_tone.lower() in ("warm", "tender"):
            hints.append("emphasize_warmth")
        return hints[:3]

    def _fallback_adaptive(self, ctx: PipelineContext) -> None:
        """Provide fallback adaptive data when AI fails."""
        # Use simple heuristics
        tone = ctx.emotions.emotional_tone if ctx.emotions else "warm"
        formality = "casual"

        if ctx.relationship:
            if ctx.relationship.formality_level > 0.7:
                formality = "formal"
            elif ctx.relationship.formality_level < 0.3:
                formality = "very_casual"

        ctx.adaptive = AdaptiveData(
            tone=tone,
            voice_style="conversational",
            formality=formality,
            personalization_hints=[],
            raw_output={"fallback": True},
        )
