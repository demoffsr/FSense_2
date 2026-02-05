import SwiftUI

struct ChatArchiveView: View {

    @Environment(\.themeAccent) private var themeAccent
    @StateObject private var archiveService = ChatArchiveService.shared

    // Pagination
    @State private var displayedCount: Int = 20
    private let batchSize: Int = 20

    var body: some View {
        ZStack {
            if archiveService.archivedSessions.isEmpty {
                emptyState
            } else {
                sessionList
            }
        }
        .navigationTitle("Chat Archive")
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            if !archiveService.archivedSessions.isEmpty {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(role: .destructive) {
                        archiveService.clearArchive()
                        displayedCount = batchSize
                    } label: {
                        Text("Clear All")
                            .foregroundColor(.red)
                    }
                }
            }
        }
        .onChange(of: archiveService.archivedSessions.count) { oldCount, newCount in
            // Reset pagination if archive was cleared or significantly changed
            if newCount < oldCount {
                displayedCount = min(displayedCount, max(newCount, batchSize))
            }
        }
    }

    // MARK: - Session List

    private var displayedSessions: [ArchivedChatSession] {
        Array(archiveService.archivedSessions.prefix(displayedCount))
    }

    private var hasMoreToLoad: Bool {
        displayedCount < archiveService.archivedSessions.count
    }

    private var sessionList: some View {
        List {
            ForEach(displayedSessions) { archivedItem in
                ChatArchiveRow(
                    session: archivedItem.session,
                    archivedAt: archivedItem.archivedAt
                )
                .contentShape(Rectangle())
            }
            .onDelete { indexSet in
                archiveService.removeSession(at: indexSet)
            }

            // Load more trigger
            if hasMoreToLoad {
                Color.clear
                    .frame(height: 1)
                    .onAppear {
                        displayedCount += batchSize
                    }
            }
        }
        .listStyle(.plain)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "bubble.left.and.bubble.right.fill")
                .font(.system(size: 64))
                .foregroundColor(.secondary.opacity(0.5))

            Text("No Archived Chats")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Archived chats will appear here")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

// MARK: - Archive Row

struct ChatArchiveRow: View {

    @Environment(\.themeAccent) private var themeAccent

    let session: ChatSession
    let archivedAt: Date

    var body: some View {
        HStack(spacing: 16) {
            // Chat Image/Thumbnail
            chatThumbnail
                .frame(width: 80, height: 80)
                .clipShape(RoundedRectangle(cornerRadius: 12))

            // Chat Info
            VStack(alignment: .leading, spacing: 6) {
                Text(session.title)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.primary)
                    .lineLimit(1)

                if !session.subtitle.isEmpty {
                    Text(session.subtitle)
                        .font(.system(size: 14))
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                } else if let preview = messagePreview {
                    Text(preview)
                        .font(.system(size: 14))
                        .foregroundColor(.secondary)
                        .lineLimit(1)
                }

                Text("Archived \(formattedDate)")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary.opacity(0.7))
            }

            Spacer()
        }
        .padding(.vertical, 8)
    }

    // MARK: - Chat Thumbnail

    @ViewBuilder
    private var chatThumbnail: some View {
        if let imageUrl = session.flowerImageUrl, let url = URL(string: imageUrl) {
            CachedAsyncImage(url: url) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } placeholder: {
                fallbackThumbnail
            }
        } else if let asset = session.flowerImageAsset {
            Image(asset)
                .resizable()
                .aspectRatio(contentMode: .fill)
        } else {
            fallbackThumbnail
        }
    }

    private var fallbackThumbnail: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [themeAccent.opacity(0.3), Color.pink.opacity(0.2)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .overlay(
                Image(systemName: "bubble.left.and.bubble.right.fill")
                    .font(.system(size: 28))
                    .foregroundColor(.white.opacity(0.8))
            )
    }

    // MARK: - Message Preview

    private var messagePreview: String? {
        // Get the last user message as preview
        if let lastUserMessage = session.messages.last(where: { $0.sender == .user }) {
            switch lastUserMessage.content {
            case .text(let text):
                return String(text.prefix(50))
            case .textWithImage(let text, _):
                return String(text.prefix(50))
            default:
                return nil
            }
        }
        return nil
    }

    // MARK: - Date Formatting

    private var formattedDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: archivedAt, relativeTo: Date())
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        ChatArchiveView()
    }
}
