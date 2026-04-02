import SwiftUI

// MARK: - Navigation Destinations

/// Type-safe navigation destinations for Home header
enum HomeNavDestination: Hashable {
    case profile
    case search
    case users
}

struct HomeHeaderView: View {
    var body: some View {
        GlassEffectContainer(spacing: 12) {
            HStack(alignment: .center, spacing: 12) {

                // 1) Profile button
                NavigationLink(value: HomeNavDestination.profile) {
                    ProfileButtonContent()
                }
                .buttonStyle(.plain)

                // 2) Search bar
                NavigationLink(value: HomeNavDestination.search) {
                    SearchBarContent()
                }
                .buttonStyle(.plain)

                // 3) Users button
                NavigationLink(value: HomeNavDestination.users) {
                    UsersButtonContent()
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.top, 8)
    }
}

// MARK: - Profile Button

struct ProfileButtonContent: View {
    var body: some View {
        Image("ProfileImage")
            .resizable()
            .aspectRatio(contentMode: .fill)
            .frame(width: 42, height: 42)
            .clipShape(Circle())
            .glassEffect(.clear.tint(.black.opacity(0.12)).interactive(), in: .circle)
    }
}

// MARK: - Search Bar

struct SearchBarContent: View {
    var body: some View {
        HStack(alignment: .center, spacing: 6) {
            
            Image(systemName: "magnifyingglass")
                .foregroundColor(.white)
                .font(.system(size: 18, weight: .medium))
            
            Text("Search")
                .foregroundColor(.white.opacity(0.9))
                .font(.system(size: 17, weight: .medium))
            
            Spacer()
        }
        .padding(.horizontal, 16)
        .frame(width: 244, height: 44)
        .glassEffect(.clear.tint(.black.opacity(0.08)).interactive())
    }
}

// MARK: - Users Button

struct UsersButtonContent: View {
    var body: some View {
        Image("UsersIcon")
            .renderingMode(.template)
            .resizable()
            .aspectRatio(contentMode: .fit)
            .frame(width: 22, height: 22)
            .foregroundColor(.white)
            .frame(width: 44, height: 44)
            .glassEffect(.clear.tint(.black.opacity(0.12)).interactive(), in: .circle)
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        ZStack {
            // Gradient background для preview
            LinearGradient(
                colors: [
                    Color("GradientBlobBlue"),
                    Color("GradientBlobPurple"),
                    Color("GradientBlobMagenta")
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            VStack {
                HomeHeaderView()
                    .padding(.horizontal, 16)
                Spacer()
            }
            .padding(.top, 60)
        }
        .navigationBarHidden(true)
    }
}
