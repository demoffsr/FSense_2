import SwiftUI

/// Section showing how appropriate this flower is for different relationship types
struct RelationshipContextSection: View {
    
    let contexts: [RelationshipContext]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Relationship context")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 16) {
                ForEach(contexts) { context in
                    contextRow(context)
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
    
    private func contextRow(_ context: RelationshipContext) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Text(relationshipEmoji(for: context.relationshipType))
                    .font(.system(size: 17))
                
                Text(context.relationshipType)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(.black.opacity(0.8))
            }
            
            Text(context.guidance.isEmpty ? " " : context.guidance)
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
    
    // MARK: - Helpers
    
    private func relationshipEmoji(for type: String) -> String {
        switch type.lowercased() {
        case let t where t.contains("romantic") || t.contains("partner"):
            return "💕"
        case let t where t.contains("new") || t.contains("dating"):
            return "💫"
        case let t where t.contains("professional") || t.contains("work"):
            return "💼"
        case let t where t.contains("friend"):
            return "🤝"
        case let t where t.contains("family"):
            return "👨‍👩‍👧"
        default:
            return "💐"
        }
    }
}

// MARK: - Preview

#Preview {
    RelationshipContextSection(contexts: [
        RelationshipContext(relationshipType: "Romantic Partner", appropriateness: .highlyAppropriate, guidance: "Perfect expression of ongoing love"),
        RelationshipContext(relationshipType: "New Relationship", appropriateness: .neutral, guidance: "May be too intense for early dating stages"),
        RelationshipContext(relationshipType: "Professional", appropriateness: .inappropriate, guidance: "Could be misinterpreted; choose neutral flowers")
    ])
    .padding()
    .background(Color(red: 0.97, green: 0.97, blue: 0.95))
}
