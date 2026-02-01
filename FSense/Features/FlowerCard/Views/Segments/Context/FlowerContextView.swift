import SwiftUI

/// Container view for the Context segment
/// Composes: ContextSummaryCard, CulturalInterpretationSection, RelationshipContextSection,
///           TimingSensitivitySection, CommonMisinterpretationsSection
struct FlowerContextView: View {
    
    let data: ContextInfo
    
    var body: some View {
        VStack(spacing: 16) {
            ContextSummaryCard(summary: data.summaryText)
            
            // Cultural & Relationship carousel
            culturalRelationshipCarousel
            
            // Timing & Misinterpretations carousel
            timingMisinterpretationsCarousel
        }
    }
    
    // MARK: - Cultural & Relationship Carousel
    
    private var culturalRelationshipCarousel: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 16) {
                CulturalInterpretationSection(interpretations: data.culturalInterpretations)
                RelationshipContextSection(contexts: data.relationshipContexts)
            }
            .padding(.vertical, 4) // Minimal padding for shadow
        }
        .scrollClipDisabled()
    }
    
    // MARK: - Timing & Misinterpretations Carousel
    
    private var timingMisinterpretationsCarousel: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 16) {
                TimingSensitivitySection(sensitivities: data.timingSensitivities)
                CommonMisinterpretationsSection(misinterpretations: data.commonMisinterpretations)
            }
            .padding(.vertical, 4) // Minimal padding for shadow
        }
        .scrollClipDisabled()
    }
}

// MARK: - Preview

#Preview {
    ScrollView {
        FlowerContextView(data: .mock)
            .padding()
    }
    .background(Color("SecondaryBackground"))
}
