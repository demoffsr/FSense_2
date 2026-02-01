import Foundation

// MARK: - Flower Card Segment

enum FlowerCardSegment: String, CaseIterable, Identifiable {
    case meaning = "Meaning"
    case gifting = "Gifting"
    case context = "Context"
    
    var id: String { rawValue }
}

// MARK: - Flower Card State

struct FlowerCardState: Equatable {
    var flower: Flower?
    var selectedSegment: FlowerCardSegment = .meaning
    var isLoading: Bool = false
    var errorMessage: String?

    // Validation state
    var validationWarnings: [String] = []

    // Find Flowers state
    var isSearchingProducts: Bool = false
    var flowerProducts: [FlowerProduct] = []
    var productSearchError: String?
    var productsCachedAt: String?  // ISO timestamp when search results were cached

    // Navigation state
    var shouldNavigateToFlowerProducts: Bool = false

    /// Whether the flower data has validation warnings (non-critical issues)
    var hasValidationWarnings: Bool {
        !validationWarnings.isEmpty
    }
}
