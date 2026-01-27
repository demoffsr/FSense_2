# FSense Backend v0.0.1

AI-powered flower recommendation backend for the FSense iOS application.

## Overview

This backend provides flower recommendations based on user input (chat messages).
Each message is analyzed by a pipeline of AI agents to produce a deterministic
JSON payload that fills the iOS FlowerCard UI.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env
```

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Test the Pipeline

```bash
python -m backend.pipeline.runner "I want to apologize to my wife" --pretty
```

## iOS Integration

### Main Entrypoint

```python
from backend.pipeline.runner import run_flower_chat

# Simple usage
result = run_flower_chat("I want to apologize sincerely")

if result["success"]:
    flower_card = result["data"]
    print(flower_card["header"]["name"])
else:
    print(f"Error: {result['error']}")
```

### Response Format

**Success:**
```json
{
  "success": true,
  "data": {
    "header": { "flower_id": "...", "name": "..." },
    "meaning": { ... },
    "gifting": { ... },
    "context": { ... },
    "ask_ai": { ... },
    "pipeline_version": "0.0.1",
    "request_id": "uuid"
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

## Architecture

### Pipeline Flow

```
User Message
     ↓
┌─────────────────────────────────────────────────────────────┐
│                     PIPELINE CONTEXT                        │
│  (Single source of truth - flows through all agents)        │
└─────────────────────────────────────────────────────────────┘
     ↓
┌─────────────────────────────────────────────────────────────┐
│  FIA  → EIA  → RIL  → FMRA → CIA  →                        │
│  AITB → RFFA → CRI  → SRFL → SFA (Final Assembler)         │
└─────────────────────────────────────────────────────────────┘
     ↓
FlowerCardPayload JSON
```

### Agent Descriptions

| Agent | Name | Purpose |
|-------|------|---------|
| FIA | Flower Intent Agent | Analyzes user intent |
| EIA | Emotion Intelligence Agent | Detects emotional context |
| RIL | Relationship Intelligence Layer | Understands relationships |
| FMRA | Flower Matching & Ranking Agent | Selects flower candidates |
| CIA | Context Intensity Agent | Calibrates emotional intensity |
| AITB | Adaptive Intelligence & Tone Builder | Shapes communication style |
| RFFA | Risk & Fit Assessment Agent | Identifies potential risks |
| CRI | Cultural & Regional Intelligence | Adds cultural context |
| SRFL | Self-Reflection Layer | Quality assurance |
| SFA | Symbolic Flower Agent | **FINAL ASSEMBLER** - builds UI payload |

### Key Principles

1. **UI-Driven Backend** - The backend exists to produce JSON for iOS
2. **Single Source of Truth** - All data flows through `PipelineContext`
3. **Agent Standardization** - All agents implement `BaseAgent` interface
4. **Final Assembly Rule** - Only SFA produces the final payload
5. **Strict Order** - Agents run in fixed sequence

## Project Structure

```
backend/
├── core/
│   ├── ai_client.py      # OpenAI client wrapper
│   └── settings.py       # Environment configuration
│
├── pipeline/
│   ├── context.py        # PipelineContext (data container)
│   ├── orchestrator.py   # Agent execution order
│   └── runner.py         # Main entrypoint
│
├── agents/
│   ├── base.py           # BaseAgent interface
│   └── adapters/         # Agent implementations
│       ├── fia_adapter.py
│       ├── eia_adapter.py
│       ├── ril_adapter.py
│       ├── fmra_adapter.py
│       ├── cia_adapter.py
│       ├── aitb_adapter.py
│       ├── rffa_adapter.py
│       ├── cri_adapter.py
│       ├── srfl_adapter.py
│       └── sfa_adapter.py  # FINAL ASSEMBLER
│
├── schemas/
│   ├── enums.py              # Shared enumerations
│   └── flower_card_payload.py # iOS UI contract
│
├── tests/
│   └── test_pipeline_smoke.py
│
├── .env.example
├── requirements.txt
└── README.md
```

## Version History

### v0.0.1 (Current)
- Initial architecture scaffold
- Pipeline with placeholder agents
- iOS-ready JSON response format
- No real AI logic (mock data)

### v0.1.0 (Planned)
- Real AI agent implementations
- FastAPI HTTP server
- Async support

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | **Yes** | - | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | Model to use |
| `FSENSE_ENV` | No | `local` | Environment name |
| `DEFAULT_REGION` | No | `us` | Default region |
| `DEBUG_MODE` | No | `false` | Enable debug logging |

## License

Proprietary - FSense
