"""
FlowerCardPayload Schema - v0.0.1

THE FINAL UI CONTRACT for iOS.

This schema MUST match the Swift models in:
- FSense/Features/FlowerCard/Models/Flower.swift
- FSense/Features/FlowerCard/Models/GiftingInfo.swift
- FSense/Features/FlowerCard/Models/ContextInfo.swift

RULES:
1. All fields should have explicit types
2. Avoid Optional where possible (iOS prefers deterministic data)
3. Use lists with fixed semantics (e.g., max 5 meanings)
4. All strings should be non-empty by contract
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

class FlowerHeader(BaseModel):
    """
    Flower identification and image.

    Maps to: Flower (partial)
    """
    flower_id: str = Field(..., description="Unique flower identifier")
    name: str = Field(..., description="Display name of the flower")
    image_url: Optional[str] = Field(None, description="Remote image URL")
    image_asset: Optional[str] = Field(None, description="Local asset name (iOS)")
    image_cache_key: Optional[str] = Field(None, description="Cache key for polling image status")


# ═══════════════════════════════════════════════════════════════════════════════
# MEANING TAB
# ═══════════════════════════════════════════════════════════════════════════════

class SymbolismCard(BaseModel):
    """
    Symbolism explanation card.
    
    Maps to: Flower.symbolismText
    """
    title: str = Field(default="Symbolism")
    text: str = Field(..., description="Symbolism explanation text")


class WhyThisFlowerCard(BaseModel):
    """
    "Why this flower" explanation card with banner.
    
    Maps to: Flower.whyThisFlowerText
    """
    title: str = Field(default="Why This Flower")
    text: str = Field(..., description="Explanation of flower selection")
    banner_image_asset: Optional[str] = Field(None, description="Banner image asset")


class MoodIntensity(BaseModel):
    """
    Mood intensity indicator.
    
    Maps to: Flower.moodIntensityValue + moodIntensityLevel
    """
    value: float = Field(..., ge=0.0, le=1.0, description="Intensity value 0.0-1.0")
    label: str = Field(..., description="Human-readable label")


class MeaningTab(BaseModel):
    """
    Complete Meaning tab content.
    
    Maps to: Flower (meaning-related fields)
    """
    meanings: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Meaning tags (1-5 items)"
    )
    symbolism: SymbolismCard
    why_this_flower: WhyThisFlowerCard
    mood_intensity: MoodIntensity


# ═══════════════════════════════════════════════════════════════════════════════
# GIFTING TAB
# ═══════════════════════════════════════════════════════════════════════════════

class GiftSuitabilityCard(BaseModel):
    """
    Overall gift suitability assessment.
    
    Maps to: GiftingInfo.overallSuitability
    """
    level: str = Field(..., description="Suitability level (excellent/good/moderate/risky/not_recommended)")
    description: str = Field(..., description="Suitability explanation")


class EmotionalRiskCard(BaseModel):
    """
    Emotional risk assessment.
    
    Maps to: GiftingInfo.emotionalRisk
    """
    level: str = Field(..., description="Risk level (none/low/moderate/high/very_high)")
    description: str = Field(..., description="Risk explanation")


class RecipientFitItem(BaseModel):
    """
    Single recipient fit assessment.
    
    Maps to: RecipientFit
    """
    recipient_type: str = Field(..., description="Type of recipient")
    fit_level: str = Field(..., description="Fit level")
    note: Optional[str] = Field(None, description="Additional note")


class GiftingOccasionItem(BaseModel):
    """
    Single occasion suitability.
    
    Maps to: GiftingOccasion
    """
    occasion: str = Field(..., description="Occasion name")
    suitability: str = Field(..., description="Suitability level")
    description: Optional[str] = Field(None, description="Optional description")


class GiftingTab(BaseModel):
    """
    Complete Gifting tab content.
    
    Maps to: GiftingInfo
    """
    suitability: GiftSuitabilityCard
    emotional_risk: EmotionalRiskCard
    recipient_fits: list[RecipientFitItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Recipient fit assessments"
    )
    when_to_gift: list[GiftingOccasionItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Good occasions to gift"
    )
    when_to_avoid: list[GiftingOccasionItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Occasions to avoid"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT TAB
# ═══════════════════════════════════════════════════════════════════════════════

class ContextSummary(BaseModel):
    """
    Context summary card.
    
    Maps to: ContextInfo.summaryText
    """
    text: str = Field(..., description="Summary text")


class CulturalInterpretationItem(BaseModel):
    """
    Single cultural interpretation.
    
    Maps to: CulturalInterpretation
    """
    emoji: str = Field(..., description="Flag or symbol emoji")
    culture: str = Field(..., description="Culture name")
    interpretation: str = Field(..., description="Cultural interpretation")
    sentiment: str = Field(..., description="Sentiment (positive/neutral/negative/mixed)")


class RelationshipContextItem(BaseModel):
    """
    Single relationship context.
    
    Maps to: RelationshipContext
    """
    relationship_type: str = Field(..., description="Relationship type")
    appropriateness: str = Field(..., description="Appropriateness level")
    guidance: str = Field(..., description="Guidance text")


class TimingSensitivityItem(BaseModel):
    """
    Single timing sensitivity.
    
    Maps to: TimingSensitivity
    """
    timing: str = Field(..., description="Timing scenario")
    sensitivity: str = Field(..., description="Sensitivity level")
    note: str = Field(..., description="Guidance note")


class CommonMisinterpretationItem(BaseModel):
    """
    Single common misinterpretation.
    
    Maps to: CommonMisinterpretation
    """
    misinterpretation: str = Field(..., description="Common misinterpretation")
    clarification: str = Field(..., description="Clarification")


class ContextTab(BaseModel):
    """
    Complete Context tab content.
    
    Maps to: ContextInfo
    """
    summary: ContextSummary
    cultural_interpretations: list[CulturalInterpretationItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Cultural interpretations"
    )
    relationship_contexts: list[RelationshipContextItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Relationship contexts"
    )
    timing_sensitivities: list[TimingSensitivityItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Timing sensitivities"
    )
    common_misinterpretations: list[CommonMisinterpretationItem] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Common misinterpretations"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ASK AI METADATA
# ═══════════════════════════════════════════════════════════════════════════════

class AskAIMetadata(BaseModel):
    """
    Metadata for the Ask AI feature.
    """
    enabled: bool = Field(default=True, description="Whether Ask AI is enabled")
    suggested_questions: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Suggested follow-up questions"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ROOT PAYLOAD
# ═══════════════════════════════════════════════════════════════════════════════

class FlowerCardPayload(BaseModel):
    """
    THE ROOT PAYLOAD for iOS FlowerCardView.
    
    This is the FINAL OUTPUT of the pipeline.
    Only SFA (Symbolic Flower Agent) should produce this.
    
    Structure:
    - header: Flower identification
    - meaning: Meaning tab content
    - gifting: Gifting tab content
    - context: Context tab content
    - ask_ai: Ask AI feature metadata
    - pipeline_version: Backend version for debugging
    - request_id: Request tracking ID
    """
    
    # Main content sections
    header: FlowerHeader
    meaning: MeaningTab
    gifting: GiftingTab
    context: ContextTab
    
    # Metadata
    ask_ai: AskAIMetadata = Field(default_factory=AskAIMetadata)
    pipeline_version: str = Field(default="0.0.1", description="Backend version")
    request_id: str = Field(..., description="Request tracking ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "header": {
                    "flower_id": "red_rose_001",
                    "name": "Red Rose",
                    "image_url": None,
                    "image_asset": "RedRose"
                },
                "meaning": {
                    "meanings": ["Love", "Passion", "Romance"],
                    "symbolism": {
                        "title": "Symbolism",
                        "text": "Symbol of love and passion..."
                    },
                    "why_this_flower": {
                        "title": "Why This Flower",
                        "text": "Perfect for expressing love...",
                        "banner_image_asset": "WhyFlowerBanner"
                    },
                    "mood_intensity": {
                        "value": 0.85,
                        "label": "Very High"
                    }
                },
                "gifting": {
                    "suitability": {
                        "level": "excellent",
                        "description": "Perfect for romantic occasions"
                    },
                    "emotional_risk": {
                        "level": "low",
                        "description": "Low risk of misinterpretation"
                    },
                    "recipient_fits": [
                        {"recipient_type": "Romantic Partner", "fit_level": "excellent", "note": None}
                    ],
                    "when_to_gift": [
                        {"occasion": "Anniversary", "suitability": "excellent", "description": None}
                    ],
                    "when_to_avoid": [
                        {"occasion": "First Date", "suitability": "risky", "description": None}
                    ]
                },
                "context": {
                    "summary": {"text": "Best for romantic situations..."},
                    "cultural_interpretations": [
                        {"emoji": "🇺🇸", "culture": "Western", "interpretation": "Love symbol", "sentiment": "positive"}
                    ],
                    "relationship_contexts": [
                        {"relationship_type": "Romantic Partner", "appropriateness": "highly_appropriate", "guidance": "Perfect choice"}
                    ],
                    "timing_sensitivities": [
                        {"timing": "After argument", "sensitivity": "high", "note": "May seem like easy fix"}
                    ],
                    "common_misinterpretations": [
                        {"misinterpretation": "Only for Valentine's", "clarification": "Appropriate year-round"}
                    ]
                },
                "ask_ai": {
                    "enabled": True,
                    "suggested_questions": ["What other flowers express love?"]
                },
                "pipeline_version": "0.0.1",
                "request_id": "abc-123-def"
            }
        }
    )
