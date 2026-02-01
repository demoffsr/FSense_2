import SwiftUI

struct AttachmentPreviewView: View {
    let image: UIImage
    let onRemove: () -> Void

    var body: some View {
        HStack(alignment: .center, spacing: 0) {
            ZStack(alignment: .topTrailing) {
                // Background image
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 96, height: 96)
                    .clipped()
                    .cornerRadius(16)
                    .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .inset(by: 0.5)
                            .stroke(.white, lineWidth: 1)
                    )

                // Close button
                Button(action: onRemove) {
                    Image(systemName: "xmark")
                        .font(.system(size: 9, weight: .semibold))
                        .foregroundStyle(.black)
                        .frame(height: 22)
                        .padding(.horizontal, 7)
                        .background(.white)
                        .cornerRadius(125)
                }
                .padding(8)
            }
            .frame(width: 96, height: 96, alignment: .trailing)

            Spacer()
        }
    }
}
