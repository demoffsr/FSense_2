import SwiftUI

/// Manages gradient theme selection with UserDefaults persistence
@MainActor
final class ThemeManager: ObservableObject {

    // MARK: - Singleton

    static let shared = ThemeManager()

    // MARK: - Accent Color

    var accentColor: Color {
        selectedTheme.accentColor
    }

    // MARK: - Published Properties

    @Published private(set) var selectedTheme: GradientTheme

    // MARK: - UserDefaults Key

    private let themeKey = "selectedGradientTheme"

    // MARK: - Initialization

    private init() {
        if let saved = UserDefaults.standard.string(forKey: themeKey),
           let theme = GradientTheme(rawValue: saved) {
            self.selectedTheme = theme
        } else {
            self.selectedTheme = .aurora
        }
    }

    // MARK: - Public Methods

    func selectTheme(_ theme: GradientTheme) {
        selectedTheme = theme
        UserDefaults.standard.set(theme.rawValue, forKey: themeKey)
    }
}
