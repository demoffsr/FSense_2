import SwiftUI

struct FlowerCardView: View {

    // MARK: - Environment

    @Environment(\.dismiss) private var dismiss
    @Environment(\.themeAccent) private var themeAccent

    // MARK: - State

    @StateObject private var viewModel: FlowerCardViewModel
    @State private var showOverlayToolbar = false

    // MARK: - Constants

    private let heroHeight: CGFloat = 360
    private let toolbarThreshold: CGFloat = 250

    // MARK: - Static Properties (cached to avoid recreation)

    private static let heroGradient = LinearGradient(
        colors: [.black.opacity(0.3), .clear, .black.opacity(0.7)],
        startPoint: .top,
        endPoint: .bottom
    )
    
    init(flower: Flower) {
        _viewModel = StateObject(wrappedValue: FlowerCardViewModel(flower: flower))
    }
    
    var body: some View {
        ZStack(alignment: .top) {
            // MARK: - Scrollable Content
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    heroSection
                    contentSection
                }
            }
            .onScrollGeometryChange(for: Bool.self) { geometry in
                geometry.contentOffset.y > toolbarThreshold
            } action: { _, newValue in
                showOverlayToolbar = newValue
            }
            
            // MARK: - Back Button on Hero
            backButtonOverlay
            
            // MARK: - Overlay Toolbar
            overlayToolbar
            
            // MARK: - Bottom CTA
            VStack {
                Spacer()
                FlowerCardCTAView(
                    isProcessing: viewModel.isSearchingProducts,
                    hasProducts: !viewModel.flowerProducts.isEmpty,
                    onTap: { viewModel.send(.findFlowersTapped) }
                )
            }
        }
        .ignoresSafeArea(edges: .top)
        .navigationBarHidden(true)
        .sheet(isPresented: Binding(
            get: { viewModel.state.shouldNavigateToFlowerProducts },
            set: { if !$0 { viewModel.send(.dismissFlowerProducts) } }
        )) {
            FlowerProductsSheet(
                products: viewModel.flowerProducts,
                flowerName: viewModel.flower?.name ?? "Flowers",
                cachedAt: viewModel.productsCachedAt,
                isRefreshing: viewModel.isSearchingProducts,
                isPresented: Binding(
                    get: { viewModel.state.shouldNavigateToFlowerProducts },
                    set: { if !$0 { viewModel.send(.dismissFlowerProducts) } }
                ),
                onRefresh: { viewModel.send(.refreshFlowerProducts) }
            )
        }
        .onAppear { viewModel.send(.onAppear) }
        .onDisappear { viewModel.send(.onDisappear) }
    }
    
    // MARK: - Hero Section
    
    private var heroSection: some View {
        ZStack(alignment: .bottom) {
            AsyncFlowerImageView(
                imageUrl: viewModel.flower?.imageURL?.absoluteString,
                imageAsset: viewModel.flower?.imageAsset,
                cacheKey: viewModel.flower?.imageCacheKey
            )
            .frame(height: heroHeight)
            .clipped()

            Self.heroGradient
            
            HStack {
                Text(viewModel.flower?.name ?? "Flower")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundColor(.white)
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 24)
        }
        .frame(height: heroHeight)
    }
    
    // MARK: - Back Button Overlay (on Hero)
    
    private var backButtonOverlay: some View {
        VStack {
            HStack {
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.white)
                        .frame(width: 40, height: 40)
                        .contentShape(Circle())
                        .glassEffect(.clear.tint(.black.opacity(0.12)).interactive(), in: .circle)
                }
                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.top, 54)
            Spacer()
        }
        .opacity(showOverlayToolbar ? 0 : 1)
        .animation(.easeInOut(duration: 0.2), value: showOverlayToolbar)
        .allowsHitTesting(!showOverlayToolbar)
    }
    
    // MARK: - Overlay Toolbar
    
    private var overlayToolbar: some View {
        VStack {
            VStack(spacing: 0) {
                Spacer().frame(height: 50)
                
                HStack(spacing: 12) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.primary)
                            .frame(width: 40, height: 40)
                            .contentShape(Circle())
                            .glassEffect(.clear.tint(.black.opacity(0.08)).interactive(), in: .circle)
                    }
                    
                    Text(viewModel.flower?.name ?? "")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.primary)
                    
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
            }
            .background(.ultraThinMaterial)
            
            Spacer()
        }
        .opacity(showOverlayToolbar ? 1 : 0)
        .offset(y: showOverlayToolbar ? 0 : -20)
        .animation(.easeInOut(duration: 0.2), value: showOverlayToolbar)
        .allowsHitTesting(showOverlayToolbar)
    }
    
    // MARK: - Content Section
    
    private var contentSection: some View {
        VStack(spacing: 0) {
            FlowerSegmentedControl(
                selectedSegment: Binding(
                    get: { viewModel.selectedSegment },
                    set: { viewModel.send(.selectSegment($0)) }
                )
            )
            .padding(.horizontal, 16)
            .padding(.top, 24)
            
            FlowerSegmentContentView(
                segment: viewModel.selectedSegment,
                meaningData: viewModel.meaningData,
                giftingData: viewModel.giftingData,
                contextData: viewModel.contextData
            )
            .padding(.horizontal, 16)
            .padding(.top, 20)
            .padding(.bottom, 120)
        }
        .background(Color(.systemBackground))
    }
}

// MARK: - Press Button Style

struct PressButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.9 : 1.0)
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

// MARK: - Placeholder

struct BouquetRecommendationsPlaceholderView: View {
    @Environment(\.themeAccent) private var themeAccent

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "sparkles")
                .font(.system(size: 48))
                .foregroundColor(themeAccent.opacity(0.6))
            
            Text("Bouquet Recommendations")
                .font(.title2)
                .fontWeight(.semibold)
            
            Text("AI-powered suggestions coming soon")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }
}

#Preview {
    NavigationStack {
        FlowerCardView(flower: .mock)
    }
}
