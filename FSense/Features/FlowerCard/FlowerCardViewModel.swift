import SwiftUI
import UIKit

/// ViewModel for Flower Card screen
/// Responsibility: Handles state and actions for the Flower Card feature
@MainActor
final class FlowerCardViewModel: ObservableObject {
    
    // MARK: - Published State
    
    @Published private(set) var state = FlowerCardState()
    
    // MARK: - Dependencies
    
    // Future: AIService, FlowerRepository, etc.
    
    // MARK: - Initialization

    init(flower: Flower? = nil) {
        if let flower = flower {
            let validation = Self.validate(flower)
            if validation.isValid {
                state.flower = flower
                print("[FlowerCardViewModel] Init with valid flower: \(flower.name)")
            } else {
                // Log validation issues but still show the flower with fallbacks
                state.flower = flower
                state.validationWarnings = validation.warnings
                print("[FlowerCardViewModel] Init with flower (warnings): \(validation.warnings)")
            }
        } else {
            state.errorMessage = "No flower data provided"
            print("[FlowerCardViewModel] Init with nil flower")
        }
    }

    // MARK: - Validation

    struct ValidationResult {
        let isValid: Bool
        let warnings: [String]
    }

    private static func validate(_ flower: Flower) -> ValidationResult {
        var warnings: [String] = []

        // Check required fields
        if flower.name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            warnings.append("Flower name is empty")
        }

        if flower.meanings.isEmpty {
            warnings.append("No meanings provided")
        }

        if flower.whyThisFlowerText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            warnings.append("Missing 'why this flower' text")
        }

        // Check value ranges
        if flower.moodIntensityValue < 0 || flower.moodIntensityValue > 1 {
            warnings.append("Mood intensity out of range: \(flower.moodIntensityValue)")
        }

        return ValidationResult(isValid: warnings.isEmpty, warnings: warnings)
    }
    
    // MARK: - Action Handler
    
    func send(_ action: FlowerCardAction) {
        switch action {
        case .onAppear:
            handleOnAppear()

        case .onDisappear:
            handleOnDisappear()

        case .selectSegment(let segment):
            state.selectedSegment = segment

        case .findFlowersTapped:
            // If products already loaded, just show the sheet
            if !state.flowerProducts.isEmpty {
                state.shouldNavigateToFlowerProducts = true
            } else {
                handleFindFlowers(skipCache: false)
            }

        case .refreshFlowerProducts:
            handleFindFlowers(skipCache: true)

        case .flowerProductsLoaded(let products, let cachedAt):
            state.isSearchingProducts = false
            state.flowerProducts = products
            state.productsCachedAt = cachedAt
            state.shouldNavigateToFlowerProducts = true

        case .flowerProductsLoadFailed(let error):
            state.isSearchingProducts = false
            state.productSearchError = error

        case .navigateToFlowerProducts:
            state.shouldNavigateToFlowerProducts = true

        case .dismissFlowerProducts:
            state.shouldNavigateToFlowerProducts = false

        case .openProductLink(let url):
            UIApplication.shared.open(url)

        case .alternativeFlowerTapped(let alternative):
            handleAlternativeFlowerTap(alternative)

        case .loadFlowerDetails(let id):
            handleLoadFlowerDetails(id: id)

        case .flowerDetailsLoaded(let flower):
            state.flower = flower
            state.isLoading = false

        case .flowerDetailsLoadFailed(let error):
            state.errorMessage = error
            state.isLoading = false
        }
    }
    
    // MARK: - Computed Properties
    
    var flower: Flower? {
        state.flower
    }
    
    var selectedSegment: FlowerCardSegment {
        state.selectedSegment
    }
    
    var isLoading: Bool {
        state.isLoading
    }

    var isSearchingProducts: Bool {
        state.isSearchingProducts
    }

    var flowerProducts: [FlowerProduct] {
        state.flowerProducts
    }

    var productsCachedAt: String? {
        state.productsCachedAt
    }
    
    // MARK: - Segment Data Accessors (with fallbacks for safety)

    var meaningData: MeaningSegmentData? {
        guard let flower = state.flower else { return nil }
        return MeaningSegmentData(
            whyThisFlowerText: flower.whyThisFlowerText.isEmpty
                ? "This flower was selected for you."
                : flower.whyThisFlowerText,
            symbolismText: flower.symbolismText.isEmpty
                ? "A beautiful choice with rich symbolism."
                : flower.symbolismText,
            meanings: flower.meanings.isEmpty
                ? ["Beauty", "Elegance"]
                : flower.meanings,
            moodIntensityValue: max(0, min(1, flower.moodIntensityValue)),  // Clamp to 0...1
            moodIntensityLevel: flower.moodIntensityLevel
        )
    }

    var giftingData: GiftingInfo? {
        state.flower?.giftingInfo
    }

    var contextData: ContextInfo? {
        state.flower?.contextInfo
    }

    /// Whether the current flower has validation warnings
    var hasValidationWarnings: Bool {
        state.hasValidationWarnings
    }

    /// Validation warnings for debugging/logging
    var validationWarnings: [String] {
        state.validationWarnings
    }
    
    // MARK: - Private Handlers
    
    private func handleOnAppear() {
        // Save flower to archive when card is opened
        if let flower = state.flower {
            FlowerArchiveService.shared.archiveFlower(flower)
        }

        // Future: Analytics tracking, data refresh, etc.
    }
    
    private func handleOnDisappear() {
        // Future: Cleanup, cancel pending requests, etc.
    }
    
    private func handleFindFlowers(skipCache: Bool) {
        guard let flower = state.flower else { return }

        state.isSearchingProducts = true
        state.productSearchError = nil

        // Get city and region from user settings
        let city = UserSettings.selectedCity
        let region = UserSettings.selectedRegion

        Task {
            do {
                let response = try await APIService.shared.searchFlowerProducts(
                    flowerName: flower.name,
                    city: city,
                    region: region,
                    skipCache: skipCache
                )

                if response.success {
                    send(.flowerProductsLoaded(response.products, cachedAt: response.cachedAt))
                } else {
                    send(.flowerProductsLoadFailed(response.error ?? "Unknown error"))
                }
            } catch {
                send(.flowerProductsLoadFailed(error.localizedDescription))
            }
        }
    }
    
    private func handleLoadFlowerDetails(id: UUID) {
        state.isLoading = true

        // Future: Load from repository/API
        // For now, use mock data
        Task {
            try? await Task.sleep(nanoseconds: 500_000_000)
            send(.flowerDetailsLoaded(.mock))
        }
    }

    private func handleAlternativeFlowerTap(_ alternative: AlternativeFlower) {
        // Log the tap for now
        print("[FlowerCardViewModel] Alternative tapped: \(alternative.name) (\(alternative.confidenceText))")

        // Future: Could navigate to a new FlowerCard with the alternative
        // This would require making an API call to get full flower details
        // For MVP, we just log it - navigation can be added in a follow-up
    }
}

// MARK: - Segment Data Models (View-specific)

struct MeaningSegmentData: Equatable {
    let whyThisFlowerText: String
    let symbolismText: String
    let meanings: [String]
    let moodIntensityValue: Double
    let moodIntensityLevel: MoodIntensityLevel
}
