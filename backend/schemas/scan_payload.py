"""
Scan Payload Schemas - v1.0

Schemas for the flower scan feature.
Separate from FlowerCardPayload - optimized for quick identification flow.

iOS Contract:
- ScanModels.swift: DetectedFlower, QuickScanResult, ScanDetailResult
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class ScanMode(str, Enum):
    """Scan mode for single flower or bouquet analysis."""
    SINGLE = "single"
    BOUQUET = "bouquet"


class CareDifficulty(str, Enum):
    """Plant care difficulty level."""
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"


class LightRequirement(str, Enum):
    """Light requirement for plant care."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL_SUN = "full_sun"


class WaterFrequency(str, Enum):
    """Watering frequency for plant care."""
    LOW = "low"
    MODERATE = "moderate"
    FREQUENT = "frequent"


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ScanRequest(BaseModel):
    """Request body for flower scan."""
    image_base64: str = Field(..., description="Base64-encoded image data")
    scan_mode: ScanMode = Field(default=ScanMode.SINGLE, description="Single flower or bouquet mode")
    region: str = Field(default="US", description="Geographic region for cultural context")


# ═══════════════════════════════════════════════════════════════════════════════
# DETECTED FLOWER INFO
# ═══════════════════════════════════════════════════════════════════════════════

class DetectedFlowerInfo(BaseModel):
    """Information about a detected flower."""
    id: str = Field(..., description="Unique identifier for this detection")
    name: str = Field(..., description="Common name of the flower")
    scientific_name: Optional[str] = Field(None, description="Scientific/botanical name", serialization_alias="scientificName")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence 0.0-1.0")
    color: Optional[str] = Field(None, description="Primary color of the flower")
    thumbnail_url: Optional[str] = Field(None, description="URL of thumbnail image", serialization_alias="thumbnailUrl")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK SCAN PAYLOAD (Fast Response)
# ═══════════════════════════════════════════════════════════════════════════════

class QuickScanPayload(BaseModel):
    """
    Quick scan result - returned immediately after image analysis (~2-3s).

    Maps to: QuickScanResult in iOS
    """
    primary_flower: DetectedFlowerInfo = Field(..., description="Main detected flower", serialization_alias="primaryFlower")
    additional_flowers: list[DetectedFlowerInfo] = Field(
        default_factory=list,
        max_length=10,
        description="Other flowers detected in the image",
        serialization_alias="additionalFlowers"
    )
    bouquet_description: Optional[str] = Field(None, description="Description of the bouquet composition", serialization_alias="bouquetDescription")
    scan_mode: str = Field(..., description="Scan mode used", serialization_alias="scanMode")
    request_id: str = Field(..., description="Request tracking ID", serialization_alias="requestId")

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SCAN DETAIL PAYLOAD (Full Information)
# ═══════════════════════════════════════════════════════════════════════════════

class ScanResultHeader(BaseModel):
    """Header information for scan result detail."""
    flower_id: str = Field(..., description="Flower identifier", serialization_alias="flowerId")
    name: str = Field(..., description="Common name")
    scientific_name: Optional[str] = Field(None, description="Scientific name", serialization_alias="scientificName")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    image_url: Optional[str] = Field(None, description="Full-size image URL", serialization_alias="imageUrl")

    model_config = ConfigDict(populate_by_name=True)


class BotanicalInfo(BaseModel):
    """Botanical information about the flower."""
    family: str = Field(..., description="Plant family (e.g., Rosaceae)")
    native_regions: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Native geographic regions",
        serialization_alias="nativeRegions"
    )
    bloom_seasons: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Seasons when the flower blooms",
        serialization_alias="bloomSeasons"
    )
    lifespan: Optional[str] = Field(None, description="Annual, perennial, biennial")

    model_config = ConfigDict(populate_by_name=True)


class CareInfo(BaseModel):
    """Care information for the flower/plant."""
    difficulty: CareDifficulty = Field(..., description="Care difficulty level")
    light: LightRequirement = Field(..., description="Light requirements")
    water: WaterFrequency = Field(..., description="Watering frequency")
    temperature_range: Optional[str] = Field(None, description="Ideal temperature range", serialization_alias="temperatureRange")
    humidity: Optional[str] = Field(None, description="Humidity preference")
    tips: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Care tips"
    )

    model_config = ConfigDict(populate_by_name=True)


class AskAIMetadata(BaseModel):
    """Metadata for Ask AI feature in scan results."""
    enabled: bool = Field(default=True, description="Whether Ask AI is enabled")
    suggested_questions: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Suggested follow-up questions",
        serialization_alias="suggestedQuestions"
    )

    model_config = ConfigDict(populate_by_name=True)


class ScanDetailPayload(BaseModel):
    """
    Full scan detail result - returned after requesting details (~1-2s).

    Maps to: ScanDetailResult in iOS
    """
    header: ScanResultHeader = Field(..., description="Header with identification info")
    botanical: BotanicalInfo = Field(..., description="Botanical information")
    meanings: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Symbolic meanings of the flower"
    )
    care: CareInfo = Field(..., description="Care information")
    similar_flowers: list[DetectedFlowerInfo] = Field(
        default_factory=list,
        max_length=5,
        description="Similar or related flowers",
        serialization_alias="similarFlowers"
    )
    ask_ai: AskAIMetadata = Field(default_factory=AskAIMetadata, serialization_alias="askAi")
    request_id: str = Field(..., description="Original request ID", serialization_alias="requestId")
    pipeline_version: str = Field(default="1.0.0", description="Pipeline version", serialization_alias="pipelineVersion")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "header": {
                    "flowerId": "rose_001",
                    "name": "Rose",
                    "scientificName": "Rosa",
                    "confidence": 0.95,
                    "imageUrl": None
                },
                "botanical": {
                    "family": "Rosaceae",
                    "nativeRegions": ["Europe", "Asia", "North America"],
                    "bloomSeasons": ["Spring", "Summer"],
                    "lifespan": "perennial"
                },
                "meanings": ["Love", "Beauty", "Passion"],
                "care": {
                    "difficulty": "moderate",
                    "light": "full_sun",
                    "water": "moderate",
                    "temperatureRange": "15-25°C",
                    "humidity": "moderate",
                    "tips": ["Prune in early spring", "Water at the base"]
                },
                "similarFlowers": [],
                "askAi": {
                    "enabled": True,
                    "suggestedQuestions": ["How do I propagate roses?"]
                },
                "requestId": "abc-123",
                "pipelineVersion": "1.0.0"
            }
        }
    )
