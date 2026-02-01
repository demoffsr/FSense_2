import SwiftUI

@main
struct FSenseApp: App {

    @StateObject private var appEnvironment = AppEnvironment()
    @StateObject private var themeManager = ThemeManager.shared

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(appEnvironment)
                .environment(\.themeAccent, themeManager.accentColor)
                .task {
                    // Pre-warm keyboard after window scene is available
                    KeyboardWarmer.shared.warmUp()
                }
        }
    }
}
