"""
Flower Database Schema and Seed Data - v2.0 EXPANDED

This file contains:
1. SQLAlchemy models for flower catalog
2. Comprehensive seed data parsed from authoritative sources

Sources:
- Almanac.com - Flower Meanings Language of Flowers
- FromYouFlowers.com - Comprehensive A-Z flower meanings
- Lovingly.com - Flower encyclopedia
- PetalAndPoem.com - Cultural taboos guide
- MyGlobalFlowers.com - International gifting traditions
- roza4u.ru - Russian flower symbolism
- Iowa State University Extension - Flowers and Their Meanings
- Arena Flowers - Flower Symbolism Guide
- Petal Republic - Ultimate Guide to Floriography

To use: Review and copy models to models.py, run seed_database() to populate.

Stats:
- 90+ flowers with detailed meanings
- 120+ emotion-to-flower mappings
- 50+ cultural context entries
- 8 regional number rules
- Comprehensive color symbolism
"""

from typing import Optional, List, Dict
import json
import logging
from sqlalchemy import Column, String, DateTime, Integer, Text, Index, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

from backend.database.connection import get_flower_db, check_flower_db_exists

logger = logging.getLogger(__name__)

Base = declarative_base()


# =============================================================================
# MODELS
# =============================================================================

class Flower(Base):
    """Master flower catalog."""
    __tablename__ = "flowers"

    id = Column(String(50), primary_key=True)  # e.g., "red_rose"
    name = Column(String(100), nullable=False)
    name_ru = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    category = Column(String(50), default="flower")
    availability = Column(String(30), default="year_round")
    price_tier = Column(String(20), default="mid")
    primary_meanings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_flower_name', 'name'),
        Index('idx_flower_color', 'color'),
    )


class FlowerMeaning(Base):
    """Meanings by emotion/occasion for flower matching."""
    __tablename__ = "flower_meanings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flower_id = Column(String(50), nullable=False, index=True)
    emotion = Column(String(50), nullable=False)
    occasion = Column(String(50), nullable=True)
    match_score = Column(Float, default=0.7)
    meaning_en = Column(Text, nullable=False)
    meaning_ru = Column(Text, nullable=True)
    phrases = Column(JSON, nullable=True)

    __table_args__ = (
        Index('idx_meaning_emotion', 'emotion'),
        Index('idx_meaning_flower_emotion', 'flower_id', 'emotion'),
    )


class FlowerCulturalContext(Base):
    """Cultural meanings and taboos by region."""
    __tablename__ = "flower_cultural_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flower_id = Column(String(50), nullable=False, index=True)
    region = Column(String(10), nullable=False)
    meaning = Column(Text, nullable=True)
    is_taboo = Column(Boolean, default=False)
    taboo_reason = Column(Text, nullable=True)
    taboo_occasions = Column(JSON, nullable=True)
    recommended_occasions = Column(JSON, nullable=True)

    __table_args__ = (
        Index('idx_cultural_region', 'region'),
        Index('idx_cultural_flower_region', 'flower_id', 'region'),
    )


class RegionNumberRule(Base):
    """Flower quantity rules by region."""
    __tablename__ = "region_number_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(10), nullable=False, index=True)
    preferred_numbers = Column(JSON, nullable=True)
    taboo_numbers = Column(JSON, nullable=True)
    rule_description = Column(Text, nullable=True)
    number_meanings = Column(JSON, nullable=True)


class FlowerColorMeaning(Base):
    """General color symbolism."""
    __tablename__ = "flower_color_meanings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    color = Column(String(30), nullable=False, index=True)
    region = Column(String(10), default="universal")
    positive_meanings = Column(JSON, nullable=True)
    negative_meanings = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)


# =============================================================================
# SEED DATA - FLOWERS
# =============================================================================

FLOWERS_DATA = [
    # ROSES
    {
        "id": "red_rose",
        "name": "Red Rose",
        "name_ru": "Красная роза",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["love", "passion", "romance", "desire"]
    },
    {
        "id": "pink_rose",
        "name": "Pink Rose",
        "name_ru": "Розовая роза",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["grace", "happiness", "gratitude", "admiration"]
    },
    {
        "id": "white_rose",
        "name": "White Rose",
        "name_ru": "Белая роза",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["purity", "innocence", "reverence", "new beginnings"]
    },
    {
        "id": "yellow_rose",
        "name": "Yellow Rose",
        "name_ru": "Жёлтая роза",
        "color": "yellow",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["friendship", "joy", "caring"]  # Note: jealousy in some cultures
    },
    {
        "id": "orange_rose",
        "name": "Orange Rose",
        "name_ru": "Оранжевая роза",
        "color": "orange",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["desire", "enthusiasm", "fascination"]
    },
    {
        "id": "lavender_rose",
        "name": "Lavender Rose",
        "name_ru": "Лавандовая роза",
        "color": "lavender",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["love at first sight", "enchantment", "mystery"]
    },

    # TULIPS
    {
        "id": "red_tulip",
        "name": "Red Tulip",
        "name_ru": "Красный тюльпан",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["declaration of love", "believe me", "passion"]
    },
    {
        "id": "yellow_tulip",
        "name": "Yellow Tulip",
        "name_ru": "Жёлтый тюльпан",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["cheerfulness", "sunshine", "hopeful love"]
    },
    {
        "id": "pink_tulip",
        "name": "Pink Tulip",
        "name_ru": "Розовый тюльпан",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["affection", "caring", "good wishes"]
    },
    {
        "id": "white_tulip",
        "name": "White Tulip",
        "name_ru": "Белый тюльпан",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["forgiveness", "worthiness", "purity"]
    },
    {
        "id": "purple_tulip",
        "name": "Purple Tulip",
        "name_ru": "Фиолетовый тюльпан",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["royalty", "admiration", "respect"]
    },

    # LILIES
    {
        "id": "white_lily",
        "name": "White Lily",
        "name_ru": "Белая лилия",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["purity", "virginity", "majesty", "heavenly"]
    },
    {
        "id": "calla_lily",
        "name": "Calla Lily",
        "name_ru": "Калла",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["magnificent beauty", "elegance", "modesty"]
    },
    {
        "id": "tiger_lily",
        "name": "Tiger Lily",
        "name_ru": "Тигровая лилия",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["wealth", "pride", "confidence", "dare to love"]
    },
    {
        "id": "stargazer_lily",
        "name": "Stargazer Lily",
        "name_ru": "Лилия Стар Гейзер",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["ambition", "encouragement", "sympathy"]
    },

    # CHRYSANTHEMUMS
    {
        "id": "white_chrysanthemum",
        "name": "White Chrysanthemum",
        "name_ru": "Белая хризантема",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["truth", "loyalty", "devoted love"]  # CAUTION: funeral in many cultures
    },
    {
        "id": "yellow_chrysanthemum",
        "name": "Yellow Chrysanthemum",
        "name_ru": "Жёлтая хризантема",
        "color": "yellow",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["slighted love", "neglected", "sorrow"]
    },
    {
        "id": "red_chrysanthemum",
        "name": "Red Chrysanthemum",
        "name_ru": "Красная хризантема",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["love", "deep passion", "sharing"]
    },

    # CARNATIONS
    {
        "id": "red_carnation",
        "name": "Red Carnation",
        "name_ru": "Красная гвоздика",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["deep love", "admiration", "my heart aches"]
    },
    {
        "id": "pink_carnation",
        "name": "Pink Carnation",
        "name_ru": "Розовая гвоздика",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["gratitude", "I'll never forget you", "mother's love"]
    },
    {
        "id": "white_carnation",
        "name": "White Carnation",
        "name_ru": "Белая гвоздика",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["pure love", "innocence", "good luck"]
    },
    {
        "id": "yellow_carnation",
        "name": "Yellow Carnation",
        "name_ru": "Жёлтая гвоздика",
        "color": "yellow",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["disappointment", "rejection", "disdain"]  # NEGATIVE
    },

    # ORCHIDS
    {
        "id": "orchid",
        "name": "Orchid",
        "name_ru": "Орхидея",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["luxury", "beauty", "refinement", "love"]
    },
    {
        "id": "white_orchid",
        "name": "White Orchid",
        "name_ru": "Белая орхидея",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["elegance", "innocence", "purity", "reverence"]
    },
    {
        "id": "pink_orchid",
        "name": "Pink Orchid",
        "name_ru": "Розовая орхидея",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["femininity", "grace", "joy", "happiness"]
    },
    {
        "id": "purple_orchid",
        "name": "Purple Orchid",
        "name_ru": "Фиолетовая орхидея",
        "color": "purple",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["admiration", "respect", "royalty", "dignity"]
    },

    # SUNFLOWERS
    {
        "id": "sunflower",
        "name": "Sunflower",
        "name_ru": "Подсолнух",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["adoration", "loyalty", "longevity", "happiness"]
    },

    # PEONIES
    {
        "id": "pink_peony",
        "name": "Pink Peony",
        "name_ru": "Розовый пион",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["romance", "prosperity", "good fortune", "happy marriage"]
    },
    {
        "id": "white_peony",
        "name": "White Peony",
        "name_ru": "Белый пион",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["bashfulness", "regret", "shame"]
    },
    {
        "id": "red_peony",
        "name": "Red Peony",
        "name_ru": "Красный пион",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["passion", "honor", "respect", "wealth"]
    },

    # HYDRANGEAS
    {
        "id": "blue_hydrangea",
        "name": "Blue Hydrangea",
        "name_ru": "Голубая гортензия",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["apology", "gratitude", "understanding", "sincerity"]
    },
    {
        "id": "pink_hydrangea",
        "name": "Pink Hydrangea",
        "name_ru": "Розовая гортензия",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["heartfelt emotion", "romance", "true feelings"]
    },
    {
        "id": "white_hydrangea",
        "name": "White Hydrangea",
        "name_ru": "Белая гортензия",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["purity", "grace", "abundance"]
    },

    # DAISIES
    {
        "id": "daisy",
        "name": "Daisy",
        "name_ru": "Маргаритка",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["innocence", "purity", "loyal love", "simplicity"]
    },
    {
        "id": "gerbera_daisy",
        "name": "Gerbera Daisy",
        "name_ru": "Гербера",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["cheerfulness", "innocence", "purity"]
    },

    # OTHERS
    {
        "id": "lavender",
        "name": "Lavender",
        "name_ru": "Лаванда",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["devotion", "serenity", "grace", "calmness"]
    },
    {
        "id": "iris",
        "name": "Iris",
        "name_ru": "Ирис",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["faith", "hope", "wisdom", "valor", "friendship"]
    },
    {
        "id": "daffodil",
        "name": "Daffodil",
        "name_ru": "Нарцисс",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["new beginnings", "rebirth", "unrequited love", "regard"]
    },
    {
        "id": "forget_me_not",
        "name": "Forget-Me-Not",
        "name_ru": "Незабудка",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["true love", "memories", "remembrance", "constancy"]
    },
    {
        "id": "gardenia",
        "name": "Gardenia",
        "name_ru": "Гардения",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["secret love", "purity", "sweetness", "joy"]
    },
    {
        "id": "jasmine",
        "name": "Jasmine",
        "name_ru": "Жасмин",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["sensuality", "grace", "elegance", "attachment"]
    },
    {
        "id": "hyacinth_purple",
        "name": "Purple Hyacinth",
        "name_ru": "Фиолетовый гиацинт",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["sorrow", "forgiveness", "please forgive me", "regret"]
    },
    {
        "id": "hyacinth_blue",
        "name": "Blue Hyacinth",
        "name_ru": "Голубой гиацинт",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["constancy", "sincerity"]
    },
    {
        "id": "hyacinth_white",
        "name": "White Hyacinth",
        "name_ru": "Белый гиацинт",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["loveliness", "prayers", "I'll pray for you"]
    },
    {
        "id": "anemone",
        "name": "Anemone",
        "name_ru": "Анемон",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["anticipation", "protection", "sincerity"]
    },
    {
        "id": "ranunculus",
        "name": "Ranunculus",
        "name_ru": "Ранункулюс",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["charm", "attractiveness", "radiant", "dazzled by charms"]
    },
    {
        "id": "sweet_pea",
        "name": "Sweet Pea",
        "name_ru": "Душистый горошек",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["goodbye", "departure", "thank you", "blissful pleasure"]
    },
    {
        "id": "poppy_red",
        "name": "Red Poppy",
        "name_ru": "Красный мак",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["remembrance", "consolation", "pleasure"]
    },
    {
        "id": "poppy_white",
        "name": "White Poppy",
        "name_ru": "Белый мак",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["consolation", "peace", "sleep", "rest"]
    },
    {
        "id": "gladiolus",
        "name": "Gladiolus",
        "name_ru": "Гладиолус",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["strength", "integrity", "remembrance", "sincerity"]
    },
    {
        "id": "dahlia",
        "name": "Dahlia",
        "name_ru": "Георгин",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["elegance", "dignity", "commitment", "bond"]
    },
    {
        "id": "marigold",
        "name": "Marigold",
        "name_ru": "Бархатцы",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["passion", "creativity"]  # CAUTION: death/mourning in some cultures
    },
    {
        "id": "lotus",
        "name": "Lotus",
        "name_ru": "Лотос",
        "color": "pink",
        "category": "flower",
        "availability": "rare",
        "price_tier": "premium",
        "primary_meanings": ["purity", "enlightenment", "rebirth", "spiritual awakening"]
    },
    {
        "id": "magnolia",
        "name": "Magnolia",
        "name_ru": "Магнолия",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["nobility", "dignity", "perseverance", "love of nature"]
    },
    {
        "id": "azalea",
        "name": "Azalea",
        "name_ru": "Азалия",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["temperance", "passion", "womanhood", "fragile"]
    },
    {
        "id": "camellia",
        "name": "Camellia",
        "name_ru": "Камелия",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["admiration", "perfection", "gratitude", "longing"]
    },
    {
        "id": "protea",
        "name": "Protea",
        "name_ru": "Протея",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["courage", "diversity", "transformation", "daring"]
    },
    {
        "id": "alstroemeria",
        "name": "Alstroemeria",
        "name_ru": "Альстромерия",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["friendship", "devotion", "wealth", "prosperity"]
    },
    {
        "id": "frangipani",
        "name": "Frangipani",
        "name_ru": "Плюмерия",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["grace", "beauty", "charm", "perfection"]  # CAUTION: funeral in India
    },
    {
        "id": "baby_breath",
        "name": "Baby's Breath",
        "name_ru": "Гипсофила",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["innocence", "purity", "everlasting love", "pure heart"]
    },
    {
        "id": "stock",
        "name": "Stock",
        "name_ru": "Левкой",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["lasting beauty", "happy life", "bonds of affection"]
    },
    {
        "id": "zinnia",
        "name": "Zinnia",
        "name_ru": "Цинния",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["thinking of absent friends", "lasting affection", "remembrance"]
    },
    {
        "id": "aster",
        "name": "Aster",
        "name_ru": "Астра",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["love", "patience", "elegance", "daintiness"]
    },
    {
        "id": "bluebell",
        "name": "Bluebell",
        "name_ru": "Колокольчик",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["humility", "constancy", "gratitude", "everlasting love"]
    },

    # =========================================================================
    # NEW FLOWERS FROM IOWA STATE UNIVERSITY & OTHER SOURCES
    # =========================================================================

    # AMARYLLIS
    {
        "id": "amaryllis",
        "name": "Amaryllis",
        "name_ru": "Амариллис",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["pride", "determination", "radiant beauty", "pastoral poetry"]
    },

    # BEGONIA
    {
        "id": "begonia",
        "name": "Begonia",
        "name_ru": "Бегония",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["beware", "caution", "dark thoughts"]
    },

    # BELLS OF IRELAND
    {
        "id": "bells_of_ireland",
        "name": "Bells of Ireland",
        "name_ru": "Молуцелла",
        "color": "green",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["good luck", "fortune", "whimsy"]
    },

    # BACHELOR BUTTON / CORNFLOWER
    {
        "id": "bachelor_button",
        "name": "Bachelor Button",
        "name_ru": "Василёк",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["single blessedness", "hope in love", "delicacy"]
    },

    # BITTERSWEET
    {
        "id": "bittersweet",
        "name": "Bittersweet",
        "name_ru": "Паслён",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["truth", "honesty"]
    },

    # CACTUS FLOWER
    {
        "id": "cactus_flower",
        "name": "Cactus Flower",
        "name_ru": "Цветок кактуса",
        "color": "mixed",
        "category": "flower",
        "availability": "rare",
        "price_tier": "premium",
        "primary_meanings": ["endurance", "warmth", "protection", "maternal love"]
    },

    # CANDYTUFT
    {
        "id": "candytuft",
        "name": "Candytuft",
        "name_ru": "Иберис",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["indifference", "sweetness"]
    },

    # CATTAIL
    {
        "id": "cattail",
        "name": "Cattail",
        "name_ru": "Рогоз",
        "color": "brown",
        "category": "plant",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["peace", "prosperity"]
    },

    # CLEOME
    {
        "id": "cleome",
        "name": "Cleome",
        "name_ru": "Клеома",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["elope with me", "escape"]
    },

    # COREOPSIS
    {
        "id": "coreopsis",
        "name": "Coreopsis",
        "name_ru": "Кореопсис",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["always cheerful", "love at first sight"]
    },

    # CROCUS
    {
        "id": "crocus",
        "name": "Crocus",
        "name_ru": "Крокус",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["cheerfulness", "youthful gladness", "rebirth"]
    },

    # CYCLAMEN
    {
        "id": "cyclamen",
        "name": "Cyclamen",
        "name_ru": "Цикламен",
        "color": "pink",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["resignation", "goodbye", "sincere tenderness"]
    },

    # DANDELION
    {
        "id": "dandelion",
        "name": "Dandelion",
        "name_ru": "Одуванчик",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["faithfulness", "happiness", "wishes come true"]
    },

    # DAYLILY
    {
        "id": "daylily",
        "name": "Daylily",
        "name_ru": "Лилейник",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["coquetry", "Chinese emblem for mother"]
    },

    # EVENING PRIMROSE
    {
        "id": "evening_primrose",
        "name": "Evening Primrose",
        "name_ru": "Энотера",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["inconstancy", "fickleness"]
    },

    # FERN
    {
        "id": "fern",
        "name": "Fern",
        "name_ru": "Папоротник",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["magic", "fascination", "confidence", "shelter", "sincerity"]
    },

    # MAIDENHAIR FERN
    {
        "id": "maidenhair_fern",
        "name": "Maidenhair Fern",
        "name_ru": "Адиантум",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["secret bond of love", "discretion"]
    },

    # FIR
    {
        "id": "fir",
        "name": "Fir",
        "name_ru": "Пихта",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["time", "elevation"]
    },

    # FLAX
    {
        "id": "flax",
        "name": "Flax",
        "name_ru": "Лён",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["domestic symbol", "fate", "I feel your kindness"]
    },

    # FORSYTHIA
    {
        "id": "forsythia",
        "name": "Forsythia",
        "name_ru": "Форзиция",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["anticipation", "good memory"]
    },

    # FOXGLOVE
    {
        "id": "foxglove",
        "name": "Foxglove",
        "name_ru": "Наперстянка",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["insincerity", "stateliness", "youth"]  # WARNING: poison
    },

    # GARLIC
    {
        "id": "garlic",
        "name": "Garlic",
        "name_ru": "Чеснок",
        "color": "white",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["courage", "strength", "protection"]
    },

    # GERANIUM
    {
        "id": "geranium",
        "name": "Geranium",
        "name_ru": "Герань",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["stupidity", "folly", "gentility"]
    },
    {
        "id": "geranium_scarlet",
        "name": "Scarlet Geranium",
        "name_ru": "Красная герань",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["comforting", "consolation"]
    },
    {
        "id": "geranium_oak",
        "name": "Oak Geranium",
        "name_ru": "Дубовая герань",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["true friendship"]
    },

    # GLOXINIA
    {
        "id": "gloxinia",
        "name": "Gloxinia",
        "name_ru": "Глоксиния",
        "color": "purple",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["love at first sight", "proud spirit"]
    },

    # GRASS
    {
        "id": "grass",
        "name": "Grass",
        "name_ru": "Трава",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["submission", "utility"]
    },

    # HEATHER (lavender and white variants)
    {
        "id": "heather_lavender",
        "name": "Lavender Heather",
        "name_ru": "Лавандовый вереск",
        "color": "lavender",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["admiration", "solitude", "beauty"]
    },
    {
        "id": "heather_white",
        "name": "White Heather",
        "name_ru": "Белый вереск",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["protection", "wishes will come true", "good luck"]
    },

    # HELLEBORE
    {
        "id": "hellebore",
        "name": "Hellebore",
        "name_ru": "Морозник",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["tranquilize my anxiety", "calm", "serenity"]
    },

    # HIBISCUS
    {
        "id": "hibiscus",
        "name": "Hibiscus",
        "name_ru": "Гибискус",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["delicate beauty", "consumed by love", "passion"]
    },

    # HOLLY
    {
        "id": "holly",
        "name": "Holly",
        "name_ru": "Остролист",
        "color": "green",
        "category": "plant",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["defense", "domestic happiness", "foresight"]
    },

    # HYACINTH (additional colors)
    {
        "id": "hyacinth_red",
        "name": "Red Hyacinth",
        "name_ru": "Красный гиацинт",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["play", "recreation", "sport"]
    },
    {
        "id": "hyacinth_yellow",
        "name": "Yellow Hyacinth",
        "name_ru": "Жёлтый гиацинт",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["jealousy"]
    },

    # IVY
    {
        "id": "ivy",
        "name": "Ivy",
        "name_ru": "Плющ",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["wedded love", "fidelity", "friendship", "affection"]
    },

    # JONQUIL
    {
        "id": "jonquil",
        "name": "Jonquil",
        "name_ru": "Жонкиль",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["love me", "affection returned", "desire", "sympathy"]
    },

    # LARKSPUR
    {
        "id": "larkspur_pink",
        "name": "Pink Larkspur",
        "name_ru": "Розовый дельфиниум",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["fickleness", "levity"]
    },
    {
        "id": "larkspur_purple",
        "name": "Purple Larkspur",
        "name_ru": "Фиолетовый дельфиниум",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["haughtiness", "first love"]
    },

    # LILAC
    {
        "id": "lilac",
        "name": "Lilac",
        "name_ru": "Сирень",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["first love", "youthful innocence", "confidence"]
    },
    {
        "id": "lilac_white",
        "name": "White Lilac",
        "name_ru": "Белая сирень",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["youthful innocence", "purity", "humility"]
    },

    # LILY OF THE VALLEY
    {
        "id": "lily_of_the_valley",
        "name": "Lily of the Valley",
        "name_ru": "Ландыш",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["sweetness", "return to happiness", "humility", "purity", "you've made my life complete"]
    },

    # ORANGE LILY (hatred meaning)
    {
        "id": "orange_lily",
        "name": "Orange Lily",
        "name_ru": "Оранжевая лилия",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["hatred", "disdain"]  # NEGATIVE - use carefully
    },

    # YELLOW LILY
    {
        "id": "yellow_lily",
        "name": "Yellow Lily",
        "name_ru": "Жёлтая лилия",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["walking on air", "gaiety", "falsehood"]  # MIXED meaning
    },

    # MISTLETOE
    {
        "id": "mistletoe",
        "name": "Mistletoe",
        "name_ru": "Омела",
        "color": "green",
        "category": "plant",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["kiss me", "affection", "overcoming difficulties"]
    },

    # MOCK ORANGE
    {
        "id": "mock_orange",
        "name": "Mock Orange",
        "name_ru": "Чубушник",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["deceit", "counterfeit"]  # NEGATIVE
    },

    # MONKSHOOD
    {
        "id": "monkshood",
        "name": "Monkshood",
        "name_ru": "Аконит",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["beware", "a deadly foe is near", "chivalry"]  # WARNING: poison
    },

    # MOSS
    {
        "id": "moss",
        "name": "Moss",
        "name_ru": "Мох",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["maternal love", "charity"]
    },

    # MYRTLE
    {
        "id": "myrtle",
        "name": "Myrtle",
        "name_ru": "Мирт",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["love", "Hebrew emblem of marriage", "good luck in marriage"]
    },

    # NARCISSUS
    {
        "id": "narcissus",
        "name": "Narcissus",
        "name_ru": "Нарцисс",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["egotism", "formality", "stay as sweet as you are", "self-love"]
    },

    # NASTURTIUM
    {
        "id": "nasturtium",
        "name": "Nasturtium",
        "name_ru": "Настурция",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["conquest", "victory in battle", "patriotism"]
    },

    # ORANGE BLOSSOM
    {
        "id": "orange_blossom",
        "name": "Orange Blossom",
        "name_ru": "Цветок апельсина",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["innocence", "eternal love", "marriage", "fruitfulness"]
    },

    # PANSY
    {
        "id": "pansy",
        "name": "Pansy",
        "name_ru": "Анютины глазки",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["modesty", "pleasant thoughts", "think of me", "loving thoughts"]
    },

    # PETUNIA
    {
        "id": "petunia",
        "name": "Petunia",
        "name_ru": "Петуния",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["resentment", "anger", "your presence soothes me"]  # MIXED
    },

    # PINE
    {
        "id": "pine",
        "name": "Pine",
        "name_ru": "Сосна",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["hope", "pity", "longevity"]
    },

    # YELLOW POPPY
    {
        "id": "poppy_yellow",
        "name": "Yellow Poppy",
        "name_ru": "Жёлтый мак",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["wealth", "success", "prosperity"]
    },

    # PRIMROSE
    {
        "id": "primrose",
        "name": "Primrose",
        "name_ru": "Примула",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["I can't live without you", "young love", "eternal love"]
    },

    # ROSEBUD variations
    {
        "id": "rosebud",
        "name": "Rosebud",
        "name_ru": "Бутон розы",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["beauty and youth", "a heart innocent of love"]
    },
    {
        "id": "rosebud_red",
        "name": "Red Rosebud",
        "name_ru": "Красный бутон розы",
        "color": "red",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["pure and lovely", "you are young and beautiful"]
    },
    {
        "id": "rosebud_white",
        "name": "White Rosebud",
        "name_ru": "Белый бутон розы",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["girlhood", "too young for love"]
    },
    {
        "id": "rosebud_moss",
        "name": "Moss Rosebud",
        "name_ru": "Моховой бутон розы",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["confessions of love", "superior merit"]
    },

    # DARK CRIMSON ROSE
    {
        "id": "crimson_rose",
        "name": "Dark Crimson Rose",
        "name_ru": "Тёмно-бордовая роза",
        "color": "crimson",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["mourning", "deep sorrow"]
    },

    # TEA ROSE
    {
        "id": "tea_rose",
        "name": "Tea Rose",
        "name_ru": "Чайная роза",
        "color": "peach",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["I'll remember always", "lasting memory"]
    },

    # DAMASK ROSE
    {
        "id": "damask_rose",
        "name": "Damask Rose",
        "name_ru": "Дамасская роза",
        "color": "pink",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["Persian ambassador of love", "brilliant complexion"]
    },

    # THORNLESS ROSE
    {
        "id": "thornless_rose",
        "name": "Thornless Rose",
        "name_ru": "Роза без шипов",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["love at first sight", "early attachment"]
    },

    # WHITE AND RED MIXED ROSE
    {
        "id": "unity_rose",
        "name": "White and Red Mixed Rose",
        "name_ru": "Бело-красная роза",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["unity", "flower emblem of England"]
    },

    # WITHERED WHITE ROSE
    {
        "id": "withered_white_rose",
        "name": "Withered White Rose",
        "name_ru": "Увядшая белая роза",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["transient impression", "fleeting beauty", "you made no impression"]  # NEGATIVE
    },

    # SMILAX
    {
        "id": "smilax",
        "name": "Smilax",
        "name_ru": "Смилакс",
        "color": "green",
        "category": "plant",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["loveliness"]
    },

    # SNAPDRAGON
    {
        "id": "snapdragon",
        "name": "Snapdragon",
        "name_ru": "Львиный зев",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["deception", "gracious lady", "presumption"]
    },

    # STEPHANOTIS
    {
        "id": "stephanotis",
        "name": "Stephanotis",
        "name_ru": "Стефанотис",
        "color": "white",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "premium",
        "primary_meanings": ["happiness in marriage", "desire to travel", "marital bliss"]
    },

    # STRIPED CARNATION
    {
        "id": "striped_carnation",
        "name": "Striped Carnation",
        "name_ru": "Полосатая гвоздика",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["no", "refusal", "sorry I can't be with you", "wish I could be with you"]
    },

    # PURPLE CARNATION
    {
        "id": "purple_carnation",
        "name": "Purple Carnation",
        "name_ru": "Фиолетовая гвоздика",
        "color": "purple",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "budget",
        "primary_meanings": ["capriciousness", "whimsy", "unpredictability"]
    },

    # VARIEGATED TULIP
    {
        "id": "variegated_tulip",
        "name": "Variegated Tulip",
        "name_ru": "Пёстрый тюльпан",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["beautiful eyes", "enchantment"]
    },

    # ORANGE TULIP
    {
        "id": "orange_tulip",
        "name": "Orange Tulip",
        "name_ru": "Оранжевый тюльпан",
        "color": "orange",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["appreciation", "understanding", "energy", "enthusiasm"]
    },

    # BLUE VIOLET
    {
        "id": "violet_blue",
        "name": "Blue Violet",
        "name_ru": "Синяя фиалка",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["watchfulness", "faithfulness", "I'll always be true"]
    },

    # WHITE VIOLET
    {
        "id": "violet_white",
        "name": "White Violet",
        "name_ru": "Белая фиалка",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["let's take a chance", "modesty", "innocence"]
    },

    # VIOLET
    {
        "id": "violet",
        "name": "Violet",
        "name_ru": "Фиалка",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["modesty", "faithfulness", "virtue"]
    },

    # WISTERIA
    {
        "id": "wisteria",
        "name": "Wisteria",
        "name_ru": "Глициния",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["welcome", "steadfast", "clinging love", "will you dance with me"]
    },

    # ZINNIA variations
    {
        "id": "zinnia_magenta",
        "name": "Magenta Zinnia",
        "name_ru": "Пурпурная цинния",
        "color": "magenta",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["lasting affection"]
    },
    {
        "id": "zinnia_scarlet",
        "name": "Scarlet Zinnia",
        "name_ru": "Алая цинния",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["constancy"]
    },
    {
        "id": "zinnia_white",
        "name": "White Zinnia",
        "name_ru": "Белая цинния",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["goodness", "purity"]
    },

    # BUTTERCUP
    {
        "id": "buttercup",
        "name": "Buttercup",
        "name_ru": "Лютик",
        "color": "yellow",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["radiant charm", "childishness", "ingratitude", "riches"]
    },

    # CLEMATIS
    {
        "id": "clematis",
        "name": "Clematis",
        "name_ru": "Клематис",
        "color": "purple",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["mental beauty", "cleverness", "ingenuity", "artifice"]
    },

    # HONEYSUCKLE
    {
        "id": "honeysuckle",
        "name": "Honeysuckle",
        "name_ru": "Жимолость",
        "color": "mixed",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["devoted affection", "bonds of love", "generous love"]
    },
    {
        "id": "honeysuckle_coral",
        "name": "Coral Honeysuckle",
        "name_ru": "Коралловая жимолость",
        "color": "coral",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["fidelity", "devoted love"]
    },

    # MORNING GLORY
    {
        "id": "morning_glory",
        "name": "Morning Glory",
        "name_ru": "Ипомея",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["affection", "love in vain", "mortality", "fleeting beauty"]
    },

    # AMARANTH
    {
        "id": "amaranth",
        "name": "Amaranth",
        "name_ru": "Амарант",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "mid",
        "primary_meanings": ["immortality", "unfading love", "constancy"]
    },

    # CHAMOMILE
    {
        "id": "chamomile",
        "name": "Chamomile",
        "name_ru": "Ромашка",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["energy in adversity", "patience", "calm"]
    },

    # CORNFLOWER (same as Bachelor Button but separate entry)
    {
        "id": "cornflower",
        "name": "Cornflower",
        "name_ru": "Василёк",
        "color": "blue",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "budget",
        "primary_meanings": ["hope in love", "delicacy", "single blessedness"]
    },

    # FREESIA
    {
        "id": "freesia",
        "name": "Freesia",
        "name_ru": "Фрезия",
        "color": "mixed",
        "category": "flower",
        "availability": "year_round",
        "price_tier": "mid",
        "primary_meanings": ["trust", "friendship", "innocence", "thoughtfulness"]
    },

    # RED CAMELLIA
    {
        "id": "camellia_red",
        "name": "Red Camellia",
        "name_ru": "Красная камелия",
        "color": "red",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["you're a flame in my heart", "unpretending excellence"]
    },
    {
        "id": "camellia_white",
        "name": "White Camellia",
        "name_ru": "Белая камелия",
        "color": "white",
        "category": "flower",
        "availability": "seasonal",
        "price_tier": "premium",
        "primary_meanings": ["you're adorable", "perfection", "loveliness"]
    },
]

# NOTE: FLOWERS_BY_ID removed - using SQLite queries instead
# See get_flower_by_id() and get_flowers_by_ids() below


# =============================================================================
# SEED DATA - FLOWER MEANINGS BY EMOTION
# =============================================================================

FLOWER_MEANINGS_DATA = [
    # LOVE
    {"flower_id": "red_rose", "emotion": "love", "match_score": 0.95, "meaning_en": "I love you", "meaning_ru": "Я тебя люблю", "phrases": ["I love you", "Be mine"]},
    {"flower_id": "red_tulip", "emotion": "love", "match_score": 0.9, "meaning_en": "Declaration of love", "meaning_ru": "Признание в любви", "phrases": ["Believe me", "I declare my love"]},
    {"flower_id": "red_carnation", "emotion": "love", "match_score": 0.85, "meaning_en": "My heart aches for you", "meaning_ru": "Моё сердце болит по тебе", "phrases": ["Deep love", "Admiration"]},
    {"flower_id": "red_chrysanthemum", "emotion": "love", "match_score": 0.8, "meaning_en": "I love you", "meaning_ru": "Я тебя люблю"},
    {"flower_id": "orchid", "emotion": "love", "match_score": 0.85, "meaning_en": "Refined love and beauty", "meaning_ru": "Утончённая любовь и красота"},
    {"flower_id": "red_peony", "emotion": "love", "match_score": 0.85, "meaning_en": "Passionate love", "meaning_ru": "Страстная любовь"},

    # APOLOGY
    {"flower_id": "hyacinth_purple", "emotion": "apology", "match_score": 0.95, "meaning_en": "Please forgive me", "meaning_ru": "Пожалуйста, прости меня", "phrases": ["I'm sorry", "Forgive me"]},
    {"flower_id": "white_tulip", "emotion": "apology", "match_score": 0.9, "meaning_en": "Forgiveness", "meaning_ru": "Прощение", "phrases": ["I ask for forgiveness"]},
    {"flower_id": "blue_hydrangea", "emotion": "apology", "match_score": 0.85, "meaning_en": "Sincere apology", "meaning_ru": "Искреннее извинение", "phrases": ["Please understand", "I'm sorry"]},
    {"flower_id": "white_rose", "emotion": "apology", "match_score": 0.75, "meaning_en": "I am worthy of you", "meaning_ru": "Я достоин тебя"},
    {"flower_id": "white_peony", "emotion": "apology", "match_score": 0.8, "meaning_en": "Bashfulness and regret", "meaning_ru": "Застенчивость и сожаление"},

    # GRATITUDE
    {"flower_id": "pink_rose", "emotion": "gratitude", "match_score": 0.95, "meaning_en": "Thank you, with grace", "meaning_ru": "Благодарю с изяществом", "phrases": ["Thank you", "I appreciate you"]},
    {"flower_id": "pink_carnation", "emotion": "gratitude", "match_score": 0.95, "meaning_en": "I'll never forget you", "meaning_ru": "Я никогда тебя не забуду", "phrases": ["Gratitude", "Remembrance"]},
    {"flower_id": "blue_hydrangea", "emotion": "gratitude", "match_score": 0.9, "meaning_en": "Thank you for understanding", "meaning_ru": "Спасибо за понимание"},
    {"flower_id": "sweet_pea", "emotion": "gratitude", "match_score": 0.85, "meaning_en": "Thank you for a lovely time", "meaning_ru": "Спасибо за прекрасное время"},
    {"flower_id": "camellia", "emotion": "gratitude", "match_score": 0.85, "meaning_en": "Gratitude and admiration", "meaning_ru": "Благодарность и восхищение"},

    # SYMPATHY
    {"flower_id": "white_lily", "emotion": "sympathy", "match_score": 0.95, "meaning_en": "Sympathy and condolence", "meaning_ru": "Сочувствие и соболезнование"},
    {"flower_id": "white_rose", "emotion": "sympathy", "match_score": 0.9, "meaning_en": "Reverence and remembrance", "meaning_ru": "Почтение и память"},
    {"flower_id": "stargazer_lily", "emotion": "sympathy", "match_score": 0.85, "meaning_en": "Sympathy and encouragement", "meaning_ru": "Сочувствие и поддержка"},
    {"flower_id": "gladiolus", "emotion": "sympathy", "match_score": 0.8, "meaning_en": "Remembrance", "meaning_ru": "Память"},
    {"flower_id": "poppy_white", "emotion": "sympathy", "match_score": 0.85, "meaning_en": "Consolation and peace", "meaning_ru": "Утешение и покой"},

    # FRIENDSHIP
    {"flower_id": "yellow_rose", "emotion": "friendship", "match_score": 0.95, "meaning_en": "Friendship and joy", "meaning_ru": "Дружба и радость", "phrases": ["You're a wonderful friend"]},
    {"flower_id": "alstroemeria", "emotion": "friendship", "match_score": 0.95, "meaning_en": "Devoted friendship", "meaning_ru": "Преданная дружба"},
    {"flower_id": "iris", "emotion": "friendship", "match_score": 0.9, "meaning_en": "Your friendship means so much", "meaning_ru": "Твоя дружба так много значит"},
    {"flower_id": "white_chrysanthemum", "emotion": "friendship", "match_score": 0.85, "meaning_en": "You're a wonderful friend", "meaning_ru": "Ты замечательный друг"},
    {"flower_id": "gerbera_daisy", "emotion": "friendship", "match_score": 0.85, "meaning_en": "Cheerful friendship", "meaning_ru": "Жизнерадостная дружба"},

    # ROMANCE
    {"flower_id": "red_rose", "emotion": "romance", "match_score": 0.95, "meaning_en": "Romantic passion", "meaning_ru": "Романтическая страсть"},
    {"flower_id": "pink_peony", "emotion": "romance", "match_score": 0.95, "meaning_en": "Romance and prosperity", "meaning_ru": "Романтика и процветание"},
    {"flower_id": "lavender_rose", "emotion": "romance", "match_score": 0.9, "meaning_en": "Love at first sight", "meaning_ru": "Любовь с первого взгляда"},
    {"flower_id": "pink_hydrangea", "emotion": "romance", "match_score": 0.85, "meaning_en": "Heartfelt romance", "meaning_ru": "Искренняя романтика"},
    {"flower_id": "gardenia", "emotion": "romance", "match_score": 0.9, "meaning_en": "Secret love", "meaning_ru": "Тайная любовь"},

    # CONGRATULATIONS
    {"flower_id": "sunflower", "emotion": "congratulations", "match_score": 0.95, "meaning_en": "You are splendid", "meaning_ru": "Ты великолепен"},
    {"flower_id": "gerbera_daisy", "emotion": "congratulations", "match_score": 0.9, "meaning_en": "Cheerful congratulations", "meaning_ru": "Радостные поздравления"},
    {"flower_id": "orchid", "emotion": "congratulations", "match_score": 0.85, "meaning_en": "Elegant celebration", "meaning_ru": "Элегантное поздравление"},
    {"flower_id": "dahlia", "emotion": "congratulations", "match_score": 0.85, "meaning_en": "Dignity and elegance", "meaning_ru": "Достоинство и элегантность"},

    # RESPECT
    {"flower_id": "purple_tulip", "emotion": "respect", "match_score": 0.95, "meaning_en": "Royalty and respect", "meaning_ru": "Величие и уважение"},
    {"flower_id": "purple_orchid", "emotion": "respect", "match_score": 0.9, "meaning_en": "Admiration and dignity", "meaning_ru": "Восхищение и достоинство"},
    {"flower_id": "gladiolus", "emotion": "respect", "match_score": 0.85, "meaning_en": "Strength and integrity", "meaning_ru": "Сила и честность"},
    {"flower_id": "magnolia", "emotion": "respect", "match_score": 0.9, "meaning_en": "Nobility and dignity", "meaning_ru": "Благородство и достоинство"},

    # NEW BEGINNINGS
    {"flower_id": "white_rose", "emotion": "new_beginnings", "match_score": 0.95, "meaning_en": "Fresh start", "meaning_ru": "Новое начало"},
    {"flower_id": "daffodil", "emotion": "new_beginnings", "match_score": 0.95, "meaning_en": "New beginnings and rebirth", "meaning_ru": "Новое начало и возрождение"},
    {"flower_id": "daisy", "emotion": "new_beginnings", "match_score": 0.9, "meaning_en": "Innocence and new starts", "meaning_ru": "Невинность и новое начало"},
    {"flower_id": "lotus", "emotion": "new_beginnings", "match_score": 0.95, "meaning_en": "Rebirth and spiritual awakening", "meaning_ru": "Возрождение и духовное пробуждение"},

    # GET WELL
    {"flower_id": "sunflower", "emotion": "get_well", "match_score": 0.9, "meaning_en": "Warmth and happiness for recovery", "meaning_ru": "Тепло и счастье для выздоровления"},
    {"flower_id": "gerbera_daisy", "emotion": "get_well", "match_score": 0.95, "meaning_en": "Cheerfulness to brighten spirits", "meaning_ru": "Бодрость для поднятия духа"},
    {"flower_id": "daisy", "emotion": "get_well", "match_score": 0.85, "meaning_en": "Innocence and good wishes", "meaning_ru": "Невинность и добрые пожелания"},
    {"flower_id": "lavender", "emotion": "get_well", "match_score": 0.85, "meaning_en": "Serenity and calm healing", "meaning_ru": "Спокойствие и умиротворяющее исцеление"},

    # ADMIRATION
    {"flower_id": "pink_rose", "emotion": "admiration", "match_score": 0.95, "meaning_en": "Grace and admiration", "meaning_ru": "Изящество и восхищение"},
    {"flower_id": "sunflower", "emotion": "admiration", "match_score": 0.9, "meaning_en": "You are splendid", "meaning_ru": "Ты великолепен"},
    {"flower_id": "camellia", "emotion": "admiration", "match_score": 0.9, "meaning_en": "Perfect admiration", "meaning_ru": "Совершенное восхищение"},
    {"flower_id": "ranunculus", "emotion": "admiration", "match_score": 0.85, "meaning_en": "I am dazzled by your charms", "meaning_ru": "Я очарован тобой"},

    # REMEMBRANCE
    {"flower_id": "forget_me_not", "emotion": "remembrance", "match_score": 0.95, "meaning_en": "True love and memories", "meaning_ru": "Настоящая любовь и память"},
    {"flower_id": "poppy_red", "emotion": "remembrance", "match_score": 0.95, "meaning_en": "Remembrance and consolation", "meaning_ru": "Память и утешение"},
    {"flower_id": "zinnia", "emotion": "remembrance", "match_score": 0.9, "meaning_en": "Thinking of absent friends", "meaning_ru": "Думая о далёких друзьях"},
    {"flower_id": "gladiolus", "emotion": "remembrance", "match_score": 0.85, "meaning_en": "Remembrance with strength", "meaning_ru": "Память с силой"},

    # MOTHERS DAY
    {"flower_id": "pink_carnation", "emotion": "mothers_day", "match_score": 0.95, "meaning_en": "A mother's undying love", "meaning_ru": "Вечная материнская любовь"},
    {"flower_id": "pink_rose", "emotion": "mothers_day", "match_score": 0.9, "meaning_en": "Grace and gratitude for mom", "meaning_ru": "Благодарность маме"},
    {"flower_id": "pink_peony", "emotion": "mothers_day", "match_score": 0.85, "meaning_en": "Happy life for mom", "meaning_ru": "Счастливой жизни маме"},

    # WEDDING
    {"flower_id": "white_rose", "emotion": "wedding", "match_score": 0.95, "meaning_en": "Purity and new love", "meaning_ru": "Чистота и новая любовь"},
    {"flower_id": "white_lily", "emotion": "wedding", "match_score": 0.95, "meaning_en": "Majesty and purity", "meaning_ru": "Величие и чистота"},
    {"flower_id": "pink_peony", "emotion": "wedding", "match_score": 0.9, "meaning_en": "Happy marriage", "meaning_ru": "Счастливый брак"},
    {"flower_id": "calla_lily", "emotion": "wedding", "match_score": 0.9, "meaning_en": "Magnificent beauty", "meaning_ru": "Великолепная красота"},
    {"flower_id": "gardenia", "emotion": "wedding", "match_score": 0.85, "meaning_en": "Joy and purity", "meaning_ru": "Радость и чистота"},

    # BIRTHDAY
    {"flower_id": "gerbera_daisy", "emotion": "birthday", "match_score": 0.95, "meaning_en": "Cheerful birthday wishes", "meaning_ru": "Радостные пожелания"},
    {"flower_id": "sunflower", "emotion": "birthday", "match_score": 0.9, "meaning_en": "Bright and happy birthday", "meaning_ru": "Яркий и счастливый день рождения"},
    {"flower_id": "pink_rose", "emotion": "birthday", "match_score": 0.85, "meaning_en": "Graceful birthday wishes", "meaning_ru": "Изящные поздравления"},
    {"flower_id": "orchid", "emotion": "birthday", "match_score": 0.85, "meaning_en": "Beautiful and refined", "meaning_ru": "Красивое и утончённое"},

    # =========================================================================
    # NEW EMOTION MAPPINGS FROM EXPANDED SOURCES
    # =========================================================================

    # LOVE AT FIRST SIGHT
    {"flower_id": "lavender_rose", "emotion": "love_at_first_sight", "match_score": 0.95, "meaning_en": "Enchantment and mystery", "meaning_ru": "Очарование и тайна"},
    {"flower_id": "gloxinia", "emotion": "love_at_first_sight", "match_score": 0.95, "meaning_en": "Love at first sight", "meaning_ru": "Любовь с первого взгляда"},
    {"flower_id": "thornless_rose", "emotion": "love_at_first_sight", "match_score": 0.9, "meaning_en": "Early attachment", "meaning_ru": "Раннее увлечение"},
    {"flower_id": "coreopsis", "emotion": "love_at_first_sight", "match_score": 0.85, "meaning_en": "Love at first sight", "meaning_ru": "Любовь с первого взгляда"},

    # FIRST LOVE
    {"flower_id": "lilac", "emotion": "first_love", "match_score": 0.95, "meaning_en": "First emotions of love", "meaning_ru": "Первые чувства любви"},
    {"flower_id": "primrose", "emotion": "first_love", "match_score": 0.95, "meaning_en": "Young love, I can't live without you", "meaning_ru": "Юная любовь"},
    {"flower_id": "larkspur_purple", "emotion": "first_love", "match_score": 0.9, "meaning_en": "First love", "meaning_ru": "Первая любовь"},

    # FAREWELL / GOODBYE
    {"flower_id": "sweet_pea", "emotion": "farewell", "match_score": 0.95, "meaning_en": "Goodbye, departure", "meaning_ru": "Прощание, расставание"},
    {"flower_id": "cyclamen", "emotion": "farewell", "match_score": 0.9, "meaning_en": "Resignation and goodbye", "meaning_ru": "Смирение и прощание"},
    {"flower_id": "morning_glory", "emotion": "farewell", "match_score": 0.85, "meaning_en": "Fleeting beauty, mortality", "meaning_ru": "Мимолётная красота"},

    # GOOD LUCK
    {"flower_id": "bells_of_ireland", "emotion": "good_luck", "match_score": 0.95, "meaning_en": "Good luck and fortune", "meaning_ru": "Удача и благополучие"},
    {"flower_id": "heather_white", "emotion": "good_luck", "match_score": 0.95, "meaning_en": "Protection, wishes will come true", "meaning_ru": "Защита, желания сбудутся"},
    {"flower_id": "white_carnation", "emotion": "good_luck", "match_score": 0.85, "meaning_en": "Good luck", "meaning_ru": "Удача"},

    # PROTECTION / SHELTER
    {"flower_id": "fern", "emotion": "protection", "match_score": 0.95, "meaning_en": "Confidence and shelter", "meaning_ru": "Уверенность и защита"},
    {"flower_id": "holly", "emotion": "protection", "match_score": 0.9, "meaning_en": "Defense and domestic happiness", "meaning_ru": "Защита и домашнее счастье"},
    {"flower_id": "heather_white", "emotion": "protection", "match_score": 0.85, "meaning_en": "Protection", "meaning_ru": "Защита"},
    {"flower_id": "garlic", "emotion": "protection", "match_score": 0.8, "meaning_en": "Courage, strength, protection", "meaning_ru": "Мужество, сила, защита"},

    # ETERNAL LOVE / IMMORTAL LOVE
    {"flower_id": "amaranth", "emotion": "eternal_love", "match_score": 0.95, "meaning_en": "Immortality, unfading love", "meaning_ru": "Бессмертие, неугасающая любовь"},
    {"flower_id": "orange_blossom", "emotion": "eternal_love", "match_score": 0.95, "meaning_en": "Eternal love", "meaning_ru": "Вечная любовь"},
    {"flower_id": "forget_me_not", "emotion": "eternal_love", "match_score": 0.9, "meaning_en": "True love, constancy", "meaning_ru": "Истинная любовь, постоянство"},

    # MARRIAGE / WEDDING (expanded)
    {"flower_id": "orange_blossom", "emotion": "wedding", "match_score": 0.95, "meaning_en": "Marriage and fruitfulness", "meaning_ru": "Брак и плодородие"},
    {"flower_id": "stephanotis", "emotion": "wedding", "match_score": 0.95, "meaning_en": "Happiness in marriage", "meaning_ru": "Счастье в браке"},
    {"flower_id": "myrtle", "emotion": "wedding", "match_score": 0.9, "meaning_en": "Love, emblem of marriage", "meaning_ru": "Любовь, символ брака"},
    {"flower_id": "ivy", "emotion": "wedding", "match_score": 0.85, "meaning_en": "Wedded love, fidelity", "meaning_ru": "Супружеская любовь, верность"},
    {"flower_id": "lily_of_the_valley", "emotion": "wedding", "match_score": 0.9, "meaning_en": "Return to happiness, purity", "meaning_ru": "Возвращение к счастью, чистота"},

    # FIDELITY / FAITHFULNESS
    {"flower_id": "ivy", "emotion": "fidelity", "match_score": 0.95, "meaning_en": "Fidelity and affection", "meaning_ru": "Верность и привязанность"},
    {"flower_id": "violet_blue", "emotion": "fidelity", "match_score": 0.95, "meaning_en": "Faithfulness, I'll always be true", "meaning_ru": "Верность, я всегда буду верен"},
    {"flower_id": "honeysuckle_coral", "emotion": "fidelity", "match_score": 0.9, "meaning_en": "Fidelity, devoted love", "meaning_ru": "Верность, преданная любовь"},

    # HOPE
    {"flower_id": "iris", "emotion": "hope", "match_score": 0.95, "meaning_en": "Faith, hope, wisdom", "meaning_ru": "Вера, надежда, мудрость"},
    {"flower_id": "pine", "emotion": "hope", "match_score": 0.9, "meaning_en": "Hope and pity", "meaning_ru": "Надежда и сострадание"},
    {"flower_id": "crocus", "emotion": "hope", "match_score": 0.85, "meaning_en": "Cheerfulness and rebirth", "meaning_ru": "Бодрость и возрождение"},

    # INNOCENCE
    {"flower_id": "daisy", "emotion": "innocence", "match_score": 0.95, "meaning_en": "Innocence and purity", "meaning_ru": "Невинность и чистота"},
    {"flower_id": "lilac_white", "emotion": "innocence", "match_score": 0.95, "meaning_en": "Youthful innocence", "meaning_ru": "Юношеская невинность"},
    {"flower_id": "rosebud_white", "emotion": "innocence", "match_score": 0.9, "meaning_en": "Girlhood, too young for love", "meaning_ru": "Девичество"},
    {"flower_id": "orange_blossom", "emotion": "innocence", "match_score": 0.85, "meaning_en": "Innocence", "meaning_ru": "Невинность"},

    # SECRET LOVE
    {"flower_id": "gardenia", "emotion": "secret_love", "match_score": 0.95, "meaning_en": "Secret love, you're lovely", "meaning_ru": "Тайная любовь"},
    {"flower_id": "maidenhair_fern", "emotion": "secret_love", "match_score": 0.95, "meaning_en": "Secret bond of love", "meaning_ru": "Тайные узы любви"},
    {"flower_id": "violet", "emotion": "secret_love", "match_score": 0.85, "meaning_en": "Modesty, secret love", "meaning_ru": "Скромность, тайная любовь"},

    # CONSOLATION / COMFORT
    {"flower_id": "poppy_white", "emotion": "consolation", "match_score": 0.95, "meaning_en": "Consolation and peace", "meaning_ru": "Утешение и покой"},
    {"flower_id": "geranium_scarlet", "emotion": "consolation", "match_score": 0.9, "meaning_en": "Comforting, consolation", "meaning_ru": "Утешение"},
    {"flower_id": "snowdrop", "emotion": "consolation", "match_score": 0.85, "meaning_en": "Consolation, friendship in trouble", "meaning_ru": "Утешение, дружба в беде"},

    # PATIENCE / ENDURANCE
    {"flower_id": "cactus_flower", "emotion": "patience", "match_score": 0.95, "meaning_en": "Endurance, warmth", "meaning_ru": "Выносливость, тепло"},
    {"flower_id": "aster", "emotion": "patience", "match_score": 0.9, "meaning_en": "Patience, love", "meaning_ru": "Терпение, любовь"},
    {"flower_id": "chamomile", "emotion": "patience", "match_score": 0.85, "meaning_en": "Energy in adversity, patience", "meaning_ru": "Энергия в невзгодах, терпение"},

    # THINKING OF YOU
    {"flower_id": "pansy", "emotion": "thinking_of_you", "match_score": 0.95, "meaning_en": "Think of me, pleasant thoughts", "meaning_ru": "Думай обо мне"},
    {"flower_id": "zinnia", "emotion": "thinking_of_you", "match_score": 0.95, "meaning_en": "Thinking of absent friends", "meaning_ru": "Думая об отсутствующих друзьях"},
    {"flower_id": "forget_me_not", "emotion": "thinking_of_you", "match_score": 0.9, "meaning_en": "True love and memories", "meaning_ru": "Истинная любовь и память"},

    # DESIRE / LONGING
    {"flower_id": "jonquil", "emotion": "desire", "match_score": 0.95, "meaning_en": "Love me, desire", "meaning_ru": "Люби меня, желание"},
    {"flower_id": "orange_rose", "emotion": "desire", "match_score": 0.95, "meaning_en": "Desire and enthusiasm", "meaning_ru": "Желание и энтузиазм"},
    {"flower_id": "camellia", "emotion": "desire", "match_score": 0.85, "meaning_en": "Longing", "meaning_ru": "Тоска"},

    # CHEERFULNESS / JOY
    {"flower_id": "crocus", "emotion": "joy", "match_score": 0.95, "meaning_en": "Cheerfulness, youthful gladness", "meaning_ru": "Бодрость, юношеская радость"},
    {"flower_id": "coreopsis", "emotion": "joy", "match_score": 0.95, "meaning_en": "Always cheerful", "meaning_ru": "Всегда весёлый"},
    {"flower_id": "gerbera_daisy", "emotion": "joy", "match_score": 0.9, "meaning_en": "Cheerfulness and innocence", "meaning_ru": "Бодрость и невинность"},
    {"flower_id": "sunflower", "emotion": "joy", "match_score": 0.9, "meaning_en": "Happiness and adoration", "meaning_ru": "Счастье и обожание"},
    {"flower_id": "dandelion", "emotion": "joy", "match_score": 0.8, "meaning_en": "Happiness", "meaning_ru": "Счастье"},

    # WELCOME
    {"flower_id": "wisteria", "emotion": "welcome", "match_score": 0.95, "meaning_en": "Welcome, steadfast", "meaning_ru": "Добро пожаловать"},

    # PRIDE / ACHIEVEMENT
    {"flower_id": "amaryllis", "emotion": "pride", "match_score": 0.95, "meaning_en": "Pride, determination", "meaning_ru": "Гордость, решимость"},
    {"flower_id": "tiger_lily", "emotion": "pride", "match_score": 0.9, "meaning_en": "Wealth and pride", "meaning_ru": "Богатство и гордость"},
    {"flower_id": "gladiolus", "emotion": "pride", "match_score": 0.85, "meaning_en": "Strength, integrity", "meaning_ru": "Сила, честность"},

    # CONFESSION / DECLARATION
    {"flower_id": "rosebud_moss", "emotion": "confession", "match_score": 0.95, "meaning_en": "Confessions of love", "meaning_ru": "Признание в любви"},
    {"flower_id": "red_tulip", "emotion": "confession", "match_score": 0.95, "meaning_en": "Declaration of love", "meaning_ru": "Признание в любви"},

    # MATERNAL LOVE / MOTHER
    {"flower_id": "pink_carnation", "emotion": "maternal_love", "match_score": 0.95, "meaning_en": "Mother's undying love", "meaning_ru": "Вечная материнская любовь"},
    {"flower_id": "moss", "emotion": "maternal_love", "match_score": 0.9, "meaning_en": "Maternal love, charity", "meaning_ru": "Материнская любовь"},
    {"flower_id": "daylily", "emotion": "maternal_love", "match_score": 0.85, "meaning_en": "Chinese emblem for mother", "meaning_ru": "Китайский символ матери"},
    {"flower_id": "cactus_flower", "emotion": "maternal_love", "match_score": 0.8, "meaning_en": "Maternal love", "meaning_ru": "Материнская любовь"},

    # PROSPERITY / WEALTH
    {"flower_id": "pink_peony", "emotion": "prosperity", "match_score": 0.95, "meaning_en": "Prosperity and good fortune", "meaning_ru": "Процветание и удача"},
    {"flower_id": "poppy_yellow", "emotion": "prosperity", "match_score": 0.95, "meaning_en": "Wealth and success", "meaning_ru": "Богатство и успех"},
    {"flower_id": "cattail", "emotion": "prosperity", "match_score": 0.85, "meaning_en": "Peace and prosperity", "meaning_ru": "Мир и процветание"},
    {"flower_id": "tiger_lily", "emotion": "prosperity", "match_score": 0.85, "meaning_en": "Wealth", "meaning_ru": "Богатство"},

    # VICTORY / CONQUEST
    {"flower_id": "nasturtium", "emotion": "victory", "match_score": 0.95, "meaning_en": "Conquest, victory in battle", "meaning_ru": "Победа в битве"},
    {"flower_id": "gladiolus", "emotion": "victory", "match_score": 0.9, "meaning_en": "Flower of the gladiators", "meaning_ru": "Цветок гладиаторов"},

    # PEACE / TRANQUILITY
    {"flower_id": "hellebore", "emotion": "peace", "match_score": 0.95, "meaning_en": "Tranquilize my anxiety", "meaning_ru": "Успокой мою тревогу"},
    {"flower_id": "cattail", "emotion": "peace", "match_score": 0.9, "meaning_en": "Peace and prosperity", "meaning_ru": "Мир и процветание"},
    {"flower_id": "lavender", "emotion": "peace", "match_score": 0.9, "meaning_en": "Serenity, calm", "meaning_ru": "Спокойствие"},
    {"flower_id": "poppy_white", "emotion": "peace", "match_score": 0.85, "meaning_en": "Peace, sleep, rest", "meaning_ru": "Покой, сон, отдых"},

    # ELEGANCE / REFINEMENT
    {"flower_id": "orchid", "emotion": "elegance", "match_score": 0.95, "meaning_en": "Luxury, beauty, refinement", "meaning_ru": "Роскошь, красота, утончённость"},
    {"flower_id": "calla_lily", "emotion": "elegance", "match_score": 0.95, "meaning_en": "Magnificent beauty", "meaning_ru": "Великолепная красота"},
    {"flower_id": "dahlia", "emotion": "elegance", "match_score": 0.9, "meaning_en": "Elegance and dignity", "meaning_ru": "Элегантность и достоинство"},

    # UNITY
    {"flower_id": "unity_rose", "emotion": "unity", "match_score": 0.95, "meaning_en": "Unity", "meaning_ru": "Единство"},

    # WARNING / CAUTION (negative flowers)
    {"flower_id": "begonia", "emotion": "warning", "match_score": 0.95, "meaning_en": "Beware, caution", "meaning_ru": "Остерегайся"},
    {"flower_id": "monkshood", "emotion": "warning", "match_score": 0.95, "meaning_en": "Beware, a deadly foe is near", "meaning_ru": "Остерегайся, враг рядом"},
]


# =============================================================================
# SEED DATA - CULTURAL TABOOS
# =============================================================================

CULTURAL_CONTEXTS_DATA = [
    # CHINA
    {"flower_id": "white_chrysanthemum", "region": "CN", "is_taboo": True, "taboo_reason": "Associated with funerals and mourning", "taboo_occasions": ["birthday", "wedding", "celebration"], "recommended_occasions": ["funeral", "memorial"]},
    {"flower_id": "yellow_chrysanthemum", "region": "CN", "is_taboo": True, "taboo_reason": "Associated with death and funerals", "taboo_occasions": ["birthday", "wedding", "celebration"]},
    {"flower_id": "white_lily", "region": "CN", "is_taboo": True, "taboo_reason": "White is color of mourning in Chinese culture", "taboo_occasions": ["birthday", "wedding"]},
    {"flower_id": "red_rose", "region": "CN", "is_taboo": False, "meaning": "Good fortune and love", "recommended_occasions": ["wedding", "romance"]},
    {"flower_id": "pink_peony", "region": "CN", "is_taboo": False, "meaning": "Prosperity and honor, national flower", "recommended_occasions": ["wedding", "celebration", "new_year"]},
    {"flower_id": "orchid", "region": "CN", "is_taboo": False, "meaning": "Fertility and many children", "recommended_occasions": ["wedding", "birthday"]},

    # JAPAN
    {"flower_id": "white_chrysanthemum", "region": "JP", "is_taboo": True, "taboo_reason": "Used at funerals and Buddhist memorials", "taboo_occasions": ["birthday", "celebration"]},
    {"flower_id": "lotus", "region": "JP", "is_taboo": True, "taboo_reason": "Connected to death and memorials", "taboo_occasions": ["birthday", "celebration"]},
    {"flower_id": "white_lily", "region": "JP", "is_taboo": False, "meaning": "Purity, suitable for weddings", "recommended_occasions": ["wedding"]},
    {"flower_id": "red_rose", "region": "JP", "is_taboo": False, "meaning": "Passionate love", "recommended_occasions": ["romance", "anniversary"]},
    {"flower_id": "pink_tulip", "region": "JP", "is_taboo": False, "meaning": "Thoughtfulness and caring", "recommended_occasions": ["any"]},

    # RUSSIA
    {"flower_id": "yellow_rose", "region": "RU", "is_taboo": True, "taboo_reason": "Symbolizes separation and infidelity", "taboo_occasions": ["romance", "anniversary"]},
    {"flower_id": "yellow_tulip", "region": "RU", "is_taboo": True, "taboo_reason": "Suggests separation", "taboo_occasions": ["romance", "wedding"]},
    {"flower_id": "red_rose", "region": "RU", "is_taboo": False, "meaning": "Passionate romantic love", "recommended_occasions": ["romance", "anniversary"]},
    {"flower_id": "white_rose", "region": "RU", "is_taboo": False, "meaning": "Purity and innocence", "recommended_occasions": ["wedding"]},

    # FRANCE
    {"flower_id": "white_chrysanthemum", "region": "FR", "is_taboo": True, "taboo_reason": "Strictly reserved for funerals and graves", "taboo_occasions": ["birthday", "romance", "celebration"]},
    {"flower_id": "yellow_carnation", "region": "FR", "is_taboo": True, "taboo_reason": "Signifies disappointment and disdain", "taboo_occasions": ["any_positive"]},
    {"flower_id": "red_rose", "region": "FR", "is_taboo": False, "meaning": "Romantic love", "recommended_occasions": ["romance"]},
    {"flower_id": "orchid", "region": "FR", "is_taboo": False, "meaning": "Elegance and luxury", "recommended_occasions": ["any"]},

    # GERMANY
    {"flower_id": "white_lily", "region": "DE", "is_taboo": True, "taboo_reason": "Used at funeral ceremonies", "taboo_occasions": ["birthday", "celebration"]},
    {"flower_id": "white_rose", "region": "DE", "is_taboo": True, "taboo_reason": "Associated with condolences", "taboo_occasions": ["celebration"]},
    {"flower_id": "red_rose", "region": "DE", "is_taboo": False, "meaning": "Romantic expression", "recommended_occasions": ["romance", "anniversary"]},

    # ITALY
    {"flower_id": "white_chrysanthemum", "region": "IT", "is_taboo": True, "taboo_reason": "Universally associated with death and mourning", "taboo_occasions": ["any_positive"]},
    {"flower_id": "yellow_rose", "region": "IT", "is_taboo": True, "taboo_reason": "May symbolize jealousy or infidelity", "taboo_occasions": ["romance"]},

    # KOREA
    {"flower_id": "white_chrysanthemum", "region": "KR", "is_taboo": True, "taboo_reason": "Mourning associations", "taboo_occasions": ["celebration", "birthday"]},

    # BRAZIL
    {"flower_id": "purple_orchid", "region": "BR", "is_taboo": True, "taboo_reason": "Purple is linked to mourning", "taboo_occasions": ["celebration", "birthday"]},
    {"flower_id": "red_rose", "region": "BR", "is_taboo": False, "meaning": "Passionate love", "recommended_occasions": ["romance"]},

    # MEXICO
    {"flower_id": "marigold", "region": "MX", "is_taboo": True, "taboo_reason": "Associated with Day of the Dead (Día de los Muertos)", "taboo_occasions": ["birthday", "celebration"]},
    {"flower_id": "yellow_rose", "region": "MX", "is_taboo": True, "taboo_reason": "Connotes death", "taboo_occasions": ["celebration"]},

    # INDIA
    {"flower_id": "frangipani", "region": "IN", "is_taboo": True, "taboo_reason": "Connected to funeral rites", "taboo_occasions": ["celebration", "birthday"]},
    {"flower_id": "marigold", "region": "IN", "is_taboo": False, "meaning": "Sacred, used in religious ceremonies", "recommended_occasions": ["religious", "wedding"]},
    {"flower_id": "lotus", "region": "IN", "is_taboo": False, "meaning": "Sacred symbol of purity and enlightenment", "recommended_occasions": ["religious", "spiritual"]},

    # UAE
    {"flower_id": "yellow_rose", "region": "AE", "is_taboo": True, "taboo_reason": "Associated with negative emotions", "taboo_occasions": ["any"]},

    # PAKISTAN
    {"flower_id": "yellow_tulip", "region": "PK", "is_taboo": True, "taboo_reason": "Yellow is considered offensive", "taboo_occasions": ["any"]},
    {"flower_id": "white_rose", "region": "PK", "is_taboo": True, "taboo_reason": "Used at weddings, inappropriate for other occasions", "taboo_occasions": ["casual"]},

    # CANADA
    {"flower_id": "white_lily", "region": "CA", "is_taboo": True, "taboo_reason": "Funeral associations", "taboo_occasions": ["celebration"]},
    {"flower_id": "white_chrysanthemum", "region": "CA", "is_taboo": True, "taboo_reason": "Funeral associations", "taboo_occasions": ["celebration"]},
    {"flower_id": "red_rose", "region": "CA", "is_taboo": False, "meaning": "Romance", "recommended_occasions": ["romance", "valentines"]},
    {"flower_id": "daisy", "region": "CA", "is_taboo": False, "meaning": "Innocence", "recommended_occasions": ["valentines", "any"]},

    # USA (generally relaxed)
    {"flower_id": "red_rose", "region": "US", "is_taboo": False, "meaning": "Romantic love", "recommended_occasions": ["romance", "valentines", "anniversary"]},
    {"flower_id": "yellow_rose", "region": "US", "is_taboo": False, "meaning": "Friendship and cordial relations", "recommended_occasions": ["friendship", "get_well"]},
    {"flower_id": "white_lily", "region": "US", "is_taboo": False, "meaning": "Sympathy and condolence", "recommended_occasions": ["funeral", "sympathy"]},

    # ARGENTINA
    {"flower_id": "white_rose", "region": "AR", "is_taboo": True, "taboo_reason": "Associated with mourning", "taboo_occasions": ["celebration"]},
    {"flower_id": "purple_orchid", "region": "AR", "is_taboo": True, "taboo_reason": "Purple associated with mourning", "taboo_occasions": ["celebration"]},

    # EGYPT
    {"flower_id": "red_rose", "region": "EG", "is_taboo": True, "taboo_reason": "Flowers generally represent death in Egypt", "taboo_occasions": ["casual"]},

    # SOUTH AFRICA
    {"flower_id": "white_lily", "region": "ZA", "is_taboo": True, "taboo_reason": "Associated with death and funerals", "taboo_occasions": ["celebration"]},
    {"flower_id": "protea", "region": "ZA", "is_taboo": False, "meaning": "National flower - diversity and courage", "recommended_occasions": ["any"]},

    # TURKEY
    {"flower_id": "orchid", "region": "TR", "is_taboo": False, "meaning": "Perfect host gift", "recommended_occasions": ["hospitality", "gift"]},
    {"flower_id": "red_tulip", "region": "TR", "is_taboo": False, "meaning": "Purity and love, national symbol", "recommended_occasions": ["romance", "any"]},
]


# =============================================================================
# SEED DATA - REGIONAL NUMBER RULES
# =============================================================================

REGION_NUMBER_RULES_DATA = [
    {
        "region": "RU",
        "preferred_numbers": [1, 3, 5, 7, 9, 11, 15, 21, 25, 51, 101],
        "taboo_numbers": [2, 4, 6, 8, 10, 12],
        "rule_description": "Only odd numbers for living recipients. Even numbers are for funerals.",
        "number_meanings": {
            "1": "Sign of respect",
            "3": "Invitation to a date",
            "5": "Declaration of love",
            "7": "Declaration of love",
            "9": "Friendship and good intentions",
            "11": "For close friends and loved ones"
        }
    },
    {
        "region": "DE",
        "preferred_numbers": [3, 5, 7, 9, 11],
        "taboo_numbers": [2, 4, 6, 13],
        "rule_description": "Odd numbers are preferred. Even numbers and 13 are unlucky.",
        "number_meanings": {}
    },
    {
        "region": "FR",
        "preferred_numbers": [3, 5, 7, 9, 11],
        "taboo_numbers": [13],
        "rule_description": "Odd numbers preferred. 13 is unlucky.",
        "number_meanings": {}
    },
    {
        "region": "CN",
        "preferred_numbers": [2, 6, 8, 9, 99],
        "taboo_numbers": [4, 14, 24],
        "rule_description": "Even numbers preferred. 4 sounds like 'death'. 8 is very lucky. 9 means longevity.",
        "number_meanings": {
            "2": "Pairs are auspicious",
            "6": "Smooth and successful",
            "8": "Wealth and prosperity",
            "9": "Longevity",
            "99": "Everlasting love"
        }
    },
    {
        "region": "JP",
        "preferred_numbers": [3, 5, 7, 8],
        "taboo_numbers": [4, 9],
        "rule_description": "4 sounds like 'death', 9 sounds like 'suffering'. Odd numbers generally preferred except 9.",
        "number_meanings": {}
    },
    {
        "region": "AR",
        "preferred_numbers": [1, 3, 5, 7, 9, 11],
        "taboo_numbers": [13],
        "rule_description": "13 is bad luck.",
        "number_meanings": {}
    },
    {
        "region": "BG",
        "preferred_numbers": [1, 3, 5, 7, 9],
        "taboo_numbers": [2, 4],
        "rule_description": "Odd numbers for gifts to living. Even numbers for funerals.",
        "number_meanings": {}
    },
    {
        "region": "US",
        "preferred_numbers": None,  # No strict rules
        "taboo_numbers": [13],
        "rule_description": "Generally no strict number rules. 13 sometimes avoided.",
        "number_meanings": {
            "12": "A dozen - classic romantic gesture"
        }
    },
]


# =============================================================================
# SEED DATA - COLOR MEANINGS
# =============================================================================

COLOR_MEANINGS_DATA = [
    # Universal meanings
    {"color": "red", "region": "universal", "positive_meanings": ["love", "passion", "romance", "desire", "courage"], "negative_meanings": ["anger", "danger"], "notes": "Most universally associated with romantic love"},
    {"color": "pink", "region": "universal", "positive_meanings": ["grace", "gentleness", "admiration", "joy", "femininity"], "negative_meanings": [], "notes": "Softer expression of love, ideal for young romance"},
    {"color": "white", "region": "universal", "positive_meanings": ["purity", "innocence", "peace", "new beginnings"], "negative_meanings": [], "notes": "In Western cultures: weddings. CAUTION: mourning in Asian cultures"},
    {"color": "yellow", "region": "universal", "positive_meanings": ["friendship", "joy", "cheerfulness", "new beginnings"], "negative_meanings": ["jealousy"], "notes": "CAUTION: negative in Russia, UAE, some Latin countries"},
    {"color": "orange", "region": "universal", "positive_meanings": ["enthusiasm", "energy", "warmth", "excitement"], "negative_meanings": [], "notes": "Uplifting and energetic"},
    {"color": "purple", "region": "universal", "positive_meanings": ["royalty", "dignity", "admiration", "mystery"], "negative_meanings": [], "notes": "CAUTION: mourning in Latin America, Brazil"},
    {"color": "blue", "region": "universal", "positive_meanings": ["tranquility", "peace", "trust", "loyalty"], "negative_meanings": [], "notes": "Calming and serene"},
    {"color": "lavender", "region": "universal", "positive_meanings": ["grace", "elegance", "refinement", "calm"], "negative_meanings": [], "notes": "Associated with serenity"},

    # Regional specifics
    {"color": "white", "region": "CN", "positive_meanings": [], "negative_meanings": ["death", "mourning", "funerals"], "notes": "Strongly associated with death. Avoid for celebrations."},
    {"color": "white", "region": "JP", "positive_meanings": ["purity"], "negative_meanings": ["death", "mourning"], "notes": "Used in funerals, but also weddings. Context matters."},
    {"color": "yellow", "region": "RU", "positive_meanings": [], "negative_meanings": ["separation", "infidelity", "betrayal"], "notes": "Yellow flowers suggest the relationship is ending"},
    {"color": "purple", "region": "BR", "positive_meanings": [], "negative_meanings": ["mourning", "death"], "notes": "Strictly associated with funerals"},
    {"color": "purple", "region": "MX", "positive_meanings": [], "negative_meanings": ["funerals", "death"], "notes": "Reserved for funerals"},
    {"color": "red", "region": "CN", "positive_meanings": ["good fortune", "luck", "celebration", "joy"], "negative_meanings": [], "notes": "Very auspicious color in Chinese culture"},
]


# =============================================================================
# DATABASE SEEDING FUNCTION
# =============================================================================

def seed_database(session):
    """
    Populate database with all seed data.

    Usage:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        engine = create_engine('sqlite:///flowers.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        seed_database(session)
    """
    # Seed Flowers
    for data in FLOWERS_DATA:
        flower = Flower(**data)
        session.merge(flower)  # merge to handle re-runs

    # Seed Flower Meanings
    for data in FLOWER_MEANINGS_DATA:
        meaning = FlowerMeaning(**data)
        session.add(meaning)

    # Seed Cultural Contexts
    for data in CULTURAL_CONTEXTS_DATA:
        context = FlowerCulturalContext(**data)
        session.add(context)

    # Seed Number Rules
    for data in REGION_NUMBER_RULES_DATA:
        rule = RegionNumberRule(**data)
        session.add(rule)

    # Seed Color Meanings
    for data in COLOR_MEANINGS_DATA:
        color = FlowerColorMeaning(**data)
        session.add(color)

    session.commit()
    print(f"Seeded {len(FLOWERS_DATA)} flowers")
    print(f"Seeded {len(FLOWER_MEANINGS_DATA)} flower meanings")
    print(f"Seeded {len(CULTURAL_CONTEXTS_DATA)} cultural contexts")
    print(f"Seeded {len(REGION_NUMBER_RULES_DATA)} regional number rules")
    print(f"Seeded {len(COLOR_MEANINGS_DATA)} color meanings")


# =============================================================================
# DATABASE LOOKUP FUNCTIONS (SQLite-backed)
# =============================================================================

def _row_to_flower_dict(row) -> dict:
    """Convert SQLite row to flower dict with JSON parsing."""
    result = dict(row)
    # Parse JSON fields
    if result.get("primary_meanings"):
        try:
            result["primary_meanings"] = json.loads(result["primary_meanings"])
        except (json.JSONDecodeError, TypeError):
            result["primary_meanings"] = []
    return result


def _row_to_meaning_dict(row) -> dict:
    """Convert SQLite row to meaning dict with JSON parsing."""
    result = dict(row)
    if result.get("phrases"):
        try:
            result["phrases"] = json.loads(result["phrases"])
        except (json.JSONDecodeError, TypeError):
            result["phrases"] = []
    return result


def get_flowers_by_emotion(emotion: str, top_n: int = 5) -> tuple:
    """
    Get best flowers for an emotion from SQLite.

    Returns tuple of meaning dicts sorted by match_score descending.
    """
    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        matches = [m for m in FLOWER_MEANINGS_DATA if m["emotion"] == emotion]
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return tuple(matches[:top_n])

    with get_flower_db() as conn:
        cursor = conn.execute("""
            SELECT flower_id, emotion, occasion, match_score, meaning_en, meaning_ru, phrases
            FROM flower_meanings
            WHERE emotion = ?
            ORDER BY match_score DESC, RANDOM()
            LIMIT ?
        """, (emotion, top_n))
        return tuple(_row_to_meaning_dict(row) for row in cursor.fetchall())


def get_flowers_by_emotions(
    emotions: list,
    top_n_per: int = 5,
    primary_emotion: Optional[str] = None,
    primary_top_n: Optional[int] = None,
) -> dict:
    """
    Batch lookup: get best flowers for multiple emotions in ONE query.

    Args:
        emotions: List of emotion strings (e.g., ["love", "gratitude"])
        top_n_per: Default max flowers per emotion (default 5)
        primary_emotion: If set, this emotion gets primary_top_n instead
        primary_top_n: Limit for primary emotion (default None = use top_n_per)

    Returns:
        Dict mapping emotion -> tuple of meaning dicts.
        Missing emotions return empty tuple.

    Note:
        - Uses window functions for per-emotion limiting
        - ORDER BY match_score DESC, RANDOM() (non-deterministic tiebreaker)
        - Fallback schema may differ from DB (no 'occasion' in FLOWER_MEANINGS_DATA)
    """
    if not emotions:
        return {}

    # Normalize: lowercase, deduplicate preserving order
    seen = set()
    normalized = []
    for e in emotions:
        e_lower = e.lower()
        if e_lower not in seen:
            seen.add(e_lower)
            normalized.append(e_lower)

    # Determine per-emotion limits
    primary_lower = primary_emotion.lower() if primary_emotion else None
    effective_primary_top_n = primary_top_n if primary_top_n else top_n_per

    if not check_flower_db_exists():
        # Fallback to in-memory data
        # Note: FLOWER_MEANINGS_DATA lacks 'occasion' key (matches existing behavior)
        result = {}
        for emotion in normalized:
            limit = effective_primary_top_n if emotion == primary_lower else top_n_per
            matches = [m for m in FLOWER_MEANINGS_DATA if m["emotion"] == emotion]
            matches.sort(key=lambda x: x["match_score"], reverse=True)
            result[emotion] = tuple(matches[:limit])
        return result

    # Build query with window function
    # Note: We fetch max(primary_top_n, top_n_per) per emotion then filter in Python.
    # This may overfetch ~2x for secondary emotions, but simplifies SQL.
    # Acceptable tradeoff: ~5 extra rows << query round-trip savings.
    max_limit = max(effective_primary_top_n, top_n_per)
    placeholders = ",".join("?" * len(normalized))
    query = f"""
        WITH ranked AS (
            SELECT
                flower_id, emotion, occasion, match_score,
                meaning_en, meaning_ru, phrases,
                ROW_NUMBER() OVER (
                    PARTITION BY emotion
                    ORDER BY match_score DESC, RANDOM()
                ) as rn
            FROM flower_meanings
            WHERE emotion IN ({placeholders})
        )
        SELECT flower_id, emotion, occasion, match_score,
               meaning_en, meaning_ru, phrases
        FROM ranked
        WHERE rn <= ?
    """

    with get_flower_db() as conn:
        cursor = conn.execute(query, (*normalized, max_limit))

        # Group and apply per-emotion limits
        result = {e: [] for e in normalized}
        for row in cursor.fetchall():
            emotion = row["emotion"]
            limit = effective_primary_top_n if emotion == primary_lower else top_n_per
            if len(result[emotion]) < limit:
                result[emotion].append(_row_to_meaning_dict(row))

        return {e: tuple(matches) for e, matches in result.items()}


def get_flower_by_id(flower_id: str) -> Optional[dict]:
    """
    Get flower by ID from SQLite.

    Returns flower dict or None if not found.
    """
    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        for f in FLOWERS_DATA:
            if f["id"] == flower_id:
                return f
        return None

    with get_flower_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM flowers WHERE id = ?", (flower_id,)
        )
        row = cursor.fetchone()
        return _row_to_flower_dict(row) if row else None


def get_flowers_by_ids(flower_ids: tuple) -> dict:
    """
    Batch lookup: get multiple flowers by IDs from SQLite.

    Returns dict mapping flower_id -> flower dict (None if not found).
    """
    if not flower_ids:
        return {}

    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        result = {}
        for fid in flower_ids:
            for f in FLOWERS_DATA:
                if f["id"] == fid:
                    result[fid] = f
                    break
            else:
                result[fid] = None
        return result

    placeholders = ",".join("?" * len(flower_ids))
    with get_flower_db() as conn:
        cursor = conn.execute(
            f"SELECT * FROM flowers WHERE id IN ({placeholders})", flower_ids
        )
        found = {row["id"]: _row_to_flower_dict(row) for row in cursor.fetchall()}
        # Return dict with None for missing IDs
        return {fid: found.get(fid) for fid in flower_ids}


def get_cultural_warnings(flower_id: str, region: str) -> Optional[dict]:
    """
    Get cultural taboo warning for flower in region from SQLite.

    Returns cultural context dict if flower is taboo in region, else None.
    """
    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        for ctx in CULTURAL_CONTEXTS_DATA:
            if ctx["flower_id"] == flower_id and ctx["region"] == region:
                if ctx["is_taboo"]:
                    return ctx
        return None

    with get_flower_db() as conn:
        cursor = conn.execute("""
            SELECT flower_id, region, meaning, is_taboo, taboo_reason,
                   taboo_occasions, recommended_occasions
            FROM flower_cultural_contexts
            WHERE flower_id = ? AND region = ? AND is_taboo = 1
        """, (flower_id, region))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ("taboo_occasions", "recommended_occasions"):
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        result[field] = []
            return result
        return None


def get_number_rules(region: str) -> Optional[dict]:
    """
    Get flower quantity rules for region from SQLite.

    Returns rule dict or None if no rules for region.
    """
    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        for rule in REGION_NUMBER_RULES_DATA:
            if rule["region"] == region:
                return rule
        return None

    with get_flower_db() as conn:
        cursor = conn.execute("""
            SELECT region, avoid_numbers, prefer_numbers, notes
            FROM region_number_rules
            WHERE region = ?
        """, (region,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ("avoid_numbers", "prefer_numbers"):
                if result.get(field):
                    try:
                        result[field] = json.loads(result[field])
                    except (json.JSONDecodeError, TypeError):
                        result[field] = []
            return result
        return None


def get_all_flower_ids() -> List[str]:
    """
    Get list of all valid flower IDs from SQLite.
    """
    if not check_flower_db_exists():
        # Fallback to in-memory data if DB not initialized
        return [f["id"] for f in FLOWERS_DATA]

    with get_flower_db() as conn:
        cursor = conn.execute("SELECT id FROM flowers")
        return [row["id"] for row in cursor.fetchall()]


# =============================================================================
# DATA SOURCES CITATION
# =============================================================================

DATA_SOURCES = """
This flower database was compiled from the following authoritative sources:

1. The Old Farmer's Almanac - Flower Meanings: The Language of Flowers
   https://www.almanac.com/flower-meanings-language-flowers

2. FromYouFlowers - Meaning of Flowers A-Z
   https://www.fromyouflowers.com/flower-resource/meaning-of-flowers.htm

3. Lovingly - Flower Meanings Encyclopedia
   https://www.lovingly.com/flower-meanings

4. Petal & Poem - Guide to Flowers to Avoid in Different Cultures
   https://www.petalandpoem.com/locations/guide-to-flowers-to-avoid-sending-in-different-cultures

5. MyGlobalFlowers - Traditions of Flower Gifting in Different Cultures
   https://myglobalflowers.com/blog/lifestyle/traditions-of-flower-gifting-in-different-cultures

6. roza4u.ru - Язык цветов: значение и символика (Russian)
   https://www.roza4u.ru/znachenie-simvolika-tsvetov

7. Wikipedia - Language of Flowers / List of plants with symbolism
   https://en.wikipedia.org/wiki/Language_of_flowers
   https://en.wikipedia.org/wiki/List_of_plants_with_symbolism

8. Iowa State University Extension - Flowers and Their Meanings
   https://yardandgarden.extension.iastate.edu/how-to/flowers-and-their-meanings-language-flowers

9. Arena Flowers - Flower Symbolism Guide
   https://www.arenaflowers.com/blogs/the-flower-press/flower-symbolism-blog/

10. Petal Republic - Ultimate Guide to Floriography
    https://www.petalrepublic.com/floriography-guide/

11. Bloom & Wild - Floriography: Language and Meaning of Flowers
    https://www.bloomandwild.com/floriography-language-of-flowers-meaning
"""
