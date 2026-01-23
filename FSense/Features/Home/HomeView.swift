import SwiftUI

struct HomeView: View {

    @StateObject private var viewModel = HomeViewModel()
    @StateObject private var chatSheetController = ChatSheetController()

    // HEADER HEIGHT — меняй это значение, высота изменится
    private let headerHeight: CGFloat = 240

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
                        VStack(spacing: 16) {
                            HomeHeaderView()
                            MeaningBannerView()
                            ScanCTAView()
                        }
                        .padding(.horizontal, 16)
                        .padding(.top, topInset + 8)
                    }
                    .frame(height: headerHeight + topInset)

                    // ══════════════════════════════════════════════════════════
                    // 2. WHITE FADE — переход
                    // ══════════════════════════════════════════════════════════
                    LinearGradient(
                        stops: [
                            .init(color: .white.opacity(0), location: 0.12),
                            .init(color: .white, location: 0.36)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                    .frame(height: 32)

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
                        
                        // Scrollable cards (только карточки скроллятся)
                        ScrollView(showsIndicators: false) {
                            RecentCardsListView(
                                viewModel: viewModel,
                                onChatTapped: { session in
                                    // Open chat with smooth bottom sheet animation
                                    chatSheetController.openChat(session: session)
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
                    BottomInputBarView(controller: chatSheetController)
                }
                .ignoresSafeArea(.container, edges: .bottom)
            }
            .navigationBarHidden(true)
            .navigationDestination(for: Flower.self) { flower in
                FlowerCardView(flower: flower)
                    .id(flower.name) // Force view recreation on flower change
            }
        }
        .onAppear {
            viewModel.send(.onAppear)
        }
    }
}
