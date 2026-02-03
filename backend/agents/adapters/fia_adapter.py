"""
FIA Adapter - Flower Intent Agent - v4 (Enhanced)

Purpose:
Analyzes user input to extract intent, occasion, tone, emotion,
relationship level, context flags, and keywords with cultural awareness.

Version: v4 - Added context_flags, regional awareness, smarter fallback
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, IntentData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

INTENT_ANALYSIS_PROMPT = """You are Flower Intent Agent v4 for FSense.
Analyze the user's message to understand their flower gifting intent.
Output STRICT JSON only.

Extract these dimensions with NUANCE:

1. RECIPIENT - Who is the gift for:
   - Specific role: girlfriend, wife, mother, boss, friend, colleague, teacher
   - If ambiguous, infer from context clues

2. OCCASION - What's the event:
   - Specific events: birthday, anniversary, apology, thank_you, get_well, congratulations
   - Life events: graduation, new_job, new_baby, wedding, sympathy
   - No occasion: just_because, appreciation, thinking_of_you

3. TONE - Emotional register:
   - subtle: understated, modest, refined
   - neutral: standard, balanced
   - warm: affectionate, caring
   - passionate: intense, ardent, fervent
   - playful: fun, lighthearted, whimsical

4. EMOTION - Primary emotional goal:
   - Love spectrum: romantic_love, tender_affection, deep_devotion
   - Gratitude spectrum: appreciation, thankfulness, indebtedness
   - Apology spectrum: remorse, regret, seeking_forgiveness
   - Joy spectrum: happiness, celebration, excitement
   - Support spectrum: encouragement, comfort, sympathy

5. RELATIONSHIP LEVEL:
   - new: early dating, new friendship, recent acquaintance
   - growing: developing relationship, building trust
   - established: stable relationship, known well
   - longterm: years together, deep history

6. CONTEXT FLAGS:
   - is_first_gift: boolean - Is this possibly their first flower gift to this person?
   - is_making_amends: boolean - Are they trying to repair a relationship?
   - is_special_milestone: boolean - Is this a significant life event?
   - budget_hint: luxury | standard | modest | unspecified

7. KEYWORDS: 3-5 significant words from the message

8. INFERRED_DETAILS: Brief note about what you inferred from context

Return JSON:
{
  "recipient": "girlfriend",
  "occasion": "anniversary",
  "tone": "passionate",
  "emotion": "romantic_love",
  "relationship_level": "established",
  "context_flags": {
    "is_first_gift": false,
    "is_making_amends": false,
    "is_special_milestone": true,
    "budget_hint": "luxury"
  },
  "keywords": ["anniversary", "love", "special"],
  "inferred_details": "3-year anniversary, wants to impress"
}

Values should be lowercase and use underscores for multi-word terms."""


class FIAAdapter(BaseAgent):
    """Flower Intent Agent - analyzes user intent."""

    name = "FIA"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze user intent and store in context."""
        try:
            client = get_ai_client_fast()

            # Check if we have vision analysis results
            has_vision = ctx.vision and ctx.vision.main_flower and ctx.vision.main_flower.name

            if has_vision:
                # Use detected flower from image analysis
                flower_name = ctx.vision.main_flower.name
                prompt = f"""User uploaded an image of a flower bouquet.
Detected flower: {flower_name}
User message: "{ctx.user_input or 'What is this flower?'}"
Region: {ctx.region.upper()}

The user wants to learn about this flower. Set:
- recipient: "self" (learning about a flower)
- occasion: "identification" (flower identification from image)
- tone: "curious"
- emotion: "interest"
- relationship_level: "unspecified"
- context_flags: all false, budget_hint: "unspecified"
- keywords: include the flower name

Analyze and extract intent dimensions."""
            else:
                # Normal text-based intent analysis with regional context
                regional_hint = self._get_regional_hint(ctx.region)
                prompt = f"""User message: "{ctx.user_input}"
Region: {ctx.region.upper()}

{regional_hint}

Analyze this message and extract intent dimensions with cultural awareness."""

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
            context_flags = response.get("context_flags", {})
            console.agent_result("FIA", {
                "Primary Intent": primary,
                "Recipient": response.get("recipient", "unspecified"),
                "Occasion": response.get("occasion", "general"),
                "Tone": response.get("tone", "neutral"),
                "Emotion": response.get("emotion", "calm"),
                "Relationship Level": response.get("relationship_level", "unspecified"),
                "Context Flags": context_flags if context_flags else "None",
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

    def _get_regional_hint(self, region: str) -> str:
        """Get cultural hint based on region."""
        region_lower = region.lower()
        hints = {
            "us": "REGIONAL NOTE: US culture - direct emotional expression is common and appreciated.",
            "eu": "REGIONAL NOTE: European culture - may prefer classic, understated elegant choices.",
            "asia": "REGIONAL NOTE: Asian culture - color symbolism is important (avoid white for celebrations, red is lucky).",
            "ru": "REGIONAL NOTE: Russian culture - odd number of flowers for celebrations, even for funerals.",
        }
        return hints.get(region_lower, "")

    def _fallback_intent(self, ctx: PipelineContext) -> None:
        """Smarter fallback using available context from user input."""
        user_input_lower = ctx.user_input.lower() if ctx.user_input else ""

        # Detect occasion from keywords
        occasion = "general"
        is_making_amends = False
        is_special_milestone = False

        if any(w in user_input_lower for w in ["sorry", "apologize", "forgive", "apolog"]):
            occasion = "apology"
            is_making_amends = True
        elif any(w in user_input_lower for w in ["birthday", "bday"]):
            occasion = "birthday"
            is_special_milestone = True
        elif any(w in user_input_lower for w in ["thank", "grateful", "appreciate"]):
            occasion = "thank_you"
        elif any(w in user_input_lower for w in ["anniversary"]):
            occasion = "anniversary"
            is_special_milestone = True
        elif any(w in user_input_lower for w in ["wedding", "married", "engagement"]):
            occasion = "wedding"
            is_special_milestone = True
        elif any(w in user_input_lower for w in ["sympathy", "condolence", "funeral", "passed", "died"]):
            occasion = "sympathy"
        elif any(w in user_input_lower for w in ["get well", "sick", "hospital", "recover"]):
            occasion = "get_well"
        elif any(w in user_input_lower for w in ["graduation", "graduate"]):
            occasion = "graduation"
            is_special_milestone = True
        elif any(w in user_input_lower for w in ["new job", "promotion"]):
            occasion = "congratulations"
            is_special_milestone = True

        # Detect recipient
        recipient = "unspecified"
        if any(w in user_input_lower for w in ["girlfriend", "gf"]):
            recipient = "girlfriend"
        elif any(w in user_input_lower for w in ["wife"]):
            recipient = "wife"
        elif any(w in user_input_lower for w in ["boyfriend", "bf"]):
            recipient = "boyfriend"
        elif any(w in user_input_lower for w in ["husband"]):
            recipient = "husband"
        elif any(w in user_input_lower for w in ["mom", "mother", "mum", "mama"]):
            recipient = "mother"
        elif any(w in user_input_lower for w in ["dad", "father", "papa"]):
            recipient = "father"
        elif any(w in user_input_lower for w in ["friend"]):
            recipient = "friend"
        elif any(w in user_input_lower for w in ["boss", "manager"]):
            recipient = "boss"
        elif any(w in user_input_lower for w in ["colleague", "coworker"]):
            recipient = "colleague"

        # Build primary intent
        if recipient != "unspecified" and occasion != "general":
            primary = f"{occasion} for {recipient}".replace("_", " ").title()
        elif recipient != "unspecified":
            primary = f"Flowers for {recipient}"
        elif occasion != "general":
            primary = occasion.replace("_", " ").title()
        else:
            primary = "General flower gift"

        ctx.intent = IntentData(
            primary_intent=primary,
            confidence=0.6,  # Higher than before since we did keyword matching
            sub_intents=[f"fallback_extracted:{occasion}"],
            raw_output={
                "fallback": True,
                "recipient": recipient,
                "occasion": occasion,
                "tone": "neutral",
                "emotion": "affection",
                "relationship_level": "unspecified",
                "context_flags": {
                    "is_first_gift": False,
                    "is_making_amends": is_making_amends,
                    "is_special_milestone": is_special_milestone,
                    "budget_hint": "unspecified",
                },
                "keywords": [],
            },
        )
