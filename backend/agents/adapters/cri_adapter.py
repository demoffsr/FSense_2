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
from backend.core.ai_client import get_ai_client, AIClientError

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
        """Generate cultural insights for recommendations."""
        try:
            client = get_ai_client()

            # Get flower name
            flower_name = "unknown"
            if ctx.candidates and ctx.candidates.candidates:
                flower_name = ctx.candidates.candidates[0].name

            # Build context
            intent_summary = ""
            if ctx.intent:
                intent_data = ctx.intent.raw_output
                occasion = intent_data.get("occasion", "general")
                recipient = intent_data.get("recipient", "unspecified")
                intent_summary = f"Occasion: {occasion}, Recipient: {recipient}"

            prompt = f"""Flower: {flower_name}
Region: {ctx.region.upper()}
{intent_summary}

User message: "{ctx.user_input}"

Analyze the cultural meanings and appropriateness of this flower in the regional context."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=CULTURAL_ANALYSIS_PROMPT,
                temperature=0.3,
            )

            # Parse insights
            insights_list: List[CulturalInsight] = []
            for insight_data in response.get("cross_cultural_insights", []):
                insight = CulturalInsight(
                    culture=insight_data.get("culture", "Unknown"),
                    emoji=insight_data.get("emoji", "🌍"),
                    interpretation=insight_data.get("interpretation", ""),
                    sentiment=insight_data.get("sentiment", "neutral"),
                )
                insights_list.append(insight)

            # Parse warnings
            warnings = response.get("warnings", [])
            risk_level = response.get("risk_level", "low")
            if risk_level in ("medium", "high"):
                risk_reasoning = response.get("risk_reasoning", "")
                if risk_reasoning and risk_reasoning not in warnings:
                    warnings.append(risk_reasoning)

            ctx.cultural_insights = CulturalData(
                detected_region=response.get("primary_region", ctx.region.upper()),
                cultural_insights=insights_list,
                warnings=warnings,
                raw_output={
                    "traditional_symbolism": response.get("traditional_symbolism", ""),
                    "modern_symbolism": response.get("modern_symbolism", ""),
                    "risk_level": risk_level,
                    "confidence": response.get("confidence", 0.75),
                    "advice": response.get("advice"),
                },
            )

            logger.info(f"CRI analyzed {flower_name} for {ctx.region.upper()}: {len(insights_list)} insights, {len(warnings)} warnings")

        except AIClientError as e:
            logger.error(f"CRI AI error: {e}")
            ctx.add_error(f"CRI: {str(e)}")
            self._fallback_cultural(ctx)

        except Exception as e:
            logger.error(f"CRI unexpected error: {e}", exc_info=True)
            ctx.add_error(f"CRI: Unexpected error")
            self._fallback_cultural(ctx)

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
