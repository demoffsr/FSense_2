import SwiftUI

/// Bottom sheet showing quick scan result with Liquid Glass design
struct QuickInfoCardView: View {
    let result: QuickScanResult
    let capturedImage: UIImage?
    let onRetake: () -> Void
    let onDetails: () -> Void
    let onSelectFlower: (Int) -> Void
    let selectedFlowerIndex: Int

    var body: some View {
        VStack(spacing: 0) {
            // Handle indicator
            Capsule()
                .fill(Color.white.opacity(0.4))
                .frame(width: 40, height: 4)
                .padding(.top, 12)
                .padding(.bottom, 16)

            VStack(spacing: 16) {
                // Primary result
                primaryFlowerSection

                // Additional flowers (bouquet mode)
                if result.hasMultipleFlowers {
                    additionalFlowersSection
                }

                // Action buttons
                actionButtons
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .background(glassBackground)
    }

    // MARK: - Glass Background

    @ViewBuilder
    private var glassBackground: some View {
        if #available(iOS 26, *) {
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
            .fill(.clear)
            .glassEffect(.regular, in: UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            ))
        } else {
            RoundedRectangle(cornerRadius: 24)
                .fill(.ultraThinMaterial)
                .shadow(color: .black.opacity(0.2), radius: 20, y: -5)
        }
    }

    // MARK: - Primary Flower Section

    private var primaryFlowerSection: some View {
        HStack(spacing: 16) {
            // Thumbnail
            thumbnailView

            // Flower info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(result.primaryFlower.name)
                        .font(.title2)
                        .fontWeight(.semibold)
                        .foregroundStyle(.primary)

                    Spacer()

                    // Glass confidence badge
                    confidenceBadge(confidence: result.primaryFlower.confidence)
                }

                if let scientificName = result.primaryFlower.scientificName {
                    Text(scientificName)
                        .font(.subheadline)
                        .italic()
                        .foregroundStyle(.secondary)
                }

                if let color = result.primaryFlower.color {
                    Text(color.capitalized)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    // MARK: - Thumbnail View

    @ViewBuilder
    private var thumbnailView: some View {
        if let image = capturedImage {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 80, height: 80)
                .clipShape(RoundedRectangle(cornerRadius: 12))
        } else {
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.gray.opacity(0.2))
                .frame(width: 80, height: 80)
                .overlay(
                    Image(systemName: "photo")
                        .foregroundStyle(.secondary)
                )
        }
    }

    // MARK: - Confidence Badge

    @ViewBuilder
    private func confidenceBadge(confidence: Double) -> some View {
        let label = "\(Int(confidence * 100))%"

        if #available(iOS 26, *) {
            Text(label)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(confidenceColor(confidence))
                .glassEffect(.regular, in: .capsule)
        } else {
            Text(label)
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
                .padding(.horizontal, 10)
                .padding(.vertical, 5)
                .background(confidenceColor(confidence), in: Capsule())
        }
    }

    // MARK: - Additional Flowers Section

    private var additionalFlowersSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Also detected:")
                .font(.caption)
                .foregroundStyle(.secondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(Array(result.additionalFlowers.enumerated()), id: \.element.id) { index, flower in
                        additionalFlowerButton(flower: flower, index: index)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func additionalFlowerButton(flower: DetectedFlower, index: Int) -> some View {
        let isSelected = selectedFlowerIndex == index + 1

        Button {
            onSelectFlower(index + 1) // +1 because primary is index 0
        } label: {
            VStack(spacing: 4) {
                flowerThumbnail(isSelected: isSelected)

                Text(flower.name)
                    .font(.caption2)
                    .lineLimit(1)
                    .foregroundStyle(.primary)

                Text(flower.confidenceLabel)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            .frame(width: 70)
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func flowerThumbnail(isSelected: Bool) -> some View {
        ZStack {
            if #available(iOS 26, *) {
                Circle()
                    .fill(.clear)
                    .frame(width: 50, height: 50)
                    .glassEffect(isSelected ? .regular.interactive() : .regular, in: .circle)
                    .overlay(
                        Image(systemName: "leaf.fill")
                            .foregroundStyle(.green.opacity(0.7))
                    )
                    .overlay(
                        Circle()
                            .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
                    )
            } else {
                Circle()
                    .fill(Color.gray.opacity(0.1))
                    .frame(width: 50, height: 50)
                    .overlay(
                        Image(systemName: "leaf.fill")
                            .foregroundStyle(.green.opacity(0.7))
                    )
                    .overlay(
                        Circle()
                            .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
                    )
            }
        }
    }

    // MARK: - Action Buttons

    private var actionButtons: some View {
        HStack(spacing: 12) {
            // Retake button (glass style)
            glassButton(title: "Retake", isProminent: false, action: onRetake)

            // Details button (prominent glass style)
            glassButton(title: "Details", isProminent: true, action: onDetails)
        }
    }

    @ViewBuilder
    private func glassButton(title: String, isProminent: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.headline)
                .foregroundStyle(isProminent ? .white : .primary)
                .frame(maxWidth: .infinity)
                .frame(height: 50)
        }
        .buttonStyle(GlassButtonStyle(isProminent: isProminent))
    }

    // MARK: - Helpers

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - Glass Button Style

struct GlassButtonStyle: ButtonStyle {
    let isProminent: Bool

    func makeBody(configuration: Configuration) -> some View {
        if #available(iOS 26, *) {
            configuration.label
                .background(isProminent ? Color.accentColor : Color.clear)
                .glassEffect(
                    isProminent ? .regular.interactive() : .regular.interactive(),
                    in: RoundedRectangle(cornerRadius: 12)
                )
                .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
                .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
        } else {
            configuration.label
                .background(
                    isProminent
                        ? Color.accentColor
                        : Color(.secondarySystemBackground),
                    in: RoundedRectangle(cornerRadius: 12)
                )
                .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
                .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
        }
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        Color.black.ignoresSafeArea()

        VStack {
            Spacer()
            QuickInfoCardView(
                result: QuickScanResult(
                    primaryFlower: DetectedFlower(
                        id: "1",
                        name: "Red Rose",
                        scientificName: "Rosa",
                        confidence: 0.92,
                        color: "red",
                        thumbnailUrl: nil
                    ),
                    additionalFlowers: [
                        DetectedFlower(
                            id: "2",
                            name: "Baby's Breath",
                            scientificName: "Gypsophila",
                            confidence: 0.85,
                            color: "white",
                            thumbnailUrl: nil
                        )
                    ],
                    bouquetDescription: nil,
                    scanMode: "bouquet",
                    requestId: "test-123"
                ),
                capturedImage: nil,
                onRetake: {},
                onDetails: {},
                onSelectFlower: { _ in },
                selectedFlowerIndex: 0
            )
        }
    }
}
