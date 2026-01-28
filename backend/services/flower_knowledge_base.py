"""
Flower Knowledge Base Service - v0.1.0

High-level API for accessing flower knowledge.
Wraps flower_database.py helpers with additional logic for QuickReplyAgent.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from backend.database.flower_database import (
    get_flower_by_id,
    get_flowers_by_emotion,
    get_cultural_warnings,
    get_number_rules,
    get_all_flower_ids,
    FLOWERS_DATA,
    FLOWER_MEANINGS_DATA,
    CULTURAL_CONTEXTS_DATA,
    REGION_NUMBER_RULES_DATA,
)


@dataclass
class FlowerInfo:
    """Structured flower information for responses."""
    flower_id: str
    name: str
    name_ru: Optional[str]
    color: Optional[str]
    primary_meanings: List[str]
    price_tier: str
    availability: str


@dataclass
class AlternativeFlower:
    """Alternative flower suggestion."""
    flower_id: str
    name: str
    name_ru: Optional[str]
    match_score: float
    meaning_en: str
    meaning_ru: Optional[str]


@dataclass
class CulturalRule:
    """Cultural rule for a flower in a region."""
    flower_id: str
    region: str
    is_taboo: bool
    taboo_reason: Optional[str]
    taboo_occasions: Optional[List[str]]
    recommended_occasions: Optional[List[str]]


@dataclass
class QuantityRule:
    """Quantity rules for a region."""
    region: str
    preferred_numbers: List[int]
    taboo_numbers: List[int]
    rule_description: str
    number_meanings: Optional[Dict[str, str]]


class FlowerKnowledgeBase:
    """
    High-level service for querying flower knowledge.

    Used by QuickReplyAgent to generate informed text responses.
    """

    # Mapping of flower name variations to IDs
    _name_to_id_cache: Optional[Dict[str, str]] = None

    @classmethod
    def _build_name_cache(cls) -> Dict[str, str]:
        """Build a cache mapping flower names (lowercase) to IDs."""
        if cls._name_to_id_cache is not None:
            return cls._name_to_id_cache

        cache = {}
        for flower in FLOWERS_DATA:
            # English name
            cache[flower["name"].lower()] = flower["id"]
            # Russian name
            if flower.get("name_ru"):
                cache[flower["name_ru"].lower()] = flower["id"]
            # ID itself
            cache[flower["id"].lower()] = flower["id"]
            # Common variations (e.g., "rose" -> "red_rose" as fallback)
            base_name = flower["name"].lower().split()[-1]  # e.g., "rose" from "Red Rose"
            if base_name not in cache:
                cache[base_name] = flower["id"]

        cls._name_to_id_cache = cache
        return cache

    @classmethod
    def resolve_flower_id(cls, flower_text: str) -> Optional[str]:
        """
        Resolve a flower name/text to a flower ID.

        Args:
            flower_text: Flower name in any form (e.g., "розы", "red rose", "tulip")

        Returns:
            Flower ID if found, None otherwise
        """
        cache = cls._build_name_cache()
        normalized = flower_text.lower().strip()

        # Direct match
        if normalized in cache:
            return cache[normalized]

        # Partial match (e.g., "роз" matches "красная роза")
        for name, flower_id in cache.items():
            if normalized in name or name in normalized:
                return flower_id

        return None

    @classmethod
    def get_flower_info(cls, flower_id: str) -> Optional[FlowerInfo]:
        """
        Get comprehensive information about a flower.

        Args:
            flower_id: Flower ID (e.g., "red_rose")

        Returns:
            FlowerInfo dataclass or None if not found
        """
        data = get_flower_by_id(flower_id)
        if data is None:
            return None

        return FlowerInfo(
            flower_id=data["id"],
            name=data["name"],
            name_ru=data.get("name_ru"),
            color=data.get("color"),
            primary_meanings=data.get("primary_meanings", []),
            price_tier=data.get("price_tier", "mid"),
            availability=data.get("availability", "year_round"),
        )

    @classmethod
    def get_alternatives(
        cls,
        emotion: str,
        exclude_flower_id: Optional[str] = None,
        top_n: int = 3
    ) -> List[AlternativeFlower]:
        """
        Get alternative flowers for an emotion, excluding a specific flower.

        Args:
            emotion: Emotion/occasion (e.g., "apology", "love")
            exclude_flower_id: Flower ID to exclude from results
            top_n: Number of alternatives to return

        Returns:
            List of AlternativeFlower dataclasses
        """
        matches = get_flowers_by_emotion(emotion, top_n=top_n + 5)  # Get extra to account for exclusion

        alternatives = []
        for match in matches:
            if exclude_flower_id and match["flower_id"] == exclude_flower_id:
                continue

            flower_data = get_flower_by_id(match["flower_id"])
            if flower_data is None:
                continue

            alternatives.append(AlternativeFlower(
                flower_id=match["flower_id"],
                name=flower_data["name"],
                name_ru=flower_data.get("name_ru"),
                match_score=match["match_score"],
                meaning_en=match["meaning_en"],
                meaning_ru=match.get("meaning_ru"),
            ))

            if len(alternatives) >= top_n:
                break

        return alternatives

    @classmethod
    def get_cultural_rules(cls, flower_id: str, region: str) -> Optional[CulturalRule]:
        """
        Get cultural rules for a flower in a specific region.

        Args:
            flower_id: Flower ID
            region: Region code (e.g., "RU", "JP", "US")

        Returns:
            CulturalRule dataclass or None if no specific rules
        """
        # Check for taboo
        warning = get_cultural_warnings(flower_id, region.upper())
        if warning:
            return CulturalRule(
                flower_id=warning["flower_id"],
                region=warning["region"],
                is_taboo=True,
                taboo_reason=warning.get("taboo_reason"),
                taboo_occasions=warning.get("taboo_occasions"),
                recommended_occasions=warning.get("recommended_occasions"),
            )

        # Check for any cultural context (not necessarily taboo)
        for ctx in CULTURAL_CONTEXTS_DATA:
            if ctx["flower_id"] == flower_id and ctx["region"] == region.upper():
                return CulturalRule(
                    flower_id=ctx["flower_id"],
                    region=ctx["region"],
                    is_taboo=ctx.get("is_taboo", False),
                    taboo_reason=ctx.get("taboo_reason"),
                    taboo_occasions=ctx.get("taboo_occasions"),
                    recommended_occasions=ctx.get("recommended_occasions"),
                )

        return None

    @classmethod
    def get_quantity_rules(cls, region: str) -> Optional[QuantityRule]:
        """
        Get flower quantity rules for a region.

        Args:
            region: Region code (e.g., "RU", "CN", "JP")

        Returns:
            QuantityRule dataclass or None if no specific rules
        """
        data = get_number_rules(region.upper())
        if data is None:
            return None

        return QuantityRule(
            region=data["region"],
            preferred_numbers=data.get("preferred_numbers", []),
            taboo_numbers=data.get("taboo_numbers", []),
            rule_description=data.get("rule_description", ""),
            number_meanings=data.get("number_meanings"),
        )

    @classmethod
    def get_emotion_flowers(cls, emotion: str, top_n: int = 5) -> List[AlternativeFlower]:
        """
        Get top flowers for an emotion/occasion.

        Args:
            emotion: Emotion/occasion (e.g., "love", "sympathy", "birthday")
            top_n: Number of flowers to return

        Returns:
            List of AlternativeFlower dataclasses
        """
        return cls.get_alternatives(emotion, exclude_flower_id=None, top_n=top_n)

    @classmethod
    def get_flower_meaning_for_emotion(
        cls,
        flower_id: str,
        emotion: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the meaning of a specific flower for a specific emotion.

        Args:
            flower_id: Flower ID
            emotion: Emotion/occasion

        Returns:
            Meaning data dict or None
        """
        for meaning in FLOWER_MEANINGS_DATA:
            if meaning["flower_id"] == flower_id and meaning["emotion"] == emotion:
                return meaning
        return None

    @classmethod
    def is_flower_suitable(cls, flower_id: str, emotion: str) -> tuple[bool, float, str]:
        """
        Check if a flower is suitable for an emotion.

        Args:
            flower_id: Flower ID
            emotion: Emotion/occasion

        Returns:
            Tuple of (is_suitable, match_score, explanation)
        """
        meaning = cls.get_flower_meaning_for_emotion(flower_id, emotion)

        if meaning is None:
            # Check if flower exists at all
            flower = get_flower_by_id(flower_id)
            if flower is None:
                return (False, 0.0, "Flower not found in database")

            # Flower exists but no specific meaning for this emotion
            return (False, 0.3, f"No specific association between this flower and {emotion}")

        score = meaning["match_score"]
        is_suitable = score >= 0.6

        if score >= 0.9:
            explanation = meaning["meaning_en"]
        elif score >= 0.7:
            explanation = f"Good choice. {meaning['meaning_en']}"
        elif score >= 0.6:
            explanation = f"Acceptable choice. {meaning['meaning_en']}"
        else:
            explanation = f"Not the best choice for {emotion}. {meaning['meaning_en']}"

        return (is_suitable, score, explanation)

    @classmethod
    def get_all_emotions(cls) -> List[str]:
        """Get list of all supported emotions/occasions."""
        emotions = set()
        for meaning in FLOWER_MEANINGS_DATA:
            emotions.add(meaning["emotion"])
        return sorted(list(emotions))
