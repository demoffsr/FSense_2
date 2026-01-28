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

    // Cached values computed once on init to avoid repeated calculations
    private let textLength: Int
    private let animationInterval: TimeInterval

    init(fullText: String, messageId: UUID, isAnimationEnabled: Bool, onComplete: (() -> Void)? = nil) {
        self.fullText = fullText
        self.messageId = messageId
        self.isAnimationEnabled = isAnimationEnabled
        self.onComplete = onComplete

        // Cache text length and interval calculation
        self.textLength = fullText.count
        let charsPerSecond: Double
        if textLength < 200 {
            charsPerSecond = 60
        } else if textLength < 500 {
            charsPerSecond = 90
        } else {
            charsPerSecond = 120
        }
        self.animationInterval = 1.0 / charsPerSecond
    }

    private var displayedText: String {
        if !isAnimationEnabled || displayedCharacterCount >= textLength {
            return fullText
        }
        return String(fullText.prefix(displayedCharacterCount))
    }

    var body: some View {
        Text(displayedText)
            .onAppear { startAnimationIfNeeded() }
            .onDisappear { cleanup() }
            .onChange(of: isAnimationEnabled) { _, newValue in
                if !newValue {
                    // Animation disabled - show full text immediately
                    displayedCharacterCount = textLength
                    cleanup()
                }
            }
    }

    private func startAnimationIfNeeded() {
        guard isAnimationEnabled, displayedCharacterCount < textLength else {
            // If animation not needed or already complete, ensure full text is shown
            if displayedCharacterCount < textLength && !isAnimationEnabled {
                displayedCharacterCount = textLength
            }
            return
        }

        timerCancellable = Timer.publish(every: animationInterval, on: .main, in: .common)
            .autoconnect()
            .sink { _ in
                if displayedCharacterCount < textLength {
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
