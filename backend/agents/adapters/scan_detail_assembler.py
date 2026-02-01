"""
SDA - Scan Detail Assembler - v1.0

Purpose:
Assembles final payloads (QuickScanPayload and ScanDetailPayload)
from FID and FSA outputs. The ONLY agent that writes to payloads.

Position in scan pipeline: LAST (after FSA)
"""

import logging

from backend.pipeline.scan_context import ScanContext
from backend.schemas.scan_payload import (
    QuickScanPayload,
    ScanDetailPayload,
    DetectedFlowerInfo,
    ScanResultHeader,
    BotanicalInfo,
    CareInfo,
    AskAIMetadata,
    CareDifficulty,
    LightRequirement,
    WaterFrequency,
)
from backend.core.console_logger import get_console_logger

logger = logging.getLogger(__name__)


class ScanDetailAssembler:
    """Assembles final scan payloads."""

    name = "SDA"

    def run(self, ctx: ScanContext) -> None:
        """Assemble quick and detail payloads from context data."""
        console = get_console_logger()

        try:
            # Build quick payload (always)
            ctx.quick_payload = self._build_quick_payload(ctx)

            # Build detail payload (if we have valid identification)
            if ctx.has_valid_identification():
                ctx.detail_payload = self._build_detail_payload(ctx)

            logger.info(f"SDA assembled payloads for request: {ctx.request_id}")
            console.agent_result("SDA", {
                "Quick Payload": "Ready",
                "Detail Payload": "Ready" if ctx.detail_payload else "N/A",
            })

        except Exception as e:
            logger.error(f"SDA assembly error: {e}", exc_info=True)
            ctx.add_error(f"SDA: {str(e)}")

    def _build_quick_payload(self, ctx: ScanContext) -> dict:
        """Build the quick scan response payload."""
        primary = ctx.identification.primary_flower
        additional = ctx.identification.additional_flowers

        # Build primary flower info
        primary_info = DetectedFlowerInfo(
            id=primary.id if primary else "unknown",
            name=primary.name if primary else "Unknown Flower",
            scientific_name=primary.scientific_name if primary else None,
            confidence=primary.confidence if primary else 0.0,
            color=primary.color if primary else None,
            thumbnail_url=None,  # Could be populated by image service
        )

        # Build additional flowers info
        additional_info = [
            DetectedFlowerInfo(
                id=flower.id,
                name=flower.name,
                scientific_name=flower.scientific_name,
                confidence=flower.confidence,
                color=flower.color,
                thumbnail_url=None,
            )
            for flower in additional[:10]
        ]

        payload = QuickScanPayload(
            primary_flower=primary_info,
            additional_flowers=additional_info,
            bouquet_description=ctx.identification.bouquet_description or None,
            scan_mode=ctx.scan_mode,
            request_id=ctx.request_id,
        )

        return payload.model_dump(by_alias=True, exclude_none=True)

    def _build_detail_payload(self, ctx: ScanContext) -> dict:
        """Build the full detail scan response payload."""
        primary = ctx.identification.primary_flower
        info = ctx.flower_info

        # Build header
        header = ScanResultHeader(
            flower_id=primary.id,
            name=primary.name,
            scientific_name=primary.scientific_name,
            confidence=primary.confidence,
            image_url=None,  # Could be populated by image service
        )

        # Build botanical info
        botanical = BotanicalInfo(
            family=info.family or "Unknown",
            native_regions=info.native_regions[:5],
            bloom_seasons=info.bloom_seasons[:4],
            lifespan=info.lifespan or None,
        )

        # Build care info with proper enums
        care = CareInfo(
            difficulty=CareDifficulty(info.care_difficulty),
            light=LightRequirement(info.light_requirement),
            water=WaterFrequency(info.water_frequency),
            temperature_range=info.temperature_range or None,
            humidity=info.humidity or None,
            tips=info.care_tips[:5],
        )

        # Build similar flowers
        similar = [
            DetectedFlowerInfo(
                id=flower.id,
                name=flower.name,
                scientific_name=flower.scientific_name,
                confidence=flower.confidence,
                color=flower.color,
                thumbnail_url=None,
            )
            for flower in info.similar_flowers[:5]
        ]

        # Build Ask AI metadata with suggested questions
        ask_ai = AskAIMetadata(
            enabled=True,
            suggested_questions=self._generate_suggested_questions(primary.name, info),
        )

        payload = ScanDetailPayload(
            header=header,
            botanical=botanical,
            meanings=info.meanings[:5] if info.meanings else ["Beauty"],
            care=care,
            similar_flowers=similar,
            ask_ai=ask_ai,
            request_id=ctx.request_id,
            pipeline_version="1.0.0",
        )

        return payload.model_dump(by_alias=True, exclude_none=True)

    def _generate_suggested_questions(self, flower_name: str, info) -> list[str]:
        """Generate context-aware suggested questions."""
        questions = []

        # Base questions
        questions.append(f"How do I care for {flower_name}?")

        # Conditional questions based on available info
        if info.meanings:
            questions.append(f"What does {flower_name} symbolize in different cultures?")

        if info.similar_flowers:
            similar_names = [f.name for f in info.similar_flowers[:2]]
            if similar_names:
                questions.append(f"What's the difference between {flower_name} and {similar_names[0]}?")

        if info.bloom_seasons:
            questions.append(f"When is the best time to plant {flower_name}?")

        # Gifting question
        questions.append(f"Is {flower_name} a good gift flower?")

        return questions[:5]
