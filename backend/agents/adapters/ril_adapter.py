"""
RIL Adapter - Relationship Intelligence Layer - v3 (Enhanced)

Purpose:
Analyzes relationship dynamics with nuance for flower gifting appropriateness.
Determines relationship type, stage, formality, and gift appropriateness factors.

Version: v3 - Added gift_appropriateness, dynamic calculations, cultural awareness
"""

import logging
from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, RelationshipData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

RELATIONSHIP_ANALYSIS_PROMPT = """You are Relationship Intelligence Layer v3 for FSense.
Analyze relationship dynamics with nuance for flower gifting appropriateness.
Output STRICT JSON only.

RELATIONSHIP TYPES:
- romantic: dating, engaged, married, long-distance love
- platonic: close friend, casual friend, acquaintance
- familial: parent, sibling, grandparent, extended family
- professional: boss, colleague, mentor, client, teacher
- ceremonial: wedding guest, funeral attendee, host gift

RELATIONSHIP STAGES:
- new: 0-3 months, still learning each other
- developing: 3-12 months, building trust and patterns
- established: 1-5 years, comfortable and known
- deep: 5+ years, profound understanding

FORMALITY SPECTRUM:
- formal: professional settings, first impressions, ceremonies
- semi_formal: known colleagues, extended family, acquaintances
- casual: close friends, established relationships
- intimate: romantic partners, immediate family

POWER DYNAMICS:
- equal: peer relationship, no hierarchy
- hierarchical_up: giving to someone above (boss, elder)
- hierarchical_down: giving to someone below (employee, student)
- respectful: parent/elder deserving special consideration

GIFT APPROPRIATENESS - assess these carefully:
- max_intensity: 0.0-1.0 - maximum emotional intensity appropriate for this relationship
- romantic_flowers_ok: boolean - are red roses and romantic flowers appropriate?
- avoid_flowers: list of flower types to avoid for this relationship/culture
- cultural_considerations: any cultural factors affecting flower choice

Return JSON:
{
  "relationship_type": "romantic",
  "relationship_stage": "established",
  "formality": "intimate",
  "intimacy_score": 0.85,
  "power_dynamic": "equal",
  "gift_appropriateness": {
    "max_intensity": 0.9,
    "romantic_flowers_ok": true,
    "avoid_flowers": [],
    "cultural_considerations": "None specific"
  },
  "stage_reasoning": "Dating for 2 years based on context clues",
  "confidence": 0.85
}"""


class RILAdapter(BaseAgent):
    """Relationship Intelligence Layer - analyzes relationship dynamics."""

    name = "RIL"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze relationship context and store in context."""
        try:
            client = get_ai_client_fast()

            # Extract rich data from previous agents
            recipient = "unspecified"
            tone = "neutral"
            relation_level = "unspecified"
            occasion = "general"
            context_flags = {}

            if ctx.intent and ctx.intent.raw_output:
                recipient = ctx.intent.raw_output.get("recipient", "unspecified")
                tone = ctx.intent.raw_output.get("tone", "neutral")
                relation_level = ctx.intent.raw_output.get("relationship_level", "unspecified")
                occasion = ctx.intent.raw_output.get("occasion", "general")
                context_flags = ctx.intent.raw_output.get("context_flags", {})

            emotion_tone = ctx.emotions.emotional_tone if ctx.emotions else "neutral"
            emotion_intensity = ctx.emotions.emotion_intensity if ctx.emotions else 0.5
            primary_emotion = ctx.emotions.primary_emotion if ctx.emotions else "affection"

            # Build rich prompt with all available context
            prompt = f"""Analyze relationship for flower gifting:

INTENT DATA:
- Recipient: {recipient}
- Tone: {tone}
- Relationship Level: {relation_level}
- Occasion: {occasion}
- Is First Gift: {context_flags.get('is_first_gift', 'unknown')}
- Is Making Amends: {context_flags.get('is_making_amends', 'unknown')}

EMOTION DATA:
- Primary Emotion: {primary_emotion}
- Emotion Tone: {emotion_tone}
- Emotion Intensity: {emotion_intensity:.2f}

User message: "{ctx.user_input}"
Region: {ctx.region.upper()}

Analyze the relationship dynamics and gift appropriateness."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=RELATIONSHIP_ANALYSIS_PROMPT,
                temperature=0.3,
            )

            # Parse response - use AI-calculated values directly
            r_type = response.get("relationship_type", "neutral")
            r_stage = response.get("relationship_stage", "established")
            formality_raw = response.get("formality", "casual")
            confidence = float(response.get("confidence", 0.7))

            # Use AI-calculated intimacy score directly
            intimacy = float(response.get("intimacy_score", 0.5))

            # Convert formality string to numeric
            formality_map = {"formal": 0.9, "semi_formal": 0.6, "casual": 0.4, "intimate": 0.2}
            formality = formality_map.get(formality_raw, 0.5)

            # Get power dynamic from AI response
            power_dynamic = response.get("power_dynamic", "equal")

            ctx.relationship = RelationshipData(
                relationship_type=r_type,
                intimacy_level=intimacy,
                formality_level=formality,
                power_dynamic=power_dynamic,
                raw_output=response,
            )

            logger.info(f"RIL detected relationship: {r_type} ({r_stage}, {formality_raw}) - intimacy={intimacy:.2f}")

            # Console output with gift appropriateness
            console = get_console_logger()
            appropriateness = response.get("gift_appropriateness", {})
            console.agent_result("RIL", {
                "Relationship Type": r_type,
                "Stage": r_stage,
                "Formality": formality_raw,
                "Intimacy Level": f"{intimacy:.2f}",
                "Power Dynamic": power_dynamic,
                "Max Intensity": appropriateness.get("max_intensity", 1.0),
                "Romantic OK": appropriateness.get("romantic_flowers_ok", True),
                "Confidence": f"{confidence:.2f}",
            })

        except AIClientError as e:
            logger.error(f"RIL AI error: {e}")
            ctx.add_error(f"RIL: {str(e)}")
            self._fallback_relationship(ctx)

        except Exception as e:
            logger.error(f"RIL unexpected error: {e}", exc_info=True)
            ctx.add_error(f"RIL: Unexpected error")
            self._fallback_relationship(ctx)

    def _fallback_relationship(self, ctx: PipelineContext) -> None:
        """Smarter fallback using FIA and EIA context when AI fails."""
        # Default values
        r_type = "neutral"
        intimacy = 0.5
        formality = 0.5
        power_dynamic = "equal"
        max_intensity = 1.0
        romantic_ok = True

        # Use FIA data to infer relationship
        if ctx.intent and ctx.intent.raw_output:
            recipient = ctx.intent.raw_output.get("recipient", "").lower()
            occasion = ctx.intent.raw_output.get("occasion", "")

            # Infer relationship type from recipient
            if recipient in ["girlfriend", "boyfriend", "wife", "husband", "partner"]:
                r_type = "romantic"
                intimacy = 0.8
                formality = 0.2
                romantic_ok = True
                max_intensity = 0.9
            elif recipient in ["mother", "father", "mom", "dad", "parent", "grandma", "grandpa"]:
                r_type = "familial"
                intimacy = 0.7
                formality = 0.3
                power_dynamic = "respectful"
                romantic_ok = False
                max_intensity = 0.7
            elif recipient in ["friend"]:
                r_type = "platonic"
                intimacy = 0.5
                formality = 0.4
                romantic_ok = False
                max_intensity = 0.6
            elif recipient in ["boss", "manager", "supervisor", "professor", "teacher"]:
                r_type = "professional"
                intimacy = 0.2
                formality = 0.8
                power_dynamic = "hierarchical_up"
                romantic_ok = False
                max_intensity = 0.4
            elif recipient in ["colleague", "coworker"]:
                r_type = "professional"
                intimacy = 0.3
                formality = 0.6
                romantic_ok = False
                max_intensity = 0.5

            # Adjust for occasion
            if occasion == "sympathy":
                max_intensity = 0.6
                romantic_ok = False

        ctx.relationship = RelationshipData(
            relationship_type=r_type,
            intimacy_level=intimacy,
            formality_level=formality,
            power_dynamic=power_dynamic,
            raw_output={
                "fallback": True,
                "fallback_source": "intent_based",
                "relationship_stage": "established",
                "formality": "casual" if formality < 0.5 else "formal",
                "gift_appropriateness": {
                    "max_intensity": max_intensity,
                    "romantic_flowers_ok": romantic_ok,
                    "avoid_flowers": [],
                    "cultural_considerations": "None",
                },
            },
        )
