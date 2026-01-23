import SwiftUI

// MARK: - Chat Sheet Controller

/// Observable controller for managing the chat bottom sheet state
/// Allows external views to open the sheet with a specific session
@MainActor
final class ChatSheetController: ObservableObject {
    @Published var isExpanded = false
    @Published var sessionToLoad: ChatSession?
    
    /// Open the chat sheet with a new empty chat
    func openNewChat() {
        sessionToLoad = nil
        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
            isExpanded = true
        }
    }
    
    /// Open the chat sheet with an existing session
    func openChat(session: ChatSession) {
        sessionToLoad = session
        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
            isExpanded = true
        }
    }
    
    /// Close the chat sheet
    func close() {
        withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
            isExpanded = false
        }
    }
}

struct BottomInputBarView: View {

    @ObservedObject var controller: ChatSheetController
    @State private var dragOffset: CGFloat = 0
    @StateObject private var chatViewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool

    // MARK: - Layout Constants

    private let collapsedHeight: CGFloat = 130
    private let bottomPadding: CGFloat = 34
    private var expandedHeight: CGFloat {
        UIScreen.main.bounds.height - 60
    }

    private var currentHeight: CGFloat {
        let base = controller.isExpanded ? expandedHeight : collapsedHeight
        // Allow dragging in both directions
        let adjusted = base - dragOffset
        return max(collapsedHeight, min(expandedHeight, adjusted))
    }

    // MARK: - Body

    var body: some View {
        VStack(spacing: 0) {

            // MARK: - Drag Handle
            Capsule()
                .fill(Color.gray.opacity(0.5))
                .frame(width: 36, height: 5)
                .padding(.top, 10)
                .padding(.bottom, controller.isExpanded ? 8 : 20)

            // MARK: - Chat Content (visible when expanded)
            if controller.isExpanded {
                ExpandedChatView(
                    viewModel: chatViewModel,
                    isInputFocused: $isInputFocused
                )
                .transition(.opacity.combined(with: .move(edge: .bottom)))
            }

            Spacer(minLength: 0)

            // MARK: - Input Row (pinned to bottom of sheet content)
            ChatInputRowView(
                controller: controller,
                viewModel: chatViewModel,
                isInputFocused: $isInputFocused
            )
            .padding(.bottom, 36)
        }
        .frame(height: currentHeight)
        .frame(maxWidth: .infinity)
        .background(
            // MARK: - Glass Background
            ZStack {
                Rectangle()
                    .fill(.ultraThinMaterial)
                Color.white.opacity(0.8)
            }
            .clipShape(RoundedRectangle(cornerRadius: 24))
        )
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .overlay(
            RoundedRectangle(cornerRadius: 24)
                .inset(by: 0.5)
                .stroke(Color.white, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: -12)
        .gesture(dragGesture)
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: controller.isExpanded)
        .animation(.interactiveSpring(response: 0.3, dampingFraction: 0.8), value: dragOffset)
        .onChange(of: controller.sessionToLoad) { _, newSession in
            // Load the session when it changes
            if let session = newSession {
                chatViewModel.loadSession(session)
            }
        }
    }

    // MARK: - Drag Gesture

    private var dragGesture: some Gesture {
        DragGesture()
            .onChanged { value in
                dragOffset = value.translation.height
            }
            .onEnded { value in
                let threshold: CGFloat = 80
                let velocity = value.predictedEndTranslation.height - value.translation.height

                withAnimation(.spring(response: 0.4, dampingFraction: 0.8)) {
                    // Swipe UP = expand
                    if value.translation.height < -threshold || velocity < -200 {
                        controller.isExpanded = true
                    }
                    // Swipe DOWN = collapse
                    else if value.translation.height > threshold || velocity > 200 {
                        controller.isExpanded = false
                        isInputFocused = false
                    }
                    dragOffset = 0
                }
            }
    }
}

// MARK: - Chat Input Row

struct ChatInputRowView: View {
    @ObservedObject var controller: ChatSheetController
    @ObservedObject var viewModel: ChatViewModel
    var isInputFocused: FocusState<Bool>.Binding
    
    var body: some View {
        HStack(spacing: 12) {
            ChatPlusButton(onTap: {
                // Start a new chat
                viewModel.send(.reset)
                controller.sessionToLoad = nil
                controller.openNewChat()
            })
            
            ChatPromptInputField(
                controller: controller,
                viewModel: viewModel,
                isInputFocused: isInputFocused
            )
        }
        .padding(.horizontal, 20)
        .padding(.top, 16)
        .padding(.bottom, 8)
    }
}

// MARK: - Chat Prompt Input Field

struct ChatPromptInputField: View {
    @ObservedObject var controller: ChatSheetController
    @ObservedObject var viewModel: ChatViewModel
    var isInputFocused: FocusState<Bool>.Binding
    
    var body: some View {
        HStack(spacing: 8) {
            if controller.isExpanded {
                TextField("Ask me about flowers...", text: Binding(
                    get: { viewModel.inputText },
                    set: { viewModel.send(.inputTextChanged($0)) }
                ))
                .font(.system(size: 16))
                .focused(isInputFocused)
                .disabled(!viewModel.isInputEnabled)
                .submitLabel(.send)
                .onSubmit {
                    if viewModel.canSendMessage {
                        viewModel.send(.sendMessage)
                    }
                }
            } else {
                Text("Ask me about...")
                    .font(.system(size: 16))
                    .foregroundColor(Color.gray.opacity(0.8))
            }
            
            Spacer()
            
            // Send button
            ChatSendButton(
                isEnabled: viewModel.canSendMessage,
                action: {
                    if controller.isExpanded && viewModel.canSendMessage {
                        viewModel.send(.sendMessage)
                        isInputFocused.wrappedValue = false
                    }
                }
            )
        }
        .padding(.leading, 18)
        .padding(.trailing, 10)
        .frame(height: 50)
        .glassEffect(
            .clear.tint(.white.opacity(0.1)).interactive(),
            in: Capsule()
        )
        .shadow(color: .black.opacity(0.08), radius: 12, x: 0, y: 4)
        .onTapGesture {
            controller.openNewChat()
            isInputFocused.wrappedValue = true
        }
    }
}

// MARK: - Chat Plus Button

struct ChatPlusButton: View {
    var onTap: () -> Void = {}
    
    var body: some View {
        Button {
            onTap()
        } label: {
            Image(systemName: "plus")
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(.black)
                .frame(width: 50, height: 50)
                .glassEffect(
                    .clear.tint(.white.opacity(0.1)).interactive(),
                    in: Circle()
                )
                .shadow(color: .black.opacity(0.08), radius: 12, x: 0, y: 4)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Chat Send Button (30x30)

struct ChatSendButton: View {
    let isEnabled: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Image(systemName: "arrow.up")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .frame(width: 30, height: 30)
                .background(
                    Circle()
                        .fill(sendButtonGradient)
                        .opacity(isEnabled ? 1 : 0.4)
                )
        }
        .buttonStyle(.plain)
        .disabled(!isEnabled)
    }
    
    private var sendButtonGradient: LinearGradient {
        LinearGradient(
            colors: [
                Color(red: 0.55, green: 0, blue: 0.92),
                Color(red: 0.91, green: 0.04, blue: 0.79)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }
}

// MARK: - Expanded Chat View

struct ExpandedChatView: View {
    @ObservedObject var viewModel: ChatViewModel
    var isInputFocused: FocusState<Bool>.Binding
    @Namespace private var bottomID
    
    // Navigation state for flower detail
    @State private var selectedFlower: Flower?
    @State private var navigateToFlowerDetail = false
    
    var body: some View {
        ScrollViewReader { proxy in
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 16) {
                    ForEach(Array(viewModel.orderedMessages.enumerated()), id: \.element.id) { index, message in
                        MessageRow(
                            message: message,
                            viewModel: viewModel,
                            messages: viewModel.orderedMessages,
                            messageIndex: index,
                            onExploreFlower: { recommendation in
                                selectedFlower = Flower(
                                    name: recommendation.flowerName,
                                    imageAsset: recommendation.imageAsset,
                                    meanings: ["Love", "Passion", "Romance"],
                                    symbolismText: recommendation.explanation,
                                    whyThisFlowerText: recommendation.meaning,
                                    moodIntensityValue: 0.85
                                )
                                navigateToFlowerDetail = true
                            }
                        )
                        .id(message.id)
                    }
                    
                    Color.clear
                        .frame(height: 1)
                        .id(bottomID)
                }
                .padding(.horizontal, 20)
                .padding(.top, 8)
                .padding(.bottom, 20)
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    withAnimation(.easeOut(duration: 0.25)) {
                        proxy.scrollTo(bottomID, anchor: .bottom)
                    }
                }
            }
        }
        .navigationDestination(isPresented: $navigateToFlowerDetail) {
            if let flower = selectedFlower {
                FlowerCardView(flower: flower)
                    .id(flower.id) // Force view recreation on flower change
            }
        }
    }
}

// MARK: - Optimized Message Row

struct MessageRow: View {
    let message: ChatMessage
    @ObservedObject var viewModel: ChatViewModel
    var messages: [ChatMessage] = []
    var messageIndex: Int = 0
    var onExploreFlower: ((FlowerRecommendation) -> Void)?
    
    /// Find associated thinking content for recommendation messages
    private var associatedThinkingContent: ThinkingContent? {
        guard case .recommendation = message.content else { return nil }
        
        // Look backwards to find the thinking message
        for i in stride(from: messageIndex - 1, through: 0, by: -1) {
            if case .thinking(let content) = messages[i].content {
                return content
            }
            // Stop if we hit a user message (new conversation turn)
            if messages[i].sender == .user {
                break
            }
        }
        return nil
    }
    
    /// Associated thinking message ID (for expand/collapse state)
    private var associatedThinkingMessageId: UUID? {
        guard case .recommendation = message.content else { return nil }
        
        for i in stride(from: messageIndex - 1, through: 0, by: -1) {
            if case .thinking = messages[i].content {
                return messages[i].id
            }
            if messages[i].sender == .user {
                break
            }
        }
        return nil
    }
    
    /// Check if this thinking message is followed by a recommendation
    private var isThinkingFollowedByRecommendation: Bool {
        guard case .thinking(let content) = message.content, content.isComplete else { return false }
        
        // Look forward to find if recommendation follows
        for i in (messageIndex + 1)..<messages.count {
            if case .recommendation = messages[i].content {
                return true
            }
            // Stop if we hit a user message
            if messages[i].sender == .user {
                break
            }
        }
        return false
    }
    
    var body: some View {
        let thinkingId = associatedThinkingMessageId ?? message.id
        
        MessageBubbleView(
            message: message,
            isThinkingExpanded: viewModel.isThinkingCardExpanded(thinkingId),
            onThinkingToggle: {
                viewModel.send(.toggleThinkingCard(thinkingId))
            },
            onExploreFlower: onExploreFlower,
            associatedThinkingContent: associatedThinkingContent,
            hideCompletedThinking: isThinkingFollowedByRecommendation
        )
    }
}
