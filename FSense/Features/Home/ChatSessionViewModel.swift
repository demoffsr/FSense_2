import SwiftUI

/// Per-session view model for granular SwiftUI dependencies
/// Performance: Each row depends only on its own view model, not the entire array
/// When one session changes, only that row updates (not all rows)
@Observable
final class ChatSessionViewModel: Identifiable {
    let id: UUID
    var title: String
    var subtitle: String
    var updatedAt: Date
    var flowerImageUrl: String?
    var flowerImageAsset: String?
    var flowerImageCacheKey: String?

    // MARK: - Computed Display Properties (cached in view model)

    /// Display title with fallback to first user message
    private(set) var displayTitle: String

    /// Time ago string (computed via DateFormattingService)
    var timeAgo: String {
        DateFormattingService.shared.timeAgo(for: updatedAt)
    }

    // MARK: - Initialization

    init(from session: ChatSession) {
        self.id = session.id
        self.title = session.title
        self.subtitle = session.subtitle
        self.updatedAt = session.updatedAt
        self.flowerImageUrl = session.flowerImageUrl
        self.flowerImageAsset = session.flowerImageAsset
        self.flowerImageCacheKey = session.flowerImageCacheKey

        // Pre-compute display title (expensive: iterates messages)
        self.displayTitle = Self.computeDisplayTitle(session: session)
    }

    // MARK: - Update Methods

    /// Update from ChatSession (called when session changes)
    func update(from session: ChatSession) {
        self.title = session.title
        self.subtitle = session.subtitle
        self.updatedAt = session.updatedAt
        self.flowerImageUrl = session.flowerImageUrl
        self.flowerImageAsset = session.flowerImageAsset
        self.flowerImageCacheKey = session.flowerImageCacheKey

        // Recompute display title if needed
        self.displayTitle = Self.computeDisplayTitle(session: session)
    }

    // MARK: - Helpers

    /// Pre-compute display title to avoid expensive computation in view body
    private static func computeDisplayTitle(session: ChatSession) -> String {
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
}
