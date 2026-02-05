import SwiftUI

/// Section showing how different cultures interpret this flower
struct CulturalInterpretationSection: View {
    
    let interpretations: [CulturalInterpretation]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Cultural interpretation")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 16) {
                ForEach(interpretations) { interpretation in
                    interpretationRow(interpretation)
                }
            }
        }
        .padding(16)
        .frame(width: 339, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
    
    // MARK: - Subviews
    
    private func interpretationRow(_ interpretation: CulturalInterpretation) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Text(interpretation.emoji)
                    .font(.system(size: 17))
                
                Text(interpretation.culture)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(.black.opacity(0.8))
            }
            
            Text(interpretation.interpretation)
                .font(.system(size: 13))
                .foregroundColor(.black)
                .lineLimit(2)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 32, alignment: .topLeading)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
}

// MARK: - Preview

#Preview {
    CulturalInterpretationSection(interpretations: [
        CulturalInterpretation(emoji: "🇯🇵", culture: "Japan", interpretation: "Associated with quiet respect and emotional restraint", sentiment: .positive),
        CulturalInterpretation(emoji: "🇺🇸", culture: "Western", interpretation: "Symbol of romantic love and passion", sentiment: .positive),
        CulturalInterpretation(emoji: "🇸🇦", culture: "Middle Eastern", interpretation: "Symbol of beauty and love, referenced in poetry", sentiment: .positive)
    ])
    .padding()
    .background(Color("SecondaryBackground"))
}
