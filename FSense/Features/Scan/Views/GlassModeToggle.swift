import SwiftUI

/// Glass segmented control for Single/Bouquet mode selection
/// Uses iOS 26+ Liquid Glass effects with fallback for earlier versions
struct GlassModeToggle: View {
    @Binding var mode: ScanMode
    @Namespace private var animation

    var body: some View {
        if #available(iOS 26, *) {
            glassContent
                .glassEffect(.regular, in: .capsule)
        } else {
            glassContent
                .background(.ultraThinMaterial, in: Capsule())
        }
    }

    private var glassContent: some View {
        HStack(spacing: 0) {
            ForEach(ScanMode.allCases, id: \.self) { scanMode in
                modeButton(for: scanMode)
            }
        }
        .padding(4)
    }

    private func modeButton(for scanMode: ScanMode) -> some View {
        Button {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                mode = scanMode
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: scanMode.icon)
                    .font(.system(size: 14, weight: .medium))
                Text(scanMode == .single ? "Single" : "Bouquet")
                    .font(.system(size: 14, weight: .semibold))
            }
            .foregroundStyle(mode == scanMode ? .primary : .secondary)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background {
                if mode == scanMode {
                    if #available(iOS 26, *) {
                        Capsule()
                            .fill(.white.opacity(0.25))
                            .matchedGeometryEffect(id: "selection", in: animation)
                    } else {
                        Capsule()
                            .fill(.white.opacity(0.2))
                            .matchedGeometryEffect(id: "selection", in: animation)
                    }
                }
            }
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        Color.black.ignoresSafeArea()

        VStack(spacing: 40) {
            GlassModeToggle(mode: .constant(.single))
            GlassModeToggle(mode: .constant(.bouquet))
        }
    }
}
