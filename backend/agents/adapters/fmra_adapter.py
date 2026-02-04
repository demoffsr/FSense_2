"""
FMRA Adapter - Flower Matching & Ranking Agent - v0.0.5 (Multi-Candidate + Diversity)

Purpose:
Selects multiple flower candidates (top 5) based on user's situation.
Uses flower database for quick lookup, AI for ranking.
Applies diversity penalty to avoid repetitive recommendations.
Returns primary flower + alternatives for SFA to assemble.
"""

import logging
import os
import re
import time
from typing import Any, Optional

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    CandidatesData,
    FlowerCandidate,
)
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger
from backend.core.budget_normalizer import normalize_budget
from backend.core.safe_parse import safe_parse_float

logger = logging.getLogger(__name__)

# Import flower database functions
try:
    from backend.database.flower_database import (
        get_flowers_by_emotion,
        get_flowers_by_emotions,
        get_flower_by_id,
        get_flowers_by_ids,
        FLOWERS_DATA,
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Flower database not available, using AI-only mode")

# Multi-candidate prompt with diversity emphasis
FLOWER_SELECTION_PROMPT = """You are a flower expert. Based on the user's situation, recommend TOP 5 flowers ranked by suitability.

IMPORTANT - DIVERSITY RULES:
1. AVOID defaulting to common flowers (Red Rose, Sunflower, Crocus) unless truly the BEST match
2. Consider unique but meaningful options: Hyacinth, Freesia, Ranunculus, Lisianthus, Anemone, Protea, Hellebore, Clematis, Sweet Pea, Stock, Delphinium, Astilbe, Scabiosa, etc.
3. Match flowers to the SPECIFIC emotional nuance, not just the general category
4. Each recommendation should be distinct (different flower families when possible)

Choose from real flowers and return your TOP 5 recommendations as JSON:
{
    "candidates": [
        {
            "flower_name": "Full Flower Name",
            "flower_id": "lowercase_snake_case_id",
            "match_score": 0.0-1.0,
            "match_reason": "Brief reason why this flower fits the situation",
            "meanings": ["meaning1", "meaning2", "meaning3", "meaning4"]
        }
    ]
}

Rank by match_score from highest to lowest. Be specific with match_reason."""


class FMRAAdapter(BaseAgent):
    """Flower selection agent - picks multiple flower candidates with diversity."""

    name = "FMRA"

    def __init__(self):
        self._enforce_budget = os.getenv("FMRA_ENFORCE_BUDGET", "true").lower() == "true"

    def run(self, ctx: PipelineContext) -> None:
        """Select multiple flowers based on user context with diversity penalty."""
        from backend.services.recommendation_history import get_recommendation_history

        try:
            # Log when budget constraint is active
            if ctx.priors and ctx.priors.budget_range and ctx.priors.budget_range.lower() not in ["any", "unspecified"]:
                logger.info(f"FMRA: Budget constraint active: {ctx.priors.budget_range}")

            history = get_recommendation_history()

            # Check if flower was already identified via vision analysis
            if ctx.vision and ctx.vision.main_flower and ctx.vision.main_flower.name:
                logger.info(f"FMRA: Using flower from vision analysis: {ctx.vision.main_flower.name}")
                candidates = [self._flower_from_vision(ctx)]
            # Try database-assisted selection first
            elif DATABASE_AVAILABLE and ctx.emotions and ctx.emotions.primary_emotion:
                db_matches = self._get_database_matches(ctx, top_n=10)
                if db_matches:
                    logger.info(f"FMRA: Found {len(db_matches)} matches in database")
                    candidates = self._rank_multiple_with_ai(ctx, db_matches)
                else:
                    logger.info("FMRA: No DB matches, using AI selection")
                    candidates = self._ai_selection_multiple(ctx)
            else:
                logger.info("FMRA: Using AI-only selection")
                candidates = self._ai_selection_multiple(ctx)

            # Apply diversity penalty to all candidates
            for candidate in candidates:
                penalty = history.calculate_diversity_penalty(candidate.flower_id)
                if penalty > 0:
                    candidate.match_score = max(0.1, candidate.match_score - penalty)
                    candidate.match_reasons.append(f"diversity_adjusted:-{penalty:.2f}")
                    logger.debug(f"FMRA: Applied penalty {penalty:.2f} to {candidate.name}")

            # Budget enforcement (after diversity penalty)
            budget_adjusted = False
            if self._enforce_budget and ctx.priors and ctx.priors.budget_range:
                user_budget = ctx.priors.budget_range
                if user_budget.lower() not in ["any", "unspecified"]:
                    for candidate in candidates:
                        multiplier = self._calculate_budget_multiplier(
                            candidate.price_tier, user_budget
                        )
                        if multiplier != 1.0:
                            old_score = candidate.match_score
                            candidate.match_score = min(1.0, max(0.1, candidate.match_score * multiplier))
                            candidate.match_reasons.append(f"budget_adjusted:{multiplier:.2f}")
                            budget_adjusted = True
                            logger.debug(
                                f"FMRA: Budget adjustment for {candidate.name}: "
                                f"{old_score:.2f} -> {candidate.match_score:.2f} "
                                f"(tier={candidate.price_tier}, user={user_budget})"
                            )
            elif not self._enforce_budget and ctx.priors and ctx.priors.budget_range:
                # Shadow mode: log what would happen without applying
                user_budget = ctx.priors.budget_range
                if user_budget.lower() not in ["any", "unspecified"]:
                    for candidate in candidates:
                        mult = self._calculate_budget_multiplier(candidate.price_tier, user_budget)
                        if mult != 1.0:
                            would_be = min(1.0, max(0.1, candidate.match_score * mult))
                            logger.info(
                                f"FMRA [shadow]: {candidate.name} "
                                f"{candidate.match_score:.2f} -> {would_be:.2f} (x{mult})"
                            )

            # Re-sort by adjusted score and take top 5
            candidates.sort(key=lambda c: c.match_score, reverse=True)
            candidates = candidates[:5]

            # Build dynamic ranking criteria
            criteria = ["emotional_match", "cultural_fit", "diversity_adjusted"]
            if budget_adjusted:
                criteria.append("budget_adjusted")

            ctx.candidates = CandidatesData(
                candidates=candidates,
                total_considered=len(candidates),
                ranking_criteria=criteria,
                raw_output={
                    "primary": candidates[0].flower_id if candidates else None,
                    "alternatives_count": len(candidates) - 1 if candidates else 0,
                },
            )

            # Record primary recommendation for future diversity
            if candidates:
                emotion = ctx.emotions.primary_emotion if ctx.emotions else None
                history.record_recommendation(
                    flower_id=candidates[0].flower_id,
                    emotion=emotion
                )

            logger.info(f"FMRA selected: {[c.name for c in candidates]}")

            # Console output
            console = get_console_logger()
            primary = candidates[0] if candidates else None
            console.agent_result("FMRA", {
                "Primary Flower": primary.name if primary else "None",
                "Match Score": f"{primary.match_score:.2f}" if primary else "N/A",
                "Budget Adjusted": budget_adjusted,
                "Alternatives": [c.name for c in candidates[1:]] if len(candidates) > 1 else [],
                "Meanings": primary.meanings[:4] if primary else [],
            })

        except AIClientError as e:
            logger.error(f"FMRA AI error: {e}")
            ctx.add_error(f"FMRA: {str(e)}")
            self._fallback_recommendation(ctx)

        except Exception as e:
            logger.error(f"FMRA error: {e}", exc_info=True)
            ctx.add_error(f"FMRA: Unexpected error")
            self._fallback_recommendation(ctx)

    def _flower_from_vision(self, ctx: PipelineContext) -> FlowerCandidate:
        """Create FlowerCandidate from vision analysis result."""
        vision_flower = ctx.vision.main_flower
        flower_name = vision_flower.name

        # Generate flower_id from name
        flower_id = flower_name.lower().replace(" ", "_").replace("-", "_")

        # Try to get data from database first
        price_tier = "mid"
        meanings = None

        if DATABASE_AVAILABLE:
            flower_data = get_flower_by_id(flower_id)
            if flower_data:
                price_tier = flower_data.get("price_tier", "mid")
                # Use primary_meanings from DB if available (optimization: skip AI call)
                db_meanings = flower_data.get("primary_meanings")
                if isinstance(db_meanings, list) and db_meanings:
                    meanings = [m.capitalize() for m in db_meanings[:6]]
                    logger.info(f"FMRA: using DB meanings for {flower_name}")
            else:
                price_tier = self._estimate_price_tier(flower_name)

        # Fallback to AI only if no meanings from DB
        if not meanings:
            logger.info(f"FMRA: using AI fallback for meanings ({flower_name})")
            client = get_ai_client_fast()
            meanings_prompt = f"""For the flower "{flower_name}", provide 4-6 symbolic meanings.
Return JSON: {{"meanings": ["meaning1", "meaning2", "meaning3", "meaning4"]}}"""

            try:
                response = client.complete_json(
                    prompt=meanings_prompt,
                    system_prompt="You are a flower symbolism expert. Return only the JSON.",
                    temperature=0.5,
                )
                meanings = response.get("meanings", ["Beauty", "Nature", "Elegance", "Grace"])[:6]
            except Exception as e:
                logger.warning(f"FMRA: AI meanings failed for {flower_name}: {e}")
                meanings = ["Beauty", "Nature", "Elegance", "Grace"]

        return FlowerCandidate(
            flower_id=flower_id,
            name=flower_name,
            match_score=vision_flower.confidence,
            match_reasons=["Identified from user image", "Vision analysis"],
            meanings=meanings,
            price_tier=price_tier,
        )

    def _get_database_matches(self, ctx: PipelineContext, top_n: int = 10) -> list[dict]:
        """Get flower matches from database based on emotion (batch query)."""
        if not ctx.emotions or not ctx.emotions.primary_emotion:
            return []

        start = time.perf_counter()

        primary = ctx.emotions.primary_emotion.lower()

        # Collect all emotions to query
        emotions_to_query = [primary]
        if ctx.emotions.secondary_emotions:
            emotions_to_query.extend(e.lower() for e in ctx.emotions.secondary_emotions[:2])

        # Single batch query with different limits: primary=top_n, secondary=5
        emotion_matches = get_flowers_by_emotions(
            emotions_to_query,
            top_n_per=5,  # Secondary emotions get 5
            primary_emotion=primary,
            primary_top_n=top_n,  # Primary gets full top_n (10)
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.debug(f"Batch emotion query ({len(emotions_to_query)} emotions): {elapsed_ms:.1f}ms")

        # Start with primary emotion matches, track IDs from the start
        matches = list(emotion_matches.get(primary, ()))
        existing_ids = {m["flower_id"] for m in matches}

        # Add secondary if not enough matches (deduplicated)
        if len(matches) < 5:
            for sec_emotion in emotions_to_query[1:]:
                for m in emotion_matches.get(sec_emotion, ()):
                    if m["flower_id"] not in existing_ids:
                        matches.append(m)
                        existing_ids.add(m["flower_id"])
                    if len(matches) >= top_n:
                        break
                if len(matches) >= top_n:
                    break

        return matches[:top_n]

    def _rank_multiple_with_ai(self, ctx: PipelineContext, db_matches: list[dict]) -> list[FlowerCandidate]:
        """Use AI to rank database matches and return top 5 candidates."""
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
                    "price_tier": flower_data.get("price_tier", "mid"),
                })

        if not flower_options:
            return [self._fallback_candidate(ctx)]

        # Ask AI to rank these specific options
        client = get_ai_client_fast()
        ranking_prompt = f"""Based on the context, rank these flower options and select THE TOP 5.

IMPORTANT: Provide DIVERSE recommendations. If multiple roses are available, only include the best one.

User context:
{self._build_prompt(ctx)}

Available flowers:
{chr(10).join(f"{i+1}. {f['name']} (ID: {f['id']}) - {f['meanings']}" for i, f in enumerate(flower_options))}

Select the top 5 matches, ranked from best to good. Return JSON:
{{
    "candidates": [
        {{"flower_id": "id_from_list", "flower_name": "Name from list", "match_score": 0.0-1.0, "match_reason": "Why"}}
    ]
}}"""

        response = client.complete_json(
            prompt=ranking_prompt,
            system_prompt="You are a flower expert. Rank flowers by fit, ensuring diversity.",
            temperature=0.6,
        )

        candidates = []
        for item in response.get("candidates", [])[:5]:
            selected_id = item.get("flower_id")
            selected = next((f for f in flower_options if f["id"] == selected_id), None)
            if selected:
                meanings = selected["meanings"]
                if isinstance(meanings, str):
                    meanings = meanings.split(", ")[:6]
                candidates.append(FlowerCandidate(
                    flower_id=selected["id"],
                    name=selected["name"],
                    match_score=safe_parse_float(
                        item.get("match_score", selected["match_score"]),
                        default=0.85,
                        context="FMRA.match_score"
                    ),
                    match_reasons=[item.get("match_reason", "database_match"), "ai_ranked"],
                    meanings=meanings[:6],
                    price_tier=selected.get("price_tier", "mid"),
                ))

        # If AI didn't return enough, fill from database matches
        if len(candidates) < 3:
            existing_ids = {c.flower_id for c in candidates}
            for opt in flower_options:
                if opt["id"] not in existing_ids:
                    meanings = opt["meanings"]
                    if isinstance(meanings, str):
                        meanings = meanings.split(", ")[:6]
                    candidates.append(FlowerCandidate(
                        flower_id=opt["id"],
                        name=opt["name"],
                        match_score=float(opt["match_score"]),
                        match_reasons=["database_match"],
                        meanings=meanings[:6],
                        price_tier=opt.get("price_tier", "mid"),
                    ))
                    if len(candidates) >= 5:
                        break

        return candidates if candidates else [self._fallback_candidate(ctx)]

    def _ai_selection_multiple(self, ctx: PipelineContext) -> list[FlowerCandidate]:
        """Pure AI selection returning multiple candidates when database doesn't have matches."""
        client = get_ai_client_fast()
        user_prompt = self._build_prompt(ctx)

        response = client.complete_json(
            prompt=user_prompt,
            system_prompt=FLOWER_SELECTION_PROMPT,
            temperature=0.7,
        )

        candidates = []
        for item in response.get("candidates", [])[:5]:
            # Estimate price tier from flower name if not in database
            flower_name = item.get("flower_name", "Unknown Flower")
            price_tier = self._estimate_price_tier(flower_name)

            candidates.append(FlowerCandidate(
                flower_id=item.get("flower_id", "unknown_flower"),
                name=flower_name,
                match_score=safe_parse_float(
                    item.get("match_score"),
                    default=0.85,
                    context="FMRA.match_score"
                ),
                match_reasons=[item.get("match_reason", "AI recommendation")],
                meanings=item.get("meanings", ["Beauty", "Emotion"])[:6],
                price_tier=price_tier,
            ))

        return candidates if candidates else [self._fallback_candidate(ctx)]

    def _estimate_price_tier(self, flower_name: str) -> str:
        """Estimate price tier for flowers not in database."""
        flower_lower = flower_name.lower()

        # Premium flowers
        premium_flowers = [
            "peony", "orchid", "protea", "king protea", "bird of paradise",
            "calla lily", "ranunculus", "anemone", "garden rose", "david austin",
            "hellebore", "stephanotis", "gardenia"
        ]

        # Budget-friendly flowers
        budget_flowers = [
            "carnation", "chrysanthemum", "daisy", "alstroemeria", "spray rose",
            "baby's breath", "statice", "aster", "mum"
        ]

        for premium in premium_flowers:
            if premium in flower_lower:
                return "premium"

        for budget in budget_flowers:
            if budget in flower_lower:
                return "budget"

        return "mid"

    def _fallback_candidate(self, ctx: PipelineContext = None) -> FlowerCandidate:
        """Create a context-aware fallback flower candidate."""
        import random

        # Diverse neutral fallbacks instead of always red_rose
        # Format: (flower_id, name, meanings, price_tier)
        NEUTRAL_FALLBACKS = [
            ("white_lily", "White Lily", ["Purity", "Elegance", "Devotion", "Renewal"], "mid"),
            ("pink_carnation", "Pink Carnation", ["Gratitude", "Admiration", "Warmth", "Affection"], "budget"),
            ("blue_hydrangea", "Blue Hydrangea", ["Understanding", "Gratitude", "Heartfelt emotions", "Apology"], "mid"),
            ("yellow_tulip", "Yellow Tulip", ["Hope", "Cheerfulness", "Friendship", "New beginnings"], "budget"),
            ("lavender", "Lavender", ["Serenity", "Grace", "Calmness", "Devotion"], "budget"),
        ]

        # Pick random neutral fallback as default
        default_choice = random.choice(NEUTRAL_FALLBACKS)
        fallback_flower = default_choice[0]
        fallback_name = default_choice[1]
        fallback_meanings = default_choice[2]
        fallback_price_tier = default_choice[3]
        fallback_reason = "Thoughtful and versatile choice"

        # Use context to pick appropriate fallback
        if ctx:
            # Check if romantic flowers are inappropriate
            romantic_ok = True
            if ctx.relationship and ctx.relationship.raw_output:
                appropriateness = ctx.relationship.raw_output.get("gift_appropriateness", {})
                romantic_ok = appropriateness.get("romantic_flowers_ok", True)

            # Use emotion to pick fallback
            if ctx.emotions:
                emotion = ctx.emotions.primary_emotion.lower()

                if emotion in ["remorse", "regret", "guilt", "shame", "contrition"]:
                    fallback_flower = "white_tulip"
                    fallback_name = "White Tulip"
                    fallback_meanings = ["Forgiveness", "New beginnings", "Sincerity", "Purity"]
                    fallback_price_tier = "budget"
                    fallback_reason = "Symbolizes forgiveness and fresh starts"
                elif emotion in ["gratitude", "appreciation", "thankfulness", "recognition"]:
                    fallback_flower = "pink_rose"
                    fallback_name = "Pink Rose"
                    fallback_meanings = ["Gratitude", "Appreciation", "Grace", "Admiration"]
                    fallback_price_tier = "mid"
                    fallback_reason = "Classic expression of gratitude"
                elif emotion in ["happiness", "joy", "excitement", "elation", "celebration"]:
                    fallback_flower = "gerbera_daisy"
                    fallback_name = "Gerbera Daisy"
                    fallback_meanings = ["Joy", "Cheerfulness", "Innocence", "Happiness"]
                    fallback_price_tier = "budget"
                    fallback_reason = "Bright and cheerful choice"
                elif emotion in ["sympathy", "compassion", "empathy", "grief", "comfort"]:
                    fallback_flower = "white_lily"
                    fallback_name = "White Lily"
                    fallback_meanings = ["Sympathy", "Peace", "Comfort", "Purity"]
                    fallback_price_tier = "mid"
                    fallback_reason = "Traditional sympathy flower"
                elif emotion in ["encouragement", "hope", "optimism", "support"]:
                    fallback_flower = "yellow_tulip"
                    fallback_name = "Yellow Tulip"
                    fallback_meanings = ["Hope", "Cheerfulness", "Friendship", "Encouragement"]
                    fallback_price_tier = "budget"
                    fallback_reason = "Uplifting and hopeful"
                elif not romantic_ok:
                    # Non-romantic default
                    fallback_flower = "pink_carnation"
                    fallback_name = "Pink Carnation"
                    fallback_meanings = ["Gratitude", "Admiration", "Remembrance", "Warmth"]
                    fallback_price_tier = "budget"
                    fallback_reason = "Appropriate for non-romantic relationships"

        return FlowerCandidate(
            flower_id=fallback_flower,
            name=fallback_name,
            match_score=0.70,
            match_reasons=[fallback_reason, "Context-based fallback"],
            meanings=fallback_meanings,
            price_tier=fallback_price_tier,
        )

    def _build_prompt(self, ctx: PipelineContext) -> str:
        """Build rich prompt from enhanced FIA/EIA/RIL context."""
        parts = [f"User's message: \"{ctx.user_input}\""]

        # Enhanced FIA data
        if ctx.intent:
            parts.append(f"Intent: {ctx.intent.primary_intent}")
            if ctx.intent.raw_output:
                occasion = ctx.intent.raw_output.get("occasion", "")
                recipient = ctx.intent.raw_output.get("recipient", "")
                if occasion and occasion != "general":
                    parts.append(f"Occasion: {occasion}")
                if recipient and recipient != "unspecified":
                    parts.append(f"Recipient: {recipient}")

                # Context flags from FIA v4
                flags = ctx.intent.raw_output.get("context_flags", {})
                if flags.get("is_first_gift"):
                    parts.append("⚠️ Note: This may be their FIRST flower gift to this person - choose something memorable but not overwhelming")
                if flags.get("is_making_amends"):
                    parts.append("⚠️ Note: User is trying to REPAIR the relationship - choose flowers symbolizing forgiveness/new beginnings")
                if flags.get("is_special_milestone"):
                    parts.append("⚠️ Note: This is a SIGNIFICANT life event - choose something special and meaningful")
                budget = flags.get("budget_hint")
                # Explicit budget_range takes precedence over inferred budget_hint
                if ctx.priors and ctx.priors.budget_range and ctx.priors.budget_range.lower() not in ["any", "unspecified"]:
                    pass  # Will be added in priors section below
                elif budget and budget != "unspecified":
                    parts.append(f"Budget hint: {budget}")

        if ctx.priors:
            if ctx.priors.occasion:
                parts.append(f"Prior occasion: {ctx.priors.occasion}")
            if ctx.priors.relationship_type:
                parts.append(f"Prior relationship: {ctx.priors.relationship_type}")
            # Add budget constraint to prompt
            if ctx.priors.budget_range and ctx.priors.budget_range.lower() not in ["any", "unspecified"]:
                parts.append(f"Budget preference: {ctx.priors.budget_range}")

        # Enhanced EIA data
        if ctx.emotions:
            parts.append(f"Primary emotion: {ctx.emotions.primary_emotion}")
            parts.append(f"Emotional intensity: {ctx.emotions.emotion_intensity:.2f}")
            if ctx.emotions.emotional_tone:
                parts.append(f"Emotional tone: {ctx.emotions.emotional_tone}")
            if ctx.emotions.secondary_emotions:
                parts.append(f"Secondary emotions: {', '.join(ctx.emotions.secondary_emotions)}")

            # Complexity markers from EIA v4
            if ctx.emotions.raw_output:
                complexity = ctx.emotions.raw_output.get("complexity", {})
                if complexity.get("has_mixed_emotions"):
                    parts.append("⚠️ Note: User has MIXED EMOTIONS - consider nuanced choices that acknowledge complexity")
                subtext = ctx.emotions.raw_output.get("emotional_subtext")
                if subtext:
                    parts.append(f"Emotional subtext: {subtext}")

        # Enhanced RIL data
        if ctx.relationship:
            parts.append(f"Relationship type: {ctx.relationship.relationship_type}")
            parts.append(f"Intimacy level: {ctx.relationship.intimacy_level:.2f}")
            parts.append(f"Formality level: {ctx.relationship.formality_level:.2f}")
            if ctx.relationship.power_dynamic != "equal":
                parts.append(f"Power dynamic: {ctx.relationship.power_dynamic}")

            # Gift appropriateness from RIL v3
            if ctx.relationship.raw_output:
                appropriateness = ctx.relationship.raw_output.get("gift_appropriateness", {})
                max_intensity = appropriateness.get("max_intensity", 1.0)
                if max_intensity < 0.7:
                    parts.append(f"⚠️ CAUTION: Keep flowers UNDERSTATED (max intensity: {max_intensity:.1f})")
                romantic_ok = appropriateness.get("romantic_flowers_ok", True)
                if not romantic_ok:
                    parts.append("⚠️ CAUTION: Avoid romantic flowers (red roses, etc.) - inappropriate for this relationship")
                avoid = appropriateness.get("avoid_flowers", [])
                if avoid:
                    parts.append(f"⚠️ AVOID these flowers: {', '.join(avoid)}")
                cultural = appropriateness.get("cultural_considerations")
                if cultural and cultural != "None" and cultural != "None specific":
                    parts.append(f"Cultural note: {cultural}")

        parts.append(f"Region: {ctx.region.upper()}")

        return "\n".join(parts)

    def _fallback_recommendation(self, ctx: PipelineContext) -> None:
        """Context-aware fallback when AI fails."""
        fallback = self._fallback_candidate(ctx)

        ctx.candidates = CandidatesData(
            candidates=[fallback],
            total_considered=1,
            ranking_criteria=["fallback_contextual"],
            raw_output={"fallback": True, "fallback_type": "context_aware"},
        )

    def _calculate_budget_multiplier(self, flower_tier: Optional[str], user_budget: str) -> float:
        """
        Calculate score multiplier based on budget match.

        Returns:
            1.2 for exact match (boost)
            1.0 for adjacent tier or unknown
            0.7 for opposite tier (penalty)
        """
        if not flower_tier or not user_budget:
            return 1.0

        user_budget_lower = user_budget.lower()

        # Skip non-constraints
        if user_budget_lower in ["any", "unspecified", "mid", "standard"]:
            return 1.0

        # Map user budget to tier
        user_tier = self._parse_budget_to_tier(user_budget_lower)
        if not user_tier:
            return 1.0  # Unknown format, no adjustment

        # Calculate multiplier
        if flower_tier == user_tier:
            return 1.2  # Exact match: boost
        elif (flower_tier == "budget" and user_tier == "premium") or \
             (flower_tier == "premium" and user_tier == "budget"):
            return 0.7  # Opposite tier: penalty
        else:
            return 1.0  # Adjacent tier (mid): neutral

    def _parse_budget_to_tier(self, budget_str: str) -> Optional[str]:
        """
        Parse budget string to tier. Delegates to central normalize_budget().
        Kept for backward compatibility and FIA budget_hint normalization.
        """
        return normalize_budget(budget_str)
