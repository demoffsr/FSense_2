import SwiftUI

struct RecentItemRowView: View {
    var title: String = "What should I give her?"
    var forLabel: String = "For: "
    var forValue: String = "Friend"
    var imageName: String? = nil
    
    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            // Thumbnail
            thumbnail
            
            // Text content
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                
                HStack(spacing: 0) {
                    Text(forLabel)
                    Text(forValue)
                }
                .font(.system(size: 13))
                .foregroundColor(.black.opacity(0.5))
            }
            
            Spacer()
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 0)
    }
    
    private var thumbnail: some View {
        RoundedRectangle(cornerRadius: 9)
            .fill(Color.gray.opacity(0.1))
            .frame(width: 46, height: 46)
            .overlay(
                Group {
                    if let imageName = imageName {
                        Image(imageName)
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    }
                }
            )
            .clipShape(RoundedRectangle(cornerRadius: 9))
            .overlay(
                RoundedRectangle(cornerRadius: 9)
                    .inset(by: 0.5)
                    .stroke(Color(red: 0.95, green: 0.95, blue: 0.95), lineWidth: 1)
            )
    }
}
