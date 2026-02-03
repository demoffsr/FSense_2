import SwiftUI

/// Async image view with local asset fallback and polling
struct AsyncFlowerImageView: View {

    @Environment(\.themeAccent) private var themeAccent

    let imageUrl: String?
    let imageAsset: String?
    let cacheKey: String?

    @State private var loadedImageUrl: String? = nil
    @State private var isPolling: Bool = false

    var body: some View {
        Group {
            if let url = displayImageUrl {
                // Display remote image with caching
                if let fullURL = constructFullURL(from: url) {
                    CachedAsyncImage(url: fullURL) { image in
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    } placeholder: {
                        localAssetView
                    }
                } else {
                    localAssetView
                }
            } else {
                // Use local asset
                localAssetView
            }
        }
        .task {
            await startPollingIfNeeded()
        }
    }

    private var displayImageUrl: String? {
        loadedImageUrl ?? imageUrl
    }

    private var localAssetView: some View {
        Group {
            if let asset = imageAsset {
                Image(asset)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } else {
                placeholderView
            }
        }
    }

    private var placeholderView: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [Color.pink.opacity(0.2), themeAccent.opacity(0.15)],
                    startPoint: .topTrailing,
                    endPoint: .bottomLeading
                )
            )
    }

    // MARK: - Polling Logic

    private func startPollingIfNeeded() async {
        // Only poll if:
        // 1. No image URL provided (image not ready)
        // 2. Cache key is available (can poll)
        // 3. Not already polling
        guard imageUrl == nil,
              let key = cacheKey,
              !isPolling else {
            print("[AsyncImage] Skipping poll - imageUrl: \(imageUrl != nil ? "present" : "nil"), cacheKey: \(cacheKey != nil ? "present" : "nil"), isPolling: \(isPolling)")
            return
        }

        isPolling = true

        print("[AsyncImage] Starting poll for cache key: \(key)")
        print("[AsyncImage] Cache key length: \(key.count) characters")

        if let url = await ImagePollingService.shared.pollForImage(cacheKey: key) {
            await MainActor.run {
                loadedImageUrl = url
            }
        }

        isPolling = false
    }

    // MARK: - Helper Methods

    private func constructFullURL(from urlString: String) -> URL? {
        // If URL is relative (starts with /), construct full URL using centralized baseURL
        if urlString.hasPrefix("/") {
            return URL(string: APIService.baseURL + urlString)
        }

        // Otherwise parse as-is
        return URL(string: urlString)
    }
}
