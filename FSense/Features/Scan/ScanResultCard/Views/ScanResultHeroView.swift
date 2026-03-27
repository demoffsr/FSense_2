import SwiftUI

/// Hero section with image, gradient, and title overlay
struct ScanResultHeroView: View {
    let name: String
    let scientificName: String?
    let capturedImage: UIImage?
    let scrollOffset: CGFloat

    private let heroHeight: CGFloat = 350

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .bottomLeading) {
                // Image
                imageLayer
                    .frame(
                        width: geometry.size.width,
                        height: stretchedHeight(geometry)
                    )
                    .clipped()
                    .offset(y: scrollOffset > 0 ? -scrollOffset : 0)

                // Gradient overlay
                LinearGradient(
                    gradient: Gradient(colors: [
                        .clear,
                        .clear,
                        Color(.systemBackground).opacity(0.3),
                        Color(.systemBackground).opacity(0.8),
                        Color(.systemBackground)
                    ]),
                    startPoint: .top,
                    endPoint: .bottom
                )

                // Title overlay
                titleOverlay
                    .padding(.horizontal, 20)
                    .padding(.bottom, 20)
            }
        }
        .frame(height: heroHeight)
    }

    // MARK: - Image Layer

    @ViewBuilder
    private var imageLayer: some View {
        if let image = capturedImage {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fill)
        } else {
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [.green.opacity(0.3), .green.opacity(0.6)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .overlay(
                    Image(systemName: "leaf.fill")
                        .font(.system(size: 60))
                        .foregroundColor(.white.opacity(0.5))
                )
        }
    }

    // MARK: - Title Overlay

    private var titleOverlay: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(name)
                .font(.largeTitle)
                .fontWeight(.bold)
                .foregroundColor(.primary)

            if let scientificName = scientificName {
                Text(scientificName)
                    .font(.title3)
                    .italic()
                    .foregroundColor(.secondary)
            }
        }
    }

    // MARK: - Helpers

    private func stretchedHeight(_ geometry: GeometryProxy) -> CGFloat {
        if scrollOffset > 0 {
            return heroHeight + scrollOffset
        }
        return heroHeight
    }
}

// MARK: - Preview

#Preview {
    ScrollView {
        ScanResultHeroView(
            name: "Red Rose",
            scientificName: "Rosa",
            capturedImage: nil,
            scrollOffset: 0
        )
    }
}
