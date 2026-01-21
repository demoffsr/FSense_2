import SwiftUI

// MARK: - Recent Section Header (Fixed)

struct RecentSectionHeaderView: View {
    @Binding var selectedTab: RecentTab
    var onSeeAll: (() -> Void)? = nil
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header row
            HStack {
                Text("Recent")
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(.black)

                Spacer()

                Button {
                    onSeeAll?()
                } label: {
                    Text("See all")
                        .font(.system(size: 16))
                        .foregroundColor(.gray)
                }
            }

            // Tabs - Native iOS segmented control with glass effect
            RecentTabsView(selectedTab: $selectedTab)
        }
    }
}

// MARK: - Recent Cards List (Scrollable)

struct RecentCardsListView: View {
    @ObservedObject var viewModel: HomeViewModel
    var onChatTapped: ((ChatSession) -> Void)? = nil
    
    var body: some View {
        VStack(spacing: 12) {
            if viewModel.state.selectedTab == .chats {
                chatsList
            } else {
                scansList
            }
        }
    }
    
    // MARK: - Chats List
    
    @ViewBuilder
    private var chatsList: some View {
        if viewModel.recentChats.isEmpty {
            EmptyStateView(
                icon: "bubble.left.and.bubble.right",
                title: "No chats yet",
                subtitle: "Start a conversation to get flower recommendations"
            )
        } else {
            ForEach(viewModel.recentChats) { session in
                Button {
                    onChatTapped?(session)
                } label: {
                    RecentChatRowView(session: session)
                }
                .buttonStyle(.plain)
            }
        }
    }
    
    // MARK: - Scans List
    
    @ViewBuilder
    private var scansList: some View {
        if viewModel.recentScans.isEmpty {
            EmptyStateView(
                icon: "camera.viewfinder",
                title: "No scans yet",
                subtitle: "Scan a flower to identify it"
            )
        } else {
            ForEach(viewModel.recentScans) { scan in
                RecentItemRowView(
                    title: scan.flowerName,
                    forLabel: "",
                    forValue: scan.subtitle,
                    imageName: scan.imageAsset
                )
            }
        }
    }
}

// MARK: - Recent Chat Row

struct RecentChatRowView: View {
    let session: ChatSession
    
    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            // Thumbnail
            thumbnail
            
            // Text content
            VStack(alignment: .leading, spacing: 4) {
                Text(displayTitle)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                    .lineLimit(1)
                
                if !session.subtitle.isEmpty {
                    Text(session.subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.5))
                        .lineLimit(1)
                } else {
                    Text(timeAgo)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.5))
                }
            }
            
            Spacer()
            
            // Chevron
            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.gray.opacity(0.5))
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 0)
    }
    
    private var displayTitle: String {
        if session.title == "New Chat" {
            // Try to get first user message
            if let firstUser = session.messages.first(where: { $0.sender == .user }),
               case .text(let text) = firstUser.content {
                let truncated = String(text.prefix(40))
                return truncated.count < text.count ? truncated + "..." : truncated
            }
        }
        return session.title
    }
    
    private var timeAgo: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: session.updatedAt, relativeTo: Date())
    }
    
    private var thumbnail: some View {
        Group {
            if let imageName = session.flowerImageAsset {
                RoundedRectangle(cornerRadius: 9)
                    .fill(Color.gray.opacity(0.1))
                    .frame(width: 46, height: 46)
                    .overlay(
                        Image(imageName)
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 9))
            } else {
                RoundedRectangle(cornerRadius: 9)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.purple.opacity(0.2),
                                Color.pink.opacity(0.2)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 46, height: 46)
                    .overlay(
                        Image(systemName: "bubble.left.fill")
                            .font(.system(size: 18))
                            .foregroundColor(.purple.opacity(0.6))
                    )
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: 9)
                .inset(by: 0.5)
                .stroke(Color(red: 0.95, green: 0.95, blue: 0.95), lineWidth: 1)
        )
    }
}

// MARK: - Empty State View

struct EmptyStateView: View {
    let icon: String
    let title: String
    let subtitle: String
    
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(.gray.opacity(0.4))
            
            Text(title)
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.gray)
            
            Text(subtitle)
                .font(.system(size: 14))
                .foregroundColor(.gray.opacity(0.7))
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }
}
