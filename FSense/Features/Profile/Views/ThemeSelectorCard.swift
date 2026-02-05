import SwiftUI

/// Individual theme selection card with mini gradient preview
struct ThemeSelectorCard: View {
    let theme: GradientTheme
    let isSelected: Bool
    let action: () -> Void

    @Environment(\.themeAccent) private var themeAccent

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                // Mini gradient preview
                ZStack {
                    // 4-color gradient simulation
                    RoundedRectangle(cornerRadius: 12)
                        .fill(
                            LinearGradient(
                                colors: theme.previewColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(height: 72)

                    // Selection indicator
                    if isSelected {
                        RoundedRectangle(cornerRadius: 12)
                            .strokeBorder(Color.white, lineWidth: 3)

                        Image(systemName: "checkmark.circle.fill")
                            .font(.system(size: 24))
                            .foregroundStyle(.white)
                            .shadow(color: .black.opacity(0.3), radius: 2)
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)

                // Theme name
                Text(theme.displayName)
                    .font(.system(size: 13, weight: isSelected ? .semibold : .medium))
                    .foregroundColor(isSelected ? theme.accentColor : .primary)
            }
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    HStack(spacing: 12) {
        ThemeSelectorCard(theme: .aurora, isSelected: true) {}
        ThemeSelectorCard(theme: .ocean, isSelected: false) {}
        ThemeSelectorCard(theme: .sunset, isSelected: false) {}
    }
    .padding()
}
