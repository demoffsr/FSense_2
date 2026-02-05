"""
CRI Adapter - Cultural & Regional Intelligence - v2.1 (DB-Enhanced)

Purpose:
Provides cultural context and regional interpretations for the recommended flower.
Analyzes traditional and modern symbolism specific to the user's region.
Uses flower database for cultural context and taboos.

Based on: cultural_reasoning_intelligence_v2.py
"""

import logging
import os
from typing import List, Optional

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    CulturalData,
    CulturalInsight,
)
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger
from backend.services.flower_knowledge_base import FlowerKnowledgeBase

logger = logging.getLogger(__name__)

# Import flower database functions
try:
    from backend.database.flower_database import (
        get_cultural_warnings,
        get_number_rules,
        get_flower_by_id,
        CULTURAL_CONTEXTS_DATA,
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("Flower database not available for CRI, using heuristics only")

# Feature flag for FlowerKnowledgeBase resolution (rollback safety)
CRI_USE_KNOWLEDGE_BASE = os.getenv("CRI_USE_KNOWLEDGE_BASE", "true").lower() == "true"

CULTURAL_ANALYSIS_PROMPT = """You are CRI v2 — Cultural Reasoning Intelligence for FSense.
Analyze flowers from the perspective of regional traditions and modern culture.
Output STRICT JSON only.

For the given flower and region, analyze:
- Traditional meaning in this culture
- Modern perception and usage
- Cultural risk level (low/medium/high)
- Risk reasoning (funeral association, wrong occasion, taboos, etc.)
- Confidence in this analysis (0.0-1.0)
- Advice if there are risks

Also provide insights for major cultures to enrich understanding:
- Primary culture (user's region)
- 2-3 other major cultures for comparison

Return JSON:
{
  "primary_region": "RU",
  "traditional_symbolism": "In Russia, traditionally associated with...",
  "modern_symbolism": "Modern Russians view this as...",
  "risk_level": "low",
  "risk_reasoning": "No major cultural issues",
  "confidence": 0.85,
  "advice": null,
  "cross_cultural_insights": [
    {
      "culture": "Russia",
      "emoji": "🇷🇺",
      "interpretation": "Symbol of romantic love and passion",
      "sentiment": "positive"
    },
    {
      "culture": "Japan",
      "emoji": "🇯🇵",
      "interpretation": "Associated with quiet respect",
      "sentiment": "neutral"
    }
  ],
  "warnings": []
}"""


class CRIAdapter(BaseAgent):
    """Cultural & Regional Intelligence - analyzes cultural meanings."""

    name = "CRI"

    def run(self, ctx: PipelineContext) -> None:
        """Generate cultural insights for recommendations (heuristic-only for speed)."""
        try:
            # Get flower name
            flower_name = "unknown"
            if ctx.candidates and ctx.candidates.candidates:
                flower_name = ctx.candidates.candidates[0].name

            region = ctx.region.upper()

            # Check database for warnings first
            warnings = self._check_cultural_warnings(flower_name, region, ctx)

            # Use AI for cultural analysis with database context
            result = self._analyze_with_ai(ctx, flower_name, region, warnings)

            insights_list = result.get("insights", self._generate_cultural_insights(flower_name, region))
            traditional = result.get("traditional_symbolism", "")
            modern = result.get("modern_symbolism", "")

            # Get number rules from database if available
            number_advice = None
            if DATABASE_AVAILABLE:
                number_rules = get_number_rules(region.lower())
                if number_rules:
                    even_rule = number_rules.get("even_number_rule", "")
                    odd_rule = number_rules.get("odd_number_rule", "")
                    if even_rule or odd_rule:
                        number_advice = f"Number rules: {even_rule or odd_rule}"

            risk_level = "medium" if warnings else "low"

            ctx.cultural_insights = CulturalData(
                detected_region=region,
                cultural_insights=insights_list,
                warnings=warnings,
                raw_output={
                    "traditional_symbolism": traditional,
                    "modern_symbolism": modern,
                    "risk_level": risk_level,
                    "confidence": 0.75,
                    "advice": number_advice,
                },
            )

            logger.info(f"CRI analyzed {flower_name} for {region}: {len(insights_list)} insights, {len(warnings)} warnings")

            # Console output
            console = get_console_logger()
            cultures = [f"{i.emoji} {i.culture}" for i in insights_list[:3]]
            cultural_raw = ctx.cultural_insights.raw_output

            console.agent_result("CRI", {
                "Primary Region": region,
                "Risk Level": risk_level,
                "Traditional Symbolism": traditional[:60] + "..." if traditional else "N/A",
                "Cultural Insights": cultures,
                "Warnings": warnings if warnings else "None",
            })

        except AIClientError as e:
            logger.error(f"CRI AI error: {e}")
            ctx.add_error(f"CRI: {str(e)}")
            self._fallback_cultural(ctx)

        except Exception as e:
            logger.error(f"CRI unexpected error: {e}", exc_info=True)
            ctx.add_error(f"CRI: Unexpected error")
            self._fallback_cultural(ctx)

    def _generate_cultural_insights(self, flower_name: str, region: str) -> List[CulturalInsight]:
        """Generate cultural insights based on heuristics."""
        flower_lower = flower_name.lower()
        insights = []

        # Universal insight
        insights.append(CulturalInsight(
            culture="Universal",
            emoji="🌍",
            interpretation=f"{flower_name} is widely recognized as a symbol of beauty and emotion",
            sentiment="positive",
        ))

        # Region-specific insights
        if region == "US":
            insights.append(CulturalInsight(
                culture="Western",
                emoji="🇺🇸",
                interpretation=f"{flower_name} is popular for expressing romantic feelings and appreciation",
                sentiment="positive",
            ))
        elif region == "RU":
            insights.append(CulturalInsight(
                culture="Russia",
                emoji="🇷🇺",
                interpretation=f"{flower_name} carries deep symbolic meaning in Russian culture",
                sentiment="positive" if "rose" not in flower_lower else "neutral",
            ))
        elif region == "JP":
            insights.append(CulturalInsight(
                culture="Japan",
                emoji="🇯🇵",
                interpretation=f"{flower_name} is appreciated for its delicate beauty",
                sentiment="positive",
            ))

        return insights[:3]

    def _check_cultural_warnings(self, flower_name: str, region: str, ctx: PipelineContext) -> List[str]:
        """Check for cultural warnings - uses database if available, combines with heuristics."""
        # Handle None region early
        if not region:
            return self._check_heuristic_warnings(flower_name, "")

        warnings = []
        db_warnings_found = False

        # Try database first
        if DATABASE_AVAILABLE:
            # Resolve flower_id using 3-tier strategy
            flower_id = self._resolve_flower_id(flower_name, ctx)

            if flower_id:
                # Check database for cultural warnings
                db_warning = get_cultural_warnings(flower_id, region.lower())
                if db_warning and db_warning.get("is_taboo"):
                    db_warnings_found = True
                    if db_warning.get("taboo_reason"):
                        warnings.append(db_warning["taboo_reason"])

                    # Add occasion-specific warnings
                    if db_warning.get("taboo_occasions"):
                        occasions = ", ".join(db_warning["taboo_occasions"])
                        warnings.append(f"Avoid for: {occasions}")

                if db_warnings_found:
                    logger.debug(f"CRI: Found cultural warnings in database for {flower_id} in {region}")

        # ALWAYS check heuristics (combine with DB warnings, don't skip)
        heuristic_warnings = self._check_heuristic_warnings(flower_name, region)

        # Deduplicate while preserving order
        seen = set(w.lower() for w in warnings)
        for hw in heuristic_warnings:
            if hw.lower() not in seen:
                warnings.append(hw)
                seen.add(hw.lower())

        return warnings

    def _analyze_with_ai(self, ctx: PipelineContext, flower_name: str, region: str, db_warnings: List[str]) -> dict:
        """Use AI for cultural analysis with database warnings as context."""
        try:
            client = get_ai_client_fast()

            warnings_context = ""
            if db_warnings:
                warnings_context = f"\nDatabase warnings: {', '.join(db_warnings)}"

            # Build rich context from previous agents
            flower_meanings = "N/A"
            if ctx.candidates and ctx.candidates.candidates:
                meanings_list = ctx.candidates.candidates[0].meanings
                if meanings_list:
                    flower_meanings = ", ".join(meanings_list[:5])

            occasion = "N/A"
            recipient = "N/A"
            is_making_amends = False
            if ctx.intent and ctx.intent.raw_output:
                occasion = ctx.intent.raw_output.get("occasion", "N/A")
                recipient = ctx.intent.raw_output.get("recipient", "N/A")
                context_flags = ctx.intent.raw_output.get("context_flags", {})
                is_making_amends = context_flags.get("is_making_amends", False)

            relationship_type = "N/A"
            if ctx.relationship:
                relationship_type = ctx.relationship.relationship_type

            emotion_intensity = "N/A"
            if ctx.emotions:
                emotion_intensity = f"{ctx.emotions.emotion_intensity:.2f}"

            prompt = f"""Analyze the cultural symbolism of {flower_name} for {region} region.

Flower Meanings: {flower_meanings}

Context:
- User message: "{ctx.user_input}"
- Occasion: {occasion}
- Recipient: {recipient}
- Relationship: {relationship_type}
- Emotional intensity: {emotion_intensity}
- Is making amends: {is_making_amends}
{warnings_context}

Provide traditional and modern symbolism considering the full context above.
Pay special attention to whether this flower is appropriate for:
1. The specific occasion (e.g., apology flowers should convey sincerity)
2. The relationship type (e.g., professional contexts need neutral flowers)
3. Any regional taboos or associations that might conflict with the intent"""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=CULTURAL_ANALYSIS_PROMPT,
                temperature=0.4,
            )

            # Parse insights from AI response
            insights = []
            for insight_data in response.get("cross_cultural_insights", []):
                insights.append(CulturalInsight(
                    culture=insight_data.get("culture", "Unknown"),
                    emoji=insight_data.get("emoji", "🌍"),
                    interpretation=insight_data.get("interpretation", ""),
                    sentiment=insight_data.get("sentiment", "neutral"),
                ))

            return {
                "traditional_symbolism": response.get("traditional_symbolism", ""),
                "modern_symbolism": response.get("modern_symbolism", ""),
                "insights": insights[:3],
            }

        except Exception as e:
            logger.warning(f"CRI AI analysis failed, using heuristics: {e}")
            # Fallback to heuristics
            traditional, modern = self._get_symbolism(flower_name, region)
            return {
                "traditional_symbolism": traditional,
                "modern_symbolism": modern,
                "insights": [],
            }

    def _get_symbolism(self, flower_name: str, region: str) -> tuple[str, str]:
        """Get traditional and modern symbolism."""
        flower_lower = flower_name.lower()

        # Default symbolism
        traditional = f"{flower_name} has been a symbol of emotion and beauty for centuries"
        modern = f"Today, {flower_name} remains a popular choice for expressing feelings"

        if "rose" in flower_lower:
            if "red" in flower_lower:
                traditional = "Red roses have symbolized romantic love since ancient times"
                modern = "Today, red roses remain the ultimate symbol of passionate love"
            elif "white" in flower_lower:
                traditional = "White roses traditionally symbolize purity and innocence"
                modern = "Modern interpretations include new beginnings and remembrance"
            elif "pink" in flower_lower:
                traditional = "Pink roses have long represented grace and gratitude"
                modern = "Pink roses are now associated with admiration and appreciation"
        elif "lily" in flower_lower:
            traditional = "Lilies have symbolized purity and rebirth across many cultures"
            modern = "Modern use includes sympathy, devotion, and celebration"
        elif "tulip" in flower_lower:
            traditional = "Tulips originated as symbols of paradise in Persian culture"
            modern = "Today, tulips represent perfect love and spring renewal"

        return (traditional, modern)

    def _fallback_cultural(self, ctx: PipelineContext) -> None:
        """Provide fallback cultural data when AI fails."""
        # Generic positive insights
        mock_insights = [
            CulturalInsight(
                culture="Universal",
                emoji="🌍",
                interpretation="Generally positive symbolism across cultures",
                sentiment="positive",
            ),
        ]

        ctx.cultural_insights = CulturalData(
            detected_region=ctx.region.upper(),
            cultural_insights=mock_insights,
            warnings=[],
            raw_output={"fallback": True},
        )

    def _resolve_flower_id(self, flower_name: str, ctx: PipelineContext) -> Optional[str]:
        """
        Resolve flower name to database ID using 3-tier strategy:
        1. Match flower_name against candidate names (case-insensitive)
        2. Use FlowerKnowledgeBase.resolve_flower_id()
        3. Return None (caller should use heuristics)

        Args:
            flower_name: Display name of the flower (e.g., "Red Rose")
            ctx: Pipeline context with candidates

        Returns:
            Resolved flower_id or None if unresolved
        """
        flower_name_lower = flower_name.lower().strip()

        # Tier 1: Match flower_name against ALL candidates (not just [0])
        if ctx.candidates and ctx.candidates.candidates:
            for candidate in ctx.candidates.candidates:
                if candidate.name and candidate.name.lower().strip() == flower_name_lower:
                    if candidate.flower_id and candidate.flower_id != "unknown":
                        logger.debug(f"CRI: Matched '{flower_name}' to candidate flower_id: {candidate.flower_id}")
                        return candidate.flower_id

        # Tier 2: Try FlowerKnowledgeBase resolution (if enabled)
        if CRI_USE_KNOWLEDGE_BASE:
            try:
                resolved_id = FlowerKnowledgeBase.resolve_flower_id(flower_name)
                if resolved_id:
                    logger.debug(f"CRI: Resolved '{flower_name}' to '{resolved_id}' via FlowerKnowledgeBase")
                    return resolved_id
            except Exception as e:
                logger.warning(f"CRI: FlowerKnowledgeBase.resolve_flower_id failed: {e}")

        # Tier 3: Could not resolve
        logger.debug(f"CRI: Could not resolve flower_id for '{flower_name}', will use heuristics")
        return None

    def _check_heuristic_warnings(self, flower_name: str, region: str) -> List[str]:
        """Generate cultural warnings based on heuristics (color/type patterns)."""
        warnings = []
        flower_lower = flower_name.lower()

        # Yellow flowers in some cultures
        if "yellow" in flower_lower and region in ("RU",):
            warnings.append("Yellow flowers may be associated with separation in Russian culture")

        # White flowers and funerals
        if "white" in flower_lower and region in ("JP", "CN"):
            warnings.append("White flowers are often associated with funerals in East Asian cultures")

        # Chrysanthemums
        if "chrysanthemum" in flower_lower and region in ("EU", "IT", "FR"):
            warnings.append("Chrysanthemums are associated with funerals in many European countries")

        return warnings
