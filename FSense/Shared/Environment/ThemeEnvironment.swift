import SwiftUI

// MARK: - Theme Accent Color Environment Key

private struct ThemeAccentColorKey: EnvironmentKey {
    static let defaultValue: Color = .purple
}

extension EnvironmentValues {
    /// Current theme accent color for UI elements
    var themeAccent: Color {
        get { self[ThemeAccentColorKey.self] }
        set { self[ThemeAccentColorKey.self] = newValue }
    }
}

// MARK: - View Extension

extension View {
    /// Applies the current theme accent color to the environment
    func withThemeAccent(_ color: Color) -> some View {
        environment(\.themeAccent, color)
    }
}
