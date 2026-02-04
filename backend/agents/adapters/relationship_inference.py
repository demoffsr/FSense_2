"""
Deterministic relationship inference from FIA intent data.

Replaces RIL AI call with pure mapping logic.
Expected savings: ~300ms per pipeline run.

Version: v0.5.0
"""

from typing import Optional
from backend.pipeline.context import RelationshipData, IntentData


# ─────────────────────────────────────────────────────────────────────
# RECIPIENT → RELATIONSHIP TYPE
# ─────────────────────────────────────────────────────────────────────
RECIPIENT_TO_RELATIONSHIP_TYPE: dict[str, str] = {
    # Romantic
    "girlfriend": "romantic",
    "boyfriend": "romantic",
    "wife": "romantic",
    "husband": "romantic",
    "partner": "romantic",
    "fiance": "romantic",
    "fiancee": "romantic",
    "fiancé": "romantic",
    "fiancée": "romantic",
    "gf": "romantic",
    "bf": "romantic",
    "ex-girlfriend": "romantic",  # Still romantic context
    "ex-boyfriend": "romantic",
    "ex-wife": "romantic",
    "ex-husband": "romantic",
    "ex": "romantic",

    # Familial - Parents
    "mother": "familial",
    "father": "familial",
    "mom": "familial",
    "mum": "familial",
    "mama": "familial",
    "dad": "familial",
    "papa": "familial",
    "parent": "familial",

    # Familial - Grandparents
    "grandma": "familial",
    "grandpa": "familial",
    "grandmother": "familial",
    "grandfather": "familial",
    "nana": "familial",
    "granny": "familial",

    # Familial - Siblings
    "sister": "familial",
    "brother": "familial",
    "sibling": "familial",

    # Familial - Extended
    "aunt": "familial",
    "uncle": "familial",
    "cousin": "familial",
    "niece": "familial",
    "nephew": "familial",

    # Familial - In-laws
    "mother-in-law": "familial",
    "father-in-law": "familial",
    "sister-in-law": "familial",
    "brother-in-law": "familial",
    "in-law": "familial",

    # Platonic
    "friend": "platonic",
    "best_friend": "platonic",
    "best friend": "platonic",
    "bestie": "platonic",
    "acquaintance": "platonic",
    "neighbor": "platonic",
    "neighbour": "platonic",
    "roommate": "platonic",

    # Professional - Hierarchical Up
    "boss": "professional",
    "manager": "professional",
    "supervisor": "professional",
    "professor": "professional",
    "teacher": "professional",
    "mentor": "professional",
    "director": "professional",
    "ceo": "professional",

    # Professional - Peer
    "colleague": "professional",
    "coworker": "professional",
    "co-worker": "professional",
    "teammate": "professional",

    # Professional - Client/External
    "client": "professional",
    "customer": "professional",

    # Professional - Hierarchical Down
    "employee": "professional",
    "assistant": "professional",
    "intern": "professional",
    "student": "professional",

    # Ceremonial
    "host": "ceremonial",
    "guest": "ceremonial",
    "bride": "ceremonial",
    "groom": "ceremonial",

    # Self (flower identification)
    "self": "self",
}

# ─────────────────────────────────────────────────────────────────────
# RELATIONSHIP LEVEL → INTIMACY + STAGE
# ─────────────────────────────────────────────────────────────────────
RELATIONSHIP_LEVEL_MAP: dict[str, tuple[float, str]] = {
    # (intimacy_level, relationship_stage)
    "new": (0.2, "new"),
    "growing": (0.4, "developing"),
    "developing": (0.4, "developing"),
    "established": (0.7, "established"),
    "longterm": (0.9, "deep"),
    "deep": (0.9, "deep"),
    "unspecified": (0.5, "established"),
}

# ─────────────────────────────────────────────────────────────────────
# RECIPIENT → POWER DYNAMIC
# ─────────────────────────────────────────────────────────────────────
RECIPIENT_TO_POWER_DYNAMIC: dict[str, str] = {
    # Hierarchical up (giving to someone "above")
    "boss": "hierarchical_up",
    "manager": "hierarchical_up",
    "supervisor": "hierarchical_up",
    "professor": "hierarchical_up",
    "teacher": "hierarchical_up",
    "mentor": "hierarchical_up",
    "director": "hierarchical_up",
    "ceo": "hierarchical_up",

    # Respectful (elders)
    "mother": "respectful",
    "father": "respectful",
    "mom": "respectful",
    "mum": "respectful",
    "mama": "respectful",
    "dad": "respectful",
    "papa": "respectful",
    "grandma": "respectful",
    "grandpa": "respectful",
    "grandmother": "respectful",
    "grandfather": "respectful",
    "nana": "respectful",
    "granny": "respectful",
    "aunt": "respectful",
    "uncle": "respectful",
    "mother-in-law": "respectful",
    "father-in-law": "respectful",

    # Hierarchical down
    "employee": "hierarchical_down",
    "assistant": "hierarchical_down",
    "intern": "hierarchical_down",
    "student": "hierarchical_down",
}
# Default: "equal"

# ─────────────────────────────────────────────────────────────────────
# FORMALITY CALCULATION
# ─────────────────────────────────────────────────────────────────────
BASE_FORMALITY: dict[str, float] = {
    "romantic": 0.2,
    "familial": 0.35,
    "platonic": 0.4,
    "professional": 0.75,
    "ceremonial": 0.65,
    "self": 0.0,
}

TONE_FORMALITY_ADJUSTMENT: dict[str, float] = {
    "subtle": 0.1,
    "neutral": 0.0,
    "warm": -0.05,
    "passionate": -0.15,
    "playful": -0.1,
    "formal": 0.2,
}


# ─────────────────────────────────────────────────────────────────────
# GIFT APPROPRIATENESS
# ─────────────────────────────────────────────────────────────────────
def _compute_gift_appropriateness(
    relationship_type: str,
    relationship_level: str,
    occasion: str,
    context_flags: dict,
    emotion_data: Optional[dict] = None,
) -> dict:
    """Compute gift_appropriateness based on relationship context.

    Args:
        relationship_type: Type of relationship (romantic, familial, etc.)
        relationship_level: Level/stage of relationship (new, established, etc.)
        occasion: The occasion for the gift
        context_flags: Additional context flags (is_first_gift, etc.)
        emotion_data: Optional EIA emotion data for cross-referencing
    """
    # Base max_intensity by relationship type
    MAX_INTENSITY_BASE = {
        "romantic": 0.95,
        "familial": 0.7,
        "platonic": 0.6,
        "professional": 0.4,
        "ceremonial": 0.5,
        "self": 1.0,
        "neutral": 0.5,  # Default for unknown
    }

    max_intensity = MAX_INTENSITY_BASE.get(relationship_type, 0.5)

    # Adjust for relationship level
    LEVEL_ADJUSTMENTS = {
        "new": -0.15,
        "growing": -0.05,
        "developing": -0.05,
        "established": 0.0,
        "longterm": 0.1,
        "deep": 0.1,
    }
    max_intensity += LEVEL_ADJUSTMENTS.get(relationship_level, 0.0)

    # Adjust for first gift
    if context_flags.get("is_first_gift"):
        max_intensity -= 0.1

    # Adjust for high-intensity negative emotions (EIA cross-reference)
    if emotion_data:
        emotion = emotion_data.get("primary_emotion", "").lower()
        intensity = emotion_data.get("emotion_intensity", 0.5)

        # "Making amends" emotions should cap intensity
        if emotion in ["remorse", "guilt", "regret", "apologetic"] and intensity > 0.7:
            max_intensity = min(max_intensity, 0.6)

    # Clamp
    max_intensity = max(0.2, min(1.0, max_intensity))

    # Romantic flowers OK only for romantic relationships
    romantic_flowers_ok = relationship_type == "romantic"

    # Avoid flowers
    avoid_flowers: list[str] = []
    if relationship_type == "professional":
        avoid_flowers.extend(["red rose", "red roses"])
    if relationship_type == "familial":
        avoid_flowers.extend(["red rose", "red roses"])  # Can be misinterpreted
    if occasion == "sympathy":
        avoid_flowers.extend(["bright colors", "yellow", "orange"])
        romantic_flowers_ok = False
        max_intensity = min(max_intensity, 0.6)

    return {
        "max_intensity": round(max_intensity, 2),
        "romantic_flowers_ok": romantic_flowers_ok,
        "avoid_flowers": avoid_flowers,
        "cultural_considerations": "None specific",
    }


# ─────────────────────────────────────────────────────────────────────
# MAIN INFERENCE FUNCTION
# ─────────────────────────────────────────────────────────────────────
def infer_relationship_from_intent(
    intent: Optional[IntentData],
    emotion_data: Optional[dict] = None,
) -> RelationshipData:
    """
    Deterministically infer relationship data from intent.

    Replaces RIL AI call with pure mapping logic.
    Falls back to safe defaults for unknown recipients.

    Args:
        intent: FIA intent data
        emotion_data: Optional EIA emotion data (primary_emotion, emotion_intensity)
                      Used to adjust gift_appropriateness for high-intensity emotions

    Returns:
        RelationshipData with inferred relationship context
    """
    raw = intent.raw_output if intent else {}

    recipient = raw.get("recipient", "unspecified").lower()
    relationship_level = raw.get("relationship_level", "unspecified").lower()
    tone = raw.get("tone", "neutral").lower()
    occasion = raw.get("occasion", "general").lower()
    context_flags = raw.get("context_flags", {})

    # Relationship type
    relationship_type = RECIPIENT_TO_RELATIONSHIP_TYPE.get(recipient, "neutral")

    # Intimacy and stage
    intimacy, stage = RELATIONSHIP_LEVEL_MAP.get(relationship_level, (0.5, "established"))

    # Power dynamic
    power_dynamic = RECIPIENT_TO_POWER_DYNAMIC.get(recipient, "equal")

    # Formality
    base_formality = BASE_FORMALITY.get(relationship_type, 0.5)
    tone_adj = TONE_FORMALITY_ADJUSTMENT.get(tone, 0.0)
    formality = max(0.0, min(1.0, base_formality + tone_adj))

    # Gift appropriateness (with optional EIA cross-reference)
    gift_appropriateness = _compute_gift_appropriateness(
        relationship_type, relationship_level, occasion, context_flags, emotion_data
    )

    # Confidence is lower for unknown recipients
    confidence = 0.9 if recipient != "unspecified" and relationship_type != "neutral" else 0.5

    return RelationshipData(
        relationship_type=relationship_type,
        intimacy_level=intimacy,
        formality_level=formality,
        power_dynamic=power_dynamic,
        raw_output={
            "relationship_stage": stage,
            "formality": "formal" if formality > 0.6 else ("casual" if formality < 0.4 else "semi_formal"),
            "gift_appropriateness": gift_appropriateness,
            "inference_source": "deterministic",
            "confidence": confidence,
        },
    )
