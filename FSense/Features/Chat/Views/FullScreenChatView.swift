import SwiftUI

/// Full-screen chat - optimized
struct FullScreenChatView: View {
    
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool
    
    @State private var selectedFlower: Flower?
    @State private var navigateToFlowerDetail = false
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                chatHeader
                messagesScrollView
                chatInputArea
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
        .ignoresSafeArea(.container, edges: .bottom)
    }
    
    // MARK: - Header
    
    private var chatHeader: some View {
        HStack {
            Button { dismiss() } label: {
                Image(systemName: "chevron.down")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.black)
                    .frame(width: 40, height: 40)
                    .background(Color(white: 0.95))
                    .clipShape(Circle())
            }
            
            Spacer()
            
            Text("FlowerSense")
                .font(.system(size: 17, weight: .semibold))
            
            Spacer()
            
            Button {
                viewModel.send(.reset)
            } label: {
                Image(systemName: "arrow.counterclockwise")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.black)
                    .frame(width: 40, height: 40)
                    .background(Color(white: 0.95))
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color.white)
    }
    
    // MARK: - Messages
    
    private var messagesScrollView: some View {
        ScrollView(showsIndicators: false) {
            LazyVStack(spacing: 16) {
                ForEach(viewModel.orderedMessages) { message in
                    MessageBubbleView(
                        message: message,
                        steps: viewModel.pipelineSteps,
                        isThinkingExpanded: viewModel.isThinkingCardExpanded(message.id),
                        onThinkingToggle: {
                            viewModel.send(.toggleThinkingCard(message.id))
                        },
                        onExploreFlower: { recommendation in
                            print("[FullScreenChatView] onExploreFlower called for: \(recommendation.flowerName)")
                            // Use real payload data from API
                            if let payload = viewModel.lastPayload {
                                print("[FullScreenChatView] Using real payload for: \(payload.header.name)")
                                selectedFlower = payload.toFlower()
                                print("[FullScreenChatView] Created flower with giftingInfo: \(selectedFlower?.giftingInfo != nil)")
                            } else {
                                print("[FullScreenChatView] WARNING: No payload! Using fallback")
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
                        },
                        shouldAnimate: viewModel.shouldAnimateMessage(message.id)
                    )
                    .id(message.id)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            .padding(.bottom, 100)
        }
        .defaultScrollAnchor(.bottom)
    }
    
    // MARK: - Input
    
    private var chatInputArea: some View {
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
                            .frame(width: 32, height: 32)
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
            .padding(.top, 12)
            .padding(.bottom, 40)
            .background(Color.white)
        }
    }
}
