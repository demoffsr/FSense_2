# FSense Agent Pipeline Improvements

**Date:** 2026-02-04
**Version:** 0.17 → 0.18
**Status:** Draft

---

## Executive Summary

Комплексный аудит 10 агентов выявил **23+ потенциальных проблем**:
- 4 критических бага (могут сломать pipeline)
- 5 средних проблем (silent failures, потеря данных)
- 14+ архитектурных улучшений

Этот план организует фиксы по приоритетам с оценкой влияния.

---

## Phase 1: Critical Bug Fixes (P0)

### 1.1 EIA: Float Conversion Crash

**Файл:** `backend/agents/adapters/eia_adapter.py:115`

**Проблема:**
```python
intensity = float(response.get("emotion_intensity", 0.7))
```
Если AI вернёт `"high"` или `"0.7.2"`, `float()` упадёт с ValueError.

**Фикс:**
```python
def _safe_parse_float(self, value: Any, default: float = 0.7) -> float:
    """Safely parse float with fallback."""
    try:
        result = float(value)
        return max(0.0, min(1.0, result))  # Clamp to valid range
    except (TypeError, ValueError):
        logger.warning(f"EIA: Invalid float value '{value}', using default {default}")
        return default

# Usage:
intensity = self._safe_parse_float(response.get("emotion_intensity"), 0.7)
```

---

### 1.2 SFA: mood_intensity None Multiplication

**Файл:** `backend/agents/adapters/sfa_adapter.py:545-550`

**Проблема:**
```python
if ctx.intensity and "meaning" in response:
    calculated_value = int(15 + (ctx.intensity.mood_intensity * 25))  # ← Crash if None
```

**Фикс:**
```python
if ctx.intensity and "meaning" in response:
    mood_val = ctx.intensity.mood_intensity
    if mood_val is not None and isinstance(mood_val, (int, float)):
        calculated_value = int(15 + (mood_val * 25))
        response["meaning"]["mood_intensity"] = calculated_value
        response["meaning"]["mood_label"] = self._get_intensity_label(calculated_value)
    else:
        logger.warning(f"SFA: Invalid mood_intensity value: {mood_val}")
```

---

### 1.3 Runner: No Fallback Payload on SFA Failure

**Файл:** `backend/pipeline/runner.py:166-171`

**Проблема:**
```python
if ctx.ui_payload is None:
    return {"success": False, "error": "Failed to generate..."}
```
Пользователь теряет все данные (intent, emotions, candidates) если SFA падает.

**Фикс:** Добавить fallback payload assembler:
```python
if ctx.ui_payload is None:
    logger.error(f"Pipeline completed but no UI payload: request_id={ctx.request_id}")

    # Attempt to build minimal payload from available context
    fallback_payload = _build_fallback_payload(ctx)
    if fallback_payload:
        logger.info("Using fallback payload from partial context")
        return {"success": True, "data": fallback_payload, "partial": True}

    return {"success": False, "error": "Failed to generate..."}

def _build_fallback_payload(ctx: PipelineContext) -> Optional[dict]:
    """Build minimal payload from whatever context is available."""
    if not ctx.candidates or not ctx.candidates.candidates:
        return None

    top_flower = ctx.candidates.candidates[0]
    return {
        "flower_header": {
            "flower_id": top_flower.flower_id,
            "flower_name": top_flower.name,
            "tagline": f"Recommended: {top_flower.name}",
            "image_url": None,
        },
        "meaning_tab": {
            "why_this_flower": {"text": top_flower.match_reasons[0] if top_flower.match_reasons else "A thoughtful choice"},
            "meanings": top_flower.symbolic_meanings[:3] if top_flower.symbolic_meanings else ["Love", "Care"],
            # ... minimal structure
        },
        "_fallback": True,  # Flag for iOS to show "simplified view"
    }
```

---

### 1.4 FMRA: "Unknown Flower" Validation

**Файл:** `backend/agents/adapters/fmra_adapter.py:373-399`

**Проблема:**
```python
flower_name = item.get("flower_name", "Unknown Flower")  # ← Literal string as fallback
candidates.append(FlowerCandidate(name=flower_name, ...))
```
AI может вернуть `{"flower_name": "Unknown Flower"}` и это будет валидная рекомендация.

**Фикс:**
```python
INVALID_FLOWER_NAMES = {"Unknown Flower", "Unknown", "N/A", "None", ""}

for item in response.get("candidates", [])[:5]:
    flower_name = item.get("flower_name", "").strip()

    if not flower_name or flower_name in INVALID_FLOWER_NAMES:
        logger.warning(f"FMRA: AI returned invalid flower name: '{flower_name}'")
        continue  # Skip invalid, don't add to candidates

    candidates.append(FlowerCandidate(name=flower_name, ...))

# If all were invalid, use fallback
if not candidates:
    logger.error("FMRA: AI returned no valid flowers, using fallback")
    return [self._fallback_candidate(ctx)]
```

---

## Phase 2: Silent Failure Fixes (P1)

### 2.1 Relationship Inference: Case-Sensitive Comparison

**Файл:** `backend/agents/adapters/relationship_inference.py:249-250`

**Проблема:**
```python
if emotion in ["remorse", "guilt", "regret", "apologetic"] and intensity > 0.7:
```
`emotion` может быть `"Remorse"` или `"REMORSE"` — не заматчится.

**Фикс:**
```python
emotion_lower = emotion.lower() if emotion else ""
if emotion_lower in ["remorse", "guilt", "regret", "apologetic"] and intensity > 0.7:
```

---

### 2.2 CRI: Flower ID Generation

**Файл:** `backend/agents/adapters/cri_adapter.py:202-204`

**Проблема:**
```python
flower_id = flower_name.lower().replace(" ", "_")  # "Red Rose" → "red_rose"
```
Но в БД может быть `rose_red`, `rose`, или `red-rose`.

**Фикс:** Использовать fuzzy matching или lookup table:
```python
def _normalize_flower_id(self, flower_name: str) -> Optional[str]:
    """Normalize flower name to database ID with fuzzy matching."""
    # Try exact match first
    normalized = flower_name.lower().replace(" ", "_")
    if self._flower_exists(normalized):
        return normalized

    # Try common variations
    variations = [
        normalized,
        flower_name.lower().replace(" ", "-"),
        "_".join(reversed(normalized.split("_"))),  # "red_rose" → "rose_red"
        normalized.split("_")[-1],  # Just "rose"
    ]

    for variant in variations:
        if self._flower_exists(variant):
            return variant

    logger.warning(f"CRI: Could not find flower ID for '{flower_name}'")
    return None
```

---

### 2.3 SRFL: Emotion Substring Matching

**Файл:** `backend/agents/adapters/srfl_adapter.py:180-191`

**Проблема:**
```python
for emotion_key, emotion_targets in EMOTION_TO_MEANING_TONES.items():
    if dominant_emotion in emotion_key or emotion_key in dominant_emotion:
        targets = emotion_targets
        break
```
`"care"` в `"care_concern"` заматчится, но порядок не гарантирован.

**Фикс:** Приоритизировать exact matches:
```python
# Try exact match first
targets = EMOTION_TO_MEANING_TONES.get(dominant_emotion, set())

# Then try compound keys (exact substring of key)
if not targets:
    for emotion_key, emotion_targets in sorted(
        EMOTION_TO_MEANING_TONES.items(),
        key=lambda x: len(x[0]),  # Longer keys first (more specific)
        reverse=True
    ):
        if dominant_emotion == emotion_key or f"_{dominant_emotion}" in f"_{emotion_key}_":
            targets = emotion_targets
            break
```

---

### 2.4 VIA: Confidence Clamping Without Logging

**Файл:** `backend/agents/adapters/via_adapter.py:83`

**Фикс:**
```python
def _safe_parse_confidence(self, value: Any) -> float:
    try:
        conf = float(value)
        if conf < 0.0 or conf > 1.0:
            logger.warning(f"VIA: Confidence {conf} outside valid range, clamping")
        return max(0.0, min(1.0, conf))
    except (TypeError, ValueError):
        logger.warning(f"VIA: Invalid confidence value '{value}', returning 0.0")
        return 0.0
```

---

### 2.5 Budget Lost in Vision Clarification Flow

**Файл:** `backend/pipeline/orchestrator.py:132-139`

**Проблема:** При vision clarification запросе budget теряется между запросами.

**Фикс:** Включить budget в clarification payload для iOS:
```python
def _build_clarification_payload(self, ctx: PipelineContext) -> dict:
    return {
        "needs_clarification": True,
        "clarification_message": ctx.vision.clarification_message,
        "detected_flowers": [...],
        # Preserve context for follow-up
        "_preserved_context": {
            "budget_range": ctx.priors.budget_range if ctx.priors else None,
            "region": ctx.region,
        }
    }
```

iOS должен отправить `_preserved_context` обратно в follow-up запросе.

---

## Phase 3: Type Safety & Validation (P2)

### 3.1 Create Central Enums

**Новый файл:** `backend/schemas/enums.py` (расширить существующий)

```python
from enum import Enum

class BudgetTier(str, Enum):
    """Canonical budget tiers used throughout the pipeline."""
    BUDGET = "budget"      # <$50
    MID = "mid"            # $50-99
    PREMIUM = "premium"    # $100+
    ANY = "any"            # No constraint

class EmotionCategory(str, Enum):
    """Primary emotion categories."""
    LOVE = "love"
    GRATITUDE = "gratitude"
    SYMPATHY = "sympathy"
    CELEBRATION = "celebration"
    APOLOGY = "apology"
    ROMANTIC = "romantic"
    CARE = "care"
    # ... etc

class RelationshipStage(str, Enum):
    """Relationship stages for gift appropriateness."""
    NEW = "new"
    EARLY = "early"
    DEVELOPING = "developing"
    ESTABLISHED = "established"
    LONG_TERM = "long_term"

class GiftSuitabilityLevel(str, Enum):
    """Gift suitability assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    RISKY = "risky"
    NOT_RECOMMENDED = "not_recommended"

class PriceTier(str, Enum):
    """Flower price tiers."""
    BUDGET = "budget"
    MID = "mid"
    PREMIUM = "premium"
    LUXURY = "luxury"
```

---

### 3.2 Convert Context Dataclasses to Validated Models

**Пример для UserPriors:**

```python
# backend/pipeline/context.py

from pydantic import BaseModel, Field, field_validator
from backend.schemas.enums import BudgetTier, RelationshipStage

class UserPriors(BaseModel):
    """User-provided context and preferences with validation."""

    relationship_type: Optional[str] = None
    relationship_stage: Optional[RelationshipStage] = None
    budget_range: Optional[BudgetTier] = None
    color_preferences: list[str] = Field(default_factory=list, max_length=10)
    flower_preferences: list[str] = Field(default_factory=list, max_length=10)
    allergies: list[str] = Field(default_factory=list, max_length=10)
    occasion: Optional[str] = None

    @field_validator("color_preferences", "flower_preferences", "allergies")
    @classmethod
    def validate_list_items(cls, v: list[str]) -> list[str]:
        return [item.strip()[:100] for item in v if item and item.strip()]

    class Config:
        use_enum_values = True
```

---

### 3.3 Add Agent Contracts

**Новый файл:** `backend/agents/contracts.py`

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class AgentContract:
    """Formal specification of agent inputs/outputs."""
    name: str
    inputs: tuple[str, ...]      # Context fields agent reads
    outputs: tuple[str, ...]     # Context fields agent writes
    critical: bool               # Stops pipeline on failure
    phase: int                   # Execution phase

AGENT_CONTRACTS = {
    "FIA": AgentContract(
        name="FIA",
        inputs=("user_input", "priors", "region"),
        outputs=("intent",),
        critical=True,
        phase=1,
    ),
    "EIA": AgentContract(
        name="EIA",
        inputs=("user_input", "priors"),
        outputs=("emotions",),
        critical=True,
        phase=1,
    ),
    "FMRA": AgentContract(
        name="FMRA",
        inputs=("intent", "emotions", "priors", "candidates"),
        outputs=("candidates",),
        critical=True,
        phase=2,
    ),
    "CIA": AgentContract(
        name="CIA",
        inputs=("intent", "emotions", "candidates"),
        outputs=("intensity",),
        critical=False,
        phase=3,
    ),
    "AITB": AgentContract(
        name="AITB",
        inputs=("intent", "emotions", "relationship"),
        outputs=("adaptive",),
        critical=False,
        phase=3,
    ),
    "RFFA": AgentContract(
        name="RFFA",
        inputs=("candidates", "emotions", "relationship"),
        outputs=("risks",),
        critical=False,
        phase=3,
    ),
    "CRI": AgentContract(
        name="CRI",
        inputs=("intent", "candidates", "emotions", "region"),
        outputs=("cultural_insights",),
        critical=False,
        phase=3,
    ),
    "SRFL": AgentContract(
        name="SRFL",
        inputs=("intent", "emotions", "candidates", "intensity", "adaptive", "risks", "cultural_insights"),
        outputs=(),  # Only validates, doesn't write
        critical=False,
        phase=4,
    ),
    "SFA": AgentContract(
        name="SFA",
        inputs=("intent", "emotions", "candidates", "intensity", "adaptive", "risks", "cultural_insights"),
        outputs=("ui_payload",),
        critical=True,
        phase=5,
    ),
}

def validate_agent_outputs(agent_name: str, ctx: "PipelineContext") -> list[str]:
    """Validate that agent populated its contracted outputs."""
    contract = AGENT_CONTRACTS.get(agent_name)
    if not contract:
        return []

    errors = []
    for output_field in contract.outputs:
        value = getattr(ctx, output_field, None)
        if value is None:
            errors.append(f"{agent_name} did not populate required output: {output_field}")
        elif hasattr(value, "__dataclass_fields__"):
            # Check if dataclass has any non-default values
            if all(getattr(value, f.name) == f.default for f in value.__dataclass_fields__.values() if f.default is not dataclasses.MISSING):
                errors.append(f"{agent_name} populated {output_field} with all default values")

    return errors
```

---

### 3.4 Centralize Thresholds

**Новый файл:** `backend/core/thresholds.py`

```python
"""Central configuration for all pipeline thresholds."""

# Confidence thresholds
CONFIDENCE_LOW = 0.3
CONFIDENCE_MEDIUM = 0.5
CONFIDENCE_HIGH = 0.7
CONFIDENCE_VERY_HIGH = 0.85

# Intensity thresholds
INTENSITY_LOW = 0.3
INTENSITY_MEDIUM = 0.5
INTENSITY_HIGH = 0.7

# Relationship stage thresholds
STAGE_NEW_INTENSITY_CAP = 0.6
STAGE_EARLY_INTENSITY_CAP = 0.7

# Diversity penalties
DIVERSITY_PENALTY_SAME_FLOWER = 0.3
DIVERSITY_PENALTY_SAME_CATEGORY = 0.1

# Timeouts (seconds)
AGENT_TIMEOUT_DEFAULT = 30
AGENT_TIMEOUT_VISION = 45
AGENT_TIMEOUT_FMRA = 40  # DB queries can be slow
```

Затем в агентах:
```python
from backend.core.thresholds import CONFIDENCE_HIGH, INTENSITY_HIGH

if confidence < CONFIDENCE_HIGH:
    needs_clarification = True
```

---

## Phase 4: Prompt Engineering Improvements (P3)

### 4.1 FIA: Add More Regional Hints

**Файл:** `backend/agents/adapters/fia_adapter.py:207-216`

```python
REGIONAL_HINTS = {
    "us": "US culture: Practical gift-giving, direct communication, roses popular for romance",
    "eu": "European culture: Formal traditions, seasonal flowers valued, lilies common for sympathy",
    "asia": "Asian culture: Symbolism crucial, white/yellow can mean mourning, orchids prestigious",
    "ru": "Russian culture: Odd numbers for gifts, even for funerals, chrysanthemums for graves",
    "cn": "Chinese culture: Avoid white flowers (funerals), red symbolizes luck, peonies prestigious",
    "jp": "Japanese culture: Avoid 4/9 stems (death associations), cherry blossoms for transience",
    "in": "Indian culture: Marigolds sacred, jasmine for weddings, lotus for spirituality",
    "br": "Brazilian culture: Vibrant colors preferred, purple for mourning, tropical flowers popular",
    "mx": "Mexican culture: Marigolds for Day of Dead, bright colors for celebration",
    "middle_east": "Middle Eastern culture: Avoid yellow (jealousy), roses and jasmine prestigious",
}

def _get_regional_hint(self, region: str) -> str:
    region_lower = region.lower()

    # Direct match
    if region_lower in REGIONAL_HINTS:
        return f"REGIONAL NOTE: {REGIONAL_HINTS[region_lower]}"

    # Map country codes to regions
    country_to_region = {
        "ca": "us", "uk": "eu", "de": "eu", "fr": "eu", "it": "eu", "es": "eu",
        "kr": "asia", "tw": "asia", "sg": "asia", "hk": "asia",
        "ae": "middle_east", "sa": "middle_east", "eg": "middle_east",
    }

    mapped_region = country_to_region.get(region_lower)
    if mapped_region and mapped_region in REGIONAL_HINTS:
        return f"REGIONAL NOTE: {REGIONAL_HINTS[mapped_region]}"

    logger.info(f"FIA: No regional hint for region '{region}'")
    return ""
```

---

### 4.2 FMRA: Enforce Diversity in Response Parsing

**Файл:** `backend/agents/adapters/fmra_adapter.py`

```python
# Add to prompt:
FLOWER_SELECTION_PROMPT = """...

CRITICAL DIVERSITY RULES:
1. NEVER recommend more than one flower from the same genus
2. If user didn't ask for roses specifically, include AT MOST one rose variety
3. Prioritize variety in color, shape, and symbolism
4. Include at least one unexpected/lesser-known flower

BAD EXAMPLE (too similar):
- Red Rose, Pink Rose, White Rose, Yellow Rose, Spray Rose

GOOD EXAMPLE (diverse):
- Red Rose (classic romance), Peony (prosperity), Orchid (elegance), Ranunculus (charm), Lisianthus (appreciation)
"""

# Add validation in response parsing:
def _validate_diversity(self, candidates: list[FlowerCandidate]) -> list[FlowerCandidate]:
    """Ensure candidates are diverse, not all roses."""
    seen_genera = {}
    filtered = []

    for candidate in candidates:
        genus = self._extract_genus(candidate.name)  # "Red Rose" → "rose"

        if genus in seen_genera:
            logger.info(f"FMRA: Skipping duplicate genus '{genus}': {candidate.name}")
            continue

        seen_genera[genus] = True
        filtered.append(candidate)

    # If too many filtered out, log warning
    if len(filtered) < len(candidates) * 0.6:
        logger.warning(f"FMRA: AI returned {len(candidates) - len(filtered)} duplicate genera")

    return filtered if filtered else candidates[:1]  # At least return something
```

---

### 4.3 SFA: Add Schema Enforcement to Prompt

**Файл:** `backend/agents/adapters/sfa_adapter.py`

```python
CONTENT_GENERATION_PROMPT = """...

STRICT OUTPUT REQUIREMENTS:
1. meanings: EXACTLY 3-5 items, each 2-5 words
2. cultural_interpretations: EXACTLY 3 items with different cultures
3. relationship_contexts: EXACTLY 3 items with different relationships
4. All text fields: 20-150 characters (not too short, not too long)

VALIDATION (your response will be rejected if these fail):
- meanings array length must be 3-5
- Each meaning must be unique (no duplicates)
- cultural_interpretations must include 3 different culture names
- No emoji in text fields unless specifically for emoji field

Example of CORRECT format:
{
  "meanings": ["Eternal love", "Deep passion", "Romantic devotion"],
  ...
}

Example of INCORRECT format (will be rejected):
{
  "meanings": ["Love", "Love and affection", "Loving feelings"],  // Too similar!
  ...
}
"""
```

---

### 4.4 EIA: Better Emotion Detection Prompt

**Файл:** `backend/agents/adapters/eia_adapter.py`

```python
EMOTION_DETECTION_PROMPT = """You are an expert emotion analyst for a flower recommendation system.

Analyze the user's message to detect:
1. PRIMARY emotion (the strongest, most relevant emotion)
2. SECONDARY emotions (supporting emotions, max 2)
3. INTENSITY (0.0-1.0 scale)
4. EMOTIONAL CONTEXT (why they feel this way)

EMOTION CATEGORIES (use these exact terms):
- love, gratitude, sympathy, celebration, apology, romantic
- care, admiration, encouragement, congratulations, comfort
- grief, longing, hope, pride, appreciation

INTENSITY GUIDE:
- 0.0-0.3: Mild/casual (just thinking about it)
- 0.4-0.6: Moderate (meaningful but not intense)
- 0.7-0.85: Strong (significant emotional investment)
- 0.86-1.0: Very intense (major life event, strong feelings)

IMPORTANT:
- Consider the RECIPIENT and OCCASION, not just words
- "I want to apologize" = apology + remorse (0.6-0.8)
- "Happy birthday to my wife" = celebration + love (0.7-0.9)
- "Thank you for your help" = gratitude (0.4-0.6)
- "My grandmother passed away" = grief + sympathy (0.8-1.0)

Return JSON:
{
  "primary_emotion": "string",
  "secondary_emotions": ["string", "string"],
  "emotion_intensity": 0.7,
  "emotional_context": "Brief explanation of why this emotion"
}
"""
```

---

## Phase 5: Error Handling Consolidation (P4)

### 5.1 Create Shared Error Handler

**Новый файл:** `backend/agents/error_handler.py`

```python
import logging
from functools import wraps
from typing import Callable, TypeVar, ParamSpec

from backend.core.ai_client import AIClientError
from backend.pipeline.context import PipelineContext

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Base exception for agent errors."""
    def __init__(self, agent_name: str, message: str, recoverable: bool = True):
        self.agent_name = agent_name
        self.message = message
        self.recoverable = recoverable
        super().__init__(f"{agent_name}: {message}")

def with_agent_error_handling(
    agent_name: str,
    fallback_method: str = "_fallback",
    critical: bool = False,
):
    """Decorator for consistent agent error handling.

    Args:
        agent_name: Name of the agent (for logging)
        fallback_method: Name of the fallback method to call on error
        critical: If True, re-raise after logging; if False, use fallback
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(self, ctx: PipelineContext, *args, **kwargs) -> T:
            try:
                return func(self, ctx, *args, **kwargs)
            except AIClientError as e:
                logger.error(f"{agent_name} AI error: {e}")
                ctx.add_error(f"{agent_name}: {str(e)}")

                if critical:
                    raise CriticalAgentError(agent_name, str(e)) from e

                # Try fallback
                if hasattr(self, fallback_method):
                    logger.info(f"{agent_name}: Using fallback method")
                    return getattr(self, fallback_method)(ctx)
                return None

            except Exception as e:
                logger.error(f"{agent_name} unexpected error: {e}", exc_info=True)
                ctx.add_error(f"{agent_name}: Unexpected error - {str(e)}")

                if critical:
                    raise CriticalAgentError(agent_name, str(e)) from e

                if hasattr(self, fallback_method):
                    return getattr(self, fallback_method)(ctx)
                return None

        return wrapper
    return decorator

# Usage in agents:
class EIAAdapter(BaseAgent):
    @with_agent_error_handling("EIA", fallback_method="_fallback_emotions", critical=True)
    def run(self, ctx: PipelineContext) -> None:
        # ... main logic ...
        pass

    def _fallback_emotions(self, ctx: PipelineContext) -> None:
        # ... fallback logic ...
        pass
```

---

## Implementation Order

| Phase | Priority | Effort | Items |
|-------|----------|--------|-------|
| 1 | P0 (Critical) | 2-3 hours | 4 critical bug fixes |
| 2 | P1 (High) | 2-3 hours | 5 silent failure fixes |
| 3 | P2 (Medium) | 4-6 hours | Enums, validation, contracts |
| 4 | P3 (Medium) | 3-4 hours | Prompt improvements |
| 5 | P4 (Low) | 2-3 hours | Error handling consolidation |

**Total estimated effort:** 13-19 hours

---

## Testing Strategy

### For Each Fix:

1. **Unit test** — isolated test of the fix
2. **Integration test** — verify fix in context of pipeline
3. **Regression test** — ensure existing behavior not broken

### Smoke Tests to Add:

```python
# test_pipeline_edge_cases.py

def test_eia_handles_invalid_intensity():
    """EIA should handle AI returning string intensity."""
    ctx = create_test_context("I love my wife")
    # Mock AI to return {"emotion_intensity": "high"}
    with mock_ai_response({"emotion_intensity": "high", ...}):
        run_eia(ctx)
    assert ctx.emotions.emotion_intensity == 0.7  # Default fallback

def test_sfa_handles_none_mood_intensity():
    """SFA should not crash when mood_intensity is None."""
    ctx = create_test_context_with_partial_data()
    ctx.intensity.mood_intensity = None
    run_sfa(ctx)  # Should not raise
    assert ctx.ui_payload is not None

def test_fmra_rejects_unknown_flower():
    """FMRA should not accept 'Unknown Flower' as valid."""
    ctx = create_test_context("Birthday flowers")
    with mock_ai_response({"candidates": [{"flower_name": "Unknown Flower"}]}):
        run_fmra(ctx)
    assert ctx.candidates.candidates[0].name != "Unknown Flower"
```

---

## Rollback Strategy

Все фиксы Phase 1-2 должны иметь feature flags:

```python
# backend/core/settings.py

FEATURE_FLAGS = {
    "EIA_SAFE_FLOAT_PARSING": os.getenv("EIA_SAFE_FLOAT_PARSING", "true") == "true",
    "SFA_VALIDATE_MOOD_INTENSITY": os.getenv("SFA_VALIDATE_MOOD_INTENSITY", "true") == "true",
    "RUNNER_FALLBACK_PAYLOAD": os.getenv("RUNNER_FALLBACK_PAYLOAD", "true") == "true",
    "FMRA_VALIDATE_FLOWER_NAMES": os.getenv("FMRA_VALIDATE_FLOWER_NAMES", "true") == "true",
}
```

При проблемах в production — отключить флаг, не откатывать код.

---

## Success Metrics

После внедрения:

1. **Pipeline crash rate** — должна снизиться на 80%+
2. **Silent failures** — должны логироваться (можно отследить в Sentry)
3. **"Unknown Flower" в ответах** — 0%
4. **Type errors в SFA** — 0%
5. **Budget consistency** — 100% (iOS → FMRA → SFA)
