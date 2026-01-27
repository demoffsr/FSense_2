import SwiftUI
import Combine

/// ViewModel for the AI Chat experience
/// Implements a state machine for the conversation flow
@MainActor
final class ChatViewModel: ObservableObject {

    // MARK: - Granular Published State (for isolated UI updates)
    // Split from monolithic ChatState to prevent TextField input from triggering message list re-render

    /// Messages array - only triggers update when messages change
    @Published private(set) var messages: [ChatMessage] = []

    /// Input text - isolated to prevent message list re-render on typing
    @Published var inputText: String = ""

    /// Input enabled state
    @Published private(set) var isInputEnabled: Bool = true

    /// Current conversation phase
    @Published private(set) var phase: ChatPhase = .idle

    /// Attached image for sending
    @Published private(set) var attachedImage: UIImage?

    /// The last received payload from the API (for FlowerCard navigation)
    @Published private(set) var lastPayload: FlowerCardPayload?

    /// Pipeline progress steps (forwarded from eventService to avoid multiple observers)
    @Published private(set) var pipelineSteps: [ProgressStep] = []

    /// Expanded thinking cards - separate @Published for efficient UI updates
    @Published private(set) var expandedThinkingCards: Set<UUID> = []

    // MARK: - Cached Precomputed Data

    /// Cached message row data - invalidated when messages change
    private var cachedMessageRowData: [MessageRowData] = []
    private var cachedMessagesHash: Int = 0

    struct MessageRowData: Equatable {
        let thinkingId: UUID
        let hideCompletedThinking: Bool
    }

    /// Get precomputed data with caching
    var precomputedMessageData: [MessageRowData] {
        let currentHash = messages.hashValue
        if currentHash != cachedMessagesHash {
            cachedMessagesHash = currentHash
            cachedMessageRowData = computeMessageRowData()
        }
        return cachedMessageRowData
    }

    private func computeMessageRowData() -> [MessageRowData] {
        var result: [MessageRowData] = []
        result.reserveCapacity(messages.count)

        for (index, message) in messages.enumerated() {
            var thinkingId = message.id
            if case .recommendation = message.content {
                for i in stride(from: index - 1, through: 0, by: -1) {
                    if case .thinking = messages[i].content {
                        thinkingId = messages[i].id
                        break
                    }
                    if messages[i].sender == .user { break }
                }
            }

            var hideCompletedThinking = false
            if case .thinking(let content) = message.content, content.isComplete {
                for i in (index + 1)..<messages.count {
                    if case .recommendation = messages[i].content {
                        hideCompletedThinking = true
                        break
                    }
                    if messages[i].sender == .user { break }
                }
            }

            result.append(MessageRowData(thinkingId: thinkingId, hideCompletedThinking: hideCompletedThinking))
        }

        return result
    }

    // MARK: - Session Management

    /// Current session ID for persistence (nil until first message is sent)
    private var sessionId: UUID?

    // MARK: - Private Properties

    private var thinkingTask: Task<Void, Never>?
    private let historyManager = ChatHistoryManager.shared
    private let eventService = PipelineEventService.shared
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Timing Constants

    private let acknowledgementDelay: UInt64 = 100_000_000 // 0.1s (minimal UX feedback)

    // MARK: - Initialization

    /// Create a new chat (session created lazily when first message is sent)
    init() {
        self.sessionId = nil
        messages = [.welcomeMessage]
        setupEventServiceBinding()
    }

    /// Restore an existing chat session
    init(session: ChatSession) {
        self.sessionId = session.id

        // Restore messages from session
        if session.messages.isEmpty {
            messages = [.welcomeMessage]
        } else {
            messages = session.messages
        }

        // Restore expanded state for any thinking cards
        for message in messages {
            if case .thinking(let content) = message.content, !content.isComplete {
                expandedThinkingCards.insert(message.id)
            }
        }

        setupEventServiceBinding()
    }

    /// Subscribe to eventService.steps to avoid multiple @ObservedObject observers
    private func setupEventServiceBinding() {
        eventService.$steps
            .removeDuplicates() // Skip redundant updates when steps haven't actually changed
            .receive(on: DispatchQueue.main)
            .sink { [weak self] steps in
                self?.pipelineSteps = steps
            }
            .store(in: &cancellables)
    }

    // MARK: - Session Helpers

    /// Ensures a session exists, creating one if needed
    private func ensureSessionExists() {
        if sessionId == nil {
            let newSession = historyManager.createNewSession()
            sessionId = newSession.id
        }
    }

    /// Load an existing session into the view model
    func loadSession(_ session: ChatSession) {
        // Cancel any ongoing tasks
        thinkingTask?.cancel()

        // Set session ID
        sessionId = session.id

        // Reset state
        resetState()

        // Restore messages from session
        if session.messages.isEmpty {
            messages = [.welcomeMessage]
        } else {
            messages = session.messages
        }

        // Restore expanded state for any thinking cards
        for message in messages {
            if case .thinking(let content) = message.content, !content.isComplete {
                expandedThinkingCards.insert(message.id)
            }
        }
    }

    // MARK: - Computed Properties

    /// Messages in their natural chronological order
    var orderedMessages: [ChatMessage] {
        messages
    }

    var canSendMessage: Bool {
        let hasText = !inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let hasImage = attachedImage != nil
        return (hasText || hasImage) && isInputEnabled
    }

    /// Check if reset would have any effect (for optimization)
    var needsReset: Bool {
        sessionId != nil || messages.count > 1 || phase != .idle
    }

    func isThinkingCardExpanded(_ messageId: UUID) -> Bool {
        expandedThinkingCards.contains(messageId)
    }

    // MARK: - Action Handler

    func send(_ action: ChatAction) {
        switch action {
        case .onAppear:
            break // Future: Analytics, restore state, etc.

        case .inputTextChanged(let text):
            inputText = text

        case .sendMessage:
            handleSendMessage()

        case .suggestionTapped(let suggestion):
            inputText = suggestion
            handleSendMessage()

        case .toggleThinkingCard(let messageId):
            handleToggleThinkingCard(messageId)

        case .thinkingStepCompleted:
            break // Handled internally in the flow

        case .allThinkingComplete:
            phase = .recommendation

        case .recommendationReady(let recommendation):
            handleRecommendationReady(recommendation)

        case .followUpReady(let suggestions):
            handleFollowUpReady(suggestions)

        case .reset:
            handleReset()

        case .attachImage(let image):
            attachedImage = compressImageForAttachment(image)

        case .removeAttachment:
            attachedImage = nil
        }
    }

    // MARK: - Private Handlers

    private func handleSendMessage() {
        guard canSendMessage else { return }

        let userText = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        let currentAttachedImage = attachedImage  // Capture before clearing

        inputText = ""
        attachedImage = nil
        isInputEnabled = false

        // STATE 1: User message appears
        let messageContent: MessageContent
        if let image = currentAttachedImage, let imageData = image.jpegData(compressionQuality: 0.7) {
            messageContent = .textWithImage(userText.isEmpty ? "Attached Image review" : userText, imageData: imageData)
        } else {
            messageContent = .text(userText)
        }

        let userMessage = ChatMessage(content: messageContent, sender: .user)
        messages.append(userMessage)
        phase = .userInput

        // Save to history
        saveToHistory()

        // Start the AI response flow
        startAIResponseFlow(for: userText, image: currentAttachedImage)
    }

    // MARK: - Persistence

    private func saveToHistory() {
        ensureSessionExists()
        guard let sessionId = sessionId else { return }
        historyManager.saveMessages(messages, to: sessionId)
    }

    private func startAIResponseFlow(for userQuery: String, image: UIImage? = nil) {
        if let existingTask = thinkingTask {
            existingTask.cancel()
            eventService.stop()
        }

        thinkingTask = Task {
            await withTaskCancellationHandler {
                try? await Task.sleep(nanoseconds: acknowledgementDelay)
                guard !Task.isCancelled else { return }

                let acknowledgement = generateAcknowledgement(for: userQuery, hasImage: image != nil)
                let ackMessage = ChatMessage(content: .acknowledgement(acknowledgement), sender: .ai)
                messages.append(ackMessage)
                phase = .acknowledgement

                await startThinkingProcessWithAPI(for: userQuery, image: image)
            } onCancel: {
                Task { @MainActor [weak self] in
                    self?.cleanupPartialState()
                }
            }
        }
    }

    private func cleanupPartialState() {
        messages.removeAll { message in
            switch message.content {
            case .thinking(let content) where !content.isComplete:
                return true
            case .acknowledgement:
                return true
            default:
                return false
            }
        }

        isInputEnabled = true
        phase = .idle
        eventService.stop()
    }

    private func startThinkingProcessWithAPI(for userQuery: String, image: UIImage? = nil) async {
        let thinkingMessage = ChatMessage(
            content: .thinking(ThinkingContent(steps: [], isExpanded: true, isComplete: false)),
            sender: .ai
        )

        messages.append(thinkingMessage)
        expandedThinkingCards.insert(thinkingMessage.id)
        phase = .thinking

        eventService.start()

        var payload: FlowerCardPayload?
        do {
            payload = try await APIService.shared.getRecommendation(prompt: userQuery, image: image)
        } catch {
            print("[ChatViewModel] API Error: \(error.localizedDescription)")
        }

        guard !Task.isCancelled else { return }

        eventService.stop()

        messages.removeAll { $0.id == thinkingMessage.id }
        expandedThinkingCards.remove(thinkingMessage.id)

        if let payload = payload {
            lastPayload = payload
            await showRecommendation(from: payload)
        } else {
            await showError()
        }
    }

    private func showRecommendation(from payload: FlowerCardPayload) async {
        let recommendation = payload.toFlowerRecommendation()
        let recMessage = ChatMessage(content: .recommendation(recommendation), sender: .ai)
        messages.append(recMessage)
        phase = .recommendation
        saveToHistory()
        isInputEnabled = true
    }

    private func showError() async {
        let errorMessage = ChatMessage(
            content: .text("I'm sorry, I couldn't process your request right now. Please try again."),
            sender: .ai
        )
        messages.append(errorMessage)
        phase = .idle
        saveToHistory()
        isInputEnabled = true
    }

    private func handleToggleThinkingCard(_ messageId: UUID) {
        if expandedThinkingCards.contains(messageId) {
            expandedThinkingCards.remove(messageId)
        } else {
            expandedThinkingCards.insert(messageId)
        }
    }

    private func handleRecommendationReady(_ recommendation: FlowerRecommendation) {
        let message = ChatMessage(content: .recommendation(recommendation), sender: .ai)
        messages.append(message)
        phase = .recommendation
    }

    private func handleFollowUpReady(_ suggestions: [String]) {
        let message = ChatMessage(content: .followUp(suggestions), sender: .ai)
        messages.append(message)
        phase = .followUp
        isInputEnabled = true
    }

    private func handleReset() {
        // Early exit if already in reset state
        guard sessionId != nil || messages.count > 1 || phase != .idle else { return }

        thinkingTask?.cancel()
        eventService.stop()
        sessionId = nil
        lastPayload = nil
        expandedThinkingCards.removeAll()
        inputText = ""
        isInputEnabled = true
        phase = .idle
        attachedImage = nil
        messages = [.welcomeMessage]
    }

    private func resetState() {
        messages = []
        inputText = ""
        isInputEnabled = true
        phase = .idle
        attachedImage = nil
    }

    // MARK: - Acknowledgement Generator

    private func generateAcknowledgement(for query: String, hasImage: Bool = false) -> String {
        if hasImage {
            if query.isEmpty {
                return "I see you've shared a beautiful bouquet! Let me identify the flowers for you."
            } else {
                return "Thanks for sharing that image! Let me analyze the flowers and find more information."
            }
        }

        let acknowledgements = [
            "That's a beautiful thought. Let me find something special.",
            "I understand. Let me think about the perfect choice for you.",
            "What a meaningful gesture. Give me a moment to consider this carefully.",
            "That's lovely. Let me explore some options that would fit perfectly.",
            "I can feel the care in your words. Let me find something meaningful."
        ]

        if query.lowercased().contains("birthday") {
            return "A birthday gift! Let me think about something that captures the joy of this celebration."
        } else if query.lowercased().contains("anniversary") {
            return "An anniversary is so special. Let me find something that honors your journey together."
        } else if query.lowercased().contains("sorry") || query.lowercased().contains("apolog") {
            return "I understand this is important. Let me think about flowers that speak from the heart."
        } else if query.lowercased().contains("love") || query.lowercased().contains("romantic") {
            return "Romance deserves something truly special. Let me consider the perfect expression."
        }

        return acknowledgements.randomElement() ?? acknowledgements[0]
    }
}
