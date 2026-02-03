import Foundation

// MARK: - Image Generation Status

/// Status of image generation for polling
struct ImageGenerationStatus: Decodable {
    let cacheKey: String
    let status: GenerationStatus
    let imageUrl: String?
    let error: String?
    let updatedAt: String

    enum GenerationStatus: String, Decodable {
        case pending
        case generating
        case completed
        case failed
    }
}
