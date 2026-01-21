import SwiftUI

/// Horizontal carousel showing "When to gift" and "When to avoid" cards
struct WhenToGiftList: View {
    
    let whenToGiftItems: [String]
    let whenToAvoidItems: [String]
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(alignment: .top, spacing: 16) {
                // When to gift card
                whenToGiftCard
                
                // When to avoid card
                whenToAvoidCard
            }
            .padding(.vertical, 4) // Minimal padding for shadow
        }
        .scrollClipDisabled()
    }
    
    // MARK: - When to Gift Card
    
    private var whenToGiftCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("When to gift")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 8) {
                ForEach(whenToGiftItems, id: \.self) { item in
                    giftRow(item, isPositive: true)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16)
        .frame(width: 334, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
    
    // MARK: - When to Avoid Card
    
    private var whenToAvoidCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("When to avoid")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 8) {
                ForEach(whenToAvoidItems, id: \.self) { item in
                    giftRow(item, isPositive: false)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16)
        .frame(width: 334, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
    
    // MARK: - Row Item
    
    private func giftRow(_ text: String, isPositive: Bool) -> some View {
        HStack(alignment: .center, spacing: 6) {
            Image(systemName: isPositive ? "checkmark.circle" : "xmark.circle")
                .font(.system(size: 15))
                .foregroundColor(isPositive ? Color(red: 0, green: 0.76, blue: 0.14) : .red)
            
            Text(text)
                .font(.system(size: 15))
                .foregroundColor(.black)
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
    WhenToGiftList(
        whenToGiftItems: [
            "Reconciliation",
            "Apology",
            "Anniversary"
        ],
        whenToAvoidItems: [
            "First Date",
            "Business Meeting",
            "Casual Friendship"
        ]
    )
    .padding()
    .background(Color(red: 0.97, green: 0.97, blue: 0.95))
}
