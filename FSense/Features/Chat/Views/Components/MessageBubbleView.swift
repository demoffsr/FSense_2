import SwiftUI

/// Message bubble - optimized for performance
struct MessageBubbleView: View {

    let message: ChatMessage
    let steps: [ProgressStep]
    let isThinkingExpanded: Bool
    let onThinkingToggle: () -> Void
    var onExploreFlower: ((FlowerRecommendation) -> Void)? = nil

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
                    steps: steps,
                    isExpanded: isThinkingExpanded,
                    onToggle: onThinkingToggle
                )
            }

        case .recommendation(let recommendation):
            RecommendationCardView(
                recommendation: recommendation,
                steps: steps,
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
                .padding(14)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
        }
    }

    // MARK: - AI Message

    private func aiMessage(text: String) -> some View {
        HStack {
            Text(text)
                .font(.subheadline)
                .foregroundColor(.black)
                .lineSpacing(3)
                .padding(14)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)

            Spacer(minLength: 40)
        }
    }
    
    // MARK: - Typing Indicator
    
    private var typingIndicator: some View {
        HStack {
            TypingIndicatorView()
                .padding(14)
                .background(Color.white)
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)

            Spacer()
        }
    }
}
