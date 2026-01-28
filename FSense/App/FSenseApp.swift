import SwiftUI

@main
struct FSenseApp: App {

    @StateObject private var appEnvironment = AppEnvironment()

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(appEnvironment)
                .task {
                    // Pre-warm keyboard after window scene is available
                    KeyboardWarmer.shared.warmUp()
                }
        }
    }
}
