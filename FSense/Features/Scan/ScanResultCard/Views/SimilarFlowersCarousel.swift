import SwiftUI

/// Horizontal carousel of similar flowers
struct SimilarFlowersCarousel: View {
    let flowers: [DetectedFlower]
    let onSelect: (DetectedFlower) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Similar Flowers")
                .font(.headline)

            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(spacing: 12) {
                    ForEach(flowers) { flower in
                        SimilarFlowerCard(flower: flower) {
                            onSelect(flower)
                        }
                    }
                }
            }
        }
    }
}

/// Card for a single similar flower
struct SimilarFlowerCard: View {
    let flower: DetectedFlower
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 8) {
                // Thumbnail or placeholder
                ZStack {
                    RoundedRectangle(cornerRadius: 12)
                        .fill(
                            LinearGradient(
                                colors: [.green.opacity(0.2), .green.opacity(0.4)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )

                    Image(systemName: "leaf.fill")
                        .font(.system(size: 24))
                        .foregroundColor(.green.opacity(0.6))
                }
                .frame(width: 100, height: 100)

                // Name
                VStack(spacing: 2) {
                    Text(flower.name)
                        .font(.subheadline)
                        .fontWeight(.medium)
                        .lineLimit(1)

                    if let scientificName = flower.scientificName {
                        Text(scientificName)
                            .font(.caption)
                            .italic()
                            .foregroundColor(.secondary)
                            .lineLimit(1)
                    }
                }
                .frame(width: 100)
            }
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    SimilarFlowersCarousel(
        flowers: [
            DetectedFlower(
                id: "1",
                name: "Peony",
                scientificName: "Paeonia",
                confidence: 1.0,
                color: "pink",
                thumbnailUrl: nil
            ),
            DetectedFlower(
                id: "2",
                name: "Camellia",
                scientificName: "Camellia japonica",
                confidence: 1.0,
                color: "red",
                thumbnailUrl: nil
            ),
            DetectedFlower(
                id: "3",
                name: "Ranunculus",
                scientificName: "Ranunculus",
                confidence: 1.0,
                color: "white",
                thumbnailUrl: nil
            )
        ],
        onSelect: { _ in }
    )
    .padding()
}
