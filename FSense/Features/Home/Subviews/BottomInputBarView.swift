import SwiftUI

// MARK: - Chat Sheet Controller

@MainActor
final class ChatSheetController: ObservableObject {
    @Published var isExpanded = false
    @Published var sessionToLoad: ChatSession?

    func openNewChat() {
        sessionToLoad = nil
        isExpanded = true
    }

    func openChat(session: ChatSession) {
        sessionToLoad = session
        isExpanded = true
    }

    func close() {
        isExpanded = false
    }
}

// MARK: - Bottom Input Bar View (Collapsed State Only)

struct BottomInputBarView: View {
    @ObservedObject var controller: ChatSheetController
    @StateObject private var chatViewModel = ChatViewModel()
    @FocusState private var isInputFocused: Bool

    private let collapsedHeight: CGFloat = 130
    private let safeAreaBottom: CGFloat = 34

    var body: some View {
        VStack(spacing: 0) {
            // Collapsed bar content
            collapsedContent
        }
        .frame(height: collapsedHeight)
        .frame(maxWidth: .infinity)
        .background(glassBackground)
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .overlay(borderOverlay)
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: -12)
        .sheet(isPresented: $controller.isExpanded) {
            // Native sheet for expanded state - handles keyboard perfectly
            ExpandedChatSheet(
                controller: controller,
                viewModel: chatViewModel
            )
            .presentationDetents([.large])
            .presentationDragIndicator(.visible)
            .presentationBackgroundInteraction(.enabled)
            .interactiveDismissDisabled(false)
        }
        .onChange(of: controller.sessionToLoad) { _, newSession in
            if let session = newSession {
                chatViewModel.loadSession(session)
            } else {
                chatViewModel.send(.reset)
            }
        }
        .onChange(of: controller.isExpanded) { _, isExpanded in
            if isExpanded && controller.sessionToLoad == nil {
                chatViewModel.send(.reset)
            }
        }
    }

    // MARK: - Collapsed Content

    private var collapsedContent: some View {
        VStack(spacing: 0) {
            // Drag indicator - активный для свайпа вверх
            Capsule()
                .fill(Color.gray.opacity(0.5))
                .frame(width: 36, height: 5)
                .padding(.top, 10)
                .padding(.bottom, 20)
                .frame(maxWidth: .infinity)
                .contentShape(Rectangle())
                .gesture(
                    DragGesture()
                        .onEnded { value in
                            if value.translation.height < -30 {
                                controller.openNewChat()
                            }
                        }
                )

            Spacer(minLength: 0)

            // Input row (without plus button in collapsed state)
            HStack(spacing: 12) {
                // Tappable input field placeholder
                HStack(spacing: 8) {
                    Text("Ask me about...")
                        .font(.system(size: 16))
                        .foregroundColor(Color.gray.opacity(0.8))

                    Spacer()

                    // Inactive send button
                    Image(systemName: "arrow.up")
                        .font(.system(size: 14, weight: .bold))
                        .foregroundColor(.white)
                        .frame(width: 30, height: 30)
                        .background(
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [
                                            Color(red: 0.55, green: 0, blue: 0.92),
                                            Color(red: 0.91, green: 0.04, blue: 0.79)
                                        ],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .opacity(0.4)
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
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, safeAreaBottom)
        }
    }

    // MARK: - Background

    private var glassBackground: some View {
        ZStack {
            Rectangle().fill(.ultraThinMaterial)
            Color.white.opacity(0.8)
        }
        .clipShape(RoundedRectangle(cornerRadius: 24))
    }

    private var borderOverlay: some View {
        RoundedRectangle(cornerRadius: 24)
            .inset(by: 0.5)
            .stroke(Color.white, lineWidth: 1)
    }
}

// MARK: - Expanded Chat Sheet (Native Sheet)

struct ExpandedChatSheet: View {
    @ObservedObject var controller: ChatSheetController
    @ObservedObject var viewModel: ChatViewModel
    @FocusState private var isInputFocused: Bool
    @State private var selectedFlower: Flower?
    @State private var navigateToFlowerDetail = false
    @State private var scrollProxy: ScrollViewProxy?
    @State private var showScrollToBottom = false
    @State private var showPlusButton = false
    @Namespace private var bottomID
    @Namespace private var toolbarNamespace

    // MARK: - Static Constants (performance optimization)
    private static let inputBgColor = Color(red: 0.98, green: 0.98, blue: 0.98)
    private static let toolbarSymbols = ["magnifyingglass", "ellipsis"]
    private static let gradientColors = [
        Color(red: 0.55, green: 0, blue: 0.92),
        Color(red: 0.91, green: 0.04, blue: 0.79)
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Messages scroll area
                messagesScrollView

                // Input area - automatically moves with keyboard in native sheet
                inputArea
            }
            .background(Color.white)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("Chat")
                        .font(.headline)
                }
                ToolbarItem(placement: .topBarTrailing) {
                    toolbarButtons
                }
            }
            .navigationDestination(isPresented: $navigateToFlowerDetail) {
                if let flower = selectedFlower {
                    FlowerCardView(flower: flower)
                        .id(flower.id)
                }
            }
        }
        .onAppear {
            showPlusButton = true
            // Auto-focus input when sheet opens
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                isInputFocused = true
            }
        }
        .onDisappear {
            showPlusButton = false
        }
        .animation(.spring(response: 0.35, dampingFraction: 0.8), value: showPlusButton)
    }

    // MARK: - Messages Scroll View

    private var messagesScrollView: some View {
        ZStack(alignment: .bottom) {
            ScrollViewReader { proxy in
                ScrollView(showsIndicators: false) {
                    LazyVStack(spacing: 16) {
                        let messages = viewModel.orderedMessages
                        ForEach(messages.indices, id: \.self) { index in
                            let message = messages[index]
                            MessageRow(
                                message: message,
                                messages: messages,
                                messageIndex: index,
                                isThinkingExpanded: viewModel.isThinkingCardExpanded(message.id),
                                onThinkingToggle: { viewModel.send(.toggleThinkingCard(message.id)) },
                                onExploreFlower: { recommendation in
                                    if let payload = viewModel.lastPayload {
                                        selectedFlower = payload.toFlower()
                                    } else {
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

                        // Bottom anchor
                        Color.clear
                            .frame(height: 1)
                            .id(bottomID)
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 16)
                    .padding(.bottom, 8)
                }
                .scrollDismissesKeyboard(.interactively)
                .onScrollGeometryChange(for: Bool.self) { geometry in
                    let contentHeight = geometry.contentSize.height
                    let visibleHeight = geometry.visibleRect.height
                    guard contentHeight > visibleHeight + 50 else { return false }
                    let bottomOffset = contentHeight - visibleHeight - geometry.contentOffset.y
                    return bottomOffset > 80
                } action: { oldValue, newValue in
                    guard oldValue != newValue else { return }
                    showScrollToBottom = newValue
                }
                .defaultScrollAnchor(.bottom)
                .onAppear { scrollProxy = proxy }
                .onChange(of: viewModel.messages.count) { _, _ in
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                        proxy.scrollTo(bottomID, anchor: .bottom)
                        showScrollToBottom = false
                    }
                }
                .onTapGesture {
                    isInputFocused = false
                }
            }

            // Floating scroll-to-bottom button (only when scrolled up)
            if showScrollToBottom {
                scrollToBottomButton
            }
        }
        .animation(.easeInOut(duration: 0.2), value: showScrollToBottom)
    }

    // MARK: - Scroll to Bottom Button

    private var scrollToBottomButton: some View {
        Button {
            scrollProxy?.scrollTo(bottomID, anchor: .bottom)
            showScrollToBottom = false
        } label: {
            Image(systemName: "chevron.down")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.primary.opacity(0.8))
                .frame(width: 36, height: 36)
                .glassEffect(.clear.tint(.black.opacity(0.12)).interactive(), in: .circle)
        }
        .padding(.bottom, 12)
        .transition(.scale.combined(with: .opacity))
    }

    // MARK: - Toolbar Buttons

    @ViewBuilder
    private var toolbarButtons: some View {
        GlassEffectContainer(spacing: 0) {
            HStack(spacing: 0) {
                // Search button
                Image(systemName: Self.toolbarSymbols[0])
                    .font(.system(size: 17, weight: .medium))
                    .frame(width: 42, height: 36)
                    .contentShape(Rectangle())
                    .glassEffect()
                    .glassEffectUnion(id: "toolbar", namespace: toolbarNamespace)
                    .onTapGesture {
                        print("Search tapped")
                    }

                // Menu button
                Menu {
                    Button {
                        viewModel.send(.reset)
                        controller.sessionToLoad = nil
                    } label: {
                        Label("Новый чат", systemImage: "plus.message")
                    }

                    Button(role: .destructive) {
                        viewModel.send(.reset)
                        controller.sessionToLoad = nil
                    } label: {
                        Label("Очистить чат", systemImage: "trash")
                    }
                } label: {
                    Image(systemName: Self.toolbarSymbols[1])
                        .font(.system(size: 17, weight: .medium))
                        .frame(width: 42, height: 36)
                        .contentShape(Rectangle())
                        .glassEffect()
                        .glassEffectUnion(id: "toolbar", namespace: toolbarNamespace)
                }
            }
        }
    }

    // MARK: - Input Area

    @ViewBuilder
    private var inputArea: some View {
        HStack(spacing: 12) {
            // Plus button - animated appearance
            if showPlusButton {
                plusButton
                    .transition(.scale.combined(with: .opacity))
            }

            // Text field container
            textFieldContainer
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
    }

    private var plusButton: some View {
        Button {
            viewModel.send(.reset)
            controller.sessionToLoad = nil
        } label: {
            Image(systemName: "plus")
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(.primary)
                .frame(width: 50, height: 50)
                .background(Self.inputBgColor)
                .clipShape(Circle())
                .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
                .overlay(
                    Circle()
                        .inset(by: 0.5)
                        .stroke(.white, lineWidth: 1)
                )
        }
        .buttonStyle(.plain)
    }

    private var textFieldContainer: some View {
        HStack(spacing: 8) {
            TextField("Ask me about flowers...", text: inputTextBinding)
                .font(.system(size: 16))
                .focused($isInputFocused)
                .disabled(!viewModel.isInputEnabled)
                .submitLabel(.send)
                .onSubmit(sendMessageIfCan)

            // Send button
            sendButton
        }
        .padding(.leading, 18)
        .padding(.trailing, 10)
        .frame(height: 50)
        .background(Self.inputBgColor)
        .cornerRadius(100)
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
        .overlay(
            RoundedRectangle(cornerRadius: 100)
                .inset(by: 0.5)
                .stroke(.white, lineWidth: 1)
        )
    }

    private var inputTextBinding: Binding<String> {
        Binding(
            get: { viewModel.inputText },
            set: { viewModel.send(.inputTextChanged($0)) }
        )
    }

    private var sendButton: some View {
        Button(action: sendMessageIfCan) {
            Image(systemName: "arrow.up")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .frame(width: 30, height: 30)
                .background(
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: Self.gradientColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .opacity(viewModel.canSendMessage ? 1 : 0.4)
                )
        }
        .buttonStyle(.plain)
        .disabled(!viewModel.canSendMessage)
    }

    private func sendMessageIfCan() {
        guard viewModel.canSendMessage else { return }
        viewModel.send(.sendMessage)
        isInputFocused = false
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

// MARK: - Message Row

struct MessageRow: View {
    let message: ChatMessage
    let messages: [ChatMessage]
    let messageIndex: Int
    let isThinkingExpanded: Bool
    let onThinkingToggle: () -> Void
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
        MessageBubbleView(
            message: message,
            isThinkingExpanded: isThinkingExpanded,
            onThinkingToggle: onThinkingToggle,
            onExploreFlower: onExploreFlower,
            hideCompletedThinking: isThinkingFollowedByRecommendation
        )
    }
}
