# FSense v0.16 - AI-Powered Flower Recommendation System

FSense — это умная система рекомендаций цветов, использующая конвейер из 10 AI-агентов для подбора идеального цветка на основе эмоционального контекста пользователя.

## 🆕 Что нового в v0.16

### Улучшения агентов
Все 10 агентов получили значительные апгрейды:
- **FIA v4**: context_flags, региональные подсказки, умный fallback
- **EIA v4**: расширенная таксономия эмоций (50+ emotions), маркеры сложности
- **RIL v3**: gift_appropriateness, динамические расчеты
- **FMRA**: обогащённые промпты, context-aware fallback
- **CIA**: поддержка 17 культурных регионов (вместо 3)
- **AITB**: исправлен dead code - heuristic методы теперь используются
- **RFFA**: исправлен баг с hardcoded confidence, 4 категории рисков
- **CRI**: обогащённый AI контекст (occasion/recipient/relationship)
- **SRFL v3**: 50+ эмоций, word boundary matching
- **VIA**: детальный промпт, валидация цветов
- **SFA**: integration guidelines, context-aware fallback

### Система разнообразия
- ✅ Уравнены top scores цветов (1.0 → 0.95) - теперь нет монополистов
- ✅ Добавлен `RANDOM()` в SQL запросы для разных результатов
- ✅ Усилен diversity penalty (0.05 → 0.15, max 0.7)
- ✅ Убран hardcoded red_rose fallback
- ✅ Автогенерация alternatives из базы данных

### iOS альтернативы
- **AlternativesSection** - горизонтальный scroll с рекомендациями
- **AlternativeFlowerCell** - карточка с изображением, названием, confidence %
- Интеграция в таб **Meaning** (секция "Также подходят:")

---

## 🏗️ Архитектура

### Agent Pipeline (10 агентов)

```
User Input → Context → Agents → FlowerCardPayload → iOS
```

**Порядок выполнения:**
1. **VIA** - Vision Image Analyzer (если есть фото)
2. **FIA** - Flower Intent Agent (парсинг намерений)
3. **EIA** - Emotion Intelligence Agent (детекция эмоций)
4. **RIL** - Relationship Intelligence Layer (анализ отношений)
5. **FMRA** - Flower Matching & Ranking Agent (выбор 5 кандидатов)
6. **CIA** - Context Intensity Agent (расчёт интенсивности)
7. **AITB** - Adaptive Intelligence & Tone Builder (адаптация тона)
8. **RFFA** - Risk & Fit Assessment Agent (оценка рисков)
9. **CRI** - Cultural & Regional Intelligence (культурный контекст)
10. **SRFL** - Self-Reflection Layer (валидация когерентности)
11. **SFA** - Symbolic Flower Agent (сборка финального payload)

### Diversity System

```python
# 1. Database scores equalized
pink_rose|gratitude|0.95  # было 1.0
crocus|joy|0.95           # было 1.0
red_rose|love|0.95        # было 1.0

# 2. Random ordering for ties
ORDER BY match_score DESC, RANDOM()

# 3. Diversity penalty
penalty = count * 0.15  # было 0.05
max_penalty = 0.7       # было 0.5

# 4. Smart fallback
NEUTRAL_FALLBACKS = ["white_lily", "pink_carnation",
                     "blue_hydrangea", "yellow_tulip", "lavender"]
```

---

## 🚀 Quick Start

### Backend

```bash
# Установка
cd backend
pip install -r requirements.txt

# Инициализация базы (обязательно после изменений в flower_database.py)
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
```

### API

```bash
# POST /api/recommend
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "I want to apologize to my wife",
    "region": "US"
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

### Relationship Context
- Анализ типа отношений (romantic, professional, familial, friendship)
- Стадия отношений (new, early, established, long_term)
- Уровень близости (intimacy_level)

### Cultural Awareness
- 17 регионов: US, RU, JP, CN, KR, UK, DE, FR, IT, ES, BR, MX, IN, EU, FI, SE, GR
- Культурные табу (белые цветы в Азии, жёлтые в России)
- Региональные правила для количества цветов

### Risk Assessment
- 4 категории рисков: intensity_mismatch, relationship_inappropriate, emotional_alignment, cultural_concern
- Severity levels: low, medium, high
- Mitigation suggestions

---

## 📁 Structure

```
FSense_2/
├── backend/
│   ├── agents/adapters/       # 10 AI агентов
│   ├── database/              # SQLite базы (flowers.db, fsense.db)
│   ├── pipeline/              # Orchestrator, Context, Runner
│   ├── schemas/               # Pydantic models (FlowerCardPayload)
│   ├── services/              # ImageService, RecommendationHistory
│   └── tests/                 # Smoke tests
│
└── FSense/                    # iOS SwiftUI app
    ├── Features/
    │   ├── FlowerCard/        # Карточка цветка
    │   │   ├── Models/        # Flower, AlternativeFlower
    │   │   └── Views/
    │   │       └── Components/  # AlternativesSection, AlternativeFlowerCell
    │   ├── Chat/              # Чат интерфейс
    │   ├── Scan/              # Сканер цветов (камера)
    │   └── Profile/           # Профиль
    └── Services/              # APIService, FlowerCardPayload
```

---

## 🧪 Testing

### Backend Tests

```bash
# Все тесты
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py -v

# Один тест
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py::test_flower_chat_success -v

# С coverage
PYTHONPATH=. pytest backend/tests/ --cov=backend --cov-report=html
```

**18 тестов:**
- ✅ FlowerChat API (7 tests)
- ✅ PipelineContext (3 tests)
- ✅ Orchestrator (2 tests)
- ✅ Schemas (1 test)
- ✅ BaseAgent (1 test)

---

## 🔧 Configuration

### Environment Variables

```bash
# backend/.env
OPENAI_API_KEY=sk-...        # Required for AI agents
OPENAI_MODEL=gpt-4o          # Default model
FSENSE_ENV=local             # local/staging/production
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

### Alternatives не показываются

1. Проверьте что backend отдаёт alternatives:
```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I love my girlfriend", "region": "US"}' | jq '.alternatives'
```

2. Clean Build в Xcode (Cmd+Shift+K)

3. Проверьте что база пересоздана с новыми scores

### Всегда одинаковые цветы

```bash
# Проверьте scores в базе
sqlite3 backend/database/flowers.db \
  "SELECT flower_id, emotion, match_score
   FROM flower_meanings
   WHERE emotion IN ('love', 'joy', 'gratitude')
   ORDER BY emotion, match_score DESC"

# Должно быть несколько цветов с 0.95 для каждой эмоции
```

---

## 📈 Roadmap

### v0.17
- [ ] Тап на alternative открывает детальную карточку
- [ ] API endpoint `/api/flower/{id}` для получения цветка по ID
- [ ] Recommendation history persistence per user
- [ ] A/B тестирование diversity penalty значений

### v0.18
- [ ] Vision analysis для распознавания цветов с камеры
- [ ] Персонализация на основе истории
- [ ] Экспорт рекомендаций в PDF/Share

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

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

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

Version: **0.16.0**
Last Updated: **February 3, 2026**
