import SwiftUI

struct SymbolismCard: View {

    let text: String

    // Static shadow color to avoid recreation on each render
    private static let shadowColor = Color.black.opacity(0.1)

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Symbolism")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .topLeading)
            
            Text(text)
                .font(.system(size: 15))
                .foregroundColor(.black.opacity(0.8))
                .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(Color.white)
        .cornerRadius(24)
        .compositingGroup()
        .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)
    }
}

#Preview {
    SymbolismCard(
        text: "In many cultures, this flower symbolizes humility and quiet reconciliation, as its form and color convey sincerity without demanding attention."
    )
    .padding()
    .background(Color(.systemGray6))
}
