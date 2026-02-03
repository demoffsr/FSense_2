import SwiftUI

struct WhyThisFlowerCard: View {

    let text: String

    // Static gradient to avoid recreation on each render
    private static let accentGradient = LinearGradient(
        colors: [
            Color("AccentPurple"),
            Color("AccentPink")
        ],
        startPoint: .top,
        endPoint: .bottom
    )

    // Static shadow color to avoid recreation on each render
    private static let shadowColor = Color.black.opacity(0.08)

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Why this flower?")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.black)

            Text(text)
                .font(.system(size: 15))
                .foregroundColor(.black.opacity(0.8))
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16)
        .padding(.leading, 6)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .overlay(alignment: .leading) {
            Self.accentGradient
                .frame(width: 6)
        }
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .compositingGroup()
        .shadow(color: Self.shadowColor, radius: 10, x: 0, y: 4)
    }
}

#Preview {
    WhyThisFlowerCard(
        text: "This flower is traditionally given when one wants to express apology"
    )
    .padding()
    .background(Color(.systemGray6))
}
