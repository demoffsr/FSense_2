import SwiftUI

struct MeaningBannerView: View {
    var body: some View {
        HStack(spacing: 0) {
            // MARK: - Text (left)
            Text("Flowers have meanings.\nLet's choose the right one.")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.leading, 18)
            
            Spacer(minLength: 12)
            
            // MARK: - Image (right)
            Image("CTA_BANNER_ASSET")
                .resizable()
                .scaledToFill()
                .frame(width: 127, height: 73)
                .clipped()
        }
        .frame(maxWidth: .infinity)
        .frame(height: 73)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .glassEffect(
            .clear.tint(.black.opacity(0.08)),
            in: RoundedRectangle(cornerRadius: 24, style: .continuous)
        )
    }
}
