import SwiftUI

struct ScanCTAView: View {

    var body: some View {
        HStack(spacing: 12) {

            // MARK: - Scanner Icon Container
            ZStack {
                RoundedRectangle(cornerRadius: 13.33333, style: .continuous)
                    .fill(Color.white.opacity(0.2))
                    .overlay(
                        RoundedRectangle(cornerRadius: 13.33333, style: .continuous)
                            .stroke(Color.white.opacity(0.2), lineWidth: 1.11111)
                    )

                Image("Scanner")
                    .resizable()
                    .scaledToFit()
                    .frame(width: 26.66666, height: 26.66666)
            }
            .frame(width: 40, height: 40)

            // MARK: - Title
            Text("Scan a flower")
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.white)

            Spacer()

            // MARK: - Arrow
            Image(systemName:"arrow.right")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white.opacity(0.7))
        }
        .padding(.leading, 12)
        .padding(.trailing, 16)
        .padding(.vertical, 12)
        .frame(maxWidth: .infinity)
        .glassEffect(
            .clear.tint(.black.opacity(0.08)).interactive(),
            in: RoundedRectangle(cornerRadius: 24, style: .continuous)
        )
    }
}