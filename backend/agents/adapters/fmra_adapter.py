"""
FMRA Adapter - Flower Matching & Ranking Agent - v0.0.4 (Optimized with DB)

Purpose:
Selects the single best flower based on user's situation.
Uses flower database for quick lookup, AI for ranking.
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
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

# Import flower database functions
try:
    from backend.database.flower_database import (
        get_flowers_by_emotion,
        get_flower_by_id,
        get_flowers_by_ids,
        FLOWERS_DATA,
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Flower database not available, using AI-only mode")

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
        """Select flower based on user context - hybrid DB + AI approach."""
        try:
            # Try database-assisted selection first
            if DATABASE_AVAILABLE and ctx.emotions and ctx.emotions.primary_emotion:
                db_matches = self._get_database_matches(ctx)
                if db_matches:
                    logger.info(f"FMRA: Found {len(db_matches)} matches in database")
                    # Use AI to rank database matches
                    candidate = self._rank_with_ai(ctx, db_matches)
                else:
                    # No DB matches, use pure AI
                    logger.info("FMRA: No DB matches, using AI selection")
                    candidate = self._ai_selection(ctx)
            else:
                # Database not available or no emotion, use pure AI
                logger.info("FMRA: Using AI-only selection")
                candidate = self._ai_selection(ctx)

            ctx.candidates = CandidatesData(
                candidates=[candidate],
                total_considered=1,
                ranking_criteria=["emotional_match", "cultural_fit", "database_assisted"],
                raw_output={"flower_id": candidate.flower_id, "name": candidate.name},
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

    def _get_database_matches(self, ctx: PipelineContext) -> list[dict]:
        """Get flower matches from database based on emotion."""
        if not ctx.emotions or not ctx.emotions.primary_emotion:
            return []

        emotion = ctx.emotions.primary_emotion.lower()
        matches = list(get_flowers_by_emotion(emotion, top_n=5))

        if not matches:
            # Try secondary emotions
            if ctx.emotions.secondary_emotions:
                for sec_emotion in ctx.emotions.secondary_emotions[:2]:
                    matches = list(get_flowers_by_emotion(sec_emotion.lower(), top_n=3))
                    if matches:
                        break

        return matches

    def _rank_with_ai(self, ctx: PipelineContext, db_matches: list[dict]) -> FlowerCandidate:
        """Use AI to rank database matches and select the best one."""
        # Batch lookup all flowers at once (fixes N+1 query pattern)
        flower_ids = tuple(m["flower_id"] for m in db_matches)
        flowers_data = get_flowers_by_ids(flower_ids)

        # Build list of flowers from database
        flower_options = []
        for match in db_matches:
            flower_data = flowers_data.get(match["flower_id"])
            if flower_data:
                flower_options.append({
                    "id": match["flower_id"],
                    "name": flower_data["name"],
                    "meanings": match["meaning_en"],
                    "match_score": match["match_score"],
                })

        # Ask AI to rank these specific options
        client = get_ai_client_fast()
        ranking_prompt = f"""Based on the context, rank these flower options and select THE BEST ONE.

User context:
{self._build_prompt(ctx)}

Available flowers:
{chr(10).join(f"{i+1}. {f['name']} - {f['meanings']}" for i, f in enumerate(flower_options))}

Select the single best match. Return JSON:
{{
    "flower_id": "id_from_list",
    "flower_name": "Name from list",
    "match_score": 0.0-1.0,
    "reasoning": "Why this flower is the best match"
}}"""

        response = client.complete_json(
            prompt=ranking_prompt,
            system_prompt="You are a flower selection expert. Choose the best match from the provided options.",
            temperature=0.5,
        )

        # Find the selected flower in our options
        selected_id = response.get("flower_id", flower_options[0]["id"])
        selected = next((f for f in flower_options if f["id"] == selected_id), flower_options[0])

        return FlowerCandidate(
            flower_id=selected["id"],
            name=selected["name"],
            match_score=float(response.get("match_score", selected["match_score"])),
            match_reasons=["database_match", "ai_ranked"],
            meanings=selected["meanings"].split(", ")[:6] if isinstance(selected["meanings"], str) else selected["meanings"][:6],
        )

    def _ai_selection(self, ctx: PipelineContext) -> FlowerCandidate:
        """Pure AI selection when database doesn't have matches."""
        client = get_ai_client_fast()
        user_prompt = self._build_prompt(ctx)

        response = client.complete_json(
            prompt=user_prompt,
            system_prompt=FLOWER_SELECTION_PROMPT,
            temperature=0.7,
        )

        return FlowerCandidate(
            flower_id=response.get("flower_id", "unknown_flower"),
            name=response.get("flower_name", "Unknown Flower"),
            match_score=float(response.get("match_score", 0.85)),
            match_reasons=["AI recommendation"],
            meanings=response.get("meanings", ["Beauty", "Emotion"])[:6],
        )

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
