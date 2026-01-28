import SwiftUI

/// Meanings chips section
struct MeaningsSection: View {
    let meanings: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Meanings")
                .font(.headline)

            FlowLayout(spacing: 8) {
                ForEach(meanings, id: \.self) { meaning in
                    MeaningChip(text: meaning)
                }
            }
        }
    }
}

/// Single meaning chip
struct MeaningChip: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.subheadline)
            .foregroundColor(.primary)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color.accentColor.opacity(0.1))
            .clipShape(Capsule())
    }
}

// NOTE: FlowLayout is defined in MeaningsChipsView.swift and reused here

// MARK: - Preview

#Preview {
    MeaningsSection(meanings: ["Love", "Beauty", "Passion", "Romance", "Affection"])
        .padding()
}
