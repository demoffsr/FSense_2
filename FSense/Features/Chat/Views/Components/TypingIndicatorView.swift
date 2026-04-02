import SwiftUI
import Combine

/// Typing indicator with "Thinking..." text and animated dots
struct TypingIndicatorView: View {

    @State private var dotIndex = 0
    @State private var timerCancellable: AnyCancellable?

    var body: some View {
        HStack(spacing: 6) {
            Text("Thinking")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack(spacing: 3) {
                ForEach(0..<3, id: \.self) { index in
                    Circle()
                        .fill(Color.secondary.opacity(index == dotIndex ? 0.9 : 0.3))
                        .frame(width: 5, height: 5)
                }
            }
        }
        .onAppear {
            timerCancellable = Timer.publish(every: 0.35, on: .main, in: .common)
                .autoconnect()
                .sink { _ in
                    dotIndex = (dotIndex + 1) % 3
                }
        }
        .onDisappear {
            timerCancellable?.cancel()
            timerCancellable = nil
        }
    }
}

#Preview {
    TypingIndicatorView()
        .padding()
}
