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
        """Adjust tone based on relationship stage and intensity."""
        # Soften tone for new relationships
        tone_adjustments = {
            "passionate": "warm" if stage in ("new", "early", "developing") else "passionate",
            "romantic": "tender" if stage in ("new", "early") else "romantic",
            "intense": "warm" if stage in ("new", "early") else "warm",
            "warm": "warm",
            "tender": "tender",
            "neutral": "warm",
            "formal": "professional",
            "professional": "professional",
            "apologetic": "apologetic",
            "supportive": "supportive",
            "celebratory": "celebratory" if stage != "new" else "warm",
        }
        return tone_adjustments.get(emotion_tone.lower(), emotion_tone)

    def _determine_voice_style(self, ctx: PipelineContext) -> str:
        """Determine voice style based on context."""
        emotion_tone = ctx.emotions.emotional_tone if ctx.emotions else "neutral"
        stage = "established"
        r_type = "neutral"

        if ctx.relationship:
            r_type = ctx.relationship.relationship_type
            stage = ctx.relationship.raw_output.get("relationship_stage", "established") if ctx.relationship.raw_output else "established"

        # Professional relationships
        if r_type == "professional":
            return "professional"

        # Romantic contexts
        if emotion_tone.lower() in ("passionate", "romantic"):
            return "romantic" if stage not in ("new", "early") else "conversational"

        # Formal tone
        if emotion_tone.lower() in ("formal", "professional"):
            return "professional"

        # Apologetic contexts
        if emotion_tone.lower() in ("apologetic", "remorseful"):
            return "sincere"

        # Celebratory occasions
        if emotion_tone.lower() in ("celebratory", "joyful", "excited"):
            return "playful"

        # Default
        return "conversational"

    def _determine_formality(self, ctx: PipelineContext) -> str:
        """Determine formality level based on relationship."""
        if ctx.relationship:
            r_type = ctx.relationship.relationship_type
            formality_level = ctx.relationship.formality_level

            # Professional always formal
            if r_type == "professional":
                return "formal"

            # Use formality level
            if formality_level > 0.7:
                return "formal"
            elif formality_level > 0.5:
                return "balanced"
            elif formality_level > 0.3:
                return "casual"
            else:
                return "very_casual"

        return "casual"

    def _generate_hints(self, ctx: PipelineContext) -> List[str]:
        """Generate personalization hints based on full context."""
        hints = []

        # Get context data
        emotion_tone = ctx.emotions.emotional_tone if ctx.emotions else "neutral"
        intensity_label = ctx.intensity.intensity_label if ctx.intensity else "balanced"
        stage = "established"
        r_type = "neutral"

        if ctx.relationship and ctx.relationship.raw_output:
            stage = ctx.relationship.raw_output.get("relationship_stage", "established")
            r_type = ctx.relationship.relationship_type

        # Stage-based hints
        if stage in ("new", "early"):
            hints.append("keep_tone_gentle")
            hints.append("avoid_overly_romantic")

        # Intensity-based hints
        if intensity_label in ("high", "very_high"):
            hints.append("emphasize_emotion")
        elif intensity_label in ("low", "very_low"):
            hints.append("keep_subtle")

        # Tone-based hints
        if emotion_tone.lower() in ("warm", "tender"):
            hints.append("emphasize_warmth")
        elif emotion_tone.lower() in ("apologetic", "remorseful"):
            hints.append("emphasize_sincerity")
        elif emotion_tone.lower() in ("celebratory", "joyful"):
            hints.append("emphasize_joy")

        # Relationship type hints
        if r_type == "professional":
            hints.append("maintain_professional_boundaries")
        elif r_type == "familial":
            hints.append("respectful_but_warm")

        return hints[:4]  # Return max 4 hints

    def _fallback_adaptive(self, ctx: PipelineContext) -> None:
        """Use heuristic methods for fallback when AI fails."""
        # Extract context data
        emotion_tone = ctx.emotions.emotional_tone if ctx.emotions else "warm"
        intensity_label = ctx.intensity.intensity_label if ctx.intensity else "balanced"
        stage = "established"

        if ctx.relationship and ctx.relationship.raw_output:
            stage = ctx.relationship.raw_output.get("relationship_stage", "established")

        # Use heuristic methods
        adjusted_tone = self._adjust_tone_heuristic(emotion_tone, intensity_label, stage)
        voice_style = self._determine_voice_style(ctx)
        formality = self._determine_formality(ctx)
        hints = self._generate_hints(ctx)

        ctx.adaptive = AdaptiveData(
            tone=adjusted_tone,
            voice_style=voice_style,
            formality=formality,
            personalization_hints=hints,
            raw_output={
                "fallback": True,
                "method": "heuristic",
                "original_tone": emotion_tone,
                "adjusted_tone": adjusted_tone,
            },
        )
