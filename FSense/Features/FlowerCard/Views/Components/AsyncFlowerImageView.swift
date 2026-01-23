import SwiftUI

/// Async image view with local asset fallback and polling
struct AsyncFlowerImageView: View {

    let imageUrl: String?
    let imageAsset: String?
    let cacheKey: String?

    @State private var loadedImageUrl: String? = nil
    @State private var isPolling: Bool = false

    var body: some View {
        Group {
            if let url = displayImageUrl, let imageURL = URL(string: url) {
                // Display remote image
                AsyncImage(url: constructFullURL(from: imageURL)) { phase in
                    switch phase {
                    case .empty:
                        placeholderView
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure:
                        // Fallback to local asset
                        localAssetView
                    @unknown default:
                        placeholderView
                    }
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
                    colors: [Color.pink.opacity(0.2), Color.purple.opacity(0.15)],
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
            return
        }

        isPolling = true

        print("[AsyncImage] Starting poll for cache key: \(key)")

        if let url = await ImagePollingService.shared.pollForImage(cacheKey: key) {
            await MainActor.run {
                loadedImageUrl = url
            }
        }

        isPolling = false
    }

    // MARK: - Helper Methods

    private func constructFullURL(from url: URL) -> URL {
        // If URL is relative (starts with /), construct full URL
        if url.path.hasPrefix("/") {
            #if DEBUG
            let baseURL = "http://192.168.1.176:8000"
            #else
            let baseURL = "http://localhost:8000"
            #endif

            if let fullURL = URL(string: baseURL + url.path) {
                return fullURL
            }
        }

        // Otherwise return as-is
        return url
    }
}
