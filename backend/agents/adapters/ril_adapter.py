"""
RIL Adapter - Relationship Intelligence Layer - v2 (Adapted)

Purpose:
Analyzes the relationship context between the user and the flower recipient.
Determines relationship type, stage, tone, and dynamics.

Based on: relationship_intent_agent_v2.py
"""

import logging
from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, RelationshipData
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

RELATIONSHIP_ANALYSIS_PROMPT = """You are Relationship Intent Layer v2 for FSense.
Analyze emotional and intent data to infer relationship dynamics and output STRICT JSON only.

Determine:
- relationship_type: romantic, platonic, familial, neutral
- relationship_stage: early, growing, established, longterm
- relationship_tone: formal, neutral, warm, romantic
- stage_reasoning: brief explanation of your assessment
- confidence: 0.0-1.0 scale

Return JSON:
{
  "relationship_type": "romantic",
  "relationship_stage": "established",
  "relationship_tone": "warm",
  "stage_reasoning": "The warm tone and established context suggest a close relationship",
  "confidence": 0.85
}"""


class RILAdapter(BaseAgent):
    """Relationship Intelligence Layer - analyzes relationship dynamics."""

    name = "RIL"

    def run(self, ctx: PipelineContext) -> None:
        """Analyze relationship context and store in context."""
        try:
            client = get_ai_client_fast()

            # Extract data from previous agents
            recipient = ctx.intent.raw_output.get("recipient", "unspecified") if ctx.intent else "unspecified"
            tone = ctx.intent.raw_output.get("tone", "neutral") if ctx.intent else "neutral"
            relation_level = ctx.intent.raw_output.get("relationship_level", "unspecified") if ctx.intent else "unspecified"

            emotion_tone = ctx.emotions.emotional_tone if ctx.emotions else "neutral"
            emotion_intensity = ctx.emotions.emotion_intensity if ctx.emotions else 0.5

            # Build prompt with all available context
            prompt = f"""Intent:
- Recipient: {recipient}
- Tone: {tone}
- Relation Level: {relation_level}

Emotions:
- Emotion tone: {emotion_tone}
- Emotion intensity: {emotion_intensity:.2f}

User message: "{ctx.user_input}"
Region: {ctx.region.upper()}

Analyze the relationship dynamics based on this information."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=RELATIONSHIP_ANALYSIS_PROMPT,
                temperature=0.3,
            )

            # Parse response
            r_type = response.get("relationship_type", "neutral")
            r_stage = response.get("relationship_stage", "established")
            r_tone = response.get("relationship_tone", "neutral")
            confidence = float(response.get("confidence", 0.7))

            # Convert to intimacy and formality levels
            intimacy = self._calculate_intimacy(r_type, r_stage, r_tone)
            formality = self._calculate_formality(r_tone, r_type)
            power_dynamic = self._infer_power_dynamic(r_type, recipient)

            ctx.relationship = RelationshipData(
                relationship_type=r_type,
                intimacy_level=intimacy,
                formality_level=formality,
                power_dynamic=power_dynamic,
                raw_output=response,
            )

            logger.info(f"RIL detected relationship: {r_type} ({r_stage}, {r_tone}) - intimacy={intimacy:.2f}")

            # Console output
            console = get_console_logger()
            console.agent_result("RIL", {
                "Relationship Type": r_type,
                "Stage": r_stage,
                "Tone": r_tone,
                "Intimacy Level": f"{intimacy:.2f}",
                "Formality Level": f"{formality:.2f}",
                "Power Dynamic": power_dynamic,
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

    def _calculate_intimacy(self, r_type: str, r_stage: str, r_tone: str) -> float:
        """Calculate intimacy level from relationship data."""
        base = 0.3

        # Type contribution
        if r_type == "romantic":
            base += 0.3
        elif r_type == "familial":
            base += 0.2
        elif r_type == "platonic":
            base += 0.1

        # Stage contribution
        stage_values = {"early": 0.0, "growing": 0.1, "established": 0.2, "longterm": 0.3}
        base += stage_values.get(r_stage, 0.1)

        # Tone contribution
        tone_values = {"formal": -0.1, "neutral": 0.0, "warm": 0.1, "romantic": 0.2}
        base += tone_values.get(r_tone, 0.0)

        return max(0.0, min(1.0, base))

    def _calculate_formality(self, r_tone: str, r_type: str) -> float:
        """Calculate formality level from relationship tone and type."""
        if r_tone == "formal":
            return 0.8
        elif r_tone == "romantic":
            return 0.2
        elif r_tone == "warm":
            return 0.3
        elif r_type == "neutral":
            return 0.6
        else:
            return 0.5

    def _infer_power_dynamic(self, r_type: str, recipient: str) -> str:
        """Infer power dynamic from relationship context."""
        if recipient in {"boss", "manager", "supervisor", "professor"}:
            return "hierarchical"
        elif recipient in {"student", "intern", "employee"}:
            return "hierarchical_reverse"
        elif r_type == "familial" and recipient in {"mother", "father"}:
            return "respectful"
        else:
            return "equal"

    def _fallback_relationship(self, ctx: PipelineContext) -> None:
        """Provide fallback relationship data when AI fails."""
        ctx.relationship = RelationshipData(
            relationship_type="neutral",
            intimacy_level=0.5,
            formality_level=0.5,
            power_dynamic="equal",
            raw_output={"fallback": True},
        )
