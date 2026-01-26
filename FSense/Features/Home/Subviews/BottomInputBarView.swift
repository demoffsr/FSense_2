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

    // Static constants for performance
    private static let collapsedHeight: CGFloat = 130
    private static let safeAreaBottom: CGFloat = 34
    private static let shadowColor = Color.black.opacity(0.15)
    private static let lightShadowColor = Color.black.opacity(0.08)
    private static let inactiveGradient = LinearGradient(
        colors: [Color(red: 0.55, green: 0, blue: 0.92), Color(red: 0.91, green: 0.04, blue: 0.79)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    var body: some View {
        collapsedContent
            .frame(height: Self.collapsedHeight)
            .frame(maxWidth: .infinity)
            .background(glassBackground)
            .clipShape(RoundedRectangle(cornerRadius: 24))
            .overlay(borderOverlay)
            .compositingGroup()
            .shadow(color: Self.shadowColor, radius: 16, x: 0, y: -12)
            .sheet(isPresented: $controller.isExpanded) {
                ExpandedChatSheet(controller: controller, viewModel: chatViewModel)
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

    @ViewBuilder
    private var collapsedContent: some View {
        VStack(spacing: 0) {
            dragIndicator
            Spacer(minLength: 0)
            collapsedInputRow
        }
    }

    private var dragIndicator: some View {
        Capsule()
            .fill(Color.gray.opacity(0.5))
            .frame(width: 36, height: 5)
            .padding(.top, 10)
            .padding(.bottom, 20)
            .frame(maxWidth: .infinity)
            .contentShape(Rectangle())
            .gesture(
                DragGesture(minimumDistance: 10)
                    .onEnded { value in
                        if value.translation.height < -30 {
                            controller.openNewChat()
                        }
                    }
            )
    }

    private var collapsedInputRow: some View {
        HStack(spacing: 8) {
            Text("Ask me about...")
                .font(.system(size: 16))
                .foregroundStyle(.gray.opacity(0.8))

            Spacer(minLength: 0)

            Image(systemName: "arrow.up")
                .font(.system(size: 14, weight: .bold))
                .foregroundStyle(.white)
                .frame(width: 30, height: 30)
                .background(Circle().fill(Self.inactiveGradient).opacity(0.4))
        }
        .padding(.leading, 18)
        .padding(.trailing, 10)
        .frame(height: 50)
        .glassEffect(.clear.tint(.white.opacity(0.1)).interactive(), in: Capsule())
        .compositingGroup()
        .shadow(color: Self.lightShadowColor, radius: 12, x: 0, y: 4)
        .contentShape(Capsule())
        .onTapGesture { controller.openNewChat() }
        .padding(.horizontal, 20)
        .padding(.bottom, Self.safeAreaBottom)
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
    @State private var showImagePicker = false
    @State private var imageSource: ImageSource = .photoLibrary
    @Namespace private var bottomID
    @Namespace private var toolbarNamespace

    // MARK: - Static Constants (performance optimization)
    private static let inputBgColor = Color(red: 0.98, green: 0.98, blue: 0.98)
    private static let shadowColor = Color.black.opacity(0.15)
    private static let lightShadowColor = Color.black.opacity(0.08)
    private static let toolbarSymbols = ["magnifyingglass", "ellipsis"]
    private static let sendButtonGradient = LinearGradient(
        colors: [Color(red: 0.55, green: 0, blue: 0.92), Color(red: 0.91, green: 0.04, blue: 0.79)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

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
                        ForEach(viewModel.orderedMessages, id: \.id) { message in
                            messageRow(for: message)
                                .id(message.id)
                        }

                        Color.clear.frame(height: 1).id(bottomID)
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
            withAnimation(.easeOut(duration: 0.3)) {
                scrollProxy?.scrollTo(bottomID, anchor: .bottom)
            }
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
        VStack(alignment: .leading, spacing: 8) {
            // Attachment preview (if exists)
            if let image = viewModel.attachedImage {
                AttachmentPreviewView(image: image) {
                    viewModel.send(.removeAttachment)
                }
            }

            HStack(spacing: 12) {
                // Plus button - animated appearance
                if showPlusButton {
                    plusButton
                        .transition(.scale.combined(with: .opacity))
                }

                // Text field container
                textFieldContainer
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
        .sheet(isPresented: $showImagePicker) {
            ImagePickerView(source: imageSource, selectedImage: attachmentBinding)
        }
    }

    private var attachmentBinding: Binding<UIImage?> {
        Binding(
            get: { viewModel.attachedImage },
            set: { image in
                if let image = image {
                    viewModel.send(.attachImage(image))
                }
            }
        )
    }

    private var plusButton: some View {
        Menu {
            Button {
                imageSource = .photoLibrary
                showImagePicker = true
            } label: {
                Label("Photo Library", systemImage: "photo.on.rectangle")
            }

            Button {
                imageSource = .camera
                showImagePicker = true
            } label: {
                Label("Camera", systemImage: "camera")
            }
        } label: {
            Image(systemName: "plus")
                .font(.system(size: 18, weight: .medium))
                .foregroundStyle(.black)
                .frame(width: 50, height: 50)
                .glassEffect(.clear.tint(.white.opacity(0.1)).interactive(), in: .circle)
                .compositingGroup()
                .shadow(color: Self.lightShadowColor, radius: 12, x: 0, y: 4)
        }
    }

    private var textFieldContainer: some View {
        HStack(spacing: 8) {
            TextField("Ask me about flowers...", text: inputTextBinding)
                .font(.system(size: 16))
                .focused($isInputFocused)
                .disabled(!viewModel.isInputEnabled)
                .submitLabel(.send)
                .onSubmit(sendMessageIfCan)

            sendButton
        }
        .padding(.leading, 18)
        .padding(.trailing, 10)
        .frame(height: 50)
        .glassEffect(.clear.tint(.white.opacity(0.1)).interactive(), in: Capsule())
        .compositingGroup()
        .shadow(color: Self.lightShadowColor, radius: 12, x: 0, y: 4)
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
                .foregroundStyle(.white)
                .frame(width: 30, height: 30)
                .background(Circle().fill(Self.sendButtonGradient).opacity(viewModel.canSendMessage ? 1 : 0.4))
        }
        .buttonStyle(.plain)
        .disabled(!viewModel.canSendMessage)
    }

    private func sendMessageIfCan() {
        guard viewModel.canSendMessage else { return }
        viewModel.send(.sendMessage)
        isInputFocused = false
    }

    @ViewBuilder
    private func messageRow(for message: ChatMessage) -> some View {
        MessageBubbleView(
            message: message,
            steps: viewModel.pipelineSteps,
            isThinkingExpanded: viewModel.isThinkingCardExpanded(message.id),
            onThinkingToggle: { [weak viewModel] in viewModel?.send(.toggleThinkingCard(message.id)) },
            onExploreFlower: handleExploreFlower,
            hideCompletedThinking: false
        )
    }

    private func handleExploreFlower(_ recommendation: FlowerRecommendation) {
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
}

