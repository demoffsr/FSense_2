import SwiftUI

/// Main chat view - optimized
struct ChatView: View {
    
    @StateObject private var viewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool
    @Namespace private var bottomID
    
    @State private var selectedFlower: Flower?
    @State private var navigateToFlowerDetail = false
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                messagesScrollView
                chatInputView
            }
            .background(Color(white: 0.97))
            .navigationBarHidden(true)
            .navigationDestination(isPresented: $navigateToFlowerDetail) {
                if let flower = selectedFlower {
                    FlowerCardView(flower: flower)
                        .id(flower.id) // Force view recreation on flower change
                }
            }
        }
        .onAppear {
            viewModel.send(.onAppear)
        }
    }
    
    // MARK: - Messages
    
    private var messagesScrollView: some View {
        ScrollViewReader { proxy in
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 16) {
                    ForEach(Array(viewModel.orderedMessages.enumerated()), id: \.element.id) { index, message in
                        ChatMessageRow(
                            message: message,
                            viewModel: viewModel,
                            messages: viewModel.orderedMessages,
                            messageIndex: index,
                            onExploreFlower: { recommendation in
                                // Use real payload data from API
                                if let payload = viewModel.lastPayload {
                                    print("[ChatView] Using real payload for: \(payload.header.name)")
                                    selectedFlower = payload.toFlower()
                                    print("[ChatView] Created flower with giftingInfo: \(selectedFlower?.giftingInfo != nil)")
                                } else {
                                    print("[ChatView] WARNING: No payload! Using fallback for: \(recommendation.flowerName)")
                                    // Fallback if payload not available
                                    selectedFlower = Flower(
                                        name: recommendation.flowerName,
                                        imageAsset: recommendation.imageAsset,
                                        meanings: ["Love", "Appreciation"],
                                        symbolismText: recommendation.explanation,
                                        whyThisFlowerText: recommendation.meaning,
                                        moodIntensityValue: 0.7
                                    )
                                }
                                navigateToFlowerDetail = true
                            }
                        )
                        .id(message.id)
                    }
                    
                    Color.clear.frame(height: 1).id(bottomID)
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)
                .padding(.bottom, 8)
            }
            .onChange(of: viewModel.messages.count) { _, _ in
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                    withAnimation(.easeOut(duration: 0.2)) {
                        proxy.scrollTo(bottomID, anchor: .bottom)
                    }
                }
            }
        }
    }
    
    // MARK: - Chat Message Row Helper
    
    private struct ChatMessageRow: View {
        let message: ChatMessage
        @ObservedObject var viewModel: ChatViewModel
        let messages: [ChatMessage]
        let messageIndex: Int
        var onExploreFlower: ((FlowerRecommendation) -> Void)?

        private var associatedThinkingMessageId: UUID? {
            guard case .recommendation = message.content else { return nil }
            for i in stride(from: messageIndex - 1, through: 0, by: -1) {
                if case .thinking = messages[i].content {
                    return messages[i].id
                }
                if messages[i].sender == .user { break }
            }
            return nil
        }
        
        private var isThinkingFollowedByRecommendation: Bool {
            guard case .thinking(let content) = message.content, content.isComplete else { return false }
            for i in (messageIndex + 1)..<messages.count {
                if case .recommendation = messages[i].content { return true }
                if messages[i].sender == .user { break }
            }
            return false
        }
        
        var body: some View {
            let thinkingId = associatedThinkingMessageId ?? message.id
            MessageBubbleView(
                message: message,
                isThinkingExpanded: viewModel.isThinkingCardExpanded(thinkingId),
                onThinkingToggle: { viewModel.send(.toggleThinkingCard(thinkingId)) },
                onExploreFlower: onExploreFlower,
                hideCompletedThinking: isThinkingFollowedByRecommendation
            )
        }
    }
    
    // MARK: - Input
    
    private var chatInputView: some View {
        VStack(spacing: 0) {
            Divider()
            
            HStack(spacing: 12) {
                HStack(spacing: 8) {
                    TextField("Ask me about flowers...", text: Binding(
                        get: { viewModel.inputText },
                        set: { viewModel.send(.inputTextChanged($0)) }
                    ))
                    .font(.system(size: 16))
                    .focused($isInputFocused)
                    .disabled(!viewModel.isInputEnabled)
                    .submitLabel(.send)
                    .onSubmit {
                        if viewModel.canSendMessage {
                            viewModel.send(.sendMessage)
                        }
                    }
                    
                    Button {
                        viewModel.send(.sendMessage)
                        isInputFocused = false
                    } label: {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.white)
                            .frame(width: 30, height: 30)
                            .background(
                                Circle().fill(Color.purple.opacity(viewModel.canSendMessage ? 1 : 0.4))
                            )
                    }
                    .disabled(!viewModel.canSendMessage)
                }
                .padding(.leading, 16)
                .padding(.trailing, 8)
                .padding(.vertical, 8)
                .background(Capsule().fill(Color(white: 0.95)))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.white)
        }
    }
}
