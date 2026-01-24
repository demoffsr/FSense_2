"""
CRI Adapter - Cultural & Regional Intelligence - v2 (Adapted)

Purpose:
Provides cultural context and regional interpretations for the recommended flower.
Analyzes traditional and modern symbolism specific to the user's region.

Based on: cultural_reasoning_intelligence_v2.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    CulturalData,
    CulturalInsight,
)
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

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

            # Heuristic-based cultural insights (no AI call for speed)
            insights_list = self._generate_cultural_insights(flower_name, region)
            warnings = self._check_cultural_warnings(flower_name, region)
            traditional, modern = self._get_symbolism(flower_name, region)

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
                    "advice": None,
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

    def _check_cultural_warnings(self, flower_name: str, region: str) -> List[str]:
        """Check for cultural warnings."""
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
