import SwiftUI

/// Message bubble - optimized for performance
struct MessageBubbleView: View {
    
    let message: ChatMessage
    let isThinkingExpanded: Bool
    let onThinkingToggle: () -> Void
    var onExploreFlower: ((FlowerRecommendation) -> Void)? = nil
    
    /// Associated thinking content (for embedding in recommendation card)
    var associatedThinkingContent: ThinkingContent? = nil
    
    /// Whether the thinking is complete (used to hide standalone thinking card)
    var hideCompletedThinking: Bool = false
    
    var body: some View {
        switch message.content {
        case .text(let text):
            if message.sender == .user {
                userMessage(text: text)
            } else {
                aiMessage(text: text)
            }
            
        case .acknowledgement(let text):
            aiMessage(text: text)
            
        case .thinking(let content):
            // Hide completed thinking cards if recommendation follows
            // (they will be shown inside the recommendation card)
            if hideCompletedThinking && content.isComplete {
                EmptyView()
            } else {
                ThinkingCardView(
                    content: content,
                    isExpanded: isThinkingExpanded,
                    onToggle: onThinkingToggle
                )
            }
            
        case .recommendation(let recommendation):
            RecommendationCardView(
                recommendation: recommendation,
                thinkingContent: associatedThinkingContent,
                isThinkingExpanded: isThinkingExpanded,
                onThinkingToggle: onThinkingToggle,
                onExplore: { onExploreFlower?(recommendation) }
            )
            
        case .followUp:
            EmptyView()
            
        case .typing:
            typingIndicator
        }
    }
    
    // MARK: - User Message
    
    private func userMessage(text: String) -> some View {
        HStack {
            Spacer(minLength: 60)
            
            Text(text)
                .font(.subheadline)
                .foregroundColor(.black)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                .shadow(color: .black.opacity(0.06), radius: 4, x: 0, y: 2)
        }
    }
    
    // MARK: - AI Message
    
    private func aiMessage(text: String) -> some View {
        HStack {
            Text(text)
                .font(.subheadline)
                .foregroundColor(.black)
                .lineSpacing(3)
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
                .shadow(color: .black.opacity(0.06), radius: 4, x: 0, y: 2)
            
            Spacer(minLength: 40)
        }
    }
    
    // MARK: - Typing Indicator
    
    private var typingIndicator: some View {
        HStack {
            TypingIndicatorView()
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: .black.opacity(0.06), radius: 4, x: 0, y: 2)
            
            Spacer()
        }
    }
}
