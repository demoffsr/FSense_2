# Clarification Chat Design

**Дата:** 2026-01-27
**Версия:** 1.0
**Статус:** Approved

## Обзор

Добавление возможности отправлять уточняющие вопросы в чате, на которые бэкенд отвечает текстом (без FlowerCardPayload).

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      iOS (ChatViewModel)                     │
│  Отправляет: message + ChatContext (optional fallback)      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 run_flower_chat_v2()                         │
│                     (новый endpoint)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              IntentClassifierAgent (новый)                   │
│  Определяет: flower_request | clarification | off_topic     │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      flower_request    clarification    off_topic
              │               │               │
              ▼               ▼               ▼
    Полный пайплайн    QuickReplyAgent   Статический
    (10 агентов)       + FlowerKnowledgeBase  ответ
              │               │               │
              ▼               ▼               ▼
    FlowerCardPayload   TextResponse     TextResponse
```

## Формат ответа

```python
# Рекомендация (как сейчас)
{"success": True, "type": "recommendation", "data": FlowerCardPayload}

# Текстовый ответ (новый)
{"success": True, "type": "text", "data": {"message": "Да, розы отлично подходят..."}}
```

## IntentClassifierAgent

### Входные данные

```python
class ClassifierInput:
    message: str           # "А розы точно подходят для извинений?"
    context: ChatContext   # Опциональный fallback от iOS
```

### Выходные данные

```python
class ClassifierOutput:
    intent: Literal["flower_request", "clarification", "off_topic"]
    confidence: float      # 0.0 - 1.0
    extracted_flower: Optional[str]   # "red_rose"
    extracted_emotion: Optional[str]  # "apology"
    detected_language: Literal["en", "ru"]
    clarification_type: Optional[Literal[
        "confirmation",      # "А точно подходит?"
        "alternatives",      # "Что ещё можно?"
        "cultural",          # "Можно ли в Японии?"
        "quantity",          # "Сколько дарить?"
        "general_info"       # "Что символизирует?"
    ]]
```

### Логика классификации

- `flower_request` — явный запрос на подбор цветов
- `clarification` — вопрос о цветах без запроса на подбор
- `off_topic` — не связано с цветами
- При `confidence < 0.7` → консервативно `flower_request`

## QuickReplyAgent + FlowerKnowledgeBase

### FlowerKnowledgeBase методы

```python
get_flower_info(flower_id) → название, значения, цена
get_alternatives(emotion, exclude) → список альтернатив
get_cultural_rules(flower_id, region) → табу, советы
get_quantity_rules(region) → правила количества
get_emotion_flowers(emotion, top_n) → топ цветов
```

### Типы уточняющих вопросов

1. **confirmation** — "А точно ли розы подходят для извинений?"
2. **alternatives** — "А что ещё можно подарить кроме роз?"
3. **cultural** — "Можно ли дарить белые цветы в Японии?"
4. **quantity** — "Сколько цветов дарить в России?"
5. **general_info** — "Что символизируют тюльпаны?"

### Язык ответа

Автоопределение по языку вопроса (en/ru).

## Изменения в iOS

### ChatContext

```swift
struct ChatContext: Codable {
    let lastFlowerName: String?
    let lastEmotion: String?
    let region: String
}
```

### ChatResponse

```swift
enum ChatResponseType: String, Codable {
    case recommendation
    case text
}

struct ChatResponse: Codable {
    let success: Bool
    let type: ChatResponseType
    let data: ChatResponseData
}
```

## План реализации

### Новые файлы

```
backend/
├── agents/adapters/
│   ├── intent_classifier_agent.py
│   └── quick_reply_agent.py
├── services/
│   └── flower_knowledge_base.py
└── schemas/
    └── chat_response.py
```

### Изменения в существующих файлах

| Файл | Изменения |
|------|-----------|
| `backend/pipeline/runner.py` | `run_flower_chat_v2()` |
| `FSense/Services/APIService.swift` | `sendMessage()` |
| `FSense/Features/Chat/ChatViewModel.swift` | `buildChatContext()`, `showTextResponse()` |

### Порядок

1. FlowerKnowledgeBase
2. IntentClassifierAgent
3. QuickReplyAgent
4. run_flower_chat_v2()
5. iOS: APIService
6. iOS: ChatViewModel
