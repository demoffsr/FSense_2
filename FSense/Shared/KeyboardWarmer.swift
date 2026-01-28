import UIKit

/// Pre-warms iOS keyboard to eliminate cold-start delay when opening chat
@MainActor
final class KeyboardWarmer: Sendable {
    static let shared = KeyboardWarmer()

    private init() {}

    /// Call on app launch to pre-warm keyboard
    nonisolated func warmUp() {
        Task { @MainActor in
            guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene else {
                return
            }

            let window = UIWindow(windowScene: scene)
            window.windowLevel = .init(rawValue: -1000)
            window.isHidden = false
            window.alpha = 0

            let textField = UITextField(frame: .zero)
            window.addSubview(textField)

            // Briefly become first responder to load keyboard
            textField.becomeFirstResponder()

            try? await Task.sleep(nanoseconds: 100_000_000)
            textField.resignFirstResponder()
            window.isHidden = true
        }
    }
}
