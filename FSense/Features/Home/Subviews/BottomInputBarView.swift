import SwiftUI

// MARK: - Chat Sheet Controller

@MainActor
final class ChatSheetController: ObservableObject {
    @Published var isExpanded = false
    @Published var sessionToLoad: ChatSession?

    private let stateManager = ActiveChatStateManager.shared
    private let historyManager = ChatHistoryManager.shared

    /// Open chat - determines whether to restore session, draft, or start fresh
    func openNewChat() {
        let state = stateManager.prepareForSheetOpen()

        switch state {
        case .fresh:
            sessionToLoad = nil
        case .draftOnly:
            // Draft will be restored by ExpandedChatSheet
            sessionToLoad = nil
        case .existingSession(let sessionId, _):
            // Restore existing session
            if let session = historyManager.getSession(by: sessionId) {
                sessionToLoad = session
            } else {
                sessionToLoad = nil
            }
        }

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
    @ObservedObject var viewModel: ChatViewModel
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
                ExpandedChatSheet(controller: controller, viewModel: viewModel)
                    .presentationDetents([.large])
                    .presentationDragIndicator(.visible)
                    .presentationBackgroundInteraction(.enabled)
                    .interactiveDismissDisabled(false)
            }
            .onChange(of: controller.sessionToLoad) { _, newSession in
                if let session = newSession {
                    viewModel.loadSession(session)
                }
                // Don't call reset here - it's handled by onChange(isExpanded)
            }
            .onChange(of: controller.isExpanded) { wasExpanded, isExpanded in
                if isExpanded {
                    // Opening the sheet
                    let state = ActiveChatStateManager.shared.prepareForSheetOpen()

                    switch state {
                    case .fresh:
                        if controller.sessionToLoad == nil && viewModel.needsReset {
                            viewModel.send(.reset)
                        }
                    case .draftOnly(let draftText):
                        // Restore draft text only
                        if viewModel.needsReset {
                            viewModel.send(.reset)
                        }
                        viewModel.inputText = draftText
                    case .existingSession(_, let draftText):
                        // Session is loaded via sessionToLoad, restore draft
                        if !draftText.isEmpty {
                            viewModel.inputText = draftText
                        }
                    }
                } else {
                    // Closing the sheet - save current state
                    ActiveChatStateManager.shared.onSheetClose(
                        currentDraft: viewModel.inputText,
                        currentSessionId: viewModel.currentSessionId
                    )
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

    // Cancellable task for scroll cleanup on disappear
    @State private var scrollTask: Task<Void, Never>?

    // Search state
    @State private var isSearching = false
    @State private var searchText = ""
    @State private var highlightedMessageId: UUID?
    @FocusState private var isSearchFocused: Bool

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
                // Search bar (when active) - padding matches input area style
                if isSearching {
                    ChatSearchBar(
                        searchText: $searchText,
                        isSearching: $isSearching,
                        isFocused: $isSearchFocused
                    )
                    .padding(.top, 24)
                    .padding(.bottom, 12)
                    .background(Color(white: 0.97))
                    .transition(.move(edge: .top).combined(with: .opacity))
                }

                // Messages scroll area
                messagesScrollView

                // Input area - automatically moves with keyboard in native sheet
                if !isSearching {
                    inputArea
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
            .animation(.spring(response: 0.35, dampingFraction: 0.9), value: isSearching)
            .background(Color(white: 0.97))
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    if !isSearching {
                        Text("Chat")
                            .font(.headline)
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    if !isSearching {
                        toolbarButtons
                    }
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
            // Show plus button immediately without animation
            withTransaction(Transaction(animation: nil)) {
                showPlusButton = true
            }
            // Focus immediately - keyboard is pre-warmed via KeyboardWarmer
            isInputFocused = true
        }
        .onDisappear {
            showPlusButton = false
            isSearching = false
            searchText = ""
            // Cancel pending scroll task to prevent updates after view disappears
            scrollTask?.cancel()
        }
        .onChange(of: isSearching) { _, newValue in
            if newValue {
                // Dismiss input keyboard and focus search field
                isInputFocused = false
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                    isSearchFocused = true
                }
            } else {
                // Dismiss search keyboard
                isSearchFocused = false
                // Clear highlight when exiting search
                highlightedMessageId = nil
            }
        }
        .onChange(of: searchText) { _, newText in
            // Scroll to first matching message when search text changes
            guard isSearching, !newText.isEmpty else {
                highlightedMessageId = nil
                return
            }

            // Find first matching message and scroll to it
            if let firstMatch = viewModel.orderedMessages.first(where: { $0.matchesSearch(newText) }) {
                scrollToMessage(firstMatch.id)
            } else {
                highlightedMessageId = nil
            }
        }
    }

    // MARK: - Scroll to Message

    private func scrollToMessage(_ messageId: UUID) {
        guard let proxy = scrollProxy else { return }

        // Highlight the message temporarily
        highlightedMessageId = messageId

        withAnimation(.easeInOut(duration: 0.3)) {
            proxy.scrollTo(messageId, anchor: .center)
        }

        // Remove highlight after 1.5 seconds
        Task { @MainActor in
            try? await Task.sleep(nanoseconds: 1_500_000_000)
            withAnimation(.easeOut(duration: 0.3)) {
                highlightedMessageId = nil
            }
        }
    }

    // MARK: - Messages Scroll View

    private var messagesScrollView: some View {
        ZStack(alignment: .bottom) {
            ScrollViewReader { proxy in
                ScrollView(showsIndicators: false) {
                    LazyVStack(spacing: 16) {
                        // Use cached precomputed data from ViewModel
                        let messages = viewModel.orderedMessages
                        let precomputed = viewModel.precomputedMessageData
                        let steps = viewModel.pipelineSteps

                        // Use indices to avoid Array() allocation - preserves LazyVStack laziness
                        ForEach(messages.indices, id: \.self) { index in
                            let message = messages[index]
                            let data = index < precomputed.count
                                ? precomputed[index]
                                : ChatViewModel.MessageRowData(thinkingId: message.id, hideCompletedThinking: false)

                            MessageBubbleView(
                                message: message,
                                steps: steps,
                                isThinkingExpanded: viewModel.isThinkingCardExpanded(data.thinkingId),
                                onThinkingToggle: { [weak viewModel] in
                                    viewModel?.send(.toggleThinkingCard(data.thinkingId))
                                },
                                onExploreFlower: handleExploreFlower,
                                hideCompletedThinking: data.hideCompletedThinking
                            )
                            .searchHighlight(
                                isHighlighted: highlightedMessageId == message.id,
                                isSearchActive: isSearching && !searchText.isEmpty,
                                matchesSearch: message.matchesSearch(searchText)
                            )
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
                    // Cancel previous scroll task if pending
                    scrollTask?.cancel()
                    scrollTask = Task { @MainActor in
                        try? await Task.sleep(nanoseconds: 100_000_000)
                        guard !Task.isCancelled else { return }
                        proxy.scrollTo(bottomID, anchor: .bottom)
                        showScrollToBottom = false
                    }
                }
                .onTapGesture {
                    isInputFocused = false
                }
            }

            // Floating scroll-to-bottom button (only when scrolled up and not searching)
            if showScrollToBottom && !isSearching {
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
                        withAnimation(.spring(response: 0.4, dampingFraction: 0.85)) {
                            isInputFocused = false
                            isSearching = true
                        }
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

    /// Direct binding to viewModel.inputText - no action dispatch per keystroke
    private var inputTextBinding: Binding<String> {
        Binding(
            get: { viewModel.inputText },
            set: { viewModel.inputText = $0 }
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

