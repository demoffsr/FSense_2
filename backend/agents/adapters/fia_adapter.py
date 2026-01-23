"""
FIA Adapter - Flower Intent Agent - v3 (Adapted)

Purpose:
Analyzes user input to extract intent, occasion, tone, emotion,
relationship level, and keywords.

Based on: flower_intent_agent_v3.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, IntentData
from backend.core.ai_client import get_ai_client, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

INTENT_ANALYSIS_PROMPT = """You are Flower Intent Agent v3 for FSense.
Extract user intent from their message and output STRICT JSON only.

Analyze these dimensions:
- recipient: who is the gift for (girlfriend, mother, friend, coworker, etc.)
- occasion: what's the event (birthday, apology, thank you, anniversary, general, etc.)
- tone: emotional tone (subtle, neutral, passionate, tender, etc.)
- emotion: primary emotion (affection, gratitude, excitement, joy, calm, etc.)
- relationship_level: stage of relationship (new, growing, established, unspecified)
- keywords: key words from the message (array of 3-5 words)

Return JSON with this structure:
{
  "recipient": "girlfriend",
  "occasion": "apology",
  "tone": "subtle",
  "emotion": "affection",
  "relationship_level": "established",
  "keywords": ["sorry", "forgive", "love"]
}

Values should be lowercase and concise."""


class FIAAdapter(BaseAgent):
    """Flower Intent Agent - analyzes user intent."""

    name = "FIA"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze user intent and store in context."""
        try:
            client = get_ai_client()

            prompt = f"""User message: "{ctx.user_input}"
Region: {ctx.region.upper()}

Analyze this message and extract intent dimensions."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=INTENT_ANALYSIS_PROMPT,
                temperature=0.3,
            )

            # Build primary intent string
            primary = self._build_primary_intent(response)

            # Extract sub-intents
            sub_intents = self._extract_sub_intents(response)

            ctx.intent = IntentData(
                primary_intent=primary,
                confidence=0.85,
                sub_intents=sub_intents,
                raw_output=response,
            )

            logger.info(f"FIA extracted intent: {primary}")

            # Console output
            console = get_console_logger()
            console.agent_result("FIA", {
                "Primary Intent": primary,
                "Recipient": response.get("recipient", "unspecified"),
                "Occasion": response.get("occasion", "general"),
                "Tone": response.get("tone", "neutral"),
                "Emotion": response.get("emotion", "calm"),
                "Relationship Level": response.get("relationship_level", "unspecified"),
                "Keywords": response.get("keywords", []),
            })

        except AIClientError as e:
            logger.error(f"FIA AI error: {e}")
            ctx.add_error(f"FIA: {str(e)}")
            self._fallback_intent(ctx)

        except Exception as e:
            logger.error(f"FIA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"FIA: Unexpected error")
            self._fallback_intent(ctx)

    def _build_primary_intent(self, data: dict) -> str:
        """Build primary intent string from parsed data."""
        parts = []

        occasion = data.get("occasion", "general")
        if occasion and occasion != "general":
            parts.append(occasion)

        recipient = data.get("recipient", "")
        if recipient and recipient != "unspecified":
            parts.append(f"for {recipient}")

        if not parts:
            return "General flower gift"

        return " ".join(parts).capitalize()

    def _extract_sub_intents(self, data: dict) -> List[str]:
        """Extract sub-intents from data."""
        sub_intents = []

        tone = data.get("tone")
        if tone and tone != "neutral":
            sub_intents.append(f"tone:{tone}")

        emotion = data.get("emotion")
        if emotion and emotion != "calm":
            sub_intents.append(f"emotion:{emotion}")

        rel_level = data.get("relationship_level")
        if rel_level and rel_level != "unspecified":
            sub_intents.append(f"relationship:{rel_level}")

        return sub_intents[:5]

    def _fallback_intent(self, ctx: PipelineContext) -> None:
        """Provide fallback intent when AI fails."""
        ctx.intent = IntentData(
            primary_intent="General flower gift",
            confidence=0.5,
            sub_intents=[],
            raw_output={"fallback": True},
        )
