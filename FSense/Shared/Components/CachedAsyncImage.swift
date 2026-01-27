import SwiftUI

/// Image cache with disk persistence
final class ImageCache: @unchecked Sendable {
    static let shared = ImageCache()

    private let cache: URLCache

    private init() {
        // 50MB memory, 200MB disk
        cache = URLCache(
            memoryCapacity: 50 * 1024 * 1024,
            diskCapacity: 200 * 1024 * 1024,
            diskPath: "flower_images"
        )
        URLCache.shared = cache
    }

    func cachedResponse(for url: URL) -> CachedURLResponse? {
        cache.cachedResponse(for: URLRequest(url: url))
    }

    func store(_ response: CachedURLResponse, for url: URL) {
        cache.storeCachedResponse(response, for: URLRequest(url: url))
    }
}

/// AsyncImage with disk caching
struct CachedAsyncImage<Content: View, Placeholder: View>: View {
    let url: URL?
    let content: (Image) -> Content
    let placeholder: () -> Placeholder

    @State private var image: UIImage?
    @State private var isLoading = false

    init(
        url: URL?,
        @ViewBuilder content: @escaping (Image) -> Content,
        @ViewBuilder placeholder: @escaping () -> Placeholder
    ) {
        self.url = url
        self.content = content
        self.placeholder = placeholder
    }

    var body: some View {
        Group {
            if let image = image {
                content(Image(uiImage: image))
            } else {
                placeholder()
                    .task(id: url) {
                        await loadImage()
                    }
            }
        }
    }

    private func loadImage() async {
        guard let url = url, !isLoading else { return }

        isLoading = true
        defer { isLoading = false }

        // Check cache first
        if let cached = ImageCache.shared.cachedResponse(for: url),
           let uiImage = UIImage(data: cached.data) {
            await MainActor.run { image = uiImage }
            return
        }

        // Download
        do {
            let (data, response) = try await URLSession.shared.data(from: url)

            // Cache the response
            let cachedResponse = CachedURLResponse(response: response, data: data)
            ImageCache.shared.store(cachedResponse, for: url)

            if let uiImage = UIImage(data: data) {
                await MainActor.run { image = uiImage }
            }
        } catch {
            print("[CachedAsyncImage] Failed to load: \(url) - \(error.localizedDescription)")
        }
    }
}

// MARK: - Convenience initializer

extension CachedAsyncImage where Placeholder == Color {
    init(url: URL?, @ViewBuilder content: @escaping (Image) -> Content) {
        self.init(url: url, content: content, placeholder: { Color.gray.opacity(0.2) })
    }
}
