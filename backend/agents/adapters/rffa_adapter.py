"""
RFFA Adapter - Risk & Fit Assessment Agent - v4 (Adapted)

Purpose:
Assesses potential risks and fit levels for the flower recommendation
in the given context. Identifies relationship, emotional, and timing risks.

Based on: red_flag_filter_agent_v4.py
"""

import logging
from typing import List

from backend.agents.base import BaseAgent
from backend.pipeline.context import PipelineContext, RisksData, RiskItem
from backend.core.ai_client import get_ai_client_fast, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

RISK_ASSESSMENT_PROMPT = """You are RFFA v4 (Risk & Fit Assessment Agent) for FSense.
Analyze the context and identify potential risks or concerns with the flower recommendation.
Output STRICT JSON only.

Consider these risk categories:
1. Relationship appropriateness (is the flower too bold/subtle for the relationship stage?)
2. Emotional alignment (does the flower match the emotional context?)
3. Timing sensitivity (is this appropriate for the occasion?)
4. Intensity mismatch (is the intensity too high/low?)
5. Cultural concerns (will be addressed by CRI separately)

For each identified risk, provide:
- risk_type: category of risk
- severity: "low" | "medium" | "high"
- description: what the concern is
- mitigation: how to address it

Also provide:
- overall_risk_level: "low" | "medium" | "high"
- fit_assessment: brief assessment of overall fit
- confidence: 0.0-1.0

Return JSON:
{
  "overall_risk_level": "low",
  "fit_assessment": "Excellent fit for the context",
  "confidence": 0.88,
  "risks": [
    {
      "risk_type": "intensity_mismatch",
      "severity": "low",
      "description": "Intensity is slightly high for early relationship",
      "mitigation": "Consider softer colors or fewer stems"
    }
  ]
}"""


class RFFAAdapter(BaseAgent):
    """Risk & Fit Assessment Agent - identifies contextual risks."""

    name = "RFFA"

    def run(self, ctx: PipelineContext) -> None:
        """Assess risks and fit for recommendations (heuristic-only for speed)."""
        try:
            # Get flower name
            flower_name = "unknown"
            if ctx.candidates and ctx.candidates.candidates:
                flower_name = ctx.candidates.candidates[0].name

            # Heuristic-based risk assessment (no AI call for speed)
            risks_list = []
            fit_assessment = "Good fit for the context"

            # Check for intensity mismatch with relationship stage
            if ctx.relationship and ctx.intensity:
                rel_data = ctx.relationship.raw_output
                stage = rel_data.get("relationship_stage", "established")
                intensity = ctx.intensity.mood_intensity

                if stage in ("new", "early") and intensity > 0.7:
                    risks_list.append(RiskItem(
                        risk_type="intensity_mismatch",
                        severity="medium",
                        description="High intensity may be too bold for early relationship stage",
                        mitigation="Consider softer colors or more subtle varieties",
                    ))

                if stage in ("new", "early") and flower_name.lower() in ("red rose", "rose"):
                    risks_list.append(RiskItem(
                        risk_type="relationship_appropriateness",
                        severity="low",
                        description="Red roses may be too romantic for early relationships",
                        mitigation="Consider pink or white roses instead",
                    ))

            # Check emotional alignment
            if ctx.emotions:
                if ctx.emotions.primary_emotion.lower() in ("sadness", "grief", "mourning"):
                    if flower_name.lower() in ("red rose", "rose"):
                        risks_list.append(RiskItem(
                            risk_type="emotional_alignment",
                            severity="medium",
                            description="Red roses may not align with somber emotions",
                            mitigation="Consider white lilies or white roses",
                        ))

            overall_risk = "medium" if len(risks_list) > 0 else "low"
            if len(risks_list) > 2:
                overall_risk = "high"
                fit_assessment = "Some concerns with the recommendation"
            elif len(risks_list) > 0:
                fit_assessment = "Generally good fit with minor considerations"

            ctx.risks = RisksData(
                overall_risk_level=overall_risk,
                risks=risks_list,
                fit_assessment=fit_assessment,
                raw_output={
                    "confidence": 0.75,
                    "risk_count": len(risks_list),
                },
            )

            risk_emoji = "⚠️" if overall_risk in ("medium", "high") else "✅"
            logger.info(f"RFFA {risk_emoji} overall risk: {overall_risk}, {len(risks_list)} risks identified")

            # Console output
            console = get_console_logger()
            risk_details = []
            for risk in risks_list[:3]:
                risk_details.append(f"{risk.risk_type} ({risk.severity})")

            console.agent_result("RFFA", {
                "Overall Risk Level": overall_risk,
                "Fit Assessment": fit_assessment,
                "Risks Identified": len(risks_list),
                "Risk Details": risk_details if risk_details else "None",
                "Confidence": "0.75",
            })

        except AIClientError as e:
            logger.error(f"RFFA AI error: {e}")
            ctx.add_error(f"RFFA: {str(e)}")
            self._fallback_risks(ctx)

        except Exception as e:
            logger.error(f"RFFA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"RFFA: Unexpected error")
            self._fallback_risks(ctx)

    def _fallback_risks(self, ctx: PipelineContext) -> None:
        """Provide fallback risk assessment when AI fails."""
        # Simple heuristic: check for obvious mismatches
        risks_list = []

        if ctx.relationship and ctx.intensity:
            # Check for intensity mismatch with relationship stage
            rel_data = ctx.relationship.raw_output
            stage = rel_data.get("relationship_stage", "established")
            intensity = ctx.intensity.mood_intensity

            if stage in ("new", "early") and intensity > 0.7:
                risks_list.append(RiskItem(
                    risk_type="intensity_mismatch",
                    severity="medium",
                    description="High intensity may be too bold for early relationship stage",
                    mitigation="Consider softer colors or more subtle varieties",
                ))

        overall_risk = "medium" if risks_list else "low"

        ctx.risks = RisksData(
            overall_risk_level=overall_risk,
            risks=risks_list,
            fit_assessment="Basic assessment (fallback mode)",
            raw_output={"fallback": True},
        )
