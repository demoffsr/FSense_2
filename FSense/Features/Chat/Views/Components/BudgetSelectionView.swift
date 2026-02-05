import SwiftUI

/// Budget selection view shown before running the flower recommendation pipeline
/// Allows user to specify their budget preference
struct BudgetSelectionView: View {

    @Environment(\.themeAccent) private var themeAccent

    let onSelect: (BudgetOption) -> Void

    // Static shadow for consistent styling
    private static let shadowColor = Color.black.opacity(0.08)

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            // Question header
            Text("What's your budget?")
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.black.opacity(0.8))

            // Budget option chips in a flow layout
            FlowLayout(spacing: 8) {
                ForEach(BudgetOption.allCases, id: \.self) { option in
                    budgetChip(option)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: Self.shadowColor, radius: 6, x: 0, y: 2)
    }

    // MARK: - Budget Chip

    private func budgetChip(_ option: BudgetOption) -> some View {
        Button {
            onSelect(option)
        } label: {
            HStack(spacing: 4) {
                Text(option.displayName)
                    .font(.system(size: 14, weight: .medium))

                if option.hasPriceHint {
                    Text(option.priceHint)
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(themeAccent.opacity(0.1))
            .foregroundColor(themeAccent)
            .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Preview

#Preview {
    BudgetSelectionView { option in
        print("Selected: \(option.displayName)")
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
