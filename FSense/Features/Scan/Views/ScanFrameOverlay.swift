import SwiftUI

/// Animated scan frame overlay with corner brackets and Liquid Glass aesthetic
struct ScanFrameOverlay: View {
    @State private var isAnimating = false
    @State private var glowOpacity: Double = 0.3

    let frameSize: CGFloat
    let cornerLength: CGFloat
    let lineWidth: CGFloat
    let color: Color

    init(
        frameSize: CGFloat = 280,
        cornerLength: CGFloat = 40,
        lineWidth: CGFloat = 4,
        color: Color = .white
    ) {
        self.frameSize = frameSize
        self.cornerLength = cornerLength
        self.lineWidth = lineWidth
        self.color = color
    }

    var body: some View {
        ZStack {
            // Subtle glow effect behind brackets
            glowLayer

            // Four corners
            ForEach(0..<4, id: \.self) { index in
                CornerBracket(
                    cornerLength: cornerLength,
                    lineWidth: lineWidth,
                    color: color
                )
                .rotationEffect(.degrees(Double(index) * 90))
            }
        }
        .frame(width: frameSize, height: frameSize)
        .scaleEffect(isAnimating ? 1.02 : 1.0)
        .animation(
            Animation.easeInOut(duration: 1.5).repeatForever(autoreverses: true),
            value: isAnimating
        )
        .onAppear {
            isAnimating = true
            withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
                glowOpacity = 0.6
            }
        }
    }

    // MARK: - Glow Layer

    private var glowLayer: some View {
        RoundedRectangle(cornerRadius: 24)
            .stroke(
                LinearGradient(
                    colors: [
                        color.opacity(glowOpacity * 0.5),
                        color.opacity(glowOpacity * 0.2),
                        color.opacity(glowOpacity * 0.5)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                ),
                lineWidth: 2
            )
            .blur(radius: 8)
            .frame(width: frameSize - 20, height: frameSize - 20)
    }
}

/// Single corner bracket shape with enhanced glass styling
struct CornerBracket: View {
    let cornerLength: CGFloat
    let lineWidth: CGFloat
    let color: Color

    var body: some View {
        ZStack {
            // Main bracket
            bracketPath
                .stroke(color, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))

            // Subtle inner glow
            bracketPath
                .stroke(
                    color.opacity(0.3),
                    style: StrokeStyle(lineWidth: lineWidth + 4, lineCap: .round)
                )
                .blur(radius: 4)
        }
        .frame(width: cornerLength, height: cornerLength)
        .offset(x: -cornerLength, y: -cornerLength)
    }

    private var bracketPath: Path {
        Path { path in
            // Horizontal line
            path.move(to: CGPoint(x: 0, y: lineWidth / 2))
            path.addLine(to: CGPoint(x: cornerLength, y: lineWidth / 2))

            // Vertical line
            path.move(to: CGPoint(x: lineWidth / 2, y: 0))
            path.addLine(to: CGPoint(x: lineWidth / 2, y: cornerLength))
        }
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        Color.black.ignoresSafeArea()
        ScanFrameOverlay()
    }
}
