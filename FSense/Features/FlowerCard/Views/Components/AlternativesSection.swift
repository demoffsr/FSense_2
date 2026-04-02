import SwiftUI

/// "Также подходят:" section displaying alternative flower recommendations.
/// Shows a horizontal scrollable list of alternative flower cards.
struct AlternativesSection: View {
    let alternatives: [AlternativeFlower]
    let onFlowerTap: (AlternativeFlower) -> Void

    var body: some View {
        if !alternatives.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                // Section header
                Text("Также подходят:")
                    .font(.headline)
                    .foregroundColor(.primary)

                // Horizontal scroll of alternatives
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 16) {
                        ForEach(alternatives) { flower in
                            AlternativeFlowerCell(flower: flower) {
                                onFlowerTap(flower)
                            }
                        }
                    }
                    .padding(.horizontal, 2)
                    .padding(.vertical, 4)
                }
            }
            .padding(.top, 16)
        }
    }
}

#Preview {
    VStack {
        AlternativesSection(alternatives: AlternativeFlower.mocks) { flower in
            print("Selected: \(flower.name)")
        }
    }
    .padding()
}
