# 🌸 FSense

> AI-powered flower recommendation system that understands context, emotion, and meaning

**Version 0.14** • Built with SwiftUI + Python
An intelligent assistant that helps you find the perfect flower for any occasion.

---

## ✨ What's New in v0.14

### 📸 Liquid Glass Scanner UI
The Scan feature gets a complete visual overhaul with iOS 26+ Liquid Glass design:

- **Glass Circular Buttons** — Large 56×56 frosted buttons for close, help, gallery, and info
- **GlassModeToggle** — Animated segmented control switching between Single Flower and Bouquet modes
- **Glowing Scan Frame** — Corner brackets with subtle pulsing glow effect
- **Glass Analyzing Overlay** — Frosted spinner with status pill while identifying flowers
- **Glass Result Card** — Bottom sheet with glass background, confidence badges, and action buttons
- **Glass Error States** — Beautiful error modals with glass containers

All components gracefully fallback to `.ultraThinMaterial` on iOS 15-25.

### 🎯 New Scanner Layout
```
┌─────────────────────────────────────┐
│  (✕)                          (?)   │  ← Glass circles, 56×56
│                                     │
│      ┌─────────────────────┐        │
│      │    ✨ Glow Frame ✨   │        │
│      │                     │        │
│      └─────────────────────┘        │
│                                     │
│       [Single] [Bouquet]            │  ← Glass segmented control
│              ⚡                      │  ← Flash toggle
│                                     │
│   (📷)        (○)        (ℹ)       │  ← Gallery, Capture, Info
└─────────────────────────────────────┘
```

### 🔧 Technical Improvements
- **GlassCircleButton** — Reusable component for all glass circular buttons
- **GlassButtonStyle** — Custom button style with glass effect and press animation
- **CaptureButtonStyle** — Scale animation for capture button feedback
- **iOS 26 availability checks** — `#available(iOS 26, *)` with fallbacks throughout

---

## 🎯 Features

### 📸 Flower Scanner (NEW!)
- **Single Flower Mode** — Point and identify any flower
- **Bouquet Mode** — Analyze multiple flowers in one shot
- **Gallery Import** — Scan photos from your library
- **Glass UI** — Premium iOS 26 Liquid Glass design
- **Confidence Scoring** — See identification accuracy
- **Quick Results** — Fast preview before full details

### 🤖 AI Chat Assistant
- Natural conversation flow with context awareness
- Real-time thinking visualization (10-agent pipeline)
- Personalized flower recommendations
- Follow-up suggestions
- **Persistent sessions** that survive app restarts

### 🔍 Search & Archive
- **In-chat full-text search** with live highlighting
- **Archive management** to organize conversations
- Quick access to recent and archived chats
- Session metadata (timestamp, message count)

### 📷 Visual Recognition
- Attach photos from library or camera
- Analyze existing bouquets with **GPT-4 Vision**
- Visual context for better recommendations

### 💬 Chat Experience
- **Instant keyboard response** (pre-warmed on launch)
- Typewriter animation for AI messages
- Smart scroll behavior with floating bottom button
- Smooth glass morphism effects throughout

### 💾 Session Management
- **Auto-save** every conversation
- Rename and organize chats
- Archive completed conversations
- Delete individual sessions

### 🎨 Native iOS Experience
- SwiftUI with iOS 26+ optimizations
- **Liquid Glass design language**
- Haptic feedback
- Dark mode ready
- Native sheet presentations

---

## 🏗️ Architecture

### iOS App (SwiftUI)
```
FSense/
├── App/                      # Entry point, environment
├── Features/
│   ├── Home/                 # Collapsed chat bar with glass UI
│   ├── Chat/                 # Full-screen chat with search
│   ├── FlowerCard/           # Recommendation details
│   ├── Scan/                 # 📸 Camera & Liquid Glass UI
│   │   ├── Views/
│   │   │   ├── GlassModeToggle.swift
│   │   │   ├── CameraControlsView.swift
│   │   │   ├── ScanFrameOverlay.swift
│   │   │   ├── AnalyzingOverlay.swift
│   │   │   └── QuickInfoCardView.swift
│   │   ├── ScanView.swift
│   │   └── ScanViewModel.swift
│   └── Profile/              # History, archive, settings
├── Services/
│   ├── ChatHistoryManager    # Session persistence
│   ├── ChatArchiveService    # Archive management
│   ├── APIService            # Backend communication
│   └── KeyboardWarmer        # Pre-warm keyboard
└── Shared/                   # Components, utilities
```

### Python Backend (Agent Pipeline)
```
backend/
├── pipeline/                 # Orchestrator, context, runner
├── agents/adapters/          # 10 specialized agents
│   ├── fia.py               # Flower Intent Agent
│   ├── eia.py               # Emotion Intelligence Agent
│   ├── ril.py               # Relationship Intelligence Layer
│   ├── fmra.py              # Flower Matching & Ranking
│   ├── cia.py               # Context Intensity Agent
│   ├── aitb.py              # Adaptive Intelligence & Tone
│   ├── rffa.py              # Risk & Fit Assessment
│   ├── cri.py               # Cultural & Regional Intelligence
│   ├── srfl.py              # Self-Reflection Layer
│   └── sfa.py               # Symbolic Flower Agent (final)
├── schemas/                  # Pydantic models
│   ├── flower_card_payload.py
│   └── pipeline_enums.py
└── core/                     # Settings, AI client
```

### Agent Flow
```
User Input → PipelineContext → FIA → EIA → RIL → FMRA → CIA →
             AITB → RFFA → CRI → SRFL → SFA → FlowerCardPayload
```

**Design Principles:**
- **Single Source of Truth:** All data flows through `PipelineContext`
- **Final Assembler:** Only SFA writes the iOS payload (`ui_payload`)
- **Stateless Agents:** No direct agent-to-agent communication
- **Idempotent Operations:** Safe to retry any step

---

## 🚀 Quick Start

### iOS Development
1. Open `FSense_2.xcodeproj` in Xcode
2. Select your device/simulator (iOS 26+ for full Liquid Glass)
3. Build & Run (`Cmd+R`)

**Instant Features:**
- Keyboard pre-warmed on launch
- Chat opens in <50ms
- Session auto-loads if returning to conversation
- Scanner with beautiful glass UI

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

| Metric | v0.13 | v0.14 | Status |
|--------|-------|-------|--------|
| Chat Open Delay | <50ms | <50ms | ✅ Maintained |
| Scanner UI | ⚠️ Basic | ✅ Liquid Glass | 🎉 Redesigned |
| iOS 26 Features | ❌ None | ✅ Full | 🎉 New |
| Glass Components | 3 | 10+ | 📈 Expanded |
| Fallback Support | — | iOS 15-25 | ✅ Complete |

---

## 🛠️ Tech Stack

### Frontend
- **SwiftUI** — Declarative UI framework (iOS 26+)
- **Combine** — Reactive state management
- **Swift Concurrency** — Async/await, actors
- **AVFoundation** — Camera capture
- **UIKit** — Keyboard pre-warming, camera integration

### Backend
- **Python 3.11+** — Core runtime
- **OpenAI GPT-4** — LLM for agent pipeline
- **GPT-4 Vision** — Image analysis
- **Pydantic** — Schema validation & type safety
- **pytest** — Testing framework

### Design System
- **Liquid Glass** — iOS 26 `.glassEffect()` API
- **Glass Morphism** — `.ultraThinMaterial` fallback
- **SF Symbols** — Native iOS icons
- **Dynamic Type** — Accessibility-ready typography
- **Haptics** — Tactile feedback for interactions

---

## 📝 Development Commands

### iOS
```bash
# Build
xcodebuild -project FSense_2.xcodeproj -scheme FSense_2 -configuration Debug

# Clean build folder
rm -rf ~/Library/Developer/Xcode/DerivedData
```

### Backend
```bash
# Run all tests
PYTHONPATH=. pytest backend/tests/ -v

# Run single test
PYTHONPATH=. pytest backend/tests/test_pipeline_smoke.py::test_run_flower_chat_success -v

# Test pipeline interactively
python -m backend.pipeline.runner "Your message here" --pretty

# Check test coverage
PYTHONPATH=. pytest backend/tests/ --cov=backend --cov-report=html
```

---

## 🎨 Design Philosophy

1. **Liquid Glass First** — Premium iOS 26 effects with graceful degradation
2. **Instant Feedback** — No loading spinners, progressive enhancement
3. **Unified Design Language** — Consistent frosted UI across all controls
4. **Context Preservation** — Sessions persist, search highlights, archive organizes
5. **Native Feel** — Respect iOS patterns (sheets, toolbars, haptics)
6. **Accessibility First** — Dynamic Type, VoiceOver, reduce motion

---

## 🔍 Feature Deep Dive

### Liquid Glass Scanner

```swift
// Glass button pattern used throughout
if #available(iOS 26, *) {
    content
        .glassEffect(.regular.interactive(), in: .circle)
} else {
    content
        .background(.ultraThinMaterial, in: Circle())
}
```

**Components:**
- `GlassModeToggle` — Segmented control with `matchedGeometryEffect`
- `GlassCircleButton` — Reusable 44/56px glass buttons
- `GlassButtonStyle` — Custom button style for action buttons
- `CaptureButtonStyle` — Scale animation on press

### Chat Session Persistence
```swift
// Auto-save on every message
ChatHistoryManager.shared.saveSession(session)

// Load session when reopening chat
if let session = controller.sessionToLoad {
    viewModel.loadSession(session)
}
```

### In-Chat Search
- **Trigger:** Tap search icon in toolbar
- **Focus:** Auto-focus search field with keyboard
- **Highlight:** Yellow background on matching messages
- **Scroll:** Smooth animation to first match
- **Exit:** Clear highlights and return to input

---

## 🔮 Roadmap

### v0.15 (Next Sprint)
- [ ] Scan history with thumbnails
- [ ] Flower detail cards from scan results
- [ ] Share scan results
- [ ] Scan-to-chat integration

### v0.2.0
- [ ] Multi-language support (localization)
- [ ] Flower dictionary with visual search
- [ ] Share recommendations to social media
- [ ] Home screen widget

### v0.3.0
- [ ] Voice input for chat (Whisper API)
- [ ] AR flower visualization (ARKit)
- [ ] Local florist integration (Maps)
- [ ] Offline mode with cached recommendations

---

## 📄 License

Proprietary — All rights reserved

---

## 🤝 Contributing

This is a private project. For questions or collaboration inquiries, please contact the maintainers.

---

## 🙏 Acknowledgments

- **OpenAI GPT-4** — Powering the agent pipeline
- **SwiftUI** — Making native iOS development delightful
- **iOS 26 Liquid Glass** — Apple's beautiful new design system

---

**Made with ❤️ and 🌸**
*Helping you say it with flowers*

> "The earth laughs in flowers." — Ralph Waldo Emerson
