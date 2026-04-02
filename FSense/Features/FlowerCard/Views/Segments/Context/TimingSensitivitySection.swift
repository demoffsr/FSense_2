import SwiftUI

/// Section showing timing considerations for gifting this flower
struct TimingSensitivitySection: View {
    
    let sensitivities: [TimingSensitivity]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Timing sensitivity")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 16) {
                ForEach(sensitivities) { sensitivity in
                    sensitivityRow(sensitivity)
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
    
    private func sensitivityRow(_ sensitivity: TimingSensitivity) -> some View {
        HStack(alignment: .center, spacing: 6) {
            Text(sensitivity.note)
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
    TimingSensitivitySection(sensitivities: [
        TimingSensitivity(timing: "After tension", sensitivity: .high, note: "Works best after emotional tension or misunderstanding"),
        TimingSensitivity(timing: "Unexpected moments", sensitivity: .low, note: "Spontaneous gifts often have the greatest impact"),
        TimingSensitivity(timing: "Public settings", sensitivity: .moderate, note: "Consider if recipient would be comfortable")
    ])
    .padding()
    .background(Color("SecondaryBackground"))
}
