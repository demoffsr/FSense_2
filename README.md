# 🌸 FSense

> AI-powered flower recommendation system that understands context, emotion, and meaning

**Version 0.15** • Built with SwiftUI + Python
An intelligent assistant that helps you find the perfect flower for any occasion—now with personalized profiles.

---

## ✨ What's New in v0.15

### 👥 Loved Ones Profiles & @Mentions
FSense now remembers the people you care about with personalized profiles:

- **Loved Ones Management** — Create profiles with photos, relationships, and preferences
- **@Mention Autocomplete** — Type `@` in chat to tag people with Liquid Glass picker
- **Taste Profiles** — Track flower style, budget, mood preferences, and allergies
- **Important Dates** — Birthdays, anniversaries, custom dates with countdown
- **Hierarchical Relationships** — Family, Romance, Friends, Professional categories
- **Users Screen** — Accessible from toolbar, organized by relationship type

### 🎨 Liquid Glass @Mention Picker
Beautiful iOS 26+ autocomplete with glass morphism:

```
When you type @ in chat:
┌───────────────────────────┐
│  👤  Anna Demidov         │  ← Glass container
│  👤  Anna Demidov         │     32pt avatars
└───────────────────────────┘     13pt medium names
      ▲ Slides up from input
```

**Features:**
- **VStack positioning** — Clean layout without overlay hacks
- **Liquid Glass UI** — `.glassEffect(.regular.tint(.white))` on iOS 26+
- **Smart filtering** — Matches name and nickname
- **Instant insertion** — Tap to insert `@Name` in chat
- **Spring animation** — Smooth slide-up transition
- **Empty states** — Helpful hints when no users exist

### 📝 Profile System
Comprehensive user profile management:

**Data Model:**
- Name + nickname + photo (stored in Documents)
- Relationship type (Mom, Girlfriend, Best Friend, Boss, etc.)
- Birthday + anniversary + custom important dates
- Flower taste profile:
  - Style (minimal, classic, modern, lush, wildflower)
  - Budget range (budget, moderate, premium, luxury)
  - Mood preferences (romantic, celebratory, apologetic, etc.)
  - Favorite flowers list
  - Disliked flowers list
  - ⚠️ **Allergies** (critical for safety!)
  - Personal notes

**Views:**
- `LovedOnesListView` — Expandable categories with search
- `LovedOneDetailView` — Hero avatar with upcoming events
- `LovedOneEditView` — PhotosPicker, date pickers, chip selection

### 🔧 Technical Implementation

**Components:**
```
FSense/Features/LovedOnes/
├── Models/
│   ├── LovedOneProfile.swift        # Core profile model
│   ├── RelationshipModels.swift     # Category + relationship enums
│   └── TasteProfile.swift           # Flower preferences
├── Views/
│   ├── LovedOnesListView.swift      # Main list with categories
│   ├── LovedOneDetailView.swift     # Profile detail screen
│   ├── LovedOneEditView.swift       # Create/edit form
│   └── Components/
│       ├── LovedOneRowView.swift
│       ├── ProfileAvatarView.swift  # 46pt (list), 120pt (detail)
│       ├── UpcomingEventCard.swift
│       ├── ChipSelectionView.swift
│       └── TagInputView.swift
└── Services/
    └── LovedOnesService.swift       # Singleton with persistence
```

**Chat Integration:**
```
FSense/Features/Chat/Views/Components/
├── MentionAutocompleteView.swift    # Glass picker UI
├── MentionInputField.swift          # Standalone component
└── BottomInputBarView.swift         # Integrated @mention
```

**Key Patterns:**
- **Singleton service** — `LovedOnesService.shared` with async UserDefaults
- **Photo storage** — Documents directory, not UserDefaults
- **VStack layout** — Mentions list positioned BEFORE input in code
- **Spring animations** — `.spring(response: 0.3, dampingFraction: 0.8)`
- **Liquid Glass** — `#available(iOS 26, *)` with material fallbacks

---

## 🎯 Features

### 👥 Loved Ones Profiles (NEW!)
- **Profile Management** — CRUD operations with photo support
- **Relationship Hierarchy** — Family, Romance, Friends, Professional
- **Taste Profiles** — Remember preferences for personalized recommendations
- **Important Dates** — Never miss birthdays or anniversaries
- **@Mention System** — Quick access in chat with autocomplete
- **Search & Filter** — Find profiles by name or nickname
- **Glass Autocomplete** — Beautiful iOS 26 Liquid Glass UI

### 📸 Flower Scanner
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
- **@Mention integration** — Reference loved ones in context
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
- **@Mention autocomplete** with Liquid Glass
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
│   ├── Chat/                 # Full-screen chat with @mentions
│   │   ├── Views/
│   │   │   ├── ChatView.swift
│   │   │   └── Components/
│   │   │       ├── MentionAutocompleteView.swift  # 🆕 Glass picker
│   │   │       └── MentionInputField.swift        # 🆕 Standalone
│   │   ├── UsersView.swift                        # 🆕 Profiles list
│   │   └── ChatViewModel.swift
│   ├── LovedOnes/            # 🆕 Profile management
│   │   ├── Models/
│   │   ├── Views/
│   │   └── Components/
│   ├── FlowerCard/           # Recommendation details
│   ├── Scan/                 # 📸 Camera & Liquid Glass UI
│   └── Profile/              # History, archive, settings
├── Services/
│   ├── LovedOnesService      # 🆕 Profile persistence
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
- **@Mention profiles** accessible from toolbar

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

| Metric | v0.14 | v0.15 | Status |
|--------|-------|-------|--------|
| Chat Open Delay | <50ms | <50ms | ✅ Maintained |
| @Mention Trigger | — | <100ms | 🎉 New |
| Profile CRUD | — | Async | 🎉 New |
| Glass Components | 10+ | 12+ | 📈 Expanded |
| Photo Storage | — | Documents | ✅ Optimized |
| Fallback Support | iOS 15-25 | iOS 15-25 | ✅ Complete |

---

## 🛠️ Tech Stack

### Frontend
- **SwiftUI** — Declarative UI framework (iOS 26+)
- **Combine** — Reactive state management
- **Swift Concurrency** — Async/await, actors
- **PhotosUI** — PhotosPicker integration
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
7. **Personalization** — Remember people and their preferences

---

## 🔍 Feature Deep Dive

### @Mention Autocomplete System

**Trigger Detection:**
```swift
// MentionParser extracts query from text
static func extractMentionQuery(from text: String) -> String? {
    guard let atIndex = text.lastIndex(of: "@") else { return nil }
    let afterAt = text[text.index(after: atIndex)...]
    if afterAt.contains(" ") { return nil }
    return String(afterAt)
}
```

**VStack Positioning:**
```swift
VStack(alignment: .leading, spacing: 8) {
    // Mentions list - appears ABOVE input
    if showMentionAutocomplete, let query = mentionQuery {
        mentionsListView(query: query)
            .padding(.leading, 62)  // Align with text field
            .transition(.move(edge: .bottom).combined(with: .opacity))
    }

    // Input bar - always at bottom
    GlassEffectContainer { ... }
}
.animation(.spring(response: 0.3), value: showMentionAutocomplete)
```

**Glass Effect:**
```swift
if #available(iOS 26, *) {
    content
        .glassEffect(
            .regular.tint(.white.opacity(0.2)),
            in: .rect(cornerRadius: 20)
        )
} else {
    content
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
}
```

### Loved Ones Service

**Persistence:**
```swift
@MainActor
class LovedOnesService: ObservableObject {
    static let shared = LovedOnesService()
    @Published private(set) var profiles: [LovedOneProfile] = []

    func addProfile(_ profile: LovedOneProfile) async {
        profiles.append(profile)
        await saveProfiles()
    }

    private func saveProfiles() async {
        // Async UserDefaults save
    }
}
```

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

### v0.16 (Next Sprint)
- [ ] AI recommendations using Loved Ones profiles
- [ ] Mention context in agent pipeline (RIL integration)
- [ ] Birthday reminders with flower suggestions
- [ ] Profile-based search filters

### v0.2.0
- [ ] Scan history with thumbnails
- [ ] Flower detail cards from scan results
- [ ] Share scan results
- [ ] Multi-language support (localization)
- [ ] Flower dictionary with visual search

### v0.3.0
- [ ] Voice input for chat (Whisper API)
- [ ] AR flower visualization (ARKit)
- [ ] Local florist integration (Maps)
- [ ] Offline mode with cached recommendations
- [ ] Home screen widget with upcoming dates

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
*Helping you say it with flowers, one person at a time*

> "The earth laughs in flowers." — Ralph Waldo Emerson
