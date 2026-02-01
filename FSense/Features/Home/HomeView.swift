import SwiftUI

struct HomeView: View {

    @StateObject private var viewModel = HomeViewModel()
    @StateObject private var chatSheetController = ChatSheetController()
    @StateObject private var chatViewModel = ChatViewModel()

    // HEADER HEIGHT — меняй это значение, высота изменится
    private let headerHeight: CGFloat = 240

    /// Static gradient to avoid recreation on each render
    private static let whiteFadeGradient = LinearGradient(
        colors: [.white.opacity(0), .white],
        startPoint: .top,
        endPoint: .bottom
    )

    // Consolidated chat edit action (replaces 4 separate @State variables)
    @State private var chatEditAction: ChatEditAction?

    /// Chat editing actions - consolidates rename/delete state
    enum ChatEditAction: Identifiable {
        case rename(ChatSession)
        case delete(ChatSession)

        var id: String {
            switch self {
            case .rename(let session): return "rename-\(session.id)"
            case .delete(let session): return "delete-\(session.id)"
            }
        }

        var session: ChatSession {
            switch self {
            case .rename(let session), .delete(let session): return session
            }
        }
    }

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
                        Self.whiteFadeGradient
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
                                    chatEditAction = .rename(session)
                                },
                                onDeleteChat: { session in
                                    chatEditAction = .delete(session)
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
            .navigationDestination(for: HomeNavDestination.self) { destination in
                switch destination {
                case .profile:
                    ProfileView()
                case .search:
                    SearchView()
                case .users:
                    UsersView()
                }
            }
        }
        .onAppear {
            viewModel.send(.onAppear)
        }
        .textFieldAlert(
            isPresented: Binding(
                get: { if case .rename = chatEditAction { return true } else { return false } },
                set: { if !$0 { chatEditAction = nil } }
            ),
            title: "Rename Chat",
            message: "Enter a new name for this chat",
            placeholder: "Chat name",
            initialText: chatEditAction?.session.title ?? "",
            confirmButtonTitle: "Rename"
        ) { newTitle in
            if let action = chatEditAction, case .rename(let session) = action {
                viewModel.send(.renameChat(session, newTitle: newTitle))
            }
            chatEditAction = nil
        }
        .alert(
            "Delete Chat",
            isPresented: Binding(
                get: { if case .delete = chatEditAction { return true } else { return false } },
                set: { if !$0 { chatEditAction = nil } }
            ),
            presenting: chatEditAction
        ) { action in
            Button("Cancel", role: .cancel) { chatEditAction = nil }
            Button("Delete", role: .destructive) {
                viewModel.send(.deleteChat(action.session))
                chatEditAction = nil
            }
        } message: { action in
            Text("Are you sure you want to delete \"\(action.session.title)\"? This action cannot be undone.")
        }
    }
}
