import SwiftUI

/// Container view that switches content based on selected segment
/// Delegates to specific segment views without containing layout logic
struct FlowerSegmentContentView: View {

    let segment: FlowerCardSegment
    let meaningData: MeaningSegmentData?
    let giftingData: GiftingInfo?
    let contextData: ContextInfo?
    let alternatives: [AlternativeFlower]
    var onAlternativeTap: ((AlternativeFlower) -> Void)?

    var body: some View {
        Group {
            switch segment {
            case .meaning:
                if let data = meaningData {
                    FlowerMeaningView(
                        data: data,
                        alternatives: alternatives,
                        onAlternativeTap: onAlternativeTap
                    )
                } else {
                    emptyState(for: segment)
                }
                
            case .gifting:
                if let data = giftingData {
                    FlowerGiftingView(data: data)
                } else {
                    emptyState(for: segment)
                }
                
            case .context:
                if let data = contextData {
                    FlowerContextView(data: data)
                } else {
                    emptyState(for: segment)
                }
            }
        }
        .transition(.opacity.combined(with: .move(edge: .trailing)))
        .animation(.easeInOut(duration: 0.2), value: segment)
    }
    
    // MARK: - Empty State
    
    private func emptyState(for segment: FlowerCardSegment) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "doc.text")
                .font(.system(size: 32))
                .foregroundColor(.secondary.opacity(0.5))
            
            Text("No \(segment.rawValue.lowercased()) information available")
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 48)
    }
}

// MARK: - Preview

#Preview {
    ScrollView {
        FlowerSegmentContentView(
            segment: .meaning,
            meaningData: MeaningSegmentData(
                whyThisFlowerText: "This flower is traditionally given when one wants to express apology.",
                symbolismText: "In Western cultures, associated with romantic love.",
                meanings: ["Love", "Passion", "Romance"],
                moodIntensityValue: 0.85,
                moodIntensityLevel: .veryHigh
            ),
            giftingData: .mock,
            contextData: .mock,
            alternatives: AlternativeFlower.mocks
        ) { flower in
            print("Tapped: \(flower.name)")
        }
        .padding()
    }
    .background(Color(.systemGray6))
}
