import SwiftUI

/// Single alternative flower preview cell.
/// Displays flower image, name, and confidence percentage.
struct AlternativeFlowerCell: View {
    let flower: AlternativeFlower
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 8) {
                // Flower image
                AsyncFlowerImageView(
                    imageUrl: flower.imageUrl,
                    imageAsset: flower.imageAsset,
                    cacheKey: nil
                )
                .frame(width: 80, height: 80)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                )

                // Flower name
                Text(flower.name)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.primary)

                // Confidence percentage
                Text(flower.confidenceText)
                    .font(.caption2)
                    .fontWeight(.semibold)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 2)
                    .background(
                        Capsule()
                            .fill(Color.gray.opacity(0.1))
                    )
            }
            .frame(width: 90)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    HStack(spacing: 16) {
        ForEach(AlternativeFlower.mocks.prefix(3)) { flower in
            AlternativeFlowerCell(flower: flower) {
                print("Tapped: \(flower.name)")
            }
        }
    }
    .padding()
}
