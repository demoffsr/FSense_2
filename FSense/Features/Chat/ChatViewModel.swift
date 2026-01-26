import SwiftUI
import Combine

/// ViewModel for the AI Chat experience
/// Implements a state machine for the conversation flow
@MainActor
final class ChatViewModel: ObservableObject {

    // MARK: - Published State

    @Published private(set) var state = ChatState()

    /// The last received payload from the API (for FlowerCard navigation)
    @Published private(set) var lastPayload: FlowerCardPayload?

    /// Pipeline progress steps (forwarded from eventService to avoid multiple observers)
    @Published private(set) var pipelineSteps: [ProgressStep] = []

    /// Expanded thinking cards - separate @Published for efficient UI updates
    @Published private(set) var expandedThinkingCards: Set<UUID> = []

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
        state.messages = [.welcomeMessage]
        setupEventServiceBinding()
    }
    
    /// Restore an existing chat session
    init(session: ChatSession) {
        self.sessionId = session.id

        // Restore messages from session
        if session.messages.isEmpty {
            state.messages = [.welcomeMessage]
        } else {
            state.messages = session.messages
        }

        // Restore expanded state for any thinking cards
        for message in state.messages {
            if case .thinking(let content) = message.content, !content.isComplete {
                expandedThinkingCards.insert(message.id)
            }
        }

        setupEventServiceBinding()
    }

    /// Subscribe to eventService.steps to avoid multiple @ObservedObject observers
    private func setupEventServiceBinding() {
        eventService.$steps
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
        state = ChatState()
        
        // Restore messages from session
        if session.messages.isEmpty {
            state.messages = [.welcomeMessage]
        } else {
            state.messages = session.messages
        }
        
        // Restore expanded state for any thinking cards
        for message in state.messages {
            if case .thinking(let content) = message.content, !content.isComplete {
                expandedThinkingCards.insert(message.id)
            }
        }
    }
    
    // MARK: - Action Handler
    
    func send(_ action: ChatAction) {
        switch action {
        case .onAppear:
            handleOnAppear()
            
        case .inputTextChanged(let text):
            state.inputText = text
            
        case .sendMessage:
            handleSendMessage()
            
        case .suggestionTapped(let suggestion):
            state.inputText = suggestion
            handleSendMessage()
            
        case .toggleThinkingCard(let messageId):
            handleToggleThinkingCard(messageId)
            
        case .thinkingStepCompleted(let index):
            handleThinkingStepCompleted(index)
            
        case .allThinkingComplete:
            handleAllThinkingComplete()
            
        case .recommendationReady(let recommendation):
            handleRecommendationReady(recommendation)
            
        case .followUpReady(let suggestions):
            handleFollowUpReady(suggestions)
            
        case .reset:
            handleReset()

        case .attachImage(let image):
            // Compress image to reduce memory usage (~200KB instead of 5-20MB)
            state.attachedImage = compressImageForAttachment(image)

        case .removeAttachment:
            state.attachedImage = nil
        }
    }
    
    // MARK: - Computed Properties
    
    var messages: [ChatMessage] {
        state.messages
    }
    
    /// Messages in their natural chronological order
    /// Each thinking card belongs to its specific AI response cycle
    var orderedMessages: [ChatMessage] {
        state.messages
    }
    
    var inputText: String {
        state.inputText
    }
    
    var isInputEnabled: Bool {
        state.isInputEnabled
    }
    
    var currentPhase: ChatPhase {
        state.phase
    }
    
    var canSendMessage: Bool {
        // Allow sending if there's text OR an attached image (or both)
        let hasText = !state.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        let hasImage = state.attachedImage != nil
        return (hasText || hasImage) && state.isInputEnabled
    }

    var attachedImage: UIImage? {
        state.attachedImage
    }
    
    func isThinkingCardExpanded(_ messageId: UUID) -> Bool {
        expandedThinkingCards.contains(messageId)
    }
    
    // MARK: - Private Handlers
    
    private func handleOnAppear() {
        // Future: Analytics, restore state, etc.
    }
    
    private func handleSendMessage() {
        guard canSendMessage else { return }

        let userText = state.inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        let attachedImage = state.attachedImage  // Capture before clearing

        state.inputText = ""
        state.attachedImage = nil // Clear attachment after sending
        state.isInputEnabled = false

        // STATE 1: User message appears
        let userMessage = ChatMessage(
            content: .text(userText),
            sender: .user
        )
        state.messages.append(userMessage)
        state.phase = .userInput

        // Save to history
        saveToHistory()

        // Start the AI response flow (with optional image)
        startAIResponseFlow(for: userText, image: attachedImage)
    }
    
    // MARK: - Persistence
    
    /// Save current messages to chat history
    private func saveToHistory() {
        ensureSessionExists()
        guard let sessionId = sessionId else { return }
        historyManager.saveMessages(state.messages, to: sessionId)
    }
    
    private func startAIResponseFlow(for userQuery: String, image: UIImage? = nil) {
        thinkingTask?.cancel()

        thinkingTask = Task {
            // STATE 2: Immediate acknowledgement
            try? await Task.sleep(nanoseconds: acknowledgementDelay)
            guard !Task.isCancelled else { return }

            let acknowledgement = generateAcknowledgement(for: userQuery, hasImage: image != nil)
            let ackMessage = ChatMessage(
                content: .acknowledgement(acknowledgement),
                sender: .ai
            )
            state.messages.append(ackMessage)
            state.phase = .acknowledgement

            // STATE 3: Start thinking mode with real API call (include image if provided)
            await startThinkingProcessWithAPI(for: userQuery, image: image)
        }
    }

    private func startThinkingProcessWithAPI(for userQuery: String, image: UIImage? = nil) async {
        // Add thinking card placeholder to messages
        let thinkingMessage = ChatMessage(
            content: .thinking(ThinkingContent(steps: [], isExpanded: true, isComplete: false)),
            sender: .ai
        )

        state.messages.append(thinkingMessage)
        expandedThinkingCards.insert(thinkingMessage.id)
        state.phase = .thinking

        // Start SSE connection BEFORE API call
        eventService.start()

        // Make API call (SSE connects in parallel)
        // Pass image if provided for vision analysis
        var payload: FlowerCardPayload?
        do {
            payload = try await APIService.shared.getRecommendation(prompt: userQuery, image: image)
        } catch {
            print("[ChatViewModel] API Error: \(error.localizedDescription)")
        }

        guard !Task.isCancelled else { return }

        // Stop SSE listening
        eventService.stop()

        // Remove standalone thinking card (recommendation has its own)
        state.messages.removeAll { $0.id == thinkingMessage.id }
        expandedThinkingCards.remove(thinkingMessage.id)

        // STATE 4: Show recommendation
        if let payload = payload {
            lastPayload = payload
            await showRecommendation(from: payload)
        } else {
            await showError()
        }
    }
    
    private func showRecommendation(from payload: FlowerCardPayload) async {
        let recommendation = payload.toFlowerRecommendation()
        let recMessage = ChatMessage(
            content: .recommendation(recommendation),
            sender: .ai
        )
        state.messages.append(recMessage)
        state.phase = .recommendation

        // Save to history (with recommendation)
        saveToHistory()

        // Re-enable input - wait for user, no follow-up suggestions
        state.isInputEnabled = true
    }

    private func showError() async {
        let errorMessage = ChatMessage(
            content: .text("I'm sorry, I couldn't process your request right now. Please try again."),
            sender: .ai
        )
        state.messages.append(errorMessage)
        state.phase = .idle

        // Save to history
        saveToHistory()

        // Re-enable input
        state.isInputEnabled = true
    }
    
    private func handleToggleThinkingCard(_ messageId: UUID) {
        // Toggle the expanded state - @Published handles UI updates automatically
        if expandedThinkingCards.contains(messageId) {
            expandedThinkingCards.remove(messageId)
        } else {
            expandedThinkingCards.insert(messageId)
        }
    }
    
    private func handleThinkingStepCompleted(_ index: Int) {
        // Handled internally in the flow
    }
    
    private func handleAllThinkingComplete() {
        state.phase = .recommendation
    }
    
    private func handleRecommendationReady(_ recommendation: FlowerRecommendation) {
        let message = ChatMessage(
            content: .recommendation(recommendation),
            sender: .ai
        )
        state.messages.append(message)
        state.phase = .recommendation
    }
    
    private func handleFollowUpReady(_ suggestions: [String]) {
        let message = ChatMessage(
            content: .followUp(suggestions),
            sender: .ai
        )
        state.messages.append(message)
        state.phase = .followUp
        state.isInputEnabled = true
    }
    
    private func handleReset() {
        thinkingTask?.cancel()
        eventService.stop()

        // Clear session ID - new session will be created lazily when user sends a message
        sessionId = nil

        // Clear last payload
        lastPayload = nil

        // Clear expanded thinking cards
        expandedThinkingCards.removeAll()

        state = ChatState()
        state.messages = [.welcomeMessage]
    }
    
    // MARK: - Acknowledgement Generator (Mock)

    private func generateAcknowledgement(for query: String, hasImage: Bool = false) -> String {
        // Handle image uploads
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

        // Simple mock logic - in production, this would be context-aware
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
