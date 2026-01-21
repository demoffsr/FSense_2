import SwiftUI

struct WhyThisFlowerCard: View {

    let text: String

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
            LinearGradient(
                colors: [
                    Color(red: 0.45, green: 0.00, blue: 1.00),
                    Color(red: 1.00, green: 0.14, blue: 0.93)
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(width: 6)
        }
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .shadow(
            color: .black.opacity(0.08),
            radius: 10,
            x: 0,
            y: 4
        )
    }
}

#Preview {
    WhyThisFlowerCard(
        text: "This flower is traditionally given when one wants to express apology"
    )
    .padding()
    .background(Color(.systemGray6))
}
