import SwiftUI

/// Card showing emotional risk level of giving this flower
struct EmotionalRiskCard: View {
    
    let riskLevel: EmotionalRiskLevel
    let description: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header with risk badge
            HStack(alignment: .center) {
                Text("Emotional risk level")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                
                Spacer()
                
                // Risk level badge
                HStack(alignment: .center, spacing: 10) {
                    Text(riskLabel)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(riskColor)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(riskColor.opacity(0.1))
                .cornerRadius(12)
            }
            
            // Description
            Text(description)
                .font(.system(size: 15))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
        .overlay(
            RoundedRectangle(cornerRadius: 24)
                .inset(by: 0.5)
                .stroke(.white, lineWidth: 1)
        )
    }
    
    // MARK: - Computed Properties
    
    private var riskLabel: String {
        switch riskLevel {
        case .none: return "No risk"
        case .low: return "Low risk"
        case .moderate: return "Moderate"
        case .high: return "High risk"
        case .veryHigh: return "Very high"
        }
    }
    
    private var riskColor: Color {
        switch riskLevel {
        case .none: return Color("Success")
        case .low: return Color("Success")
        case .moderate: return .orange
        case .high: return .red.opacity(0.8)
        case .veryHigh: return .red
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 12) {
        EmotionalRiskCard(
            riskLevel: .low,
            description: "Low risk of misinterpretation in delicate situations"
        )
        EmotionalRiskCard(
            riskLevel: .moderate,
            description: "May create awkwardness if given too early in a relationship."
        )
        EmotionalRiskCard(
            riskLevel: .high,
            description: "High risk of sending unintended signals. Consider carefully."
        )
    }
    .padding()
    .background(Color("SecondaryBackground"))
}
