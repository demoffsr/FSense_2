import SwiftUI

/// Full detail view for a scanned flower
struct ScanResultCardView: View {
    let result: ScanDetailResult
    let capturedImage: UIImage?
    let onDismiss: () -> Void
    let onAskAI: (String) -> Void

    @State private var scrollOffset: CGFloat = 0

    var body: some View {
        ZStack(alignment: .top) {
            // Background
            Color(.systemBackground)
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 0) {
                    // Hero section
                    ScanResultHeroView(
                        name: result.header.name,
                        scientificName: result.header.scientificName,
                        capturedImage: capturedImage,
                        scrollOffset: scrollOffset
                    )

                    // Content sections
                    VStack(spacing: 24) {
                        // Confidence banner
                        ConfidenceBanner(confidence: result.header.confidence)

                        // Botanical info
                        BotanicalInfoSection(info: result.botanical)

                        // Meanings
                        MeaningsSection(meanings: result.meanings)

                        // Care info
                        CareInfoSection(info: result.care)

                        // Similar flowers
                        if !result.similarFlowers.isEmpty {
                            SimilarFlowersCarousel(
                                flowers: result.similarFlowers,
                                onSelect: { _ in }
                            )
                        }

                        // Ask AI CTA
                        if result.askAi.enabled {
                            AskAICTASection(
                                suggestedQuestions: result.askAi.suggestedQuestions,
                                onAsk: onAskAI
                            )
                        }

                        // Bottom spacer
                        Spacer().frame(height: 80)
                    }
                    .padding(.horizontal, 20)
                    .padding(.top, 20)
                }
                .background(
                    GeometryReader { geometry in
                        Color.clear.preference(
                            key: ScrollOffsetKey.self,
                            value: geometry.frame(in: .named("scroll")).minY
                        )
                    }
                )
            }
            .coordinateSpace(name: "scroll")
            .onPreferenceChange(ScrollOffsetKey.self) { value in
                scrollOffset = value
            }

            // Floating header
            floatingHeader
        }
    }

    // MARK: - Floating Header

    private var floatingHeader: some View {
        HStack {
            Button(action: onDismiss) {
                Image(systemName: "xmark")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.primary)
                    .frame(width: 36, height: 36)
                    .background(.ultraThinMaterial)
                    .clipShape(Circle())
            }

            Spacer()

            // Show title when scrolled
            if scrollOffset < -200 {
                Text(result.header.name)
                    .font(.headline)
                    .transition(.opacity)
            }

            Spacer()

            Button {
                // Share action
            } label: {
                Image(systemName: "square.and.arrow.up")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.primary)
                    .frame(width: 36, height: 36)
                    .background(.ultraThinMaterial)
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .animation(.easeInOut(duration: 0.2), value: scrollOffset < -200)
    }
}

// MARK: - Scroll Offset Key

private struct ScrollOffsetKey: PreferenceKey {
    nonisolated(unsafe) static var defaultValue: CGFloat = 0
    static func reduce(value: inout CGFloat, nextValue: () -> CGFloat) {
        value = nextValue()
    }
}

// MARK: - Ask AI CTA Section

struct AskAICTASection: View {
    let suggestedQuestions: [String]
    let onAsk: (String) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Ask AI")
                .font(.headline)

            VStack(spacing: 12) {
                ForEach(suggestedQuestions.prefix(3), id: \.self) { question in
                    Button {
                        onAsk(question)
                    } label: {
                        HStack {
                            Text(question)
                                .font(.subheadline)
                                .foregroundColor(.primary)
                                .multilineTextAlignment(.leading)

                            Spacer()

                            Image(systemName: "arrow.right")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .padding(16)
                        .background(Color(.secondarySystemBackground))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    ScanResultCardView(
        result: ScanDetailResult(
            header: ScanResultHeader(
                flowerId: "rose_001",
                name: "Red Rose",
                scientificName: "Rosa",
                confidence: 0.92,
                imageUrl: nil
            ),
            botanical: BotanicalInfo(
                family: "Rosaceae",
                nativeRegions: ["Europe", "Asia"],
                bloomSeasons: ["Spring", "Summer"],
                lifespan: "Perennial"
            ),
            meanings: ["Love", "Beauty", "Passion"],
            care: CareInfo(
                difficulty: .moderate,
                light: .fullSun,
                water: .moderate,
                temperatureRange: "15-25°C",
                humidity: "Medium",
                tips: ["Prune in spring", "Water at base"]
            ),
            similarFlowers: [],
            askAi: ScanAskAIMetadata(
                enabled: true,
                suggestedQuestions: ["How do I care for roses?", "When should I prune?"]
            ),
            requestId: "test",
            pipelineVersion: "1.0"
        ),
        capturedImage: nil,
        onDismiss: {},
        onAskAI: { _ in }
    )
}
