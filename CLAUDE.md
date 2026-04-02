# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FSense is an AI-powered flower recommendation system with a Python backend (agent pipeline) and iOS SwiftUI frontend. The backend processes user messages through a 10-agent pipeline to generate contextual flower recommendations.

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
```

### iOS Development

- Open `FSense_2.xcodeproj` in Xcode
- Build server configured at `/opt/homebrew/bin/xcode-build-server`

## Architecture

### Agent Pipeline

User input flows through a fixed-sequence pipeline where each agent enriches a shared `PipelineContext`:

```
User Message → PipelineContext → FIA → EIA → RIL → FMRA → CIA → AITB → RFFA → CRI → SRFL → SFA → FlowerCardPayload
```

**Agents (in execution order):**
1. **FIA** - Flower Intent Agent: Parses user intent
2. **EIA** - Emotion Intelligence Agent: Detects emotions
3. **RIL** - Relationship Intelligence Layer: Analyzes relationship context
4. **FMRA** - Flower Matching & Ranking Agent: Selects candidate flowers
5. **CIA** - Context Intensity Agent: Scores emotional intensity
6. **AITB** - Adaptive Intelligence & Tone Builder: Adapts tone
7. **RFFA** - Risk & Fit Assessment Agent: Evaluates gifting risks
8. **CRI** - Cultural & Regional Intelligence: Adds cultural context
9. **SRFL** - Self-Reflection Layer: Validates coherence
10. **SFA** - Symbolic Flower Agent: **Assembles final payload (only agent that writes `ui_payload`)**

### Key Design Principles

- **Single Source of Truth**: All data flows through `PipelineContext` (`backend/pipeline/context.py`)
- **Agent Standardization**: All agents implement `BaseAgent` interface (`backend/agents/base.py`)
- **Final Assembler Rule**: Only SFA writes the iOS payload - other agents write to their designated context sections
- **Stateless Design**: No direct agent-to-agent communication

### iOS Integration

```python
from backend.pipeline.runner import run_flower_chat

result = run_flower_chat("I want to apologize to my wife", region="US")
# Returns: {"success": bool, "data": FlowerCardPayload | None, "error": str | None}
```

The `FlowerCardPayload` schema (`backend/schemas/flower_card_payload.py`) defines the iOS contract with three tabs: meaning, gifting, and context.

### Directory Structure

```
backend/
├── core/           # Settings, AI client singleton
├── pipeline/       # Orchestrator, context, runner (iOS entrypoint)
├── agents/adapters/  # 10 agent implementations
├── schemas/        # Pydantic models (enums, FlowerCardPayload)
└── tests/          # Smoke tests

FSense/             # iOS SwiftUI app
├── Features/       # Home, Chat, FlowerCard, Scan, Profile
└── App/            # Entry point, environment
```

## Configuration

Copy `backend/.env.example` to `backend/.env` and set:
- `OPENAI_API_KEY` (required) - OpenAI API key
- `OPENAI_MODEL` - defaults to gpt-4o
- `FSENSE_ENV` - local/staging/production

## Current Status

**Version 0.0.1** - Foundation architecture with placeholder agent implementations. Agent adapters return mock data; real AI logic planned for v0.1.0.
