# 🌸 FSense

> AI-powered flower recommendation system that understands context, emotion, and meaning

**Version 0.1.2** • Built with SwiftUI + Python
An intelligent assistant that helps you find the perfect flower for any occasion.

---

## ✨ What's New in v0.1.2

### ⚡️ Instant Chat Opening
- **Pre-warmed keyboard** loads on app launch for zero-delay typing
- Removed 300ms focus delay → chat opens in **<50ms**
- Eliminated double reset on chat open
- Idempotent state management for smoother UX

### 🖼️ Bouquet Image Analysis
- Upload bouquet photos for **GPT-4 Vision** analysis
- Identifies flowers in complex arrangements
- Smart context understanding from images

### 💎 UI/UX Polish
- Refined chat interface with glass morphism effects
- Smooth gradient transitions on home screen
- Optimized scroll performance with lazy loading
- Enhanced message bubbles and thinking cards

---

## 🎯 Features

### 🤖 AI Chat Assistant
- Natural conversation flow with context awareness
- Real-time thinking visualization (10-agent pipeline)
- Personalized flower recommendations
- Follow-up suggestions

### 📸 Visual Recognition
- Attach photos from library or camera
- Analyze existing bouquets
- Visual context for better recommendations

### 💾 Session Management
- Persistent chat history
- Quick access to recent conversations
- Rename and organize chats

### 🎨 Native iOS Experience
- SwiftUI with iOS 26+ optimizations
- Glass morphism design language
- Haptic feedback
- Dark mode ready

---

## 🏗️ Architecture

### iOS App (SwiftUI)
```
FSense/
├── App/              # Entry point, environment
├── Features/         # Home, Chat, FlowerCard, Scan, Profile
├── Services/         # API, History, Archive, Pipeline events
└── Shared/           # Components, utilities, KeyboardWarmer
```

### Python Backend (Agent Pipeline)
```
backend/
├── pipeline/         # Orchestrator, context, runner
├── agents/adapters/  # 10 specialized agents (FIA, EIA, RIL, etc.)
├── schemas/          # Pydantic models (FlowerCardPayload)
└── core/             # Settings, AI client
```

### Agent Flow
```
User Input → FIA → EIA → RIL → FMRA → CIA → AITB → RFFA → CRI → SRFL → SFA → Recommendation
```

**Single Source of Truth:** All data flows through `PipelineContext`
**Final Assembler:** Only SFA writes the iOS payload

---

## 🚀 Quick Start

### iOS Development
1. Open `FSense_2.xcodeproj` in Xcode
2. Select your device/simulator
3. Build & Run (`Cmd+R`)

### Backend Development
```bash
cd backend
pip install -r requirements.txt

# Configure
cp .env.example .env
# Set OPENAI_API_KEY in .env

# Run tests
PYTHONPATH=. pytest backend/tests/ -v

# Test pipeline CLI
python -m backend.pipeline.runner "I want to apologize to my wife" --pretty
```

---

## 📊 Performance Metrics

| Metric | Before | After (v0.1.2) |
|--------|--------|----------------|
| Chat Open Delay | 400-600ms | **<50ms** ⚡️ |
| Keyboard Focus | Cold start | Pre-warmed 🔥 |
| Message Render | Full re-render | Cached + Lazy 📦 |
| State Updates | Multiple resets | Idempotent ✅ |

---

## 🛠️ Tech Stack

### Frontend
- **SwiftUI** - Declarative UI framework
- **Combine** - Reactive programming
- **Swift Concurrency** - Async/await, actors
- **UIKit** - Keyboard pre-warming, camera

### Backend
- **Python 3.11+** - Core runtime
- **OpenAI GPT-4** - LLM for agents
- **GPT-4 Vision** - Image analysis
- **Pydantic** - Schema validation
- **pytest** - Testing framework

---

## 📝 Development Commands

```bash
# iOS Build
xcodebuild -project FSense_2.xcodeproj -scheme FSense_2 -configuration Debug

# Python Tests
PYTHONPATH=. pytest backend/tests/ -v

# Run Single Test
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py::test_run_flower_chat_success -v

# Pipeline CLI
python -m backend.pipeline.runner "Your message here" --pretty
```

---

## 🎨 Design Philosophy

1. **Instant Feedback** - No loading spinners, progressive enhancement
2. **Glass Morphism** - Modern, translucent UI elements
3. **Context-Aware** - AI understands emotion, culture, relationships
4. **Native Feel** - Respect iOS design patterns and interactions

---

## 🔮 Roadmap

### v0.2.0 (Next)
- [ ] Multi-language support (localization)
- [ ] Flower dictionary with search
- [ ] Share recommendations to social media
- [ ] Widget for quick access

### v0.3.0
- [ ] Voice input for chat
- [ ] AR flower visualization
- [ ] Local florist integration
- [ ] Offline mode

---

## 📄 License

Proprietary - All rights reserved

---

## 🤝 Contributing

This is a private project. For questions or collaboration inquiries, please contact the maintainers.

---

**Made with ❤️ and 🌸**
*Helping you say it with flowers*
