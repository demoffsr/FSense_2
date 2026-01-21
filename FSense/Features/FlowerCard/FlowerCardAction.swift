import Foundation

// MARK: - Flower Card Action

enum FlowerCardAction: Equatable {
    // Lifecycle
    case onAppear
    case onDisappear
    
    // Segment selection
    case selectSegment(FlowerCardSegment)
    
    // CTA actions
    case askAITapped
    case aiResponseReceived(String)
    case aiRequestFailed(String)
    
    // Navigation
    case navigateToBouquetRecommendations
    case dismissBouquetRecommendations
    
    // Data loading (for future dynamic content)
    case loadFlowerDetails(UUID)
    case flowerDetailsLoaded(Flower)
    case flowerDetailsLoadFailed(String)
}
