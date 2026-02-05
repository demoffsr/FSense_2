import SwiftUI

/// Card showing overall gift suitability rating
struct GiftSuitabilityCard: View {
    
    let suitability: GiftSuitability
    let description: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header with title and suitability badge
            HStack(alignment: .center) {
                Text("Gift suitability")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                
                Spacer()
                
                // Suitability badge
                HStack(alignment: .center, spacing: 10) {
                    Text(suitabilityLabel)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(suitabilityColor)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(suitabilityColor.opacity(0.1))
                .cornerRadius(12)
            }
            
            // Description
            Text(description)
                .font(.system(size: 15))
                .foregroundColor(.black)
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
    
    private var suitabilityColor: Color {
        switch suitability {
        case .excellent: return Color("Success")
        case .good: return Color("Success")
        case .moderate: return .orange
        case .risky: return .red.opacity(0.8)
        case .notRecommended: return .red
        }
    }
    
    private var suitabilityLabel: String {
        switch suitability {
        case .excellent: return "Safe choice"
        case .good: return "Good choice"
        case .moderate: return "Use with care"
        case .risky: return "Risky"
        case .notRecommended: return "Not recommended"
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 12) {
        GiftSuitabilityCard(
            suitability: .excellent,
            description: "Suitable for sincere apologies and calm reconciliation"
        )
        GiftSuitabilityCard(
            suitability: .risky,
            description: "May create awkwardness in certain situations."
        )
    }
    .padding()
    .background(Color("SecondaryBackground"))
}
