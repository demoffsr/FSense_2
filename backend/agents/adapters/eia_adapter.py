"""
EIA Adapter - Emotion Intelligence Agent - v3 (Adapted)

Purpose:
Analyzes the emotional context and tone of the user's request.
Identifies dominant and secondary emotions with tone and subtext.

Based on: emotional_intent_agent_v3.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, EmotionData
from backend.core.ai_client import get_ai_client, AIClientError

logger = logging.getLogger(__name__)

EMOTION_ANALYSIS_PROMPT = """You are Emotional Intent Agent v3 for FSense.
Analyze the emotional state behind a message and output STRICT JSON only.

Identify:
- dominant_emotion: main emotion (love, gratitude, joy, sadness, guilt, excitement, etc.)
- secondary_emotion: secondary emotion if present
- emotion_tone: tone (tender, warm, passionate, bittersweet, hopeful, serene, etc.)
- emotional_subtext: brief description of emotional nuance
- emotion_intensity: 0.0-1.0 scale

Return JSON:
{
  "dominant_emotion": "affection",
  "secondary_emotion": "gratitude",
  "emotion_tone": "tender",
  "emotional_subtext": "A gentle expression of care",
  "emotion_intensity": 0.7
}"""


class EIAAdapter(BaseAgent):
    """Emotion Intelligence Agent - analyzes emotional context."""

    name = "EIA"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze emotional context and store in context."""
        try:
            client = get_ai_client()

            # Build prompt with context
            intent_hint = f"\nIntent context: {ctx.intent.primary_intent}" if ctx.intent else ""

            prompt = f"""User message: "{ctx.user_input}"{intent_hint}
Region: {ctx.region.upper()}

Analyze the emotional state behind this message."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=EMOTION_ANALYSIS_PROMPT,
                temperature=0.4,
            )

            # Parse emotional data
            dominant = response.get("dominant_emotion", "affection")
            secondary = response.get("secondary_emotion")
            tone = response.get("emotion_tone", "warm")
            intensity = float(response.get("emotion_intensity", 0.7))

            # Build secondary emotions list
            secondary_emotions = []
            if secondary:
                secondary_emotions.append(secondary)

            ctx.emotions = EmotionData(
                primary_emotion=dominant,
                emotion_intensity=intensity,
                secondary_emotions=secondary_emotions,
                emotional_tone=tone,
                raw_output=response,
            )

            logger.info(f"EIA detected emotion: {dominant} (tone: {tone}, intensity: {intensity:.2f})")

        except AIClientError as e:
            logger.error(f"EIA AI error: {e}")
            ctx.add_error(f"EIA: {str(e)}")
            self._fallback_emotions(ctx)

        except Exception as e:
            logger.error(f"EIA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"EIA: Unexpected error")
            self._fallback_emotions(ctx)

    def _fallback_emotions(self, ctx: PipelineContext) -> None:
        """Provide fallback emotions when AI fails."""
        ctx.emotions = EmotionData(
            primary_emotion="affection",
            emotion_intensity=0.6,
            secondary_emotions=[],
            emotional_tone="warm",
            raw_output={"fallback": True},
        )
