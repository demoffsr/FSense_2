import SwiftUI

/// Theme selection section with grid of theme cards
struct ThemeSelectionSection: View {
    @StateObject private var themeManager = ThemeManager.shared

    // Grid layout: 3 columns for 5 themes
    private let columns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Section header
            Text("Appearance")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.secondary)
                .textCase(.uppercase)
                .padding(.horizontal, 16)
                .padding(.bottom, 8)

            // Theme cards grid
            VStack(spacing: 0) {
                LazyVGrid(columns: columns, spacing: 12) {
                    ForEach(GradientTheme.allCases) { theme in
                        ThemeSelectorCard(
                            theme: theme,
                            isSelected: themeManager.selectedTheme == theme
                        ) {
                            withAnimation(.easeInOut(duration: 0.3)) {
                                themeManager.selectTheme(theme)
                            }
                        }
                    }
                }
                .padding(16)
            }
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 16)

            // Info text
            Text("Choose a theme for your home screen background.")
                .font(.system(size: 13))
                .foregroundColor(.secondary)
                .padding(.horizontal, 32)
                .padding(.top, 12)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
        }
    }
}

#Preview {
    ThemeSelectionSection()
        .padding(.vertical)
}
