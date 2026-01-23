import SwiftUI

/// ViewModel for the AI Chat experience
/// Implements a state machine for the conversation flow
@MainActor
final class ChatViewModel: ObservableObject {

    // MARK: - Published State

    @Published private(set) var state = ChatState()

    /// The last received payload from the API (for FlowerCard navigation)
    @Published private(set) var lastPayload: FlowerCardPayload?

    // MARK: - Session Management

    /// Current session ID for persistence (nil until first message is sent)
    private var sessionId: UUID?

    // MARK: - Private Properties

    private var thinkingTask: Task<Void, Never>?
    private let historyManager = ChatHistoryManager.shared

    // MARK: - Timing Constants

    private let acknowledgementDelay: UInt64 = 300_000_000 // 0.3s
    private let thinkingStepDelay: UInt64 = 400_000_000 // 0.4s per step during API call
    private let minThinkingTime: UInt64 = 2_000_000_000 // 2s minimum thinking display
    
    // MARK: - Initialization
    
    /// Create a new chat (session created lazily when first message is sent)
    init() {
        self.sessionId = nil
        state.messages = [.welcomeMessage]
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
                state.expandedThinkingCards.insert(message.id)
            }
        }
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
                state.expandedThinkingCards.insert(message.id)
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
        !state.inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && state.isInputEnabled
    }
    
    func isThinkingCardExpanded(_ messageId: UUID) -> Bool {
        state.expandedThinkingCards.contains(messageId)
    }
    
    // MARK: - Private Handlers
    
    private func handleOnAppear() {
        // Future: Analytics, restore state, etc.
    }
    
    private func handleSendMessage() {
        guard canSendMessage else { return }
        
        let userText = state.inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        state.inputText = ""
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
        
        // Start the AI response flow
        startAIResponseFlow(for: userText)
    }
    
    // MARK: - Persistence
    
    /// Save current messages to chat history
    private func saveToHistory() {
        ensureSessionExists()
        guard let sessionId = sessionId else { return }
        historyManager.saveMessages(state.messages, to: sessionId)
    }
    
    private func startAIResponseFlow(for userQuery: String) {
        thinkingTask?.cancel()

        thinkingTask = Task {
            // STATE 2: Immediate acknowledgement
            try? await Task.sleep(nanoseconds: acknowledgementDelay)
            guard !Task.isCancelled else { return }

            let acknowledgement = generateAcknowledgement(for: userQuery)
            let ackMessage = ChatMessage(
                content: .acknowledgement(acknowledgement),
                sender: .ai
            )
            state.messages.append(ackMessage)
            state.phase = .acknowledgement

            // Short pause before thinking
            try? await Task.sleep(nanoseconds: 200_000_000)
            guard !Task.isCancelled else { return }

            // STATE 3: Start thinking mode with real API call
            await startThinkingProcessWithAPI(for: userQuery)
        }
    }

    private func startThinkingProcessWithAPI(for userQuery: String) async {
        // Create thinking content with all steps pending
        var thinkingContent = ThinkingContent(
            steps: ThinkingStep.mockSteps,
            isExpanded: true,
            isComplete: false
        )

        let thinkingMessage = ChatMessage(
            content: .thinking(thinkingContent),
            sender: .ai
        )

        state.messages.append(thinkingMessage)
        state.expandedThinkingCards.insert(thinkingMessage.id)
        state.phase = .thinking

        // Start API call concurrently with thinking animation
        let apiTask = Task<FlowerCardPayload?, Never> {
            do {
                return try await APIService.shared.getRecommendation(prompt: userQuery)
            } catch {
                print("API Error: \(error.localizedDescription)")
                return nil
            }
        }

        // Animate through thinking steps while API call is in progress
        let startTime = DispatchTime.now()

        for index in 0..<thinkingContent.steps.count {
            guard !Task.isCancelled else { return }

            // Set current step to active
            thinkingContent.steps[index].status = .active
            updateThinkingMessage(thinkingMessage.id, with: thinkingContent)

            // Wait for step duration
            try? await Task.sleep(nanoseconds: thinkingStepDelay)
            guard !Task.isCancelled else { return }

            // Mark step as completed
            thinkingContent.steps[index].status = .completed
            updateThinkingMessage(thinkingMessage.id, with: thinkingContent)
        }

        // Wait for API result
        let payload = await apiTask.value

        // Ensure minimum thinking time has elapsed
        let elapsed = DispatchTime.now().uptimeNanoseconds - startTime.uptimeNanoseconds
        if elapsed < minThinkingTime {
            try? await Task.sleep(nanoseconds: minThinkingTime - elapsed)
        }

        guard !Task.isCancelled else { return }

        // Mark thinking as complete
        thinkingContent.isComplete = true
        thinkingContent.isExpanded = false
        updateThinkingMessage(thinkingMessage.id, with: thinkingContent)
        state.expandedThinkingCards.remove(thinkingMessage.id)

        // Short pause before recommendation
        try? await Task.sleep(nanoseconds: 300_000_000)
        guard !Task.isCancelled else { return }

        // STATE 4: Show recommendation
        if let payload = payload {
            lastPayload = payload
            await showRecommendation(from: payload)
        } else {
            await showError()
        }
    }
    
    private func updateThinkingMessage(_ messageId: UUID, with content: ThinkingContent) {
        if let index = state.messages.firstIndex(where: { $0.id == messageId }) {
            state.messages[index] = ChatMessage(
                id: messageId,
                content: .thinking(content),
                sender: .ai,
                timestamp: state.messages[index].timestamp
            )
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
        // Toggle the expanded state
        if state.expandedThinkingCards.contains(messageId) {
            state.expandedThinkingCards.remove(messageId)
        } else {
            state.expandedThinkingCards.insert(messageId)
        }
        
        // Force UI update by triggering objectWillChange
        objectWillChange.send()
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

        // Clear session ID - new session will be created lazily when user sends a message
        sessionId = nil

        // Clear last payload
        lastPayload = nil

        state = ChatState()
        state.messages = [.welcomeMessage]
    }
    
    // MARK: - Acknowledgement Generator (Mock)
    
    private func generateAcknowledgement(for query: String) -> String {
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
