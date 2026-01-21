import SwiftUI

/// Individual thinking step - optimized
struct ThinkingStepView: View {
    
    let step: ThinkingStep
    
    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            // Status indicator
            statusIcon
                .frame(width: 16, height: 16)
                .padding(.top, 2)
            
            // Step text
            Text(step.text)
                .font(.system(size: 13))
                .foregroundColor(textColor)
                .fixedSize(horizontal: false, vertical: true)
                .lineSpacing(2)
            
            Spacer(minLength: 0)
        }
        .padding(.vertical, 4)
    }
    
    // MARK: - Status Icon
    
    @ViewBuilder
    private var statusIcon: some View {
        switch step.status {
        case .pending:
            Circle()
                .fill(Color.gray.opacity(0.2))
                .frame(width: 6, height: 6)
            
        case .active:
            Circle()
                .fill(Color.purple.opacity(0.6))
                .frame(width: 6, height: 6)
            
        case .completed:
            Image(systemName: "checkmark")
                .font(.system(size: 9, weight: .semibold))
                .foregroundColor(.gray)
        }
    }
    
    private var textColor: Color {
        switch step.status {
        case .pending: return .gray.opacity(0.5)
        case .active: return .black.opacity(0.9)
        case .completed: return .black.opacity(0.6)
        }
    }
}
