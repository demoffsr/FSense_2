import SwiftUI

/// Message bubble - optimized for performance
struct MessageBubbleView: View {

    let message: ChatMessage
    let steps: [ProgressStep]
    let isThinkingExpanded: Bool
    let onThinkingToggle: () -> Void
    var onExploreFlower: ((FlowerRecommendation) -> Void)? = nil

    /// Whether the thinking is complete (used to hide standalone thinking card)
    var hideCompletedThinking: Bool = false

    /// Whether to show typewriter animation for AI text messages
    var shouldAnimate: Bool = false

    // Static colors to avoid recreation on each render
    private static let shadowColor = Color.black.opacity(0.1)
    private static let imageShadowColor = Color.black.opacity(0.15)

    var body: some View {
        switch message.content {
        case .text(let text):
            if message.sender == .user {
                userMessage(text: text)
            } else {
                aiMessage(text: text)
            }

        case .textWithImage(let text, let imageData):
            if message.sender == .user {
                userMessageWithImage(text: text, imageData: imageData)
            } else {
                // AI messages with images (if ever needed)
                aiMessage(text: text)
            }

        case .acknowledgement(let text):
            aiMessage(text: text)

        case .thinking(let content):
            // Hide completed thinking cards if recommendation follows
            // (they will be shown inside the recommendation card)
            if hideCompletedThinking && content.isComplete {
                EmptyView()
            } else {
                ThinkingCardView(
                    steps: steps,
                    isExpanded: isThinkingExpanded,
                    onToggle: onThinkingToggle
                )
            }

        case .recommendation(let recommendation):
            RecommendationCardView(
                recommendation: recommendation,
                steps: steps,
                isThinkingExpanded: isThinkingExpanded,
                onThinkingToggle: onThinkingToggle,
                onExplore: { onExploreFlower?(recommendation) }
            )

        case .followUp:
            EmptyView()

        case .typing:
            typingIndicator
        }
    }

    // MARK: - User Message

    private func userMessage(text: String) -> some View {
        HStack {
            Spacer(minLength: 60)

            Text(text)
                .font(.subheadline)
                .foregroundColor(.black)
                .padding(14)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)
        }
    }

    // MARK: - User Message with Image

    private func userMessageWithImage(text: String, imageData: Data) -> some View {
        HStack(alignment: .top) {
            Spacer(minLength: 60)

            VStack(alignment: .trailing, spacing: 8) {
                // Attached image with lazy loading
                LazyImageView(imageData: imageData, messageId: message.id)

                // Text message
                Text(text)
                    .font(.subheadline)
                    .foregroundColor(.black)
                    .padding(14)
                    .frame(maxWidth: .infinity, alignment: .trailing)
                    .background(Color.white)
                    .cornerRadius(16)
                    .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)
            }
        }
    }

    // MARK: - AI Message

    private func aiMessage(text: String) -> some View {
        HStack {
            TypewriterText(
                fullText: text,
                messageId: message.id,
                isAnimationEnabled: shouldAnimate,
                onComplete: nil
            )
            .font(.subheadline)
            .foregroundColor(.black)
            .lineSpacing(3)
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white)
            .cornerRadius(16)
            .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)

            Spacer(minLength: 40)
        }
    }

    // MARK: - Typing Indicator

    private var typingIndicator: some View {
        HStack {
            TypingIndicatorView()
                .padding(14)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)

            Spacer()
        }
    }
}

// MARK: - Lazy Image View with Caching

/// Lazily loads and caches images to reduce memory pressure
private struct LazyImageView: View {
    let imageData: Data
    let messageId: UUID

    @State private var loadedImage: UIImage?

    // Static shadow color
    private static let imageShadowColor = Color.black.opacity(0.15)

    var body: some View {
        Group {
            if let image = loadedImage {
                Image(uiImage: image)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 126, height: 126)
                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .stroke(Color.white, lineWidth: 1)
                    )
                    .shadow(color: Self.imageShadowColor, radius: 16, x: 0, y: 0)
            } else {
                // Placeholder while loading
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 126, height: 126)
                    .overlay(
                        ProgressView()
                    )
            }
        }
        .onAppear {
            loadImageIfNeeded()
        }
    }

    private func loadImageIfNeeded() {
        guard loadedImage == nil else { return }

        // Check cache first
        if let cached = MessageImageCache.shared.image(for: messageId) {
            loadedImage = cached
            return
        }

        // Load in background to avoid blocking UI
        Task.detached(priority: .userInitiated) {
            let image = UIImage(data: imageData)

            await MainActor.run {
                if let image = image {
                    MessageImageCache.shared.setImage(image, for: messageId)
                    loadedImage = image
                }
            }
        }
    }
}

// MARK: - In-Memory Image Cache

/// Simple in-memory cache for decoded images to avoid repeated decoding
private final class MessageImageCache: @unchecked Sendable {
    static let shared = MessageImageCache()

    private let cache = NSCache<NSUUID, UIImage>()

    private init() {
        // Limit cache to ~50MB (assuming ~1MB per image)
        cache.countLimit = 50
    }

    func image(for id: UUID) -> UIImage? {
        cache.object(forKey: id as NSUUID)
    }

    func setImage(_ image: UIImage, for id: UUID) {
        cache.setObject(image, forKey: id as NSUUID)
    }
}
