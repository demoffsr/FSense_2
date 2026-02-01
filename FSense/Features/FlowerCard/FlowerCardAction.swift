import Foundation

// MARK: - Flower Card Action

enum FlowerCardAction: Equatable {
    // Lifecycle
    case onAppear
    case onDisappear

    // Segment selection
    case selectSegment(FlowerCardSegment)

    // Find Flowers CTA
    case findFlowersTapped
    case flowerProductsLoaded([FlowerProduct])
    case flowerProductsLoadFailed(String)

    // Navigation
    case navigateToFlowerProducts
    case dismissFlowerProducts
    case openProductLink(URL)

    // Data loading (for future dynamic content)
    case loadFlowerDetails(UUID)
    case flowerDetailsLoaded(Flower)
    case flowerDetailsLoadFailed(String)
}
