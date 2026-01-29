import SwiftUI

/// Avatar component with photo and initials fallback
struct ProfileAvatarView: View {
    let profile: LovedOneProfile
    var size: CGFloat = 46
    var showBorder: Bool = true

    @StateObject private var service = LovedOnesService.shared

    var body: some View {
        ZStack {
            if let photoPath = profile.photoPath,
               let photo = service.loadPhoto(path: photoPath) {
                Image(uiImage: photo)
                    .resizable()
                    .scaledToFill()
            } else {
                // Gradient initials fallback
                LinearGradient(
                    colors: [
                        profile.category.color,
                        profile.category.color.opacity(0.7)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )

                Text(profile.initials)
                    .font(.system(size: size * 0.4, weight: .semibold))
                    .foregroundColor(.white)
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
        .overlay {
            if showBorder {
                Circle()
                    .stroke(Color.white, lineWidth: size > 60 ? 3 : 2)
            }
        }
        .shadow(color: .black.opacity(0.1), radius: 4, x: 0, y: 2)
    }
}

/// Smaller avatar for compact views (autocomplete, etc.)
struct CompactProfileAvatarView: View {
    let profile: LovedOneProfile
    var size: CGFloat = 32

    @StateObject private var service = LovedOnesService.shared

    var body: some View {
        ZStack {
            if let photoPath = profile.photoPath,
               let photo = service.loadPhoto(path: photoPath) {
                Image(uiImage: photo)
                    .resizable()
                    .scaledToFill()
            } else {
                profile.category.color

                Text(profile.initials)
                    .font(.system(size: size * 0.38, weight: .semibold))
                    .foregroundColor(.white)
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
    }
}

#Preview {
    VStack(spacing: 20) {
        ProfileAvatarView(
            profile: LovedOneProfile(
                name: "Sarah Johnson",
                relationship: .girlfriend
            ),
            size: 120
        )

        ProfileAvatarView(
            profile: LovedOneProfile(
                name: "Mom",
                relationship: .mom
            ),
            size: 46
        )

        CompactProfileAvatarView(
            profile: LovedOneProfile(
                name: "Alex",
                relationship: .closeFriend
            )
        )
    }
    .padding()
    .background(Color.gray.opacity(0.2))
}
