import SwiftUI

/// Glass pill toggle for Flower/Bouquet/Plant mode selection
/// Beautiful glass effect with smooth selection animation
struct GlassModeToggle: View {
    @Binding var mode: ScanMode
    @Namespace private var animation

    // Selected mode accent color #E90ACA
    private let accentColor = Color(red: 0.914, green: 0.039, blue: 0.792)

    var body: some View {
        if #available(iOS 26, *) {
            glassContainer
        } else {
            fallbackContainer
        }
    }

    // MARK: - iOS 26+ Glass Container

    @available(iOS 26, *)
    private var glassContainer: some View {
        HStack(spacing: 4) {
            ForEach(ScanMode.allCases, id: \.self) { scanMode in
                glassPillButton(for: scanMode)
            }
        }
        .padding(4)
        .glassEffect(
            .clear.tint(.black.opacity(0.12)).interactive(),
            in: .capsule
        )
    }

    @available(iOS 26, *)
    private func glassPillButton(for scanMode: ScanMode) -> some View {
        let isSelected = mode == scanMode

        return Button {
            withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
                mode = scanMode
            }
        } label: {
            Text(scanMode.displayName)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(.white.opacity(isSelected ? 1.0 : 0.7))
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .background {
                    if isSelected {
                        Capsule()
                            .fill(accentColor.opacity(0.6))
                            .matchedGeometryEffect(id: "pill_selection", in: animation)
                    }
                }
        }
        .buttonStyle(.plain)
    }

    // MARK: - Fallback Container

    private var fallbackContainer: some View {
        HStack(spacing: 4) {
            ForEach(ScanMode.allCases, id: \.self) { scanMode in
                fallbackPillButton(for: scanMode)
            }
        }
        .padding(4)
        .background(.ultraThinMaterial, in: Capsule())
    }

    private func fallbackPillButton(for scanMode: ScanMode) -> some View {
        let isSelected = mode == scanMode

        return Button {
            withAnimation(.spring(response: 0.35, dampingFraction: 0.7)) {
                mode = scanMode
            }
        } label: {
            Text(scanMode.displayName)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(.white.opacity(isSelected ? 1.0 : 0.7))
                .padding(.horizontal, 18)
                .padding(.vertical, 10)
                .background {
                    if isSelected {
                        Capsule()
                            .fill(accentColor.opacity(0.6))
                            .matchedGeometryEffect(id: "pill_selection", in: animation)
                    }
                }
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        LinearGradient(
            colors: [
                Color(red: 0, green: 0.11, blue: 0.92),
                Color(red: 0.55, green: 0, blue: 0.92),
                Color(red: 0.91, green: 0, blue: 0.89)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()

        VStack(spacing: 40) {
            GlassModeToggle(mode: .constant(.flower))
            GlassModeToggle(mode: .constant(.bouquet))
            GlassModeToggle(mode: .constant(.plant))
        }
    }
}
