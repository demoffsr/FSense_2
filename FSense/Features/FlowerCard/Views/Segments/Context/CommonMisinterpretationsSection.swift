import SwiftUI

/// Section showing common misinterpretations and clarifications
struct CommonMisinterpretationsSection: View {
    
    let misinterpretations: [CommonMisinterpretation]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Common misinterpretations")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 16) {
                ForEach(misinterpretations) { item in
                    misinterpretationRow(item)
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
    
    private func misinterpretationRow(_ item: CommonMisinterpretation) -> some View {
        HStack(alignment: .center, spacing: 6) {
            Text(item.clarification)
                .font(.system(size: 15))
                .foregroundColor(.black)
                .lineLimit(2)
                .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .padding(12)
        .frame(maxWidth: .infinity, minHeight: 60, alignment: .leading)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
}

// MARK: - Preview

#Preview {
    CommonMisinterpretationsSection(misinterpretations: [
        CommonMisinterpretation(
            misinterpretation: "Only for Valentine's",
            clarification: "Appropriate year-round for romantic partners and special occasions"
        ),
        CommonMisinterpretation(
            misinterpretation: "Any number is fine",
            clarification: "Different quantities carry different meanings in some cultures"
        )
    ])
    .padding()
    .background(Color("SecondaryBackground"))
}
