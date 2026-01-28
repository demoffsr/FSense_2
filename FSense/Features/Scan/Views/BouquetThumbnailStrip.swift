import SwiftUI

/// Horizontal strip of bouquet flower thumbnails for multi-scan mode
struct BouquetThumbnailStrip: View {
    let flowers: [DetectedFlower]
    let selectedIndex: Int
    let onSelect: (Int) -> Void

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(spacing: 12) {
                ForEach(Array(flowers.enumerated()), id: \.element.id) { index, flower in
                    BouquetThumbnail(
                        flower: flower,
                        isSelected: index == selectedIndex,
                        isPrimary: index == 0
                    ) {
                        onSelect(index)
                    }
                }
            }
            .padding(.horizontal, 20)
        }
    }
}

/// Single bouquet flower thumbnail
struct BouquetThumbnail: View {
    let flower: DetectedFlower
    let isSelected: Bool
    let isPrimary: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 6) {
                // Thumbnail
                ZStack {
                    Circle()
                        .fill(
                            LinearGradient(
                                colors: [.green.opacity(0.2), .green.opacity(0.4)],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 60, height: 60)

                    Image(systemName: "leaf.fill")
                        .font(.system(size: 20))
                        .foregroundColor(.green.opacity(0.7))

                    // Primary badge
                    if isPrimary {
                        VStack {
                            Spacer()
                            HStack {
                                Spacer()
                                Image(systemName: "star.fill")
                                    .font(.system(size: 10))
                                    .foregroundColor(.yellow)
                                    .padding(3)
                                    .background(Color.black.opacity(0.6))
                                    .clipShape(Circle())
                            }
                        }
                        .frame(width: 60, height: 60)
                    }
                }
                .overlay(
                    Circle()
                        .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 3)
                )

                // Name
                Text(flower.name)
                    .font(.caption2)
                    .fontWeight(isSelected ? .semibold : .regular)
                    .foregroundColor(isSelected ? .primary : .secondary)
                    .lineLimit(1)

                // Confidence
                Text(flower.confidenceLabel)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            .frame(width: 70)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    VStack {
        BouquetThumbnailStrip(
            flowers: [
                DetectedFlower(
                    id: "1",
                    name: "Red Rose",
                    scientificName: "Rosa",
                    confidence: 0.92,
                    color: "red",
                    thumbnailUrl: nil
                ),
                DetectedFlower(
                    id: "2",
                    name: "Baby's Breath",
                    scientificName: "Gypsophila",
                    confidence: 0.85,
                    color: "white",
                    thumbnailUrl: nil
                ),
                DetectedFlower(
                    id: "3",
                    name: "Eucalyptus",
                    scientificName: "Eucalyptus",
                    confidence: 0.78,
                    color: "green",
                    thumbnailUrl: nil
                )
            ],
            selectedIndex: 0,
            onSelect: { _ in }
        )
    }
    .padding(.vertical)
    .background(Color(.systemBackground))
}
