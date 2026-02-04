# FSense v0.17 - AI-Powered Flower Recommendation System

FSense — это умная система рекомендаций цветов, использующая конвейер из 10 AI-агентов с параллельным выполнением для подбора идеального цветка на основе эмоционального контекста пользователя.

## 🆕 Что нового в v0.17

### Deterministic Relationship Inference
- **RIL агент заменён** на детерминистический `relationship_inference.py`
- Мгновенный (~0ms) вместо AI-вызова (~500ms)
- Полное покрытие: 30+ типов отношений, алиасы (mom/mum/mama, gf/bf)
- Эмоциональный контекст влияет на результат (apology → lower intimacy)

### Batch Emotion Query Optimization
- Новая функция `get_flowers_by_emotions()` с window functions
- **1 SQL запрос** вместо 3 последовательных
- Экономия ~10-15ms на запрос
- Логирование timing для мониторинга

### Parallel Pipeline Execution
- FIA + EIA запускаются **параллельно** (Phase 1)
- CIA + AITB + RFFA + CRI запускаются **параллельно** (Phase 3)
- ~2.3x ускорение pipeline

### Budget Support
- Новый параметр `budget_range` в API
- Интеграция с вопросами перед pipeline
- Фильтрация цветов по ценовому диапазону

---

## 🏗️ Архитектура

### Agent Pipeline (10 агентов)

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

**Агенты:**
| # | Agent | Name | Description | Critical? |
|---|-------|------|-------------|-----------|
| 0 | **VIA** | Vision Image Analyzer | Анализ фото букетов (опционально) | No |
| 1 | **FIA** | Flower Intent Agent | Парсинг намерений | **Yes** |
| 2 | **EIA** | Emotion Intelligence Agent | Детекция эмоций | **Yes** |
| - | *Relationship Inference* | (deterministic) | Мгновенный, без AI | - |
| 3 | **FMRA** | Flower Matching & Ranking | Выбор кандидатов (DB-first для vision) | **Yes** |
| 4 | **CIA** | Context Intensity Agent | Расчёт интенсивности | No |
| 5 | **AITB** | Adaptive Tone Builder | Адаптация тона | No |
| 6 | **RFFA** | Risk & Fit Assessment | Оценка рисков | No |
| 7 | **CRI** | Cultural Intelligence | Культурный контекст | No |
| 8 | **SRFL** | Self-Reflection Layer | Валидация когерентности | No |
| 9 | **SFA** | Symbolic Flower Agent | **Сборка финального payload** | **Yes** |

**Critical agents** (FIA, EIA, FMRA, SFA) останавливают pipeline при ошибке. Non-critical агенты логируют ошибки, но продолжают работу.

### Relationship Inference

```python
# Мгновенный детерминистический маппинг
from backend.agents.adapters.relationship_inference import infer_relationship

result = infer_relationship(
    recipient="wife",
    occasion="apology",
    primary_emotion="guilt"
)
# → RelationshipData(type="romantic", stage="established", intimacy=0.7, ...)
```

**Покрытие:**
- Romantic: wife, husband, girlfriend, boyfriend, partner, fiancé/fiancée
- Family: mother/mom/mum/mama, father/dad, sister, brother, grandma, grandpa, aunt, uncle, niece, nephew
- Professional: boss, colleague, coworker, client, mentor, employee
- Social: friend, best friend, roommate, neighbor
- Special: ex-*, in-laws (mother-in-law, etc.)

### Batch Emotion Query

```python
# Один запрос вместо 3
from backend.database.flower_database import get_flowers_by_emotions

results = get_flowers_by_emotions(
    emotions=["love", "gratitude", "apology"],
    top_n_per=5,
    primary_emotion="love",
    primary_top_n=10
)
# → {"love": (10 matches), "gratitude": (5 matches), "apology": (5 matches)}
```

---

## 🚀 Quick Start

### Backend

```bash
# Установка
cd backend
pip install -r requirements.txt

# Инициализация базы
python -m backend.database.init_db

# Запуск сервера
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Тесты
PYTHONPATH=. pytest backend/tests/ -v
```

### iOS

```bash
# Открыть в Xcode
open FSense_2.xcodeproj

# Build Server (если используется)
xcode-build-server config -scheme FSense_2 -workspace .
```

**Base URL:**
- Simulator: `http://localhost:8000`
- Device: `http://192.168.1.16:8000` (замените на IP вашего Mac)

---

## 📊 Примеры использования

### Python CLI

```bash
# Простая рекомендация
python -m backend.pipeline.runner "I love my girlfriend" --pretty

# С регионом
python -m backend.pipeline.runner "Хочу извиниться" --region RU --pretty

# С изображением (bouquet scan)
python -m backend.pipeline.runner "What flower is this?" --image path/to/image.jpg --pretty
```

### API

```bash
# POST /api/recommend
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I want to apologize to my wife",
    "region": "US",
    "budget_range": "50-100"
  }'
```

**Response:**
```json
{
  "header": {
    "name": "White Tulip",
    "imageUrl": null,
    "imageCacheKey": "white_tulip_apology_remorse"
  },
  "meaning": {
    "meanings": ["Forgiveness", "Sincerity", "New beginnings"],
    "moodIntensity": { "value": 0.65, "label": "High" }
  },
  "alternatives": [
    {
      "flowerId": "blue_hydrangea",
      "name": "Blue Hydrangea",
      "confidence": 0.87,
      "briefReason": "Also expresses apology"
    }
  ]
}
```

---

## 🎯 Key Features

### Emotional Intelligence
- 50+ распознаваемых эмоций
- Интенсивность эмоций (0.0-1.0)
- Контекстные флаги (is_making_amends, is_celebration, etc.)

### Relationship Context (Deterministic)
- 30+ типов отношений с алиасами
- Стадия отношений (new, early, established, long_term)
- Уровень близости (intimacy_level)
- Эмоциональный контекст влияет на результат

### Cultural Awareness
- 17 регионов: US, RU, JP, CN, KR, UK, DE, FR, IT, ES, BR, MX, IN, EU, FI, SE, GR
- Культурные табу (белые цветы в Азии, жёлтые в России)
- Региональные правила для количества цветов

### Risk Assessment
- 4 категории рисков: intensity_mismatch, relationship_inappropriate, emotional_alignment, cultural_concern
- Severity levels: low, medium, high
- Mitigation suggestions

### Vision Analysis
- Распознавание цветов с фото
- DB-first подход (meanings из базы, без AI-вызова)
- Confidence scoring

---

## 📁 Structure

```
FSense_2/
├── backend/
│   ├── agents/
│   │   ├── base.py                    # BaseAgent interface
│   │   └── adapters/
│   │       ├── fia_adapter.py         # Flower Intent Agent
│   │       ├── eia_adapter.py         # Emotion Intelligence Agent
│   │       ├── relationship_inference.py  # Deterministic (NEW)
│   │       ├── fmra_adapter.py        # Flower Matching & Ranking
│   │       ├── cia_adapter.py         # Context Intensity Agent
│   │       ├── aitb_adapter.py        # Adaptive Tone Builder
│   │       ├── rffa_adapter.py        # Risk & Fit Assessment
│   │       ├── cri_adapter.py         # Cultural Intelligence
│   │       ├── srfl_adapter.py        # Self-Reflection Layer
│   │       ├── via_adapter.py         # Vision Image Analyzer
│   │       └── sfa_adapter.py         # Symbolic Flower Agent
│   │
│   ├── database/
│   │   ├── flower_database.py         # SQLite queries + batch functions
│   │   ├── flowers.db                 # Flower data
│   │   └── fsense.db                  # App data (cache, sessions)
│   │
│   ├── pipeline/
│   │   ├── orchestrator.py            # Parallel execution
│   │   ├── context.py                 # PipelineContext
│   │   └── runner.py                  # iOS entrypoint
│   │
│   ├── schemas/                       # Pydantic models
│   ├── services/                      # ImageService, History
│   └── tests/
│       ├── test_pipeline_smoke.py     # 32 tests
│       └── test_flower_database.py    # 9 tests (batch query)
│
└── FSense/                            # iOS SwiftUI app
    ├── App/                           # FSenseApp, AppEnvironment
    ├── Features/
    │   ├── Home/                      # HomeView, HomeViewModel
    │   ├── Chat/                      # Chat UI, history
    │   ├── FlowerCard/                # Card views (3 tabs)
    │   ├── Scan/                      # Camera, ScanResultCard
    │   ├── LovedOnes/                 # Profile management
    │   └── Profile/                   # Settings, archives
    ├── Services/                      # API clients
    └── Shared/                        # Reusable components
```

---

## 🧪 Testing

### Backend Tests

```bash
# Все тесты
PYTHONPATH=. pytest backend/tests/ -v

# Pipeline tests (32 tests)
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py -v

# Database batch query tests (9 tests)
PYTHONPATH=. pytest backend/tests/test_flower_database.py -v

# Один тест
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py::TestRelationshipInference -v

# С coverage
PYTHONPATH=. pytest backend/tests/ --cov=backend --cov-report=html
```

**41 тестов:**
- ✅ FlowerChat API (11 tests)
- ✅ Relationship Inference (8 tests)
- ✅ Relationship Integration (3 tests)
- ✅ PipelineContext (3 tests)
- ✅ Orchestrator (2 tests)
- ✅ FMRA Vision (3 tests)
- ✅ Schemas (1 test)
- ✅ BaseAgent (1 test)
- ✅ Batch Query (9 tests)

---

## 🔧 Configuration

### Environment Variables

```bash
# backend/.env
OPENAI_API_KEY=sk-...           # Required for AI agents
OPENAI_MODEL=gpt-4o             # Default model
OPENAI_MODEL_FAST=gpt-4o-mini   # For simple tasks
FSENSE_ENV=local                # local/staging/production

# Optional
DATABASE_URL=postgresql://...   # Supabase
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
```

### iOS Configuration

```swift
// FSense/Services/APIService.swift
var baseURL: String {
    #if DEBUG
        return "http://192.168.1.16:8000"  // Ваш Mac IP
    #else
        return "http://localhost:8000"     // Production URL
    #endif
}
```

---

## 📝 Database

### Flower Database (flowers.db)

**Tables:**
- `flowers` (155 цветов)
- `flower_meanings` (148 emotion-flower mappings)
- `flower_cultural_contexts` (49 культурных контекстов)
- `region_number_rules` (8 региональных правил)
- `flower_color_meanings` (14 цветовых значений)

**Key functions:**
```python
# Single emotion (legacy)
get_flowers_by_emotion("love", top_n=5)

# Batch emotions (v0.17+)
get_flowers_by_emotions(["love", "gratitude"], top_n_per=5)
```

**Reseed after changes:**
```bash
python -m backend.database.init_db
```

### App Database (fsense.db)

**Tables:**
- `image_cache` - кэш сгенерированных изображений
- `sessions` - пользовательские сессии
- `conversation_history` - история чатов

---

## 🎨 iOS UI

### FlowerCard

**3 таба:**
1. **Meaning** - символизм, mood intensity, alternatives
2. **Gifting** - пригодность, риски, when to gift/avoid
3. **Context** - культурный контекст, отношения, timing

### Alternatives Section

```swift
if !flower.alternatives.isEmpty {
    AlternativesSection(
        alternatives: flower.alternatives,
        onTap: { alternative in
            // Navigate to alternative flower card
        }
    )
}
```

**Отображение:**
- Горизонтальный ScrollView
- До 4 альтернатив
- Изображение 80x80pt
- Название (2 lines)
- Confidence badge (87%)

---

## 🐛 Troubleshooting

### Backend не запускается

```bash
# Check database
ls -la backend/database/*.db

# Reinit if needed
python -m backend.database.init_db

# Check dependencies
pip install -r backend/requirements.txt
```

### Relationship inference возвращает unknown

```bash
# Проверьте логи
python -c "
from backend.agents.adapters.relationship_inference import infer_relationship
result = infer_relationship('girlfriend', 'birthday')
print(result)
"
```

### Slow pipeline

```bash
# Проверьте batch query timing
python -m backend.pipeline.runner "I love you" --pretty 2>&1 | grep "Batch emotion"
# Expected: "Batch emotion query (3 emotions): 1-2ms"
```

---

## 📈 Performance

### v0.17 Optimizations

| Optimization | Before | After | Savings |
|--------------|--------|-------|---------|
| Relationship inference | ~500ms (AI) | ~0ms (deterministic) | **500ms** |
| Emotion queries | 3 × 7ms = 21ms | 1 × 2ms | **~15ms** |
| Parallel Phase 1 | ~1000ms | ~500ms | **~500ms** |
| Parallel Phase 3 | ~2000ms | ~600ms | **~1400ms** |

**Total pipeline time:** ~3-4s → ~1.5-2s (~2x faster)

---

## 📈 Roadmap

### v0.18
- [ ] User-specific recommendation history
- [ ] Персонализация на основе истории
- [ ] A/B тестирование diversity penalty

### v0.19
- [ ] Voice input support
- [ ] Экспорт рекомендаций в PDF/Share
- [ ] Push notifications для праздников

---

## 👥 Contributing

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
# ...

# Run tests
PYTHONPATH=. pytest backend/tests/ -v

# Commit
git commit -m "feat: your feature description

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push
git push origin feature/your-feature
```

---

## 📄 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- OpenAI GPT-4 для AI agents
- SwiftUI для iOS UI
- FastAPI для backend API
- SQLite для database

**Built with ❤️ by FSense Team**

Version: **0.17.0**
Last Updated: **February 4, 2026**
