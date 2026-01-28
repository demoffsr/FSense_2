import SwiftUI
import Combine

/// A text view that reveals characters one at a time with a typewriter effect
struct TypewriterText: View {
    let fullText: String
    let messageId: UUID
    let isAnimationEnabled: Bool
    let onComplete: (() -> Void)?

    @State private var displayedCharacterCount: Int = 0
    @State private var timerCancellable: AnyCancellable?

    private var displayedText: String {
        if !isAnimationEnabled || displayedCharacterCount >= fullText.count {
            return fullText
        }
        return String(fullText.prefix(displayedCharacterCount))
    }

    /// Adaptive speed: longer messages type faster to keep total duration reasonable
    private var interval: TimeInterval {
        let length = fullText.count
        let charsPerSecond: Double
        if length < 200 {
            charsPerSecond = 60
        } else if length < 500 {
            charsPerSecond = 90
        } else {
            charsPerSecond = 120
        }
        return 1.0 / charsPerSecond
    }

    var body: some View {
        Text(displayedText)
            .onAppear { startAnimationIfNeeded() }
            .onDisappear { cleanup() }
            .onChange(of: isAnimationEnabled) { _, newValue in
                if !newValue {
                    // Animation disabled - show full text immediately
                    displayedCharacterCount = fullText.count
                    cleanup()
                }
            }
    }

    private func startAnimationIfNeeded() {
        guard isAnimationEnabled, displayedCharacterCount < fullText.count else {
            // If animation not needed or already complete, ensure full text is shown
            if displayedCharacterCount < fullText.count && !isAnimationEnabled {
                displayedCharacterCount = fullText.count
            }
            return
        }

        timerCancellable = Timer.publish(every: interval, on: .main, in: .common)
            .autoconnect()
            .sink { _ in
                if displayedCharacterCount < fullText.count {
                    displayedCharacterCount += 1
                } else {
                    cleanup()
                    onComplete?()
                }
            }
    }

    private func cleanup() {
        timerCancellable?.cancel()
        timerCancellable = nil
    }
}
