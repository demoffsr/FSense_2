import Foundation
import UIKit

// MARK: - Image Storage Manager

/// Manages file-based storage for chat images to reduce memory usage
/// Images are stored in the app's caches directory and referenced by path
final class ImageStorageManager: @unchecked Sendable {
    static let shared = ImageStorageManager()

    private let fileManager = FileManager.default
    private let cacheDirectory: URL

    private init() {
        let caches = fileManager.urls(for: .cachesDirectory, in: .userDomainMask).first!
        cacheDirectory = caches.appendingPathComponent("ChatImages", isDirectory: true)

        // Create directory if needed
        try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
    }

    /// Save image to disk and return the relative path
    func saveImage(_ image: UIImage, messageId: UUID) -> String? {
        let compressed = compressImageForAttachment(image)
        guard let data = compressed.jpegData(compressionQuality: 0.7) else { return nil }

        let filename = "\(messageId.uuidString).jpg"
        let url = cacheDirectory.appendingPathComponent(filename)

        do {
            try data.write(to: url)
            return filename
        } catch {
            print("[ImageStorage] Failed to save image: \(error)")
            return nil
        }
    }

    /// Load image from disk by path
    func loadImage(path: String) -> UIImage? {
        let url = cacheDirectory.appendingPathComponent(path)
        guard let data = try? Data(contentsOf: url) else { return nil }
        return UIImage(data: data)
    }

    /// Delete image from disk
    func deleteImage(path: String) {
        let url = cacheDirectory.appendingPathComponent(path)
        try? fileManager.removeItem(at: url)
    }

    /// Clean up orphaned images (optional maintenance)
    func cleanupOrphanedImages(validPaths: Set<String>) {
        guard let contents = try? fileManager.contentsOfDirectory(at: cacheDirectory, includingPropertiesForKeys: nil) else { return }

        for url in contents {
            let filename = url.lastPathComponent
            if !validPaths.contains(filename) {
                try? fileManager.removeItem(at: url)
            }
        }
    }
}

// MARK: - Image Utilities

/// Convert UIImage to base64 string for API transmission
/// - Parameters:
///   - image: The UIImage to convert
///   - maxSize: Maximum dimensions (default 1024x1024)
///   - compressionQuality: JPEG quality 0.0-1.0 (default 0.6 for balance)
/// - Returns: Base64 encoded string or nil if conversion fails
func imageToBase64(_ image: UIImage, maxSize: CGSize = CGSize(width: 1024, height: 1024), compressionQuality: CGFloat = 0.6) -> String? {
    // First compress/resize the image
    let compressed = compressImageForAttachment(image, maxSize: maxSize, compressionQuality: compressionQuality)

    // Convert to JPEG data and then base64
    guard let data = compressed.jpegData(compressionQuality: compressionQuality) else {
        return nil
    }

    return data.base64EncodedString()
}

/// Compress image for chat attachment to reduce memory usage
func compressImageForAttachment(_ image: UIImage, maxSize: CGSize = CGSize(width: 1024, height: 1024), compressionQuality: CGFloat = 0.7) -> UIImage {
    let size = image.size

    // Calculate scale to fit within maxSize while maintaining aspect ratio
    let widthRatio = maxSize.width / size.width
    let heightRatio = maxSize.height / size.height
    let scale = min(widthRatio, heightRatio, 1.0) // Don't upscale

    // If image is already small enough, just compress quality
    guard scale < 1.0 else {
        // Still compress to JPEG to reduce memory
        if let data = image.jpegData(compressionQuality: compressionQuality),
           let compressed = UIImage(data: data) {
            return compressed
        }
        return image
    }

    let newSize = CGSize(width: size.width * scale, height: size.height * scale)

    // Resize image
    let renderer = UIGraphicsImageRenderer(size: newSize)
    let resized = renderer.image { _ in
        image.draw(in: CGRect(origin: .zero, size: newSize))
    }

    // Compress to JPEG
    if let data = resized.jpegData(compressionQuality: compressionQuality),
       let compressed = UIImage(data: data) {
        return compressed
    }

    return resized
}

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
    var flowerImageUrl: String?

    init(
        id: UUID = UUID(),
        title: String = "New Chat",
        subtitle: String = "",
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        messages: [ChatMessage] = [],
        flowerName: String? = nil,
        flowerImageAsset: String? = nil,
        flowerImageUrl: String? = nil
    ) {
        self.id = id
        self.title = title
        self.subtitle = subtitle
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.messages = messages
        self.flowerName = flowerName
        self.flowerImageAsset = flowerImageAsset
        self.flowerImageUrl = flowerImageUrl
    }
    
    /// Generate title from first user message
    mutating func updateTitleFromMessages() {
        if let firstUserMessage = messages.first(where: { $0.sender == .user }) {
            let text: String
            switch firstUserMessage.content {
            case .text(let messageText):
                text = messageText
            case .textWithImage(let messageText, _):
                text = messageText
            default:
                return
            }
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

            // Set flower image ONLY for the first recommendation (don't overwrite)
            if flowerImageAsset == nil && flowerImageUrl == nil {
                flowerName = rec.flowerName
                flowerImageAsset = rec.imageAsset
                flowerImageUrl = rec.imageUrl
            }
        }
    }
}

// MARK: - Chat Mode

/// Chat interaction mode - determines how messages are processed
enum ChatMode: String, Codable, Equatable {
    case ask   // Simple GPT chat - no flower pipeline
    case find  // Full flower recommendation pipeline (default)

    var displayName: String {
        switch self {
        case .ask: return "Ask"
        case .find: return "Find"
        }
    }

    var subtitle: String {
        switch self {
        case .ask: return "Speak mode"
        case .find: return "Search mode"
        }
    }

    var iconName: String {
        switch self {
        case .ask: return "bubble.left.and.bubble.right"
        case .find: return "globe"
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
struct ChatMessage: Identifiable, Equatable, Hashable, Codable {
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

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
        hasher.combine(timestamp)
    }
}

enum MessageSender: String, Equatable, Codable {
    case user
    case ai
}

/// Different types of message content
enum MessageContent: Equatable, Codable {
    case text(String)
    case textWithImage(String, imageData: Data) // Text message with attached image
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
    var attachedImage: UIImage?

    // Expand/collapse state for thinking cards (by message ID)
    var expandedThinkingCards: Set<UUID> = []

    // Custom Equatable implementation to handle UIImage
    static func == (lhs: ChatState, rhs: ChatState) -> Bool {
        lhs.phase == rhs.phase &&
        lhs.messages == rhs.messages &&
        lhs.inputText == rhs.inputText &&
        lhs.isInputEnabled == rhs.isInputEnabled &&
        lhs.currentThinkingContent == rhs.currentThinkingContent &&
        lhs.attachedImage === rhs.attachedImage &&
        lhs.expandedThinkingCards == rhs.expandedThinkingCards
    }
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
    case attachImage(UIImage)
    case removeAttachment
    // Mode actions
    case setMode(ChatMode)
    case toggleMode(ChatMode)  // Toggles mode on/off (nil = general mode)
    case showModeSheet
    case hideModeSheet
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
