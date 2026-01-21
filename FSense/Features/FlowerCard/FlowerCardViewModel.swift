import SwiftUI

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
            
        case .askAITapped:
            handleAskAI()
            
        case .aiResponseReceived(let response):
            state.isAIProcessing = false
            // Future: Handle AI response presentation
            _ = response
            
        case .aiRequestFailed(let error):
            state.isAIProcessing = false
            state.errorMessage = error
            
        case .navigateToBouquetRecommendations:
            state.shouldNavigateToBouquetRecommendations = true
            
        case .dismissBouquetRecommendations:
            state.shouldNavigateToBouquetRecommendations = false
            
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
    
    var isAIProcessing: Bool {
        state.isAIProcessing
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
        // Future: Analytics tracking, data refresh, etc.
    }
    
    private func handleOnDisappear() {
        // Future: Cleanup, cancel pending requests, etc.
    }
    
    private func handleAskAI() {
        state.isAIProcessing = true
        
        // Future: Call AI service
        // For now, simulate with placeholder
        Task {
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            send(.navigateToBouquetRecommendations)
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
