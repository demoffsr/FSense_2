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
    
    // Navigation state
    var shouldNavigateToBouquetRecommendations: Bool = false
    
    // AI CTA state
    var isAIProcessing: Bool = false
}
