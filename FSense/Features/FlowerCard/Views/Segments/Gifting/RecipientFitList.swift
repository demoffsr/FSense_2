import SwiftUI

/// List showing how appropriate this flower is for different recipient types
struct RecipientFitList: View {
    
    let recipients: [RecipientFit]
    @State private var selectedRecipient: RecipientFit?
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header
            Text("Recipient fit")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            // Recipients list
            VStack(alignment: .leading, spacing: 8) {
                ForEach(recipients) { recipient in
                    recipientRow(recipient)
                        .onTapGesture {
                            selectedRecipient = recipient
                        }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(.white)
        .cornerRadius(24)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
        .navigationDestination(item: $selectedRecipient) { recipient in
            RecipientProfileView(recipient: recipient)
        }
    }
    
    // MARK: - Subviews
    
    private func recipientRow(_ recipient: RecipientFit) -> some View {
        HStack(alignment: .center) {
            // Avatar
            Image("ProfileImage")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 40, height: 40)
                .clipShape(Circle())
            
            // Name and note
            VStack(alignment: .leading, spacing: 2) {
                Text(recipient.recipientType)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(.black)
                
                if let note = recipient.note {
                    Text(note)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                }
            }
            
            Spacer()
            
            // Fit level badge
            HStack(alignment: .center, spacing: 10) {
                Text(fitLabel(for: recipient.fitLevel))
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(fitColor(for: recipient.fitLevel))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(fitColor(for: recipient.fitLevel).opacity(0.1))
            .cornerRadius(12)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .center)
        .background(.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
    }
    
    // MARK: - Helpers
    
    private func fitLabel(for fit: GiftSuitability) -> String {
        switch fit {
        case .excellent: return "Perfect"
        case .good: return "Good"
        case .moderate: return "Maybe"
        case .risky: return "Risky"
        case .notRecommended: return "Avoid"
        }
    }
    
    private func fitColor(for fit: GiftSuitability) -> Color {
        switch fit {
        case .excellent: return Color(red: 0, green: 0.76, blue: 0.14)
        case .good: return Color(red: 0, green: 0.76, blue: 0.14)
        case .moderate: return .orange
        case .risky: return .red.opacity(0.8)
        case .notRecommended: return .red
        }
    }
}

// MARK: - Recipient Profile View

struct RecipientProfileView: View {
    @Environment(\.dismiss) private var dismiss
    let recipient: RecipientFit
    
    var body: some View {
        VStack(spacing: 24) {
            // Avatar
            Image("ProfileImage")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 100, height: 100)
                .clipShape(Circle())
            
            // Name
            Text(recipient.recipientType)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.black)
            
            if let note = recipient.note {
                Text(note)
                    .font(.system(size: 15))
                    .foregroundColor(.secondary)
            }
            
            Spacer()
        }
        .padding(.top, 60)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(red: 0.97, green: 0.97, blue: 0.95))
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    dismiss()
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("Back")
                    }
                }
            }
        }
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        RecipientFitList(recipients: [
            RecipientFit(recipientType: "Romantic Partner", fitLevel: .excellent, note: "Classic choice"),
            RecipientFit(recipientType: "New Crush", fitLevel: .risky, note: "Consider lighter options first"),
            RecipientFit(recipientType: "Friend", fitLevel: .notRecommended, note: "May send wrong signals")
        ])
        .padding()
        .background(Color(red: 0.97, green: 0.97, blue: 0.95))
    }
}
