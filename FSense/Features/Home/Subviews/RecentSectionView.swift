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
    var onRenameChat: ((ChatSession) -> Void)? = nil
    var onDeleteChat: ((ChatSession) -> Void)? = nil

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
        if viewModel.recentChatViewModels.isEmpty {
            EmptyStateView(
                icon: "bubble.left.and.bubble.right",
                title: "No chats yet",
                subtitle: "Start a conversation to get flower recommendations"
            )
        } else {
            // Build lookup once per chatsList evaluation (O(n) once, not per row)
            let lookup = Dictionary(uniqueKeysWithValues:
                viewModel.chatHistory.sessions.map { ($0.id, $0) })
            ForEach(viewModel.recentChatViewModels) { chatVM in
                Button {
                    if let session = lookup[chatVM.id] {
                        onChatTapped?(session)
                    }
                } label: {
                    RecentChatRowView(
                        viewModel: chatVM,
                        onRename: {
                            if let session = lookup[chatVM.id] {
                                onRenameChat?(session)
                            }
                        },
                        onDelete: {
                            if let session = lookup[chatVM.id] {
                                onDeleteChat?(session)
                            }
                        }
                    )
                }
                .id(chatVM.id) // Explicit identity for SwiftUI
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
                RecentScanRowView(scan: scan)
            }
        }
    }
}

// MARK: - Recent Scan Row

struct RecentScanRowView: View {
    let scan: RecentScanItem
    @State private var showingScanDetail = false

    /// Static gradient for placeholder
    private static let placeholderGradient = LinearGradient(
        colors: [Color.green.opacity(0.2), Color.teal.opacity(0.2)],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    var body: some View {
        Button {
            showingScanDetail = true
        } label: {
            HStack(alignment: .center, spacing: 14) {
                // Thumbnail
                thumbnail

                // Text content
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(scan.flowerName)
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(.black)
                            .lineLimit(1)

                        if let confidence = scan.confidence, confidence >= 0.8 {
                            Image(systemName: "checkmark.seal.fill")
                                .font(.system(size: 12))
                                .foregroundColor(.green)
                        }
                    }

                    Text(scan.subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.5))
                        .lineLimit(1)
                }

                Spacer()

                // Confidence badge
                if let confidence = scan.confidence {
                    Text("\(Int(confidence * 100))%")
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(.white)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(confidenceColor(confidence))
                        .clipShape(Capsule())
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.white)
            .cornerRadius(16)
            .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 0)
        }
        .buttonStyle(.plain)
        // TODO: Add navigation to scan detail when tapped
        // .fullScreenCover(isPresented: $showingScanDetail) { ... }
    }

    private var thumbnail: some View {
        Group {
            if let imagePath = scan.imagePath {
                // Load from saved image
                if let image = loadImage(from: imagePath) {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 46, height: 46)
                        .clipShape(RoundedRectangle(cornerRadius: 9))
                } else {
                    placeholderThumbnail
                }
            } else if let imageAsset = scan.imageAsset {
                // Local asset
                Image(imageAsset)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 46, height: 46)
                    .clipShape(RoundedRectangle(cornerRadius: 9))
            } else {
                placeholderThumbnail
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: 9)
                .inset(by: 0.5)
                .stroke(Color("BorderStroke"), lineWidth: 1)
        )
    }

    private var placeholderThumbnail: some View {
        RoundedRectangle(cornerRadius: 9)
            .fill(Self.placeholderGradient)
            .frame(width: 46, height: 46)
            .overlay(
                Image(systemName: "camera.viewfinder")
                    .font(.system(size: 18))
                    .foregroundColor(.green.opacity(0.6))
            )
    }

    private func loadImage(from path: String) -> UIImage? {
        guard let documentsDir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else {
            return nil
        }
        let url = documentsDir.appendingPathComponent("scan_images/\(path)")
        return UIImage(contentsOfFile: url.path)
    }

    private func confidenceColor(_ confidence: Double) -> Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }
}

// MARK: - Recent Chat Row

struct RecentChatRowView: View {
    @Environment(\.themeAccent) private var themeAccent

    let viewModel: ChatSessionViewModel
    var onRename: (() -> Void)? = nil
    var onDelete: (() -> Void)? = nil

    /// Gradient using theme accent
    private var placeholderGradient: LinearGradient {
        LinearGradient(
            colors: [themeAccent.opacity(0.2), Color.pink.opacity(0.2)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }

    var body: some View {
        HStack(alignment: .center, spacing: 14) {
            // Thumbnail
            thumbnail

            // Text content
            VStack(alignment: .leading, spacing: 4) {
                Text(viewModel.displayTitle)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                    .lineLimit(1)

                if !viewModel.subtitle.isEmpty {
                    Text(viewModel.subtitle)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.5))
                        .lineLimit(1)
                } else {
                    Text(viewModel.timeAgo)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.5))
                }
            }

            Spacer()

            // More button (three dots)
            Menu {
                Button {
                    onRename?()
                } label: {
                    Label("Rename", systemImage: "pencil")
                }

                Button(role: .destructive) {
                    onDelete?()
                } label: {
                    Label("Delete", systemImage: "trash")
                }
            } label: {
                Image(systemName: "ellipsis")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.gray.opacity(0.6))
                    .frame(width: 32, height: 32)
                    .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 0)
    }
    
    private var thumbnail: some View {
        Group {
            // Priority: imageUrl > imageAsset > placeholder
            if let imageUrlString = viewModel.flowerImageUrl,
               let imageUrl = URL(string: imageUrlString) {
                // Remote AI-generated image with caching
                CachedAsyncImage(url: imageUrl) { image in
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 46, height: 46)
                        .clipShape(RoundedRectangle(cornerRadius: 9))
                } placeholder: {
                    localImageOrPlaceholder
                }
            } else {
                localImageOrPlaceholder
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: 9)
                .inset(by: 0.5)
                .stroke(Color("BorderStroke"), lineWidth: 1)
        )
    }

    private var localImageOrPlaceholder: some View {
        Group {
            if let imageName = viewModel.flowerImageAsset {
                // Local asset image
                Image(imageName)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 46, height: 46)
                    .clipShape(RoundedRectangle(cornerRadius: 9))
            } else {
                // Placeholder gradient (uses static property to avoid recreation)
                RoundedRectangle(cornerRadius: 9)
                    .fill(placeholderGradient)
                    .frame(width: 46, height: 46)
                    .overlay(
                        Image(systemName: "bubble.left.fill")
                            .font(.system(size: 18))
                            .foregroundColor(themeAccent.opacity(0.6))
                    )
            }
        }
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
