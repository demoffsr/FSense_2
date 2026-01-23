"""
FMRA Adapter - Flower Matching & Ranking Agent - v0.0.3

Purpose:
Selects the single best flower based on user's situation.
Returns flower name and basic meanings for SFA to expand.
"""

import logging
from typing import Any

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    CandidatesData,
    FlowerCandidate,
)
from backend.core.ai_client import get_ai_client, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

# Simplified prompt - just pick the flower
FLOWER_SELECTION_PROMPT = """You are a flower expert. Based on the user's situation, recommend the single best flower.

Choose from real flowers like: Red Rose, White Rose, Pink Rose, Yellow Rose, Tulip, Lily, Sunflower, Orchid, Peony, Carnation, Daisy, Lavender, Chrysanthemum, Iris, Hydrangea, Gardenia, Jasmine, Magnolia, Camellia, Amaryllis, Daffodil, Violet, etc.

Be creative and match the flower to the specific emotional context. Don't always recommend roses.

Return JSON:
{
    "flower_name": "Full Flower Name",
    "flower_id": "lowercase_id",
    "match_score": 0.0-1.0,
    "meanings": ["meaning1", "meaning2", "meaning3", "meaning4"]
}"""


class FMRAAdapter(BaseAgent):
    """Flower selection agent - picks the best flower."""

    name = "FMRA"

    def run(self, ctx: PipelineContext) -> None:
        """Select flower based on user context."""
        try:
            client = get_ai_client()
            user_prompt = self._build_prompt(ctx)

            response = client.complete_json(
                prompt=user_prompt,
                system_prompt=FLOWER_SELECTION_PROMPT,
                temperature=0.7,
            )

            candidate = FlowerCandidate(
                flower_id=response.get("flower_id", "unknown_flower"),
                name=response.get("flower_name", "Unknown Flower"),
                match_score=float(response.get("match_score", 0.85)),
                match_reasons=["AI recommendation"],
                meanings=response.get("meanings", ["Beauty", "Emotion"])[:6],
            )

            ctx.candidates = CandidatesData(
                candidates=[candidate],
                total_considered=1,
                ranking_criteria=["emotional_match", "cultural_fit"],
                raw_output=response,
            )

            logger.info(f"FMRA selected: {candidate.name}")

            # Console output
            console = get_console_logger()
            console.agent_result("FMRA", {
                "Selected Flower": candidate.name,
                "Flower ID": candidate.flower_id,
                "Match Score": f"{candidate.match_score:.2f}",
                "Meanings": candidate.meanings[:4],
            })

        except AIClientError as e:
            logger.error(f"FMRA AI error: {e}")
            ctx.add_error(f"FMRA: {str(e)}")
            self._fallback_recommendation(ctx)

        except Exception as e:
            logger.error(f"FMRA error: {e}", exc_info=True)
            ctx.add_error(f"FMRA: Unexpected error")
            self._fallback_recommendation(ctx)

    def _build_prompt(self, ctx: PipelineContext) -> str:
        """Build prompt from context."""
        parts = [f"User's message: \"{ctx.user_input}\""]

        if ctx.intent and ctx.intent.primary_intent:
            parts.append(f"Intent: {ctx.intent.primary_intent}")

        if ctx.priors:
            if ctx.priors.occasion:
                parts.append(f"Occasion: {ctx.priors.occasion}")
            if ctx.priors.relationship_type:
                parts.append(f"Relationship: {ctx.priors.relationship_type}")

        if ctx.emotions and ctx.emotions.primary_emotion:
            parts.append(f"Primary emotion: {ctx.emotions.primary_emotion}")

        if ctx.relationship and ctx.relationship.relationship_type:
            parts.append(f"Detected relationship: {ctx.relationship.relationship_type}")

        parts.append(f"Region: {ctx.region.upper()}")

        return "\n".join(parts)

    def _fallback_recommendation(self, ctx: PipelineContext) -> None:
        """Fallback when AI fails."""
        fallback = FlowerCandidate(
            flower_id="red_rose",
            name="Red Rose",
            match_score=0.80,
            match_reasons=["Classic choice"],
            meanings=["Love", "Appreciation", "Respect"],
        )

        ctx.candidates = CandidatesData(
            candidates=[fallback],
            total_considered=1,
            ranking_criteria=["fallback"],
            raw_output={"fallback": True},
        )
