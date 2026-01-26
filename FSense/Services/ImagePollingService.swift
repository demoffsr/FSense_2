import Foundation

/// Service for polling image generation status
actor ImagePollingService {

    static let shared = ImagePollingService()

    private let baseURL: String
    private let session: URLSession
    private let decoder: JSONDecoder

    // Active polling tasks
    private var pollingTasks: [String: Task<String?, Never>] = [:]

    private init() {
        #if DEBUG
        self.baseURL = "http://192.168.1.176:8000"
        #else
        self.baseURL = "http://localhost:8000"
        #endif

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
    }

    /// Start polling for image generation
    /// - Parameters:
    ///   - cacheKey: Cache key from FlowerCardPayload
    ///   - maxAttempts: Maximum polling attempts (default: 20)
    ///   - intervalSeconds: Polling interval (default: 3)
    /// - Returns: Final image URL or nil if failed/timeout
    func pollForImage(
        cacheKey: String,
        maxAttempts: Int = 20,
        intervalSeconds: TimeInterval = 3.0
    ) async -> String? {
        // Check if already polling
        if let existingTask = pollingTasks[cacheKey] {
            return await existingTask.value
        }

        // Create new polling task
        let task = Task<String?, Never> {
            for attempt in 1...maxAttempts {
                do {
                    let status = try await fetchImageStatus(cacheKey: cacheKey)

                    switch status.status {
                    case .completed:
                        if let imageUrl = status.imageUrl {
                            print("[ImagePoll] Image ready: \(imageUrl)")
                            return imageUrl
                        }
                    case .failed:
                        print("[ImagePoll] Generation failed: \(status.error ?? "unknown")")
                        return nil
                    case .pending, .generating:
                        print("[ImagePoll] Attempt \(attempt)/\(maxAttempts): \(status.status.rawValue)")
                        // Continue polling
                    }

                } catch {
                    print("[ImagePoll] Poll error: \(error.localizedDescription)")
                }

                // Wait before next poll
                if attempt < maxAttempts {
                    try? await Task.sleep(nanoseconds: UInt64(intervalSeconds * 1_000_000_000))
                }
            }

            print("[ImagePoll] Timeout after \(maxAttempts) attempts")
            return nil
        }

        pollingTasks[cacheKey] = task

        let result = await task.value
        pollingTasks.removeValue(forKey: cacheKey)

        return result
    }

    /// Cancel polling for a specific cache key
    func cancelPolling(cacheKey: String) {
        pollingTasks[cacheKey]?.cancel()
        pollingTasks.removeValue(forKey: cacheKey)
    }

    /// Cancel all polling tasks
    func cancelAllPolling() {
        for task in pollingTasks.values {
            task.cancel()
        }
        pollingTasks.removeAll()
    }

    // MARK: - Private Methods

    private func fetchImageStatus(cacheKey: String) async throws -> ImageGenerationStatus {
        let endpoint = "\(baseURL)/api/images/status/\(cacheKey)"

        guard let url = URL(string: endpoint) else {
            throw ImagePollingError.invalidURL
        }

        let (data, response) = try await session.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw ImagePollingError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            throw ImagePollingError.httpError(httpResponse.statusCode)
        }

        return try decoder.decode(ImageGenerationStatus.self, from: data)
    }
}

enum ImagePollingError: LocalizedError {
    case invalidURL
    case invalidResponse
    case httpError(Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid polling URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .httpError(let code):
            return "HTTP error: \(code)"
        }
    }
}
