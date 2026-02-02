"""
VIA Adapter - Vision Image Analyzer - v1.0

Purpose:
Analyzes user-uploaded bouquet images using GPT-4 Vision.
Identifies the main flower and secondary flowers in the image.
Sets needs_clarification if the main flower cannot be determined.

Position in pipeline: FIRST (before FIA), only runs if image_base64 is present.
"""

import logging
from typing import Any, Optional

from backend.agents.base import BaseAgent
from backend.pipeline.context import (
    PipelineContext,
    VisionAnalysisData,
    DetectedFlower,
)
from backend.core.ai_client import get_ai_client, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

VISION_ANALYSIS_PROMPT = """You are an expert florist analyzing a flower bouquet image.

Your task:
1. Identify the MAIN/DOMINANT flower in the image (the most prominent one)
2. Identify any SECONDARY flowers present
3. Describe the overall bouquet composition

Rules for main_flower identification:
- Pick the single most prominent flower
- Include color if clearly visible (e.g., "Red Rose", "White Lily")
- Set confidence between 0.0-1.0 based on how certain you are
- If confidence < 0.7, or if there are multiple equally prominent flowers, set needs_clarification: true

Return JSON with this exact structure:
{
    "main_flower": {
        "name": "Red Rose",
        "color": "red",
        "confidence": 0.95
    },
    "secondary_flowers": [
        {"name": "Baby's Breath", "color": "white", "confidence": 0.9},
        {"name": "Eucalyptus", "color": "green", "confidence": 0.85}
    ],
    "bouquet_description": "A romantic bouquet featuring red roses as the centerpiece...",
    "needs_clarification": false,
    "clarification_message": ""
}

If you cannot determine the main flower:
{
    "main_flower": null,
    "secondary_flowers": [...],
    "bouquet_description": "...",
    "needs_clarification": true,
    "clarification_message": "I see multiple flowers that could be the main one. Which flower would you like information about: Red Rose, Pink Lily, or White Carnation?"
}"""


class VIAAdapter(BaseAgent):
    """Vision Image Analyzer - analyzes bouquet photos."""

    name = "VIA"

    def _safe_parse_confidence(self, value: Any) -> float:
        """Safely parse confidence value to float in range [0.0, 1.0]."""
        try:
            conf = float(value)
            # Clamp to valid range
            return max(0.0, min(1.0, conf))
        except (TypeError, ValueError):
            return 0.0

    def _parse_detected_flower(self, data: Any) -> Optional[DetectedFlower]:
        """Parse and validate flower data from Vision API response.

        Returns None if data is invalid (missing name, wrong type, etc.)
        """
        if not isinstance(data, dict):
            return None

        name = data.get("name", "")
        if not name or not isinstance(name, str):
            return None

        name = name.strip()
        if not name:
            return None

        color = data.get("color")
        return DetectedFlower(
            name=name,
            color=color if isinstance(color, str) else None,
            confidence=self._safe_parse_confidence(data.get("confidence", 0.0)),
        )

    def run(self, ctx: PipelineContext) -> None:
        """Analyze bouquet image and extract flower information."""
        # Skip if no image provided
        if not ctx.image_base64:
            logger.debug("VIA: No image provided, skipping")
            return

        try:
            client = get_ai_client()

            # Build prompt for image analysis
            prompt = """Analyze this flower bouquet image.
Identify the main flower, any secondary flowers, and describe the composition.
If you cannot clearly identify a single main flower, indicate that clarification is needed."""

            response = client.analyze_image(
                image_base64=ctx.image_base64,
                prompt=prompt,
                system_prompt=VISION_ANALYSIS_PROMPT,
                temperature=0.3,
                max_tokens=600,
            )

            # Parse main flower with validation
            main_flower = None
            main_data = response.get("main_flower")
            if main_data:
                main_flower = self._parse_detected_flower(main_data)
                if main_data and not main_flower:
                    logger.warning(f"VIA: Invalid main_flower data: {main_data}")

            # Parse secondary flowers with validation
            secondary_flowers = []
            for flower_data in response.get("secondary_flowers", [])[:5]:
                flower = self._parse_detected_flower(flower_data)
                if flower:
                    secondary_flowers.append(flower)
                elif flower_data:
                    logger.debug(f"VIA: Skipping invalid secondary flower: {flower_data}")

            # Determine if clarification is needed
            needs_clarification = response.get("needs_clarification", False)

            # Also trigger clarification if confidence is low
            if main_flower and main_flower.confidence < 0.7:
                needs_clarification = True

            ctx.vision = VisionAnalysisData(
                main_flower=main_flower,
                secondary_flowers=secondary_flowers,
                bouquet_description=response.get("bouquet_description", ""),
                needs_clarification=needs_clarification,
                clarification_message=response.get("clarification_message", ""),
                raw_output=response,
            )

            # Log results
            if main_flower:
                logger.info(f"VIA detected: {main_flower.name} (confidence: {main_flower.confidence:.2f})")
            else:
                logger.info("VIA: Could not determine main flower, needs clarification")

            # Console output
            console = get_console_logger()
            console.agent_result("VIA", {
                "Main Flower": main_flower.name if main_flower else "Unknown",
                "Confidence": f"{main_flower.confidence:.2f}" if main_flower else "N/A",
                "Secondary": [f.name for f in secondary_flowers[:3]],
                "Needs Clarification": needs_clarification,
            })

        except AIClientError as e:
            logger.error(f"VIA AI error: {e}")
            ctx.add_error(f"VIA: {str(e)}")
            self._fallback_analysis(ctx)

        except Exception as e:
            logger.error(f"VIA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"VIA: Unexpected error")
            self._fallback_analysis(ctx)

    def _fallback_analysis(self, ctx: PipelineContext) -> None:
        """Provide fallback when vision analysis fails."""
        ctx.vision = VisionAnalysisData(
            main_flower=None,
            secondary_flowers=[],
            bouquet_description="Unable to analyze image",
            needs_clarification=True,
            clarification_message="I couldn't analyze the image. Could you tell me which flower you're interested in?",
            raw_output={"fallback": True},
        )
