import SwiftUI

/// Card displaying the overall context summary
struct ContextSummaryCard: View {
    
    let summary: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Context summary")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            Text(summary)
                .font(.system(size: 15))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .padding(16)
        .frame(maxWidth: .infinity, minHeight: 103, maxHeight: 103, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
}

// MARK: - Preview

#Preview {
    ContextSummaryCard(
        summary: "Best suited for emotionally sensitive situations where subtlety and restraint are important."
    )
    .padding()
    .background(Color(red: 0.97, green: 0.97, blue: 0.95))
}
