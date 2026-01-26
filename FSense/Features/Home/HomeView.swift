import SwiftUI

struct HomeView: View {

    @StateObject private var viewModel = HomeViewModel()
    @StateObject private var chatSheetController = ChatSheetController()
    @StateObject private var chatViewModel = ChatViewModel()

    // HEADER HEIGHT — меняй это значение, высота изменится
    private let headerHeight: CGFloat = 240

    // Rename alert state
    @State private var showRenameAlert = false
    @State private var sessionToRename: ChatSession?

    // Delete confirmation alert state
    @State private var showDeleteConfirmation = false
    @State private var sessionToDelete: ChatSession?

    var body: some View {
        NavigationStack {
            GeometryReader { geo in
                let topInset = geo.safeAreaInsets.top

                VStack(spacing: 0) {

                    // ══════════════════════════════════════════════════════════
                    // 1. GRADIENT HEADER — фиксированная высота
                    // ══════════════════════════════════════════════════════════
                    ZStack(alignment: .top) {
                        // Gradient background (blurred blobs)
                        HomeGradientBackground()

                        // Header content
                        VStack(spacing: 12) {
                            HomeHeaderView()
                            MeaningBannerView()
                            ScanCTAView()
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, topInset + 2)
                    }
                    .frame(height: headerHeight + topInset)
                    .overlay(alignment: .bottom) {
                        // ══════════════════════════════════════════════════════════
                        // 2. WHITE FADE — переход (накладывается на низ хедера)
                        // ══════════════════════════════════════════════════════════
                        LinearGradient(
                            colors: [.white.opacity(0), .white],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                        .frame(height: 20)
                    }

                    // ══════════════════════════════════════════════════════════
                    // 3. WHITE CONTENT — заголовок + скролл карточек
                    // ══════════════════════════════════════════════════════════
                    VStack(alignment: .leading, spacing: 12) {
                        // Fixed header (не скроллится)
                        RecentSectionHeaderView(
                            selectedTab: Binding(
                                get: { viewModel.state.selectedTab },
                                set: { viewModel.send(.tabChanged($0)) }
                            ),
                            onSeeAll: {
                                // TODO: Navigate to see all
                            }
                        )
                        .padding(.horizontal, 16)
                        .padding(.top, 16)
                        
                        // Scrollable cards (только карточки скроллятся)
                        ScrollView(showsIndicators: false) {
                            RecentCardsListView(
                                viewModel: viewModel,
                                onChatTapped: { session in
                                    // Open chat with smooth bottom sheet animation
                                    chatSheetController.openChat(session: session)
                                },
                                onRenameChat: { session in
                                    sessionToRename = session
                                    showRenameAlert = true
                                },
                                onDeleteChat: { session in
                                    sessionToDelete = session
                                    showDeleteConfirmation = true
                                }
                            )
                            .padding(.horizontal, 16)
                            .padding(.top, 12)
                            .padding(.bottom, 160)
                        }
                    }
                    .background(Color.white)
                    .clipped()
                }
                .ignoresSafeArea(edges: .top)
                .overlay(alignment: .bottom) {
                    BottomInputBarView(controller: chatSheetController, viewModel: chatViewModel)
                }
                .ignoresSafeArea(.container, edges: .bottom)
            }
            .navigationBarHidden(true)
            .navigationDestination(for: Flower.self) { flower in
                FlowerCardView(flower: flower)
                    .id(flower.id) // Force view recreation on flower change
            }
        }
        .onAppear {
            viewModel.send(.onAppear)
        }
        .textFieldAlert(
            isPresented: $showRenameAlert,
            title: "Rename Chat",
            message: "Enter a new name for this chat",
            placeholder: "Chat name",
            initialText: sessionToRename?.title ?? "",
            confirmButtonTitle: "Rename"
        ) { newTitle in
            if let session = sessionToRename {
                viewModel.send(.renameChat(session, newTitle: newTitle))
            }
        }
        .alert("Delete Chat", isPresented: $showDeleteConfirmation, presenting: sessionToDelete) { session in
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                viewModel.send(.deleteChat(session))
            }
        } message: { session in
            Text("Are you sure you want to delete \"\(session.title)\"? This action cannot be undone.")
        }
    }
}
