import SwiftUI
import Combine

/// Simple typing indicator - optimized
struct TypingIndicatorView: View {

    @State private var dotIndex = 0
    @State private var timerCancellable: AnyCancellable?

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3, id: \.self) { index in
                Circle()
                    .fill(Color.gray.opacity(index == dotIndex ? 0.8 : 0.3))
                    .frame(width: 6, height: 6)
            }
        }
        .onAppear {
            timerCancellable = Timer.publish(every: 0.4, on: .main, in: .common)
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
