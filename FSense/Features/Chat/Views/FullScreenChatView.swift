import SwiftUI

/// Full-screen chat - optimized
struct FullScreenChatView: View {
    
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool
    @Namespace private var bottomID
    
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
        ScrollViewReader { proxy in
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 16) {
                    ForEach(viewModel.orderedMessages) { message in
                        MessageBubbleView(
                            message: message,
                            isThinkingExpanded: viewModel.isThinkingCardExpanded(message.id),
                            onThinkingToggle: {
                                viewModel.send(.toggleThinkingCard(message.id))
                            },
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
                    
                    Color.clear.frame(height: 1).id(bottomID)
                }
                .padding(.horizontal, 16)
                .padding(.top, 16)
                .padding(.bottom, 100)
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
