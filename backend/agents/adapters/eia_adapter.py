"""
EIA Adapter - Emotion Intelligence Agent - v4 (Enhanced)

Purpose:
Analyzes the emotional context and tone of the user's request with
psychological depth. Uses expanded emotional taxonomy for precise matching.

Version: v4 - Expanded taxonomy, intensity calibration, complexity markers
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, EmotionData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger
from backend.core.safe_parse import safe_parse_float

logger = logging.getLogger(__name__)

EMOTION_ANALYSIS_PROMPT = """You are Emotional Intelligence Agent v4 for FSense.
Analyze the emotional state behind the user's message with psychological depth.
Output STRICT JSON only.

EMOTIONAL TAXONOMY (use these EXACT terms):

PRIMARY EMOTIONS - pick ONE from these categories:
- Love: romantic_love, tender_affection, deep_devotion, puppy_love, mature_love
- Joy: happiness, excitement, elation, contentment, pride
- Gratitude: appreciation, thankfulness, indebtedness, recognition
- Sadness: grief, melancholy, disappointment, longing, nostalgia
- Guilt: remorse, regret, shame, contrition
- Hope: optimism, anticipation, encouragement
- Admiration: respect, awe, inspiration
- Compassion: sympathy, empathy, care, concern

SECONDARY EMOTIONS - up to 2 from ANY category:
- Can be from different categories than primary
- Often create emotional complexity (joy + sadness = bittersweet)

EMOTIONAL TONE - pick ONE:
- tender: gentle, soft, nurturing
- warm: affectionate, friendly, cozy
- passionate: intense, fervent, ardent
- bittersweet: mixed joy and sadness
- hopeful: optimistic, forward-looking
- apologetic: regretful, seeking reconciliation
- celebratory: festive, joyful, triumphant
- supportive: encouraging, comforting
- solemn: serious, respectful, dignified

INTENSITY CALIBRATION (0.0-1.0):
- 0.0-0.3: Subtle, understated emotion (casual thanks, mild appreciation)
- 0.3-0.5: Moderate, clear but measured (sincere gratitude, friendly warmth)
- 0.5-0.7: Strong, unmistakable feeling (deep love, genuine remorse)
- 0.7-0.9: Intense, deeply felt (passionate declaration, profound grief)
- 0.9-1.0: Overwhelming, all-consuming (wedding day love, devastating loss)

COMPLEXITY MARKERS:
- has_mixed_emotions: boolean - are there conflicting feelings?
- unexpressed_feeling: what they might not be saying directly
- cultural_modifier: how region affects expression (direct_expression, reserved, formal)

Return JSON:
{
  "dominant_emotion": "romantic_love",
  "secondary_emotions": ["excitement", "nervousness"],
  "emotion_tone": "passionate",
  "emotion_intensity": 0.75,
  "emotional_subtext": "Wants to make a strong romantic impression, possibly nervous about the gesture",
  "complexity": {
    "has_mixed_emotions": true,
    "unexpressed_feeling": "fear of rejection",
    "cultural_modifier": "direct_expression"
  }
}"""


class EIAAdapter(BaseAgent):
    """Emotion Intelligence Agent - analyzes emotional context."""

    name = "EIA"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze emotional context and store in context."""
        try:
            client = get_ai_client_fast()

            # Build rich prompt with all available context
            intent_context = ""
            if ctx.intent:
                intent_context = f"\nIntent context: {ctx.intent.primary_intent}"
                if ctx.intent.raw_output:
                    occasion = ctx.intent.raw_output.get("occasion", "")
                    recipient = ctx.intent.raw_output.get("recipient", "")
                    if occasion:
                        intent_context += f"\nOccasion: {occasion}"
                    if recipient:
                        intent_context += f"\nRecipient: {recipient}"

            prompt = f"""User message: "{ctx.user_input}"{intent_context}
Region: {ctx.region.upper()}

Analyze the emotional state behind this message with nuance and depth."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=EMOTION_ANALYSIS_PROMPT,
                temperature=0.4,
            )

            # Parse emotional data
            dominant = response.get("dominant_emotion", "affection")
            tone = response.get("emotion_tone", "warm")
            intensity = safe_parse_float(
                response.get("emotion_intensity"),
                default=0.7,
                context="EIA.emotion_intensity"
            )

            # Build secondary emotions list (now can be array in response)
            secondary_emotions = []
            sec_data = response.get("secondary_emotions") or response.get("secondary_emotion")
            if sec_data:
                if isinstance(sec_data, list):
                    secondary_emotions = sec_data[:2]  # Max 2
                else:
                    secondary_emotions = [sec_data]

            ctx.emotions = EmotionData(
                primary_emotion=dominant,
                emotion_intensity=intensity,
                secondary_emotions=secondary_emotions,
                emotional_tone=tone,
                raw_output=response,
            )

            logger.info(f"EIA detected emotion: {dominant} (tone: {tone}, intensity: {intensity:.2f})")

            # Console output with complexity info
            console = get_console_logger()
            complexity = response.get("complexity", {})
            console.agent_result("EIA", {
                "Dominant Emotion": dominant,
                "Emotion Tone": tone,
                "Intensity": f"{intensity:.2f}",
                "Secondary Emotions": secondary_emotions if secondary_emotions else "None",
                "Subtext": response.get("emotional_subtext", "N/A"),
                "Mixed Emotions": complexity.get("has_mixed_emotions", False),
            })

        except AIClientError as e:
            logger.error(f"EIA AI error: {e}")
            ctx.add_error(f"EIA: {str(e)}")
            self._fallback_emotions(ctx)

        except Exception as e:
            logger.error(f"EIA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"EIA: Unexpected error")
            self._fallback_emotions(ctx)

    def _fallback_emotions(self, ctx: PipelineContext) -> None:
        """Smarter fallback using FIA context when AI fails."""
        # Default values
        default_emotion = "affection"
        default_tone = "warm"
        default_intensity = 0.6
        secondary = []

        # Use FIA data to infer appropriate emotion
        if ctx.intent and ctx.intent.raw_output:
            occasion = ctx.intent.raw_output.get("occasion", "")
            context_flags = ctx.intent.raw_output.get("context_flags", {})

            if occasion == "apology" or context_flags.get("is_making_amends"):
                default_emotion = "remorse"
                default_tone = "apologetic"
                default_intensity = 0.7
                secondary = ["regret"]
            elif occasion == "birthday":
                default_emotion = "happiness"
                default_tone = "celebratory"
                default_intensity = 0.65
                secondary = ["excitement"]
            elif occasion == "anniversary":
                default_emotion = "romantic_love"
                default_tone = "tender"
                default_intensity = 0.75
                secondary = ["appreciation"]
            elif occasion in ["thank_you", "appreciation"]:
                default_emotion = "gratitude"
                default_tone = "warm"
                default_intensity = 0.6
                secondary = ["appreciation"]
            elif occasion == "sympathy":
                default_emotion = "compassion"
                default_tone = "supportive"
                default_intensity = 0.7
                secondary = ["sympathy"]
            elif occasion == "get_well":
                default_emotion = "care"
                default_tone = "supportive"
                default_intensity = 0.6
                secondary = ["encouragement"]
            elif occasion in ["wedding", "graduation", "new_job", "congratulations"]:
                default_emotion = "happiness"
                default_tone = "celebratory"
                default_intensity = 0.7
                secondary = ["pride"]
            elif occasion == "just_because":
                default_emotion = "tender_affection"
                default_tone = "warm"
                default_intensity = 0.55
                secondary = ["appreciation"]

        ctx.emotions = EmotionData(
            primary_emotion=default_emotion,
            emotion_intensity=default_intensity,
            secondary_emotions=secondary,
            emotional_tone=default_tone,
            raw_output={
                "fallback": True,
                "fallback_source": "intent_based",
                "complexity": {
                    "has_mixed_emotions": False,
                    "unexpressed_feeling": None,
                    "cultural_modifier": "direct_expression",
                },
            },
        )
