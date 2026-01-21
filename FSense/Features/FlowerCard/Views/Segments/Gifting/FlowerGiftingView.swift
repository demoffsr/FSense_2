import SwiftUI

/// Container view for the Gifting segment
/// Composes: GiftSuitabilityCard, EmotionalRiskCard, WhenToGiftList, RecipientFitList
struct FlowerGiftingView: View {
    
    let data: GiftingInfo
    
    var body: some View {
        VStack(spacing: 16) {
            GiftSuitabilityCard(
                suitability: data.overallSuitability,
                description: data.suitabilityDescription
            )
            
            EmotionalRiskCard(
                riskLevel: data.emotionalRisk,
                description: data.emotionalRiskDescription
            )
            
            WhenToGiftList(
                whenToGiftItems: data.whenToGiftItems,
                whenToAvoidItems: data.whenToAvoidItems
            )
            
            RecipientFitList(recipients: data.recipientFits)
        }
    }
}

// MARK: - Preview

#Preview {
    ScrollView {
        FlowerGiftingView(data: .mock)
            .padding()
    }
}
