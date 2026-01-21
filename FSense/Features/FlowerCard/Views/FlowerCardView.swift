import SwiftUI

struct FlowerCardView: View {
    
    @StateObject private var viewModel: FlowerCardViewModel
    @Environment(\.dismiss) private var dismiss
    
    @State private var scrollOffset: CGFloat = 0
    
    private let heroHeight: CGFloat = 360
    private let toolbarThreshold: CGFloat = 250
    
    private var showOverlayToolbar: Bool {
        scrollOffset > toolbarThreshold
    }
    
    init(flower: Flower) {
        _viewModel = StateObject(wrappedValue: FlowerCardViewModel(flower: flower))
    }
    
    var body: some View {
        ZStack(alignment: .top) {
            // MARK: - Scrollable Content
            ScrollView(showsIndicators: false) {
                VStack(spacing: 0) {
                    // Anchor for tracking
                    Color.clear
                        .frame(height: 0)
                        .id("top")
                    
                    heroSection
                    contentSection
                }
                .background(
                    GeometryReader { proxy in
                        let offset = -proxy.frame(in: .global).minY
                        Color.clear
                            .onChange(of: offset) { _, newValue in
                                scrollOffset = newValue
                            }
                            .onAppear {
                                scrollOffset = offset
                            }
                    }
                )
            }
            
            // MARK: - Back Button on Hero
            backButtonOverlay
            
            // MARK: - Overlay Toolbar
            overlayToolbar
            
            // MARK: - Bottom CTA
            VStack {
                Spacer()
                FlowerCardCTAView(
                    isProcessing: viewModel.isAIProcessing,
                    onTap: { viewModel.send(.askAITapped) }
                )
            }
        }
        .ignoresSafeArea(edges: .top)
        .navigationBarHidden(true)
        .navigationDestination(isPresented: Binding(
            get: { viewModel.state.shouldNavigateToBouquetRecommendations },
            set: { if !$0 { viewModel.send(.dismissBouquetRecommendations) } }
        )) {
            BouquetRecommendationsPlaceholderView()
        }
        .onAppear { viewModel.send(.onAppear) }
        .onDisappear { viewModel.send(.onDisappear) }
    }
    
    // MARK: - Hero Section
    
    private var heroSection: some View {
        ZStack(alignment: .bottom) {
            if let imageAsset = viewModel.flower?.imageAsset {
                Image(imageAsset)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(height: heroHeight)
                    .clipped()
            } else {
                Rectangle()
                    .fill(Color(.systemGray4))
                    .frame(height: heroHeight)
            }
            
            LinearGradient(
                colors: [.black.opacity(0.3), .clear, .black.opacity(0.7)],
                startPoint: .top,
                endPoint: .bottom
            )
            
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
    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "sparkles")
                .font(.system(size: 48))
                .foregroundColor(.purple.opacity(0.6))
            
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
