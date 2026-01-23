import SwiftUI

/// Flower recommendation card with embedded reasoning panel
struct RecommendationCardView: View {
    
    let recommendation: FlowerRecommendation
    var thinkingContent: ThinkingContent? = nil
    var isThinkingExpanded: Bool = false
    var onThinkingToggle: (() -> Void)? = nil
    var onExplore: (() -> Void)? = nil
    
    // Custom smooth animation
    private var expandAnimation: Animation {
        .interpolatingSpring(stiffness: 300, damping: 30)
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Image
            imageSection
            
            // Content
            contentSection
            
            // Embedded reasoning panel (if thinking content exists)
            if let thinking = thinkingContent, thinking.isComplete {
                reasoningSection(thinking)
            }
        }
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
        .shadow(color: .black.opacity(0.08), radius: 8, x: 0, y: 4)
    }
    
    // MARK: - Image Section

    private var imageSection: some View {
        AsyncFlowerImageView(
            imageUrl: nil,  // FlowerRecommendation doesn't have imageUrl
            imageAsset: recommendation.imageAsset,
            cacheKey: nil
        )
        .frame(height: 140)
        .clipped()
        .clipShape(
            UnevenRoundedRectangle(
                topLeadingRadius: 24,
                bottomLeadingRadius: 0,
                bottomTrailingRadius: 0,
                topTrailingRadius: 24
            )
        )
    }
    
    // MARK: - Content Section
    
    private var contentSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(recommendation.flowerName)
                .font(.system(size: 22, weight: .bold))
                .foregroundColor(.black)
            
            Text(recommendation.meaning)
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black.opacity(0.8))
            
            Text(recommendation.explanation)
                .font(.subheadline)
                .foregroundColor(.black.opacity(0.6))
                .lineSpacing(3)
                .fixedSize(horizontal: false, vertical: true)
            
            // Explore button
            Button {
                onExplore?()
            } label: {
                Text("Explore this flower")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(
                        LinearGradient(
                            colors: [Color.purple, Color.purple.opacity(0.8)],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
            .buttonStyle(.plain)
            .padding(.top, 4)
        }
        .padding(18)
    }
    
    // MARK: - Reasoning Section (Embedded)
    
    private func reasoningSection(_ thinking: ThinkingContent) -> some View {
        VStack(spacing: 0) {
            // Divider
            Rectangle()
                .fill(Color.gray.opacity(0.15))
                .frame(height: 1)
            
            // Collapsible reasoning panel
            VStack(spacing: 0) {
                // Header - always visible
                reasoningHeader
                    .animation(nil, value: isThinkingExpanded)
                
                // Expandable steps with smooth reveal animation
                reasoningStepsContainer(thinking)
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .contentShape(Rectangle())
            .onTapGesture {
                withAnimation(expandAnimation) {
                    onThinkingToggle?()
                }
            }
        }
    }
    
    private var reasoningHeader: some View {
        HStack(spacing: 10) {
            Image(systemName: "brain")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.purple.opacity(0.7))
            
            Text("Here's how I thought about this")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.black.opacity(0.8))
                .lineLimit(1)
            
            Spacer()
            
            Image(systemName: "chevron.down")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.gray)
                .rotationEffect(.degrees(isThinkingExpanded ? 180 : 0))
                .animation(expandAnimation, value: isThinkingExpanded)
        }
    }
    
    // MARK: - Smooth Height Animation Container
    
    @ViewBuilder
    private func reasoningStepsContainer(_ thinking: ThinkingContent) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            reasoningStepsContent(thinking)
                .opacity(isThinkingExpanded ? 1 : 0)
        }
        .frame(height: isThinkingExpanded ? nil : 0, alignment: .top)
        .clipped()
        .animation(expandAnimation, value: isThinkingExpanded)
    }
    
    private func reasoningStepsContent(_ thinking: ThinkingContent) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            // Subtle divider
            Rectangle()
                .fill(Color.gray.opacity(0.08))
                .frame(height: 1)
                .padding(.top, 12)
                .padding(.bottom, 4)
            
            ForEach(Array(thinking.steps.enumerated()), id: \.element.id) { index, step in
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 13))
                        .foregroundColor(.green.opacity(0.7))
                    
                    Text(step.text)
                        .font(.system(size: 13))
                        .foregroundColor(.black.opacity(0.65))
                        .fixedSize(horizontal: false, vertical: true)
                }
                .padding(.vertical, 2)
            }
        }
        .padding(.bottom, 4)
    }
}
