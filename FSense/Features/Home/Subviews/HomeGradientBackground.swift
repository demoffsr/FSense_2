import SwiftUI

// MARK: - Home Gradient Background

/// Multi-color gradient background for header.
/// Includes noise texture overlay and subtle floating animation.

struct HomeGradientBackground: View {
    
    // Animation state
    @State private var animateBlobs = false
    
    // Animation parameters
    private let animationDuration: Double = 3.0
    private let offsetAmount: CGFloat = 35

    // Opacity range for pulsing effect
    private let opacityMin: Double = 0.7
    private let opacityMax: Double = 1.4

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // Layer 1: Color blobs with floating + pulsing animation
                ZStack {
                    // Blob A: Top-left blue
                    Circle()
                        .fill(Color(red: 0, green: 0.11, blue: 0.92))
                        .frame(width: 350, height: 350)
                        .blur(radius: 80)
                        .opacity(animateBlobs ? opacityMax : opacityMin)
                        .scaleEffect(animateBlobs ? 1.1 : 0.95)
                        .position(
                            x: 50 + (animateBlobs ? offsetAmount : -offsetAmount),
                            y: 80 + (animateBlobs ? -offsetAmount * 0.7 : offsetAmount * 0.7)
                        )

                    // Blob B: Top-right purple
                    Circle()
                        .fill(Color(red: 0.55, green: 0, blue: 0.92))
                        .frame(width: 320, height: 320)
                        .blur(radius: 80)
                        .opacity(animateBlobs ? opacityMin : opacityMax)
                        .scaleEffect(animateBlobs ? 0.9 : 1.05)
                        .position(
                            x: geo.size.width - 30 + (animateBlobs ? -offsetAmount * 0.8 : offsetAmount * 0.8),
                            y: 100 + (animateBlobs ? offsetAmount * 0.6 : -offsetAmount * 0.6)
                        )

                    // Blob C: Center-left magenta
                    Circle()
                        .fill(Color(red: 0.91, green: 0, blue: 0.89))
                        .frame(width: 300, height: 300)
                        .blur(radius: 60)
                        .opacity(animateBlobs ? opacityMax * 0.9 : opacityMin * 1.1)
                        .scaleEffect(animateBlobs ? 1.08 : 0.92)
                        .position(
                            x: 80 + (animateBlobs ? -offsetAmount * 0.5 : offsetAmount * 0.5),
                            y: geo.size.height - 80 + (animateBlobs ? offsetAmount * 0.9 : -offsetAmount * 0.9)
                        )

                    // Blob D: Center-right orange
                    Circle()
                        .fill(Color(red: 0.96, green: 0.29, blue: 0.05))
                        .frame(width: 280, height: 280)
                        .blur(radius: 60)
                        .opacity(animateBlobs ? opacityMin * 1.2 : opacityMax)
                        .scaleEffect(animateBlobs ? 0.93 : 1.12)
                        .position(
                            x: geo.size.width - 60 + (animateBlobs ? offsetAmount * 0.6 : -offsetAmount * 0.6),
                            y: geo.size.height - 40 + (animateBlobs ? -offsetAmount * 0.8 : offsetAmount * 0.8)
                        )
                }
                .drawingGroup() // Rasterize blurred circles for better performance

                // Layer 2: Noise texture overlay
                Image("NoiseTexture")
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: geo.size.width, height: geo.size.height)
                    .clipped()
                    .opacity(1)
                    .blendMode(.overlay)
            }
        }
        .onAppear {
            withAnimation(
                .easeInOut(duration: animationDuration)
                .repeatForever(autoreverses: true)
            ) {
                animateBlobs = true
            }
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 0) {
        HomeGradientBackground()
            .frame(height: 400)

        LinearGradient(
            colors: [.white.opacity(0), .white],
            startPoint: .top,
            endPoint: .bottom
        )
        .frame(height: 80)

        Color.white
    }
    .ignoresSafeArea()
}
