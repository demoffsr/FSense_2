import SwiftUI

@main
struct FSenseApp: App {

    @StateObject private var appEnvironment = AppEnvironment()
    @StateObject private var themeManager = ThemeManager.shared

    /// Language manager for tracking language changes
    private var languageManager = LanguageManager.shared

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(appEnvironment)
                .environment(\.themeAccent, themeManager.accentColor)
                .environment(\.languageManager, languageManager)
                .environment(\.locale, currentLocale)
                .id(languageManager.currentLanguage) // Force view refresh on language change
                .task {
                    // Pre-warm keyboard after window scene is available
                    KeyboardWarmer.shared.warmUp()
                }
        }
    }

    /// Compute the locale based on selected language
    private var currentLocale: Locale {
        switch languageManager.currentLanguage {
        case .system:
            return .current
        case .english:
            return Locale(identifier: "en")
        case .russian:
            return Locale(identifier: "ru")
        case .spanish:
            return Locale(identifier: "es")
        case .german:
            return Locale(identifier: "de")
        case .french:
            return Locale(identifier: "fr")
        case .chinese:
            return Locale(identifier: "zh-Hans")
        case .japanese:
            return Locale(identifier: "ja")
        }
    }
}
