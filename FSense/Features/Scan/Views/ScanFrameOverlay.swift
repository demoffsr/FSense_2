import SwiftUI

/// Modern scan frame overlay with dimmed surroundings
/// Clean frame without corner brackets, lifted up for better ergonomics
struct ScanFrameOverlay: View {
    @State private var pulseOpacity: Double = 0.4

    // Frame dimensions
    let frameWidth: CGFloat
    let frameHeight: CGFloat
    let cornerRadius: CGFloat = 24
    let borderWidth: CGFloat = 2
    let verticalOffset: CGFloat // Negative = move up

    init(
        frameWidth: CGFloat = 290,
        frameHeight: CGFloat = 358,
        verticalOffset: CGFloat = -60 // Raised up by default
    ) {
        self.frameWidth = frameWidth
        self.frameHeight = frameHeight
        self.verticalOffset = verticalOffset
    }

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Dimmed overlay with cutout
                dimmedOverlay(in: geometry.size)

                // Frame border
                frameBorder
                    .offset(y: verticalOffset)
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
                pulseOpacity = 0.7
            }
        }
    }

    // MARK: - Dimmed Overlay with Cutout

    private func dimmedOverlay(in size: CGSize) -> some View {
        let centerX = size.width / 2
        let centerY = size.height / 2 + verticalOffset

        return Rectangle()
            .fill(Color.black.opacity(0.5))
            .mask(
                Canvas { context, canvasSize in
                    // Fill entire canvas
                    context.fill(
                        Path(CGRect(origin: .zero, size: canvasSize)),
                        with: .color(.white)
                    )

                    // Cut out the scan area
                    let cutoutRect = CGRect(
                        x: centerX - frameWidth / 2,
                        y: centerY - frameHeight / 2,
                        width: frameWidth,
                        height: frameHeight
                    )
                    let cutoutPath = Path(roundedRect: cutoutRect, cornerRadius: cornerRadius)

                    context.blendMode = .destinationOut
                    context.fill(cutoutPath, with: .color(.white))
                }
            )
            .ignoresSafeArea()
    }

    // MARK: - Frame Border

    private var frameBorder: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .stroke(
                .white.opacity(pulseOpacity),
                lineWidth: borderWidth
            )
            .frame(width: frameWidth, height: frameHeight)
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        // Simulate camera feed
        LinearGradient(
            colors: [.green.opacity(0.6), .blue.opacity(0.4)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()

        ScanFrameOverlay()
    }
}
