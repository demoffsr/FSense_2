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
        """Assess risks and fit for recommendations with AI analysis."""
        try:
            # Get flower name
            flower_name = "unknown"
            if ctx.candidates and ctx.candidates.candidates:
                flower_name = ctx.candidates.candidates[0].name

            # Use AI for comprehensive risk assessment
            result = self._assess_with_ai(ctx, flower_name)

            # Parse AI response
            overall_risk = result.get("overall_risk_level", "low")
            fit_assessment = result.get("fit_assessment", "Good fit for the context")
            confidence = result.get("confidence", 0.85)

            # Convert risks to RiskItem objects
            risks_list = []
            for risk_data in result.get("risks", []):
                risks_list.append(RiskItem(
                    risk_type=risk_data.get("risk_type", "general"),
                    severity=risk_data.get("severity", "low"),
                    description=risk_data.get("description", ""),
                    mitigation=risk_data.get("mitigation", ""),
                ))

            ctx.risks = RisksData(
                overall_risk_level=overall_risk,
                risks=risks_list,
                fit_assessment=fit_assessment,
                raw_output={
                    "confidence": confidence,
                    "risk_count": len(risks_list),
                },
            )

            risk_emoji = "⚠️" if overall_risk in ("medium", "high") else "✅"
            logger.info(f"RFFA {risk_emoji} overall risk: {overall_risk}, {len(risks_list)} risks identified (AI)")

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
                "Confidence": f"{confidence:.2f}",
            })

        except AIClientError as e:
            logger.error(f"RFFA AI error: {e}")
            ctx.add_error(f"RFFA: {str(e)}")
            self._fallback_risks(ctx)

        except Exception as e:
            logger.error(f"RFFA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"RFFA: Unexpected error")
            self._fallback_risks(ctx)

    def _assess_with_ai(self, ctx: PipelineContext, flower_name: str) -> dict:
        """Use AI to assess risks and fit."""
        try:
            client = get_ai_client_fast()

            # Build context summary
            emotion_summary = ""
            if ctx.emotions:
                emotion_summary = f"Emotion: {ctx.emotions.primary_emotion}, tone: {ctx.emotions.emotional_tone}"

            intensity_summary = ""
            if ctx.intensity:
                intensity_summary = f"Intensity: {ctx.intensity.intensity_label} ({ctx.intensity.mood_intensity:.2f})"

            relationship_summary = ""
            if ctx.relationship:
                rel_data = ctx.relationship.raw_output
                relationship_summary = f"Relationship: {ctx.relationship.relationship_type}, stage: {rel_data.get('relationship_stage', 'unknown')}, intimacy: {ctx.relationship.intimacy_level:.2f}"

            intent_summary = ""
            if ctx.intent:
                intent_data = ctx.intent.raw_output
                intent_summary = f"Intent: {ctx.intent.primary_intent}, occasion: {intent_data.get('occasion', 'unknown')}"

            prompt = f"""Context:
- User message: "{ctx.user_input}"
- Recommended flower: {flower_name}
- Region: {ctx.region.upper()}
- {emotion_summary}
- {intensity_summary}
- {relationship_summary}
- {intent_summary}

Assess potential risks and fit for this flower recommendation."""

            response = client.complete_json(
                prompt=prompt,
                system_prompt=RISK_ASSESSMENT_PROMPT,
                temperature=0.3,
            )

            return response

        except Exception as e:
            logger.warning(f"RFFA AI assessment failed, using fallback: {e}")
            # Fallback response
            return {
                "overall_risk_level": "low",
                "fit_assessment": "Basic assessment (fallback)",
                "confidence": 0.6,
                "risks": [],
            }

    def _fallback_risks(self, ctx: PipelineContext) -> None:
        """Comprehensive heuristic risk assessment when AI fails."""
        risks_list = []

        # 1. Intensity mismatch with relationship stage
        if ctx.relationship and ctx.intensity:
            rel_data = ctx.relationship.raw_output or {}
            stage = rel_data.get("relationship_stage", "established")
            intensity = ctx.intensity.mood_intensity

            if stage in ("new", "early", "developing") and intensity > 0.7:
                risks_list.append(RiskItem(
                    risk_type="intensity_mismatch",
                    severity="medium",
                    description="High emotional intensity may be too bold for early relationship stage",
                    mitigation="Consider softer colors or more subtle varieties",
                ))

        # 2. Relationship inappropriateness (romantic flowers for professional)
        if ctx.relationship and ctx.candidates and ctx.candidates.candidates:
            r_type = ctx.relationship.relationship_type
            flower_name = ctx.candidates.candidates[0].name.lower()

            if r_type == "professional":
                # Check for romantic flowers
                romantic_flowers = ["red rose", "red roses", "passion"]
                if any(rf in flower_name for rf in romantic_flowers):
                    risks_list.append(RiskItem(
                        risk_type="relationship_inappropriate",
                        severity="high",
                        description="Red roses are inappropriate for professional relationships",
                        mitigation="Choose neutral flowers like orchids, lilies, or mixed arrangements",
                    ))

        # 3. Emotional alignment (flower meanings vs emotion)
        if ctx.emotions and ctx.candidates and ctx.candidates.candidates:
            emotion = ctx.emotions.primary_emotion.lower()
            meanings = " ".join(ctx.candidates.candidates[0].meanings).lower()

            # Check for mismatch: somber emotion + joyful meanings
            somber_emotions = ["sympathy", "grief", "compassion", "sadness", "melancholy"]
            if emotion in somber_emotions and any(word in meanings for word in ["joy", "excitement", "celebration", "cheer"]):
                risks_list.append(RiskItem(
                    risk_type="emotional_alignment",
                    severity="medium",
                    description="Flower meanings may not match the somber emotional context",
                    mitigation="Consider white lilies, chrysanthemums, or other sympathy flowers",
                ))

        # 4. Cultural concerns (white flowers in Asian cultures)
        if ctx.region and ctx.candidates and ctx.candidates.candidates:
            flower_name = ctx.candidates.candidates[0].name.lower()
            region = ctx.region.lower()

            if region in ["cn", "jp", "kr", "tw", "vn"]:
                if "white" in flower_name:
                    # Check if it's for sympathy (then it's OK)
                    occasion = ""
                    if ctx.intent and ctx.intent.raw_output:
                        occasion = ctx.intent.raw_output.get("occasion", "")

                    if occasion not in ["sympathy", "funeral", "memorial"]:
                        risks_list.append(RiskItem(
                            risk_type="cultural_concern",
                            severity="medium",
                            description="White flowers may symbolize death or mourning in Asian cultures",
                            mitigation="Consider pink, red, or yellow flowers for celebratory occasions",
                        ))

        # Determine overall risk level
        if any(r.severity == "high" for r in risks_list):
            overall_risk = "high"
        elif any(r.severity == "medium" for r in risks_list):
            overall_risk = "medium"
        else:
            overall_risk = "low"

        ctx.risks = RisksData(
            overall_risk_level=overall_risk,
            risks=risks_list,
            fit_assessment="Needs review" if risks_list else "Good fit (heuristic assessment)",
            raw_output={"fallback": True, "checked_categories": 4},
        )
