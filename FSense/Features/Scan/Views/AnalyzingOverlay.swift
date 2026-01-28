import SwiftUI

/// Overlay shown while analyzing the captured image with Liquid Glass design
struct AnalyzingOverlay: View {
    @State private var rotation: Double = 0
    @State private var pulseScale: Double = 1.0

    var body: some View {
        ZStack {
            // Semi-transparent background (reduced opacity for glass integration)
            Color.black.opacity(0.5)
                .ignoresSafeArea()

            VStack(spacing: 24) {
                // Glass-style animated spinner
                glassSpinner

                // Glass status pill
                statusPill
            }
        }
        .onAppear {
            startAnimations()
        }
    }

    // MARK: - Glass Spinner

    private var glassSpinner: some View {
        ZStack {
            // Outer pulsing ring
            Circle()
                .stroke(Color.white.opacity(0.1), lineWidth: 3)
                .frame(width: 88, height: 88)
                .scaleEffect(pulseScale)

            // Glass-style rotating ring
            Circle()
                .strokeBorder(
                    AngularGradient(
                        gradient: Gradient(colors: [
                            .clear,
                            .white.opacity(0.2),
                            .white.opacity(0.6),
                            .white.opacity(0.9)
                        ]),
                        center: .center,
                        startAngle: .degrees(0),
                        endAngle: .degrees(360)
                    ),
                    lineWidth: 4
                )
                .frame(width: 80, height: 80)
                .rotationEffect(.degrees(rotation))

            // Inner glass circle with icon
            innerIconCircle
        }
    }

    @ViewBuilder
    private var innerIconCircle: some View {
        if #available(iOS 26, *) {
            Image(systemName: "camera.metering.spot")
                .font(.system(size: 28, weight: .medium))
                .foregroundStyle(.white)
                .frame(width: 56, height: 56)
                .glassEffect(.regular, in: .circle)
        } else {
            Image(systemName: "camera.metering.spot")
                .font(.system(size: 28, weight: .medium))
                .foregroundStyle(.white)
                .frame(width: 56, height: 56)
                .background(.ultraThinMaterial, in: Circle())
        }
    }

    // MARK: - Status Pill

    @ViewBuilder
    private var statusPill: some View {
        if #available(iOS 26, *) {
            statusContent
                .glassEffect(.regular, in: .capsule)
        } else {
            statusContent
                .background(.ultraThinMaterial, in: Capsule())
        }
    }

    private var statusContent: some View {
        VStack(spacing: 4) {
            Text("Analyzing...")
                .font(.headline)
                .foregroundStyle(.white)

            Text("Identifying your flower")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.7))
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
    }

    // MARK: - Animations

    private func startAnimations() {
        // Rotating spinner
        withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
            rotation = 360
        }

        // Pulsing outer ring
        withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
            pulseScale = 1.15
        }
    }
}

// MARK: - Preview

#Preview {
    AnalyzingOverlay()
}
