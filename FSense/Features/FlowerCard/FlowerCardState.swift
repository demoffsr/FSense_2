import Foundation
import SwiftUI

// MARK: - Flower Card Segment

enum FlowerCardSegment: String, CaseIterable, Identifiable {
    case meaning, gifting, context

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .meaning: return "Meaning"
        case .gifting: return "Gifting"
        case .context: return "Context"
        }
    }

    var emptyStateMessage: LocalizedStringKey {
        switch self {
        case .meaning: return "No meaning information available"
        case .gifting: return "No gifting information available"
        case .context: return "No context information available"
        }
    }
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
