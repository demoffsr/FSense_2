"""
FID - Flower Identification Agent - v1.0

Purpose:
Analyzes images using GPT-4o Vision to identify flowers.
Handles both single flower and bouquet (multi-flower) modes.

Position in scan pipeline: FIRST
"""

import logging
import uuid

from backend.pipeline.scan_context import ScanContext, IdentifiedFlower, IdentificationData
from backend.core.ai_client import get_ai_client, AIClientError
from backend.core.console_logger import get_console_logger
from backend.core.safe_parse import safe_parse_float

logger = logging.getLogger(__name__)

SINGLE_FLOWER_PROMPT = """You are an expert botanist and florist analyzing a flower image.

Your task:
1. Identify the flower in the image
2. Determine its common name and scientific name
3. Note the color variant if applicable
4. Rate your confidence (0.0-1.0)

Return JSON with this exact structure:
{
    "flower": {
        "name": "Red Rose",
        "scientific_name": "Rosa",
        "color": "red",
        "confidence": 0.95
    },
    "additional_notes": "This appears to be a hybrid tea rose variety..."
}

If you cannot identify the flower:
{
    "flower": {
        "name": "Unknown Flower",
        "scientific_name": null,
        "color": "the visible color",
        "confidence": 0.2
    },
    "additional_notes": "Unable to confidently identify this flower..."
}"""

BOUQUET_PROMPT = """You are an expert botanist and florist analyzing a bouquet image.

Your task:
1. Identify the MAIN/DOMINANT flower (most prominent)
2. Identify SECONDARY flowers present (up to 5)
3. Describe the overall bouquet composition
4. Rate confidence for each identification

Return JSON with this exact structure:
{
    "primary_flower": {
        "name": "Red Rose",
        "scientific_name": "Rosa",
        "color": "red",
        "confidence": 0.95
    },
    "secondary_flowers": [
        {"name": "Baby's Breath", "scientific_name": "Gypsophila", "color": "white", "confidence": 0.9},
        {"name": "Eucalyptus", "scientific_name": "Eucalyptus", "color": "green", "confidence": 0.85}
    ],
    "bouquet_description": "A romantic bouquet with red roses as the centerpiece, accented with delicate baby's breath and eucalyptus greenery."
}

If no clear primary flower:
{
    "primary_flower": null,
    "secondary_flowers": [...all visible flowers...],
    "bouquet_description": "A mixed arrangement with no clear dominant flower..."
}"""


class FlowerIdentificationAgent:
    """Identifies flowers from images using GPT-4o Vision."""

    name = "FID"

    def run(self, ctx: ScanContext) -> None:
        """Analyze image and identify flowers."""
        if not ctx.image_base64:
            ctx.add_error("FID: No image provided")
            return

        try:
            client = get_ai_client()
            console = get_console_logger()

            # Choose prompt based on scan mode
            is_bouquet = ctx.scan_mode == "bouquet"
            system_prompt = BOUQUET_PROMPT if is_bouquet else SINGLE_FLOWER_PROMPT

            prompt = "Analyze this flower image and identify the flower(s) present."

            response = client.analyze_image(
                image_base64=ctx.image_base64,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=800,
            )

            # Parse response based on mode
            if is_bouquet:
                ctx.identification = self._parse_bouquet_response(response)
            else:
                ctx.identification = self._parse_single_response(response)

            # Log results
            primary = ctx.identification.primary_flower
            if primary:
                logger.info(f"FID identified: {primary.name} (confidence: {primary.confidence:.2f})")
                console.agent_result("FID", {
                    "Flower": primary.name,
                    "Scientific": primary.scientific_name or "N/A",
                    "Confidence": f"{primary.confidence:.0%}",
                    "Additional": len(ctx.identification.additional_flowers),
                })
            else:
                logger.warning("FID: Could not identify primary flower")
                console.agent_result("FID", {
                    "Flower": "Unknown",
                    "Confidence": "0%",
                })

        except AIClientError as e:
            logger.error(f"FID AI error: {e}")
            ctx.add_error(f"FID: {str(e)}")
            self._fallback(ctx)

        except Exception as e:
            logger.error(f"FID unexpected error: {e}", exc_info=True)
            ctx.add_error(f"FID: Unexpected error")
            self._fallback(ctx)

    def _parse_single_response(self, response: dict) -> IdentificationData:
        """Parse single flower identification response."""
        flower_data = response.get("flower", {})

        primary = None
        if flower_data and flower_data.get("name"):
            primary = IdentifiedFlower(
                id=str(uuid.uuid4())[:8],
                name=flower_data.get("name", "Unknown"),
                scientific_name=flower_data.get("scientific_name"),
                confidence=safe_parse_float(
                    flower_data.get("confidence"),
                    default=0.0,
                    context="FlowerID.confidence"
                ),
                color=flower_data.get("color"),
                position="primary",
            )

        return IdentificationData(
            primary_flower=primary,
            additional_flowers=[],
            bouquet_description=response.get("additional_notes", ""),
            raw_response=response,
        )

    def _parse_bouquet_response(self, response: dict) -> IdentificationData:
        """Parse bouquet/multi-flower identification response."""
        # Parse primary flower
        primary = None
        primary_data = response.get("primary_flower")
        if primary_data and isinstance(primary_data, dict) and primary_data.get("name"):
            primary = IdentifiedFlower(
                id=str(uuid.uuid4())[:8],
                name=primary_data.get("name", "Unknown"),
                scientific_name=primary_data.get("scientific_name"),
                confidence=safe_parse_float(
                    primary_data.get("confidence"),
                    default=0.0,
                    context="FlowerID.confidence"
                ),
                color=primary_data.get("color"),
                position="primary",
            )

        # Parse secondary flowers
        additional = []
        for flower_data in response.get("secondary_flowers", [])[:5]:
            if isinstance(flower_data, dict) and flower_data.get("name"):
                additional.append(IdentifiedFlower(
                    id=str(uuid.uuid4())[:8],
                    name=flower_data.get("name", ""),
                    scientific_name=flower_data.get("scientific_name"),
                    confidence=safe_parse_float(
                        flower_data.get("confidence"),
                        default=0.0,
                        context="FlowerID.confidence"
                    ),
                    color=flower_data.get("color"),
                    position="secondary",
                ))

        return IdentificationData(
            primary_flower=primary,
            additional_flowers=additional,
            bouquet_description=response.get("bouquet_description", ""),
            raw_response=response,
        )

    def _fallback(self, ctx: ScanContext) -> None:
        """Provide fallback when identification fails."""
        ctx.identification = IdentificationData(
            primary_flower=IdentifiedFlower(
                id=str(uuid.uuid4())[:8],
                name="Unknown Flower",
                scientific_name=None,
                confidence=0.0,
                color=None,
                position="primary",
            ),
            additional_flowers=[],
            bouquet_description="Unable to analyze the image.",
            raw_response={"fallback": True},
        )
