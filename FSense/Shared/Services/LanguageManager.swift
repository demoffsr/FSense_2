import SwiftUI

// MARK: - Supported Language

/// Supported app languages
enum AppLanguage: String, CaseIterable, Identifiable {
    case system = "system"
    case english = "en"
    case russian = "ru"
    case spanish = "es"
    case german = "de"
    case french = "fr"
    case chinese = "zh-Hans"
    case japanese = "ja"

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .system: return "System"
        case .english: return "English"
        case .russian: return "Русский"
        case .spanish: return "Español"
        case .german: return "Deutsch"
        case .french: return "Français"
        case .chinese: return "中文"
        case .japanese: return "日本語"
        }
    }

    /// Native name shown in picker (always in that language)
    var nativeName: String {
        switch self {
        case .system: return "System"
        case .english: return "English"
        case .russian: return "Русский"
        case .spanish: return "Español"
        case .german: return "Deutsch"
        case .french: return "Français"
        case .chinese: return "中文"
        case .japanese: return "日本語"
        }
    }

    var icon: String {
        switch self {
        case .system: return "gear"
        case .english: return "globe.americas"
        case .russian: return "globe.europe.africa"
        case .spanish: return "globe.americas"
        case .german: return "globe.europe.africa"
        case .french: return "globe.europe.africa"
        case .chinese: return "globe.asia.australia"
        case .japanese: return "globe.asia.australia"
        }
    }
}

// MARK: - Language Manager

/// Manages app language selection and persistence
/// Uses UserDefaults to store preference and Bundle extension to apply changes
@Observable
final class LanguageManager {
    static let shared = LanguageManager()

    private let languageKey = "AppLanguage"

    /// Currently selected language
    var currentLanguage: AppLanguage {
        didSet {
            guard oldValue != currentLanguage else { return }
            saveLanguage()
            applyLanguage()
        }
    }

    /// Whether a restart is needed for full language change
    private(set) var needsRestart: Bool = false

    private init() {
        // Load saved language or use system default
        if let savedCode = UserDefaults.standard.string(forKey: languageKey),
           let language = AppLanguage(rawValue: savedCode) {
            currentLanguage = language
        } else {
            currentLanguage = .system
        }

        // Apply language on init
        applyLanguage()
    }

    // MARK: - Private Methods

    private func saveLanguage() {
        UserDefaults.standard.set(currentLanguage.rawValue, forKey: languageKey)
    }

    private func applyLanguage() {
        let languageCode: String?

        switch currentLanguage {
        case .system:
            // Remove override, use system language
            languageCode = nil
            UserDefaults.standard.removeObject(forKey: "AppleLanguages")
        case .english, .russian, .spanish, .german, .french, .chinese, .japanese:
            languageCode = currentLanguage.rawValue
            UserDefaults.standard.set([languageCode], forKey: "AppleLanguages")
        }

        // Update Bundle language
        Bundle.setLanguage(languageCode)

        // Mark that restart may be needed for complete UI refresh
        needsRestart = true
    }

    /// Reset restart flag (call after user dismisses restart alert)
    func clearRestartFlag() {
        needsRestart = false
    }
}

// MARK: - Bundle Extension for Runtime Language Change

private var bundleKey: UInt8 = 0

extension Bundle {
    /// Override the main bundle's language at runtime
    static func setLanguage(_ language: String?) {
        defer {
            // Ensure we refresh the bundle
            object_setClass(Bundle.main, language != nil ? LanguageBundle.self : Bundle.self)
        }

        if let language = language {
            objc_setAssociatedObject(
                Bundle.main,
                &bundleKey,
                Bundle.main.path(forResource: language, ofType: "lproj"),
                .OBJC_ASSOCIATION_RETAIN_NONATOMIC
            )
        } else {
            objc_setAssociatedObject(
                Bundle.main,
                &bundleKey,
                nil,
                .OBJC_ASSOCIATION_RETAIN_NONATOMIC
            )
        }
    }
}

/// Custom bundle class that redirects localization to selected language
private class LanguageBundle: Bundle {
    override func localizedString(forKey key: String, value: String?, table tableName: String?) -> String {
        if let path = objc_getAssociatedObject(self, &bundleKey) as? String,
           let bundle = Bundle(path: path) {
            return bundle.localizedString(forKey: key, value: value, table: tableName)
        }
        return super.localizedString(forKey: key, value: value, table: tableName)
    }
}

// MARK: - Environment Key

private struct LanguageManagerKey: EnvironmentKey {
    static let defaultValue = LanguageManager.shared
}

extension EnvironmentValues {
    var languageManager: LanguageManager {
        get { self[LanguageManagerKey.self] }
        set { self[LanguageManagerKey.self] = newValue }
    }
}
