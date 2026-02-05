# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FSense is an AI-powered flower recommendation system with a Python backend (agent pipeline) and iOS SwiftUI frontend. The backend processes user messages through a **10-agent pipeline** with parallel execution to generate contextual flower recommendations.

## Commands

### Backend Development

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run tests (from project root)
PYTHONPATH=. pytest backend/tests/ -v

# Run single test
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py::test_run_flower_chat_success -v

# Test pipeline CLI
python -m backend.pipeline.runner "I want to apologize to my wife" --pretty

# Test with image (bouquet scan)
python -m backend.pipeline.runner "What flower is this?" --image path/to/image.jpg --pretty
```

### iOS Development

- Open `FSense_2.xcodeproj` in Xcode
- Build server configured at `/opt/homebrew/bin/xcode-build-server`

### Adding New Languages

```bash
# Export template with all 217 strings
python scripts/add_language.py --export > scripts/translations/ko.json

# Translate the JSON file, then add the language
python scripts/add_language.py ko "한국어" scripts/translations/ko.json

# Build to verify (catches switch exhaustiveness errors)
xcodebuild -project FSense_2.xcodeproj -scheme FSense_2 build
```

The script updates: `LanguageManager.swift`, `project.pbxproj`, `Localizable.xcstrings`, `InfoPlist.xcstrings`, `FSenseApp.swift`

**Current languages (7):** English, Russian, Spanish, German, French, Chinese (Simplified), Japanese

## Architecture

### Agent Pipeline

User input flows through a fixed-sequence pipeline where each agent enriches a shared `PipelineContext`. Independent agents run in **parallel** for ~2.3x speedup:

```
                          ┌─────────────────────────────────────────┐
                          │           Phase 0 (if image)           │
                          │              VIA (vision)              │
                          └─────────────────────────────────────────┘
                                            │
                          ┌─────────────────────────────────────────┐
                          │        Phase 1 (parallel)              │
                          │           FIA    EIA                   │
                          └─────────────────────────────────────────┘
                                            │
                          ┌─────────────────────────────────────────┐
                          │    Phase 1.5 (deterministic, instant)  │
                          │       Relationship Inference           │
                          └─────────────────────────────────────────┘
                                            │
                          ┌─────────────────────────────────────────┐
                          │        Phase 2 (sequential)            │
                          │              FMRA                      │
                          └─────────────────────────────────────────┘
                                            │
                          ┌─────────────────────────────────────────┐
                          │        Phase 3 (parallel)              │
                          │      CIA   AITB   RFFA   CRI           │
                          └─────────────────────────────────────────┘
                                            │
                          ┌─────────────────────────────────────────┐
                          │        Phase 4-5 (sequential)          │
                          │           SRFL → SFA                   │
                          └─────────────────────────────────────────┘
```

**Agents (10 total):**
| # | Agent | Name | Description | Critical? |
|---|-------|------|-------------|-----------|
| 0 | **VIA** | Vision Image Analyzer | Analyzes bouquet images (optional) | No |
| 1 | **FIA** | Flower Intent Agent | Parses user intent | **Yes** |
| 2 | **EIA** | Emotion Intelligence Agent | Detects emotions | **Yes** |
| - | *Relationship inference* | (deterministic) | Instant, no AI call | - |
| 3 | **FMRA** | Flower Matching & Ranking Agent | Selects candidate flowers (DB-first for vision, budget enforcement) | **Yes** |
| 4 | **CIA** | Context Intensity Agent | Scores emotional intensity | No |
| 5 | **AITB** | Adaptive Intelligence & Tone Builder | Adapts tone | No |
| 6 | **RFFA** | Risk & Fit Assessment Agent | Evaluates gifting risks | No |
| 7 | **CRI** | Cultural & Regional Intelligence | Adds cultural context | No |
| 8 | **SRFL** | Self-Reflection Layer | Validates coherence | No |
| 9 | **SFA** | Symbolic Flower Agent | **Assembles final payload** | **Yes** |

Critical agents (FIA, EIA, FMRA, SFA) stop the pipeline on failure. Non-critical agents log errors but allow continuation.

### Key Design Principles

- **Single Source of Truth**: All data flows through `PipelineContext` (`backend/pipeline/context.py`)
- **Agent Standardization**: All agents implement `BaseAgent` interface (`backend/agents/base.py`)
- **Final Assembler Rule**: Only SFA writes the iOS payload - other agents write to their designated context sections
- **Stateless Design**: No direct agent-to-agent communication
- **Parallel Execution**: Independent agents run concurrently via `ThreadPoolExecutor`
- **Early Normalization**: External inputs (iOS budget terms) normalized at pipeline entry before agents run

### Budget Normalization Flow

Budget terms from different sources are normalized to canonical tiers (`budget`, `mid`, `premium`, `any`):

```
iOS sends budget_range (e.g., "Luxury", "Moderate")
        ↓
runner.py: normalize_budget() → canonical tier ("premium", "mid")
        ↓
ctx.priors.budget_range = normalized
        ↓
FIA runs → outputs budget_hint (legacy terms: "modest", "luxury")
        ↓
FMRA: normalize_budget(budget_hint) → canonical tier
        ↓
FMRA precedence: budget_range > budget_hint
        ↓
SFA: receives only canonical terms for warnings
```

**Canonical tiers:** `budget` (<$50), `mid` ($50-99), `premium` ($100+), `any` (no constraint), `None` (parse error)

### iOS Integration

```python
from backend.pipeline.runner import run_flower_chat

# Text-only request
result = run_flower_chat("I want to apologize to my wife", region="US")

# With image (bouquet scan)
result = run_flower_chat("What flower is this?", region="US", image_base64="...")

# With budget (any format - normalized automatically)
result = run_flower_chat("Birthday gift for mom", region="US", budget_range="Luxury")  # iOS term
result = run_flower_chat("Birthday gift for mom", region="US", budget_range="premium")  # canonical
result = run_flower_chat("Birthday gift for mom", region="US", budget_range="$50-100")  # dollar range

# Returns: {"success": bool, "data": FlowerCardPayload | None, "error": str | None}
```

The `FlowerCardPayload` schema (`backend/schemas/flower_card_payload.py`) defines the iOS contract with three tabs: meaning, gifting, and context.

### Directory Structure

```
backend/
├── core/             # Settings, AI client singleton, rate limiter, input validator, budget_normalizer, safe_parse
├── pipeline/         # Orchestrator, context, runner (iOS entrypoint), scan_*
├── agents/
│   ├── base.py       # BaseAgent interface
│   └── adapters/     # 10 agent implementations + relationship_inference.py
├── schemas/          # Pydantic models (enums, FlowerCardPayload, scan_payload)
├── database/         # SQLite DBs, flower_database.py, models, repository
├── services/         # Knowledge base, image service, search providers, history
└── tests/            # Smoke tests (pipeline, providers, scan)

FSense/               # iOS SwiftUI app
├── App/              # FSenseApp.swift, AppEnvironment
├── Features/
│   ├── Home/         # HomeView, HomeViewModel
│   ├── Chat/         # Chat UI, history manager
│   ├── FlowerCard/   # Card views (Meaning, Gifting, Context tabs)
│   ├── Scan/         # Camera, ScanResultCard
│   ├── LovedOnes/    # Profile management
│   └── Profile/      # Settings, archives
├── Services/         # API clients, state managers
├── Shared/           # Reusable components
└── Resources/        # Assets, colors
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and set:

**Required:**
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string (Supabase)

**Optional:**
- `OPENAI_MODEL` - defaults to `gpt-4o`
- `OPENAI_MODEL_FAST` - defaults to `gpt-4o-mini` (for simple tasks)
- `FSENSE_ENV` - local/staging/production
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` - for Storage
- `YANDEX_CLOUD_API_KEY`, `YANDEX_CLOUD_FOLDER_ID` - Yandex search (Russia)
- `FLORIST_ONE_API_KEY`, `FLORIST_ONE_API_PASSWORD` - FloristOne (US/Canada)
- `FMRA_ENFORCE_BUDGET` - defaults to `true`; set `false` for shadow-only logging
- `FMRA_VALIDATE_FLOWER_NAMES` - defaults to `true`; set `false` to disable flower name validation (rollback)
- `BUDGET_NORMALIZE_ENABLED` - defaults to `true`; set `false` to disable budget normalization (rollback)
- `FALLBACK_PAYLOAD_ENABLED` - defaults to `true`; set `false` to disable fallback payload on SFA failure
- `CRI_USE_KNOWLEDGE_BASE` - defaults to `true`; set `false` to disable FlowerKnowledgeBase resolution in CRI (rollback)

## Current Status

**Version 0.6.1** - CRI flower ID resolution fix: Fixed naive `flower_name.lower().replace(" ", "_")` ID generation in CRI that caused `get_cultural_warnings()` to silently fail when IDs didn't match database format. Implemented 3-tier resolution strategy: (1) match flower_name against ALL candidates by name (case-insensitive), (2) use `FlowerKnowledgeBase.resolve_flower_id()` for fuzzy matching, (3) fallback to heuristics only. Extracted `_check_heuristic_warnings()` method for reuse. Combined DB + heuristic warnings with deduplication instead of early-return on DB match. Added `None` region handling. Rollback via `CRI_USE_KNOWLEDGE_BASE=false`. Tests in `backend/tests/test_cri_flower_id.py` (21 tests).

**Version 0.6.0** - Full iOS localization with in-app language picker: Added support for 7 languages (English, Russian, Spanish, German, French, Chinese Simplified, Japanese). `LanguageManager.swift` extended with new `AppLanguage` cases, each with `displayName`, `nativeName`, and globe icons. `Localizable.xcstrings` contains 217 translated strings covering: navigation titles, buttons, relationships (24 types), categories, mood intensity levels, flower card sections, empty states, alerts, placeholders, date types, and taste profile enums. `InfoPlist.xcstrings` updated with camera/photo library permission descriptions for all languages. `project.pbxproj` updated with `knownRegions`. `FSenseApp.swift` updated with locale mappings. Users can switch languages in Settings → Language.

**Version 0.5.9** - Multiline chat input with smooth expansion: TextField in `ChatView.swift` and `BottomInputBarView.swift` now supports multiline input via `axis: .vertical` with `.lineLimit(1...5)`. Tracks `isInputMultiline` state based on newlines or text length (>35 chars). HStack alignment dynamically switches: `.center` for single line (text vertically centered), `.bottom` for multiline (send button stays at bottom). Spring animation (0.3s, 0.85 damping) triggers only on line count change, not every keystroke, for smooth transitions. ChatView background changes corner radius (25→20) when expanded.

**Version 0.5.8** - FMRA flower name validation: Validates AI-returned flower names in `_ai_selection_multiple()` to reject placeholder/error values like "Unknown Flower", "N/A", "Error". Uses blocklist + substring pattern matching via `is_valid_flower_name()` helper. Skipped candidates logged at DEBUG level; approximate counter `_invalid_flower_count` for observability. Also adds defensive handling for malformed AI responses (null/string candidates, non-dict items, non-string flower_name). Generates flower_id from name when AI provides invalid ID. Rollback via `FMRA_VALIDATE_FLOWER_NAMES=false`. Tests in `backend/tests/test_fmra_validation.py`.

**Version 0.5.7** - SFA fallback payload: When SFA fails but FMRA has candidates, builds minimal valid FlowerCardPayload from available context (flower name, meanings, RFFA risk data). Pydantic-validated, with `_fallback: true` flag for iOS to optionally show simplified view indicator. Rollback via `FALLBACK_PAYLOAD_ENABLED=false`. Warning-level logging when activated.

**Version 0.5.6** - SFA mood_intensity None safety: Added defensive handling in SFA for `mood_intensity` being `None`. New helper methods `_get_safe_mood_intensity(ctx)` and `_calculate_mood_intensity_ui(raw_value)` centralize None-safe access and scale conversion. Default `0.4` (raw) yields `25` on UI scale (15-40), preserving original fallback behavior. Applied to 4 locations in SFA: CIA context summary, AI prompt template, post-AI intensity application, and fallback content. Tests in `backend/tests/test_sfa_mood_intensity.py`. No rollback needed — purely defensive code.

**Version 0.5.5** - Safe float parsing for AI responses: Central `safe_parse_float()` utility in `backend/core/safe_parse.py` handles invalid AI responses (e.g., `"high"` instead of `0.8`, `"nan"`, `"inf"`, malformed strings like `"0.7.2"`). Applied to all adapters parsing numeric values: EIA (emotion_intensity), CIA (intensity_score), FIA (confidence), FMRA (match_score ×2), FlowerID (confidence ×3), VIA (confidence). Prevents crashes and uses sensible defaults with logging. No rollback needed — purely defensive code.

**Version 0.5.4** - Budget terminology normalization: Central `normalize_budget()` utility in `backend/core/budget_normalizer.py` converts all budget terms to canonical tiers (`budget`, `mid`, `premium`, `any`). Normalization happens at two points: (1) `budget_range` from iOS normalized in `runner.py` at pipeline entry, (2) `budget_hint` from FIA normalized by FMRA. Supports iOS terms (`Luxury`, `Moderate`), FIA terms (`modest`, `standard`), synonyms (`cheap`, `expensive`), and dollar ranges with exclusive upper bounds (`$49` → budget, `$50` → mid, `$100` → premium). Rollback via `BUDGET_NORMALIZE_ENABLED=false`.

**Version 0.5.3** - FMRA budget range enforcement: When user selects a budget tier in iOS UI (`priors.budget_range`), FMRA applies score multipliers to candidates (1.2x boost for match, 0.7x penalty for opposite tier). Explicit `budget_range` takes precedence over inferred `budget_hint` from FIA. Rollback via `FMRA_ENFORCE_BUDGET=false` with shadow logging.

---

## Planning Guidelines

### When Adding New Agents

1. **Implement `BaseAgent` interface** (`backend/agents/base.py`)
2. **Determine execution phase** - can it run in parallel with others?
3. **Update orchestrator** - add to appropriate phase in `PipelineOrchestrator.run()`
4. **Mark criticality** - add to `CRITICAL_AGENTS` set if pipeline cannot continue without it
5. **Update this file** - add to agent table above

### When Replacing AI Logic with Deterministic Mappings

1. **Check existing fallback code** for ALL handled cases
   - Look for `_fallback_*` methods that already implement deterministic logic
   - Include all aliases (mom/mum/mama, gf/bf, ex-*, in-laws)
   - Document unknown value handling with lower confidence

2. **Always include rollback strategy**
   - Add feature flag (env var) to toggle between old/new behavior
   - Use shadow comparison (non-blocking) for A/B validation
   - Log outputs for offline analysis

3. **Test coverage must be comprehensive**
   - Unit tests: Test each mapping/function in isolation
   - Integration tests: Verify downstream consumers receive expected data
   - Edge case tests: Unknown values, empty inputs
   - Cross-cutting tests: Same input with different contexts (e.g., emotions)

4. **Respect Single Responsibility Principle**
   - Don't bloat existing agents with new responsibilities
   - Prefer calling new logic from orchestrator
   - Keep modules testable in isolation

5. **Update all documentation**
   - Dataclass docstrings (ownership changes)
   - Pipeline comments in context.py
   - CLAUDE.md agent list and diagram

6. **Consider cross-cutting data**
   - Check what other agents' data the removed agent consumed
   - Preserve valuable cross-references in deterministic logic
   - Add optional parameters for enrichment data

### When Parsing AI Responses

Always use `safe_parse_float()` from `backend.core.safe_parse` when parsing numeric values from AI responses:

```python
from backend.core.safe_parse import safe_parse_float

# Instead of: intensity = float(response.get("intensity", 0.7))
intensity = safe_parse_float(
    response.get("intensity"),
    default=0.7,
    context="AgentName.field_name"  # For logging
)
```

This handles:
- Non-numeric strings (`"high"`, `"low"`) → default
- Malformed values (`"0.7.2"`, `""`, `None`) → default
- Special floats (`"nan"`, `"inf"`, `"-inf"`) → default
- Out-of-range values → clamped to `[min_val, max_val]`

### When Writing Helper Methods

Before implementing a helper method, verify these common pitfalls:

1. **Parameter-data alignment**
   - If method takes `item_name` as parameter, don't blindly use `collection[0]` — verify the item matches
   - Bad: `def resolve_id(flower_name, ctx): return ctx.candidates[0].flower_id`
   - Good: `for c in ctx.candidates: if c.name == flower_name: return c.flower_id`

2. **Parameter None checks**
   - Always validate parameters before calling methods on them
   - Bad: `region.lower()` — crashes if `region=None`
   - Good: `if not region: return default` or `(region or "").lower()`

3. **Collection edge cases**
   - `if collection:` is True for non-empty, but `collection[0]` still fails on empty list
   - Always handle: `None`, empty list `[]`, missing keys

4. **External service calls need try/except**
   ```python
   # Bad: assumes service never fails
   result = SomeService.lookup(name)

   # Good: defensive
   try:
       result = SomeService.lookup(name)
   except Exception as e:
       logger.warning(f"Service failed: {e}")
       result = None
   ```

5. **Verify method signatures before using**
   - Is it `@staticmethod`, `@classmethod`, or instance method?
   - Check the actual file, don't assume from naming convention

6. **Thread safety for parallel phases**
   - Phase 3 agents (CIA, AITB, RFFA, CRI) run concurrently
   - Any shared state or service must be thread-safe
   - Check if called service uses file handles, caches, or mutable globals

### When Planning Changes

1. **Feature flag default: YES**
   - "No feature flag needed" requires explicit justification
   - Defensive code with no behavior change → OK without flag
   - Any behavior change (different results, new calls) → needs flag

2. **Test levels required**
   - Unit tests for helper methods in isolation
   - Integration tests verifying the helper is called correctly AND results used properly
   - Don't just test `_resolve_id()` — also test that `_check_warnings()` uses resolved ID

3. **Early return logic review**
   ```python
   # Risky: may skip heuristics when DB returns empty/false
   if db_result:
       return db_result
   # Heuristics here...

   # Better: combine sources
   warnings = []
   if db_result:
       warnings.extend(db_result)
   warnings.extend(heuristic_warnings)
   return warnings
   ```

4. **Signature changes cascade**
   - When adding parameter to method, grep for ALL call sites
   - `def foo(a, b)` → `def foo(a, b, ctx)` breaks callers

5. **Tests must patch feature flags for code paths**
   ```python
   # Bad: test won't exercise DB path if DATABASE_AVAILABLE=False
   def test_db_lookup(self):
       with patch('module.get_warnings') as mock:
           result = check_warnings("Rose", "IT", ctx)

   # Good: explicitly enable the code path
   @patch('module.DATABASE_AVAILABLE', True)
   def test_db_lookup(self):
       with patch('module.get_warnings') as mock:
           result = check_warnings("Rose", "IT", ctx)
   ```

6. **Check existing imports before adding**
   - Read the file header before planning import additions
   - `List`, `Optional`, `Dict` may already be imported
   - Avoid duplicate imports that cause linter warnings

### Code Style

- **Python**: Type hints required, Pydantic for schemas
- **Swift**: SwiftUI, MVVM pattern, `@Observable` for state
- **Naming**: Agents use 3-4 letter acronyms (FIA, EIA, FMRA, etc.)
