import Foundation

/// Lightweight alternative flower recommendation.
/// Displayed in "Также подходят:" section with preview image and confidence percentage.
struct AlternativeFlower: Identifiable, Codable, Equatable, Hashable {
    let flowerId: String
    let name: String
    let imageAsset: String?
    let imageUrl: String?
    let confidence: Double
    let briefReason: String

    var id: String { flowerId }

    /// Formatted confidence as percentage (e.g., "87%")
    var confidenceText: String {
        "\(Int(confidence * 100))%"
    }

    /// URL for the image if available
    var imageURL: URL? {
        guard let urlString = imageUrl else { return nil }
        return URL(string: urlString)
    }
}

// MARK: - Mock Data

extension AlternativeFlower {
    static let mocks: [AlternativeFlower] = [
        AlternativeFlower(
            flowerId: "blue_hydrangea",
            name: "Blue Hydrangea",
            imageAsset: "BlueHydrangea",
            imageUrl: nil,
            confidence: 0.87,
            briefReason: "Sincere apology"
        ),
        AlternativeFlower(
            flowerId: "white_tulip",
            name: "White Tulip",
            imageAsset: "WhiteTulip",
            imageUrl: nil,
            confidence: 0.82,
            briefReason: "Forgiveness"
        ),
        AlternativeFlower(
            flowerId: "white_peony",
            name: "White Peony",
            imageAsset: "WhitePeony",
            imageUrl: nil,
            confidence: 0.78,
            briefReason: "Regret and bashfulness"
        ),
        AlternativeFlower(
            flowerId: "purple_hyacinth",
            name: "Purple Hyacinth",
            imageAsset: "PurpleHyacinth",
            imageUrl: nil,
            confidence: 0.75,
            briefReason: "Seeking forgiveness"
        )
    ]
}
