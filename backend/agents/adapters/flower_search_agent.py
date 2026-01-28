"""
FSA - Flower Search Agent - v1.0

Purpose:
Retrieves botanical information, meanings, and care instructions
for identified flowers. Uses AI to generate comprehensive flower data.

Position in scan pipeline: SECOND (after FID)
"""

import logging
import uuid

from backend.pipeline.scan_context import ScanContext, FlowerInfoData, IdentifiedFlower
from backend.core.ai_client import get_ai_client, AIClientError
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)

FLOWER_INFO_PROMPT = """You are an expert botanist and floriculture specialist.

Given a flower name, provide comprehensive information about it.

Return JSON with this exact structure:
{
    "botanical": {
        "family": "Rosaceae",
        "native_regions": ["Europe", "Asia", "North America"],
        "bloom_seasons": ["Spring", "Summer"],
        "lifespan": "perennial"
    },
    "meanings": ["Love", "Beauty", "Passion"],
    "care": {
        "difficulty": "moderate",
        "light": "full_sun",
        "water": "moderate",
        "temperature_range": "15-25°C",
        "humidity": "moderate",
        "tips": [
            "Prune in early spring",
            "Water at the base to prevent disease",
            "Fertilize monthly during growing season"
        ]
    },
    "similar_flowers": [
        {"name": "Peony", "scientific_name": "Paeonia"},
        {"name": "Camellia", "scientific_name": "Camellia japonica"}
    ]
}

Field constraints:
- difficulty: "easy", "moderate", or "hard"
- light: "low", "medium", "high", or "full_sun"
- water: "low", "moderate", or "frequent"
- meanings: 3-5 symbolic meanings
- similar_flowers: 2-4 related flowers
- tips: 3-5 care tips"""


class FlowerSearchAgent:
    """Retrieves botanical information for identified flowers."""

    name = "FSA"

    def run(self, ctx: ScanContext) -> None:
        """Fetch flower information from knowledge base."""
        primary = ctx.get_primary_flower()

        if not primary or not primary.name or primary.name == "Unknown Flower":
            logger.warning("FSA: No valid flower to search")
            self._fallback(ctx)
            return

        try:
            client = get_ai_client()
            console = get_console_logger()

            # Build search prompt
            search_prompt = f"""Provide comprehensive information about this flower:

Name: {primary.name}
Scientific Name: {primary.scientific_name or 'Unknown'}
Color Variant: {primary.color or 'Standard'}

Include botanical classification, symbolic meanings, care instructions, and similar flowers."""

            response = client.complete_json(
                prompt=search_prompt,
                system_prompt=FLOWER_INFO_PROMPT,
                temperature=0.3,
                max_tokens=1000,
            )

            ctx.flower_info = self._parse_response(response)

            # Log results
            logger.info(f"FSA found info for: {primary.name}")
            console.agent_result("FSA", {
                "Family": ctx.flower_info.family,
                "Meanings": ctx.flower_info.meanings[:3],
                "Difficulty": ctx.flower_info.care_difficulty,
                "Similar": len(ctx.flower_info.similar_flowers),
            })

        except AIClientError as e:
            logger.error(f"FSA AI error: {e}")
            ctx.add_error(f"FSA: {str(e)}")
            self._fallback(ctx)

        except Exception as e:
            logger.error(f"FSA unexpected error: {e}", exc_info=True)
            ctx.add_error(f"FSA: Unexpected error")
            self._fallback(ctx)

    def _parse_response(self, response: dict) -> FlowerInfoData:
        """Parse flower information response."""
        botanical = response.get("botanical", {})
        care = response.get("care", {})

        # Parse similar flowers
        similar = []
        for flower_data in response.get("similar_flowers", [])[:4]:
            if isinstance(flower_data, dict) and flower_data.get("name"):
                similar.append(IdentifiedFlower(
                    id=str(uuid.uuid4())[:8],
                    name=flower_data.get("name", ""),
                    scientific_name=flower_data.get("scientific_name"),
                    confidence=1.0,  # Reference data, not detection
                    color=flower_data.get("color"),
                    position=None,
                ))

        return FlowerInfoData(
            # Botanical
            family=botanical.get("family", "Unknown"),
            native_regions=botanical.get("native_regions", [])[:5],
            bloom_seasons=botanical.get("bloom_seasons", [])[:4],
            lifespan=botanical.get("lifespan", ""),

            # Meanings
            meanings=response.get("meanings", ["Beauty"])[:5],

            # Care
            care_difficulty=self._normalize_difficulty(care.get("difficulty", "moderate")),
            light_requirement=self._normalize_light(care.get("light", "medium")),
            water_frequency=self._normalize_water(care.get("water", "moderate")),
            temperature_range=care.get("temperature_range", ""),
            humidity=care.get("humidity", ""),
            care_tips=care.get("tips", [])[:5],

            # Similar
            similar_flowers=similar,

            raw_response=response,
        )

    def _normalize_difficulty(self, value: str) -> str:
        """Normalize care difficulty to valid enum value."""
        value = value.lower() if value else "moderate"
        if value in ("easy", "low", "beginner"):
            return "easy"
        elif value in ("hard", "high", "difficult", "expert"):
            return "hard"
        return "moderate"

    def _normalize_light(self, value: str) -> str:
        """Normalize light requirement to valid enum value."""
        value = value.lower() if value else "medium"
        if value in ("low", "shade", "indirect"):
            return "low"
        elif value in ("full_sun", "full sun", "direct", "bright"):
            return "full_sun"
        elif value in ("high", "partial sun"):
            return "high"
        return "medium"

    def _normalize_water(self, value: str) -> str:
        """Normalize water frequency to valid enum value."""
        value = value.lower() if value else "moderate"
        if value in ("low", "infrequent", "drought tolerant"):
            return "low"
        elif value in ("frequent", "high", "regular", "often"):
            return "frequent"
        return "moderate"

    def _fallback(self, ctx: ScanContext) -> None:
        """Provide fallback data when search fails."""
        primary = ctx.get_primary_flower()
        flower_name = primary.name if primary else "Unknown"

        ctx.flower_info = FlowerInfoData(
            family="Unknown",
            native_regions=[],
            bloom_seasons=[],
            lifespan="",
            meanings=["Beauty"],
            care_difficulty="moderate",
            light_requirement="medium",
            water_frequency="moderate",
            temperature_range="",
            humidity="",
            care_tips=[f"Research specific care requirements for {flower_name}"],
            similar_flowers=[],
            raw_response={"fallback": True},
        )
