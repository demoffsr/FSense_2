import SwiftUI

/// Animated shimmer overlay for loading states
/// Shows a sweeping gradient animation to indicate content is loading
struct ShimmerView: View {

    @State private var phase: CGFloat = -0.5

    var body: some View {
        GeometryReader { geometry in
            LinearGradient(
                stops: [
                    .init(color: .clear, location: 0),
                    .init(color: .white.opacity(0.4), location: 0.5),
                    .init(color: .clear, location: 1.0)
                ],
                startPoint: UnitPoint(x: phase - 0.3, y: 0.5),
                endPoint: UnitPoint(x: phase + 0.3, y: 0.5)
            )
            .frame(width: geometry.size.width, height: geometry.size.height)
        }
        .onAppear {
            withAnimation(
                .linear(duration: 1.5)
                .repeatForever(autoreverses: false)
            ) {
                phase = 1.5
            }
        }
    }
}

/// View modifier for adding shimmer effect
struct ShimmerModifier: ViewModifier {

    let isActive: Bool

    func body(content: Content) -> some View {
        content
            .overlay {
                if isActive {
                    ShimmerView()
                }
            }
    }
}

extension View {
    /// Adds a shimmer loading animation overlay
    /// - Parameter isActive: Whether the shimmer should be visible
    func shimmer(isActive: Bool) -> some View {
        modifier(ShimmerModifier(isActive: isActive))
    }
}

#Preview {
    VStack(spacing: 20) {
        // Preview of shimmer over placeholder
        RoundedRectangle(cornerRadius: 12)
            .fill(Color.gray.opacity(0.2))
            .frame(width: 200, height: 200)
            .shimmer(isActive: true)

        // Preview of shimmer over image
        Image(systemName: "photo")
            .resizable()
            .aspectRatio(contentMode: .fit)
            .frame(width: 200, height: 200)
            .background(Color.gray.opacity(0.2))
            .shimmer(isActive: true)
    }
    .padding()
}
