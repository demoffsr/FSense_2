import SwiftUI

/// Compact reasoning card - optimized for performance
struct ThinkingCardView: View {
    
    let content: ThinkingContent
    let isExpanded: Bool
    let onToggle: () -> Void
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView
            
            // Expandable content
            if isExpanded {
                expandedContent
            }
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(white: 0.96))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                onToggle()
            }
        }
    }
    
    // MARK: - Header
    
    private var headerView: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Here's how I thought about this")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.black.opacity(0.8))
                
                if !isExpanded {
                    Text("Tap to see my reasoning")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }
            
            Spacer()
            
            Image(systemName: "chevron.down")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.gray)
                .rotationEffect(.degrees(isExpanded ? 180 : 0))
        }
    }
    
    // MARK: - Expanded Content
    
    private var expandedContent: some View {
        VStack(alignment: .leading, spacing: 6) {
            Divider()
                .padding(.vertical, 10)
            
            ForEach(content.steps) { step in
                ThinkingStepView(step: step)
            }
        }
    }
}

#Preview {
    ThinkingCardView(
        content: ThinkingContent(
            steps: ThinkingStep.mockSteps,
            isExpanded: true,
            isComplete: true
        ),
        isExpanded: true,
        onToggle: {}
    )
    .padding()
}
