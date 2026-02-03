import SwiftUI

/// Async image view with local asset fallback, polling, and loading animations
struct AsyncFlowerImageView: View {

    @Environment(\.themeAccent) private var themeAccent

    let imageUrl: String?
    let imageAsset: String?
    let cacheKey: String?

    @State private var loadedImageUrl: String? = nil
    @State private var isPolling: Bool = false
    @State private var generationStatus: ImageGenerationStatus.GenerationStatus = .pending
    @State private var currentAttempt: Int = 0
    @State private var maxAttempts: Int = 20

    var body: some View {
        ZStack {
            // Layer 1: Background (local asset with blur OR placeholder)
            backgroundView

            // Layer 2: AI-generated image (when ready)
            if let url = displayImageUrl, let fullURL = constructFullURL(from: url) {
                CachedAsyncImage(url: fullURL) { image in
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .transition(.opacity.animation(.easeInOut(duration: 0.5)))
                } placeholder: {
                    // While remote image loads, show loading state
                    loadingOverlayView
                }
            } else if isPolling {
                // Layer 3: Loading overlay when polling
                loadingOverlayView
            }
        }
        .task {
            await startPollingIfNeeded()
        }
    }

    private var displayImageUrl: String? {
        loadedImageUrl ?? imageUrl
    }

    // MARK: - Background View

    private var backgroundView: some View {
        Group {
            if let asset = imageAsset {
                // Local asset with blur during generation
                Image(asset)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .blur(radius: isPolling ? 10 : 0)
                    .animation(.easeInOut(duration: 0.3), value: isPolling)
            } else {
                // Gradient placeholder
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

    // MARK: - Loading Overlay

    private var loadingOverlayView: some View {
        ZStack {
            // Shimmer animation
            ShimmerView()

            // Status text overlay
            VStack(spacing: 8) {
                ProgressView()
                    .tint(.white)
                    .scaleEffect(1.2)

                Text(statusText)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.white)
                    .shadow(color: .black.opacity(0.5), radius: 2, x: 0, y: 1)
                    .multilineTextAlignment(.center)
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(.ultraThinMaterial.opacity(0.7))
            )
        }
    }

    private var statusText: String {
        switch generationStatus {
        case .pending:
            return "Preparing image..."
        case .generating:
            return "Generating unique image..."
        case .completed:
            return "Loading..."
        case .failed:
            return "Image unavailable"
        }
    }

    // MARK: - Legacy local asset view (for CachedAsyncImage placeholder)

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
        generationStatus = .pending

        print("[AsyncImage] Starting poll for cache key: \(key)")
        print("[AsyncImage] Cache key length: \(key.count) characters")

        // Register status callback to receive updates
        await ImagePollingService.shared.registerStatusCallback(cacheKey: key) { status, attempt, max in
            self.generationStatus = status
            self.currentAttempt = attempt
            self.maxAttempts = max
        }

        if let url = await ImagePollingService.shared.pollForImage(cacheKey: key) {
            await MainActor.run {
                withAnimation(.easeInOut(duration: 0.5)) {
                    loadedImageUrl = url
                    isPolling = false
                }
            }
        } else {
            await MainActor.run {
                isPolling = false
            }
        }
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
