import SwiftUI
import Combine

/// ViewModel for the AI Chat experience
/// Implements a state machine for the conversation flow
@MainActor
final class ChatViewModel: ObservableObject {

    // MARK: - Granular Published State (for isolated UI updates)
    // Split from monolithic ChatState to prevent TextField input from triggering message list re-render

    /// Messages array - only triggers update when messages change
    /// Cache is automatically invalidated via didSet
    @Published private(set) var messages: [ChatMessage] = [] {
        didSet {
            // Invalidate cache when messages actually change
            cachedMessageRowData = computeMessageRowData()
        }
    }

    /// Input text - isolated to prevent message list re-render on typing
    @Published var inputText: String = "" {
        didSet {
            // Update state manager on text changes for draft persistence
            stateManager.updateDraft(inputText)
        }
    }

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

    /// Message IDs that should show typewriter animation (new AI messages only)
    @Published private(set) var animatingMessageIds: Set<UUID> = []

    /// Current chat mode - determines how messages are processed (nil = general mode)
    @Published private(set) var chatMode: ChatMode?

    /// Controls the mode selection bottom sheet
    @Published var showModeSheet: Bool = false

    // MARK: - Cached Precomputed Data

    /// Cached message row data - automatically invalidated via didSet on messages
    private var cachedMessageRowData: [MessageRowData] = []

    struct MessageRowData: Equatable {
        let thinkingId: UUID
        let hideCompletedThinking: Bool
    }

    /// Get precomputed data (cached, updated automatically when messages change)
    var precomputedMessageData: [MessageRowData] {
        cachedMessageRowData
    }

    private func computeMessageRowData() -> [MessageRowData] {
        var result: [MessageRowData] = []
        result.reserveCapacity(messages.count)

        // O(n) approach: Build index maps in single passes instead of nested O(n²) loops

        // Pass 1: Build thinking card map (recommendation index -> thinking card id)
        // Track the last thinking index seen, reset on user message
        var thinkingCardMap: [Int: UUID] = [:]
        var lastThinkingIndex: Int? = nil

        for (index, message) in messages.enumerated() {
            if case .thinking = message.content {
                lastThinkingIndex = index
            } else if case .recommendation = message.content {
                if let thinkingIdx = lastThinkingIndex {
                    thinkingCardMap[index] = messages[thinkingIdx].id
                }
                lastThinkingIndex = nil
            } else if message.sender == .user {
                lastThinkingIndex = nil
            }
        }

        // Pass 2: Build set of thinking indices that have recommendations following
        var thinkingHasRecommendation: Set<Int> = []
        var lastThinkingIdx: Int? = nil

        for (index, message) in messages.enumerated() {
            if case .thinking = message.content {
                lastThinkingIdx = index
            } else if case .recommendation = message.content {
                if let idx = lastThinkingIdx {
                    thinkingHasRecommendation.insert(idx)
                }
                lastThinkingIdx = nil
            } else if message.sender == .user {
                lastThinkingIdx = nil
            }
        }

        // Pass 3: Build result using O(1) lookups
        for (index, message) in messages.enumerated() {
            let thinkingId = thinkingCardMap[index] ?? message.id

            var hideCompletedThinking = false
            if case .thinking(let content) = message.content, content.isComplete {
                hideCompletedThinking = thinkingHasRecommendation.contains(index)
            }

            result.append(MessageRowData(thinkingId: thinkingId, hideCompletedThinking: hideCompletedThinking))
        }

        return result
    }

    // MARK: - Session Management

    /// Current session ID for persistence (nil until first message is sent)
    private var sessionId: UUID?

    /// Read-only accessor for current session ID
    var currentSessionId: UUID? { sessionId }

    /// Reference to state manager for active session tracking
    private let stateManager = ActiveChatStateManager.shared

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

    /// Check if a message should show typewriter animation
    func shouldAnimateMessage(_ messageId: UUID) -> Bool {
        animatingMessageIds.contains(messageId)
    }

    /// Mark animation as complete for a message
    func markAnimationComplete(_ messageId: UUID) {
        animatingMessageIds.remove(messageId)
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

        case .setMode(let mode):
            chatMode = mode
            showModeSheet = false

        case .toggleMode(let mode):
            // If same mode selected, deselect it (go to general mode)
            if chatMode == mode {
                chatMode = nil
            } else {
                chatMode = mode
            }
            showModeSheet = false

        case .showModeSheet:
            showModeSheet = true

        case .hideModeSheet:
            showModeSheet = false
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

        // Notify state manager about active session
        if let sessionId = sessionId {
            stateManager.setActiveSession(sessionId)
        }

        // Start the AI response flow
        startAIResponseFlow(for: userText, image: currentAttachedImage)
    }

    // MARK: - Persistence

    private func saveToHistory() {
        ensureSessionExists()
        guard let sessionId = sessionId else { return }
        historyManager.saveMessages(messages, to: sessionId)

        // Notify state manager about active session
        stateManager.setActiveSession(sessionId)
    }

    private func startAIResponseFlow(for userQuery: String, image: UIImage? = nil) {
        if let existingTask = thinkingTask {
            existingTask.cancel()
            eventService.stop()
        }

        let currentMode = chatMode

        thinkingTask = Task {
            await withTaskCancellationHandler {
                let context = buildChatContextV2()

                // Branch based on chat mode
                switch currentMode {
                case .ask:
                    // Ask mode: simple GPT chat without flower pipeline
                    await handleAskModeQuery(userQuery, image: image, context: context)

                case .find:
                    // Find mode: skip intent classification, go straight to flower pipeline
                    await handleFlowerRequest(userQuery, image: image, context: context)

                case nil:
                    // General mode: use existing intent classification + pipeline logic
                    let classification = try? await APIService.shared.classifyIntent(
                        prompt: userQuery,
                        context: context
                    )

                    guard !Task.isCancelled else { return }

                    let intent = classification?.intent ?? "flower_request"

                    // Route based on intent
                    if intent == "off_topic" || intent == "clarification" {
                        // Non-flower query: get text response directly (no acknowledgement)
                        await handleNonFlowerQuery(userQuery, image: image, context: context)
                    } else {
                        // Flower request: show acknowledgement + pipeline
                        await handleFlowerRequest(userQuery, image: image, context: context)
                    }
                }
            } onCancel: {
                Task { @MainActor [weak self] in
                    self?.cleanupPartialState()
                }
            }
        }
    }

    /// Handle Ask mode queries - simple GPT chat without flower pipeline
    private func handleAskModeQuery(_ query: String, image: UIImage?, context: ChatContextV2) async {
        // Show typing indicator while waiting for response
        let typingMessage = ChatMessage(content: .typing, sender: .ai)
        messages.append(typingMessage)
        let typingMessageId = typingMessage.id

        do {
            let response = try await APIService.shared.sendAskMessage(
                prompt: query,
                context: context,
                image: image
            )

            guard !Task.isCancelled else {
                messages.removeAll { $0.id == typingMessageId }
                return
            }

            // Remove typing indicator
            messages.removeAll { $0.id == typingMessageId }

            await showTextResponse(response)
        } catch {
            // Remove typing indicator on error
            messages.removeAll { $0.id == typingMessageId }
            await showError()
        }
    }

    /// Handle greetings, off-topic, clarification queries (no acknowledgement)
    private func handleNonFlowerQuery(_ query: String, image: UIImage?, context: ChatContextV2) async {
        // Show typing indicator while waiting for response
        let typingMessage = ChatMessage(content: .typing, sender: .ai)
        messages.append(typingMessage)
        let typingMessageId = typingMessage.id

        do {
            let response = try await APIService.shared.sendMessage(
                prompt: query,
                context: context,
                image: image
            )

            guard !Task.isCancelled else {
                messages.removeAll { $0.id == typingMessageId }
                return
            }

            // Remove typing indicator
            messages.removeAll { $0.id == typingMessageId }

            if let textMessage = response.textMessage {
                await showTextResponse(textMessage)
            } else {
                await showError()
            }
        } catch {
            // Remove typing indicator on error
            messages.removeAll { $0.id == typingMessageId }
            await showError()
        }
    }

    /// Handle flower recommendation requests (show acknowledgement + thinking + pipeline)
    private func handleFlowerRequest(_ query: String, image: UIImage?, context: ChatContextV2) async {
        // Show acknowledgement
        try? await Task.sleep(nanoseconds: acknowledgementDelay)
        guard !Task.isCancelled else { return }

        let acknowledgement = generateAcknowledgement(for: query, hasImage: image != nil)
        let ackMessage = ChatMessage(content: .acknowledgement(acknowledgement), sender: .ai)
        animatingMessageIds.insert(ackMessage.id)
        messages.append(ackMessage)
        phase = .acknowledgement
        saveToHistory()

        // Continue with thinking + API call
        await startThinkingProcessWithAPI(for: query, image: image, context: context)
    }

    private func cleanupPartialState() {
        messages.removeAll { message in
            switch message.content {
            case .thinking(let content) where !content.isComplete:
                return true
            case .acknowledgement:
                return true
            case .typing:
                return true
            default:
                return false
            }
        }

        isInputEnabled = true
        phase = .idle
        eventService.stop()
    }

    private func startThinkingProcessWithAPI(for userQuery: String, image: UIImage? = nil, context: ChatContextV2? = nil) async {
        // Use provided context or build new one
        let chatContext = context ?? buildChatContextV2()

        guard !Task.isCancelled else { return }

        // Show thinking progress for flower recommendations
        let thinkingMessage = ChatMessage(
            content: .thinking(ThinkingContent(steps: [], isExpanded: true, isComplete: false)),
            sender: .ai
        )
        messages.append(thinkingMessage)
        expandedThinkingCards.insert(thinkingMessage.id)
        let thinkingMessageId = thinkingMessage.id
        phase = .thinking
        eventService.start()

        // Main API call
        var response: ChatResponse?
        do {
            response = try await APIService.shared.sendMessage(
                prompt: userQuery,
                context: chatContext,
                image: image
            )
        } catch {
            print("[ChatViewModel] API Error: \(error.localizedDescription)")
        }

        guard !Task.isCancelled else { return }

        // Cleanup thinking state
        eventService.stop()
        messages.removeAll { $0.id == thinkingMessageId }
        expandedThinkingCards.remove(thinkingMessageId)

        // Handle response
        if let response = response {
            switch response.type {
            case .recommendation:
                if let payload = response.recommendation {
                    lastPayload = payload
                    await showRecommendation(from: payload)
                } else {
                    await showError()
                }
            case .text:
                if let textMessage = response.textMessage {
                    await showTextResponse(textMessage)
                } else {
                    await showError()
                }
            }
        } else {
            await showError()
        }
    }

    /// Build extended context with full conversation history
    private func buildChatContextV2() -> ChatContextV2 {
        var history: [ConversationMessage] = []
        var lastFlowerName: String?
        var lastEmotion: String?

        for message in messages {
            switch message.content {
            case .text(let text):
                history.append(ConversationMessage(
                    role: message.sender == .user ? "user" : "assistant",
                    content: text,
                    messageType: "text",
                    flowerName: nil
                ))

            case .textWithImage(let text, _):
                history.append(ConversationMessage(
                    role: message.sender == .user ? "user" : "assistant",
                    content: text,
                    messageType: "text",
                    flowerName: nil
                ))

            case .recommendation(let rec):
                lastFlowerName = rec.flowerName
                // Extract emotion from meaning field (e.g., "Deep love and passion")
                lastEmotion = extractEmotion(from: rec.meaning)
                history.append(ConversationMessage(
                    role: "assistant",
                    content: "Recommended: \(rec.flowerName)",
                    messageType: "recommendation",
                    flowerName: rec.flowerName
                ))

            case .acknowledgement, .thinking, .followUp, .typing:
                // Skip transient messages
                break
            }
        }

        return ChatContextV2(
            conversationHistory: history,
            lastFlowerName: lastFlowerName,
            lastEmotion: lastEmotion,
            region: "US" // TODO: Get from user settings
        )
    }

    /// Extract emotion/occasion from recommendation subtitle
    private func extractEmotion(from subtitle: String) -> String? {
        // Common patterns: "Perfect for apology", "Ideal for birthday"
        let patterns = ["for ", "на "]
        for pattern in patterns {
            if let range = subtitle.lowercased().range(of: pattern) {
                let startIndex = range.upperBound
                let remaining = subtitle[startIndex...]
                // Take first word or two
                let words = remaining.split(separator: " ").prefix(2)
                if !words.isEmpty {
                    return words.joined(separator: " ")
                }
            }
        }
        return nil
    }

    /// Show a text response from the AI (for clarification questions)
    private func showTextResponse(_ text: String) async {
        let textMessage = ChatMessage(content: .text(text), sender: .ai)
        animatingMessageIds.insert(textMessage.id)
        messages.append(textMessage)
        phase = .idle
        saveToHistory()
        isInputEnabled = true
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
        animatingMessageIds.insert(errorMessage.id)
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
        animatingMessageIds.removeAll()
        inputText = ""
        isInputEnabled = true
        phase = .idle
        attachedImage = nil
        messages = [.welcomeMessage]

        // Clear active session state
        stateManager.clearActiveState()
    }

    private func resetState() {
        messages = []
        inputText = ""
        isInputEnabled = true
        phase = .idle
        attachedImage = nil
        animatingMessageIds.removeAll()
        expandedThinkingCards.removeAll()
    }

    // MARK: - Acknowledgement Generator

    private func generateAcknowledgement(for query: String, hasImage: Bool = false) -> String {
        let isRussian = containsCyrillic(query)

        if hasImage {
            if isRussian {
                return query.isEmpty
                    ? "Вижу, вы поделились красивым букетом! Дайте мне определить цветы для вас."
                    : "Красивый букет! Дайте мне рассмотреть его внимательнее."
            } else {
                return query.isEmpty
                    ? "I see you've shared a beautiful bouquet! Let me identify the flowers for you."
                    : "Thanks for sharing that image! Let me analyze the flowers and find more information."
            }
        }

        let queryLower = query.lowercased()

        // Russian context-specific acknowledgements
        if isRussian {
            if queryLower.contains("день рождения") || queryLower.contains("днюху") {
                return "День рождения! Дайте подумать о чём-то, что передаст радость этого праздника."
            } else if queryLower.contains("годовщин") {
                return "Годовщина — это особенный момент. Дайте найти что-то, что почтит ваш совместный путь."
            } else if queryLower.contains("извин") || queryLower.contains("прости") {
                return "Понимаю, это важно. Дайте подумать о цветах, которые говорят от сердца."
            } else if queryLower.contains("люб") || queryLower.contains("романтич") {
                return "Романтика заслуживает чего-то особенного. Дайте найти идеальное выражение чувств."
            }

            let russianAcknowledgements = [
                "Красивая мысль. Позвольте подобрать что-то особенное.",
                "Понимаю. Дайте мне подумать об идеальном выборе для вас.",
                "Какой значимый жест. Дайте мне момент обдумать это.",
                "Прекрасно. Позвольте найти что-то, что подойдёт идеально."
            ]
            return russianAcknowledgements.randomElement() ?? russianAcknowledgements[0]
        }

        // English context-specific acknowledgements
        if queryLower.contains("birthday") {
            return "A birthday gift! Let me think about something that captures the joy of this celebration."
        } else if queryLower.contains("anniversary") {
            return "An anniversary is so special. Let me find something that honors your journey together."
        } else if queryLower.contains("sorry") || queryLower.contains("apolog") {
            return "I understand this is important. Let me think about flowers that speak from the heart."
        } else if queryLower.contains("love") || queryLower.contains("romantic") {
            return "Romance deserves something truly special. Let me consider the perfect expression."
        }

        let englishAcknowledgements = [
            "That's a beautiful thought. Let me find something special.",
            "I understand. Let me think about the perfect choice for you.",
            "What a meaningful gesture. Give me a moment to consider this carefully.",
            "That's lovely. Let me explore some options that would fit perfectly."
        ]
        return englishAcknowledgements.randomElement() ?? englishAcknowledgements[0]
    }

    /// Check if string contains Cyrillic characters (Russian/Ukrainian/etc)
    private func containsCyrillic(_ text: String) -> Bool {
        text.unicodeScalars.contains { scalar in
            // Cyrillic range: U+0400 to U+04FF
            scalar.value >= 0x0400 && scalar.value <= 0x04FF
        }
    }
}
