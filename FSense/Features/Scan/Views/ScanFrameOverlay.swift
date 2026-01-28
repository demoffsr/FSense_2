import SwiftUI

/// Modern scan frame overlay matching Figma specs
/// 290×358px frame with corner brackets inside
struct ScanFrameOverlay: View {
    @State private var isAnimating = false
    @State private var pulseOpacity: Double = 0.5

    // Figma specs
    let frameWidth: CGFloat
    let frameHeight: CGFloat
    let cornerRadius: CGFloat = 24
    let borderWidth: CGFloat = 2

    init(
        frameWidth: CGFloat = 290,
        frameHeight: CGFloat = 358
    ) {
        self.frameWidth = frameWidth
        self.frameHeight = frameHeight
    }

    var body: some View {
        ZStack {
            // Main frame with background and border
            frameBackground

            // Corner brackets inside the frame
            cornerBrackets
        }
        .frame(width: frameWidth, height: frameHeight)
        .onAppear {
            withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
                pulseOpacity = 0.8
                isAnimating = true
            }
        }
    }

    // MARK: - Frame Background

    private var frameBackground: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(.white.opacity(0.1)) // rgba(255,255,255,0.1)
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(
                        .white.opacity(pulseOpacity * 0.625), // Animates between 0.31-0.5 (targeting ~0.5)
                        lineWidth: borderWidth
                    )
            )
            .scaleEffect(isAnimating ? 1.003 : 1.0)
    }

    // MARK: - Corner Brackets

    private var cornerBrackets: some View {
        GeometryReader { geo in
            let bracketSize: CGFloat = 40 // Bracket arm length
            let offset: CGFloat = 16 // Distance from frame edge

            // Top-left
            CornerBracket()
                .frame(width: bracketSize, height: bracketSize)
                .position(x: offset + bracketSize/2, y: offset + bracketSize/2)

            // Top-right
            CornerBracket()
                .rotationEffect(.degrees(90))
                .frame(width: bracketSize, height: bracketSize)
                .position(x: geo.size.width - offset - bracketSize/2, y: offset + bracketSize/2)

            // Bottom-right
            CornerBracket()
                .rotationEffect(.degrees(180))
                .frame(width: bracketSize, height: bracketSize)
                .position(x: geo.size.width - offset - bracketSize/2, y: geo.size.height - offset - bracketSize/2)

            // Bottom-left
            CornerBracket()
                .rotationEffect(.degrees(270))
                .frame(width: bracketSize, height: bracketSize)
                .position(x: offset + bracketSize/2, y: geo.size.height - offset - bracketSize/2)
        }
    }
}

// MARK: - Corner Bracket

struct CornerBracket: View {
    var body: some View {
        Canvas { context, size in
            let lineWidth: CGFloat = 2
            let cornerRadius: CGFloat = 6

            var path = Path()

            // Vertical line (going down from top-left corner)
            path.move(to: CGPoint(x: lineWidth/2, y: size.height))
            path.addLine(to: CGPoint(x: lineWidth/2, y: cornerRadius))

            // Curved corner
            path.addQuadCurve(
                to: CGPoint(x: cornerRadius, y: lineWidth/2),
                control: CGPoint(x: lineWidth/2, y: lineWidth/2)
            )

            // Horizontal line (going right)
            path.addLine(to: CGPoint(x: size.width, y: lineWidth/2))

            context.stroke(
                path,
                with: .color(.white),
                style: StrokeStyle(lineWidth: lineWidth, lineCap: .round, lineJoin: .round)
            )
        }
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        LinearGradient(
            colors: [.black, .gray.opacity(0.3)],
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()

        ScanFrameOverlay()
    }
}
