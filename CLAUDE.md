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
- `BUDGET_NORMALIZE_ENABLED` - defaults to `true`; set `false` to disable budget normalization (rollback)

## Current Status

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

### Code Style

- **Python**: Type hints required, Pydantic for schemas
- **Swift**: SwiftUI, MVVM pattern, `@Observable` for state
- **Naming**: Agents use 3-4 letter acronyms (FIA, EIA, FMRA, etc.)
