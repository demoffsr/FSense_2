import Foundation

// MARK: - Chat Session (Persistable)

/// Represents a saved chat session that can be restored
struct ChatSession: Identifiable, Codable, Equatable {
    let id: UUID
    var title: String
    var subtitle: String
    var createdAt: Date
    var updatedAt: Date
    var messages: [ChatMessage]
    var flowerName: String?
    var flowerImageAsset: String?
    
    init(
        id: UUID = UUID(),
        title: String = "New Chat",
        subtitle: String = "",
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        messages: [ChatMessage] = [],
        flowerName: String? = nil,
        flowerImageAsset: String? = nil
    ) {
        self.id = id
        self.title = title
        self.subtitle = subtitle
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messages = messages
        self.flowerName = flowerName
        self.flowerImageAsset = flowerImageAsset
    }
    
    /// Generate title from first user message
    mutating func updateTitleFromMessages() {
        if let firstUserMessage = messages.first(where: { $0.sender == .user }),
           case .text(let text) = firstUserMessage.content {
            // Take first 40 characters or until newline
            let truncated = String(text.prefix(40))
            title = truncated.count < text.count ? truncated + "..." : truncated
        }
    }
    
    /// Generate subtitle from recommendation or context
    mutating func updateSubtitleFromRecommendation() {
        if let recMessage = messages.last(where: {
            if case .recommendation = $0.content { return true }
            return false
        }), case .recommendation(let rec) = recMessage.content {
            subtitle = "For: \(rec.meaning)"
            flowerName = rec.flowerName
            flowerImageAsset = rec.imageAsset
        }
    }
}

// MARK: - Chat State Machine

/// Represents the current state of the chat conversation
enum ChatPhase: Equatable {
    case idle
    case userInput
    case acknowledgement
    case thinking
    case recommendation
    case followUp
}

// MARK: - Thinking Step

/// Individual step in the AI thinking process
struct ThinkingStep: Identifiable, Equatable, Codable {
    let id: UUID
    let text: String
    var status: ThinkingStepStatus
    
    init(id: UUID = UUID(), text: String, status: ThinkingStepStatus = .pending) {
        self.id = id
        self.text = text
        self.status = status
    }
}

enum ThinkingStepStatus: String, Equatable, Codable {
    case pending
    case active
    case completed
}

// MARK: - Chat Message

/// Represents a single message in the chat
struct ChatMessage: Identifiable, Equatable, Codable {
    let id: UUID
    let content: MessageContent
    let sender: MessageSender
    let timestamp: Date
    
    init(
        id: UUID = UUID(),
        content: MessageContent,
        sender: MessageSender,
        timestamp: Date = Date()
    ) {
        self.id = id
        self.content = content
        self.sender = sender
        self.timestamp = timestamp
    }
}

enum MessageSender: String, Equatable, Codable {
    case user
    case ai
}

/// Different types of message content
enum MessageContent: Equatable, Codable {
    case text(String)
    case acknowledgement(String)
    case thinking(ThinkingContent)
    case recommendation(FlowerRecommendation)
    case followUp([String])
    case typing
}

// MARK: - Thinking Content

/// Content for the expandable thinking card
struct ThinkingContent: Equatable, Codable {
    var steps: [ThinkingStep]
    var isExpanded: Bool
    var isComplete: Bool
    
    init(steps: [ThinkingStep] = [], isExpanded: Bool = true, isComplete: Bool = false) {
        self.steps = steps
        self.isExpanded = isExpanded
        self.isComplete = isComplete
    }
}

// MARK: - Flower Recommendation

/// The final AI recommendation
struct FlowerRecommendation: Equatable, Codable {
    let flowerName: String
    let imageAsset: String?
    let imageUrl: String?
    let imageCacheKey: String?
    let meaning: String
    let explanation: String
    let confidence: String

    static let mock = FlowerRecommendation(
        flowerName: "Red Rose",
        imageAsset: "RedRose",
        imageUrl: nil,
        imageCacheKey: nil,
        meaning: "Deep love and passion",
        explanation: "Given the romantic context you described, a red rose perfectly expresses deep emotional connection. Its timeless symbolism of love makes it ideal for your anniversary.",
        confidence: "Perfect match"
    )
}

// MARK: - Chat State

/// Complete state of the chat feature
struct ChatState: Equatable {
    var phase: ChatPhase = .idle
    var messages: [ChatMessage] = []
    var inputText: String = ""
    var isInputEnabled: Bool = true
    var currentThinkingContent: ThinkingContent?
    
    // Expand/collapse state for thinking cards (by message ID)
    var expandedThinkingCards: Set<UUID> = []
}

// MARK: - Chat Action

/// Actions that can be dispatched to the chat
enum ChatAction {
    case onAppear
    case inputTextChanged(String)
    case sendMessage
    case suggestionTapped(String)
    case toggleThinkingCard(UUID)
    case thinkingStepCompleted(Int)
    case allThinkingComplete
    case recommendationReady(FlowerRecommendation)
    case followUpReady([String])
    case reset
}

// MARK: - Mock Data

extension ThinkingStep {
    static let mockSteps: [ThinkingStep] = [
        ThinkingStep(text: "Understanding who the gift is for…"),
        ThinkingStep(text: "Considering emotional tone and intent…"),
        ThinkingStep(text: "Exploring flower meanings…"),
        ThinkingStep(text: "Making sure the choice is culturally appropriate…"),
        ThinkingStep(text: "Refining the final recommendation…")
    ]
}

extension ChatMessage {
    static let welcomeMessage = ChatMessage(
        content: .text("Hi! I'm here to help you find the perfect flower. Tell me about the occasion or the person you're thinking of."),
        sender: .ai
    )
    
    static let mockUserMessage = ChatMessage(
        content: .text("I need flowers for my wife's birthday. We've been married for 5 years."),
        sender: .user
    )
    
    static let mockAcknowledgement = ChatMessage(
        content: .acknowledgement("That's a special milestone. Let me think about something meaningful for you."),
        sender: .ai
    )
}
