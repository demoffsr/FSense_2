# 🌸 FSense

> AI-powered flower recommendation system that understands context, emotion, and meaning

**Version 0.13** • Built with SwiftUI + Python
An intelligent assistant that helps you find the perfect flower for any occasion.

---

## ✨ What's New in v0.13

### 💾 Persistent Chat Sessions
- **Auto-save conversations** with timestamp and preview
- **Seamless session loading** when reopening chat
- Smart session management with ChatHistoryManager
- Never lose your conversation context

### 🔍 In-Chat Search
- **Full-text search** across all messages in current session
- **Live highlighting** with smooth scroll to matches
- Keyboard-first UX with instant focus
- Clean search bar that slides from top

### 🗄️ Chat Archive
- **Archive completed conversations** from menu
- Dedicated archive view in Profile tab
- **Success toast notification** with auto-dismiss
- Keep your active chats organized

### 💎 Unified Glass Effect UI
- **Single frosted background** for all toolbar buttons
- Replaced double glass backgrounds with `.ultraThinMaterial`
- Consistent design language: New Chat, Search, Menu buttons
- Clean white stroke overlays for depth

### ⬇️ Smart Scroll-to-Bottom Button
- **Shows when scrolling up** from bottom
- **Hides when reaching bottom** manually or via tap
- Stays visible until user action (no flickering)
- Matches toolbar button style with frosted glass

### ⌨️ Typewriter Text Animation
- Smooth character-by-character reveal for AI responses
- Natural reading pace with configurable speed
- SwiftUI-native implementation with `TimelineView`

### 🎨 Visual Refinements
- **Unified background color** (Color(white: 0.97)) for chat and input areas
- Removed unused namespace properties for cleaner code
- Enhanced button foreground styles (`.foregroundStyle(.black)`)
- Better visual hierarchy throughout chat interface

---

## 🎯 Features

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

### 📸 Visual Recognition
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
- **Unified glass design language**
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
│   ├── Scan/                 # Camera & image recognition
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
2. Select your device/simulator (iOS 26+)
3. Build & Run (`Cmd+R`)

**Instant Features:**
- Keyboard pre-warmed on launch
- Chat opens in <50ms
- Session auto-loads if returning to conversation

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

| Metric | v0.1.2 | v0.13 | Improvement |
|--------|--------|-------|-------------|
| Chat Open Delay | <50ms | <50ms | ✅ Maintained |
| Session Persistence | ❌ None | ✅ Full | 🎉 New |
| In-Chat Search | ❌ None | ✅ Live | 🎉 New |
| UI Consistency | ⚠️ Mixed | ✅ Unified | 📈 Better |
| Scroll Button UX | ⚠️ Glitchy | ✅ Smooth | 📈 Fixed |
| Chat Archive | ❌ None | ✅ Full | 🎉 New |

---

## 🛠️ Tech Stack

### Frontend
- **SwiftUI** - Declarative UI framework (iOS 26+)
- **Combine** - Reactive state management
- **Swift Concurrency** - Async/await, actors
- **UIKit** - Keyboard pre-warming, camera integration

### Backend
- **Python 3.11+** - Core runtime
- **OpenAI GPT-4** - LLM for agent pipeline
- **GPT-4 Vision** - Bouquet image analysis
- **Pydantic** - Schema validation & type safety
- **pytest** - Testing framework

### Design System
- **Glass Morphism** - `.ultraThinMaterial` with white stroke overlays
- **SF Symbols** - Native iOS icons
- **Dynamic Type** - Accessibility-ready typography
- **Haptics** - Tactile feedback for interactions

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

1. **Instant Feedback** - No loading spinners, progressive enhancement
2. **Unified Glass Language** - Consistent frosted UI across all controls
3. **Context Preservation** - Sessions persist, search highlights, archive organizes
4. **Native Feel** - Respect iOS patterns (sheets, toolbars, haptics)
5. **Accessibility First** - Dynamic Type, VoiceOver, reduce motion

---

## 🔍 Feature Deep Dive

### Chat Session Persistence
```swift
// Auto-save on every message
ChatHistoryManager.shared.saveSession(session)

// Load session when reopening chat
if let session = controller.sessionToLoad {
    viewModel.loadSession(session)
}
```

Sessions include:
- Message history (user + AI)
- Attached images
- Timestamp metadata
- Preview text (first user message)

### In-Chat Search
- **Trigger:** Tap search icon in toolbar
- **Focus:** Auto-focus search field with keyboard
- **Highlight:** Yellow background on matching messages
- **Scroll:** Smooth animation to first match
- **Exit:** Clear highlights and return to input

### Archive System
```swift
// Archive current session
ChatArchiveService.shared.archiveSession(session)

// Remove from active history
ChatHistoryManager.shared.deleteSession(session)

// View archives in Profile tab
ChatArchiveView() // Standalone list view
```

---

## 🔮 Roadmap

### v0.14 (Next Sprint)
- [ ] Search across **all sessions** (not just current)
- [ ] Export chat as PDF/text
- [ ] Session tags and categories
- [ ] Pin important conversations

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

Proprietary - All rights reserved

---

## 🤝 Contributing

This is a private project. For questions or collaboration inquiries, please contact the maintainers.

---

## 🙏 Acknowledgments

- **OpenAI GPT-4** - Powering the agent pipeline
- **SwiftUI** - Making native iOS development delightful
- **Glass Morphism** - Modern UI design trend

---

**Made with ❤️ and 🌸**
*Helping you say it with flowers*

> "The earth laughs in flowers." — Ralph Waldo Emerson
