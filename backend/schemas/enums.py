"""
Shared Enums - v0.0.1

Enumerations that match iOS Swift enums.
MUST be kept in sync with:
- FSense/Features/FlowerCard/Models/Flower.swift
- FSense/Features/FlowerCard/Models/GiftingInfo.swift
- FSense/Features/FlowerCard/Models/ContextInfo.swift
"""

from enum import Enum


class MoodIntensityLevel(str, Enum):
    """
    Matches iOS: MoodIntensityLevel
    
    Maps to numeric ranges:
    - very_low: 0.0 - 0.2
    - low: 0.2 - 0.4
    - balanced: 0.4 - 0.6
    - high: 0.6 - 0.8
    - very_high: 0.8 - 1.0
    """
    VERY_LOW = "very_low"
    LOW = "low"
    BALANCED = "balanced"
    HIGH = "high"
    VERY_HIGH = "very_high"


class GiftSuitabilityLevel(str, Enum):
    """
    Matches iOS: GiftSuitability
    """
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    RISKY = "risky"
    NOT_RECOMMENDED = "not_recommended"


class EmotionalRiskLevel(str, Enum):
    """
    Matches iOS: EmotionalRiskLevel
    """
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ContextSentiment(str, Enum):
    """
    Matches iOS: ContextSentiment
    """
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


class ContextAppropriatenessLevel(str, Enum):
    """
    Matches iOS: ContextAppropriatenessLevel
    """
    HIGHLY_APPROPRIATE = "highly_appropriate"
    APPROPRIATE = "appropriate"
    NEUTRAL = "neutral"
    INAPPROPRIATE = "inappropriate"
    HIGHLY_INAPPROPRIATE = "highly_inappropriate"


class ContextSensitivityLevel(str, Enum):
    """
    Matches iOS: ContextSensitivityLevel
    """
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
