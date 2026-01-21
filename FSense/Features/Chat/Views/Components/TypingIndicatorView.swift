import SwiftUI

/// Simple typing indicator - optimized
struct TypingIndicatorView: View {
    
    @State private var dotIndex = 0
    
    private let timer = Timer.publish(every: 0.4, on: .main, in: .common).autoconnect()
    
    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3, id: \.self) { index in
                Circle()
                    .fill(Color.gray.opacity(index == dotIndex ? 0.8 : 0.3))
                    .frame(width: 6, height: 6)
            }
        }
        .onReceive(timer) { _ in
            dotIndex = (dotIndex + 1) % 3
        }
    }
}

#Preview {
    TypingIndicatorView()
        .padding()
}
