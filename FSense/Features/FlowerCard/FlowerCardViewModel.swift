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
        state.flower = flower

        if let f = flower {
            print("[FlowerCardViewModel] Init with flower: \(f.name)")
            print("[FlowerCardViewModel] meanings: \(f.meanings)")
            print("[FlowerCardViewModel] giftingInfo: \(f.giftingInfo != nil)")
            print("[FlowerCardViewModel] contextInfo: \(f.contextInfo != nil)")
        } else {
            print("[FlowerCardViewModel] Init with nil flower")
        }
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
            handleFindFlowers()

        case .flowerProductsLoaded(let products):
            state.isSearchingProducts = false
            state.flowerProducts = products
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
    
    // MARK: - Segment Data Accessors
    
    var meaningData: MeaningSegmentData? {
        guard let flower = state.flower else { return nil }
        return MeaningSegmentData(
            whyThisFlowerText: flower.whyThisFlowerText,
            symbolismText: flower.symbolismText,
            meanings: flower.meanings,
            moodIntensityValue: flower.moodIntensityValue,
            moodIntensityLevel: flower.moodIntensityLevel
        )
    }
    
    var giftingData: GiftingInfo? {
        state.flower?.giftingInfo
    }
    
    var contextData: ContextInfo? {
        state.flower?.contextInfo
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
    
    private func handleFindFlowers() {
        guard let flower = state.flower else { return }

        state.isSearchingProducts = true
        state.productSearchError = nil

        // TODO: Get city from user settings or location
        let city = "Москва"  // Default city for testing
        let region = "RU"    // Default region for testing

        Task {
            do {
                let response = try await APIService.shared.searchFlowerProducts(
                    flowerName: flower.name,
                    city: city,
                    region: region
                )

                if response.success {
                    send(.flowerProductsLoaded(response.products))
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
}

// MARK: - Segment Data Models (View-specific)

struct MeaningSegmentData: Equatable {
    let whyThisFlowerText: String
    let symbolismText: String
    let meanings: [String]
    let moodIntensityValue: Double
    let moodIntensityLevel: MoodIntensityLevel
}
