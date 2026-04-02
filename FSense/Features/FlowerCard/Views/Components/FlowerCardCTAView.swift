import SwiftUI

struct FlowerCardCTAView: View {

    let isProcessing: Bool
    let hasProducts: Bool
    let onTap: () -> Void

    private var buttonText: String {
        if isProcessing {
            return "Searching..."
        } else if hasProducts {
            return "Show links"
        } else {
            return "Find Flowers"
        }
    }

    var body: some View {
        VStack(alignment: .center, spacing: 0) {
            Button(action: onTap) {
                HStack(alignment: .center) {
                    Spacer()

                    if isProcessing {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .gray))
                    }

                    Text(buttonText)
                        .font(.system(size: 16, weight: .medium))
                        .foregroundColor(.black)
                    
                    Spacer()
                }
                .padding(14)
                .frame(maxWidth: .infinity)
                .frame(height: 50)
                .glassEffect(
                    .clear.tint(.white.opacity(0.9)).interactive(),
                    in: RoundedRectangle(cornerRadius: 16, style: .continuous)
                )
            }
            .buttonStyle(.plain)
            .disabled(isProcessing)
            .padding(.horizontal, 16)
        }
        .padding(.top, 16)
        .padding(.bottom, 16)
        .frame(maxWidth: .infinity, alignment: .bottom)
        .background(
            Rectangle()
                .fill(.ultraThinMaterial)
                .shadow(color: .black.opacity(0.1), radius: 16, x: 0, y: -12)
                .ignoresSafeArea(edges: .bottom)
        )
    }
}

#Preview("Find Flowers") {
    VStack {
        Spacer()
        FlowerCardCTAView(isProcessing: false, hasProducts: false, onTap: {})
    }
    .background(Color(.systemGray6))
}

#Preview("Show Links") {
    VStack {
        Spacer()
        FlowerCardCTAView(isProcessing: false, hasProducts: true, onTap: {})
    }
    .background(Color(.systemGray6))
}

#Preview("Processing") {
    VStack {
        Spacer()
        FlowerCardCTAView(isProcessing: true, hasProducts: false, onTap: {})
    }
    .background(Color(.systemGray6))
}
