import SwiftUI

/// Single-select chip picker
struct ChipSelectionView<T: Identifiable & Hashable>: View where T: RawRepresentable, T.RawValue == String {
    let title: String
    let options: [T]
    @Binding var selection: T?
    var iconProvider: ((T) -> String)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.secondary)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    ForEach(options) { option in
                        ChipButton(
                            label: option.rawValue,
                            icon: iconProvider?(option),
                            isSelected: selection == option
                        ) {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                if selection == option {
                                    selection = nil
                                } else {
                                    selection = option
                                }
                            }
                        }
                    }
                }
                .padding(.horizontal, 1)
            }
        }
    }
}

/// Multi-select chip picker
struct MultiChipSelectionView<T: Identifiable & Hashable>: View where T: RawRepresentable, T.RawValue == String {
    @Environment(\.themeAccent) private var themeAccent

    let title: String
    let options: [T]
    @Binding var selection: [T]
    var iconProvider: ((T) -> String)? = nil
    var colorProvider: ((T) -> Color)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.secondary)

            FlowLayout(spacing: 10) {
                ForEach(options) { option in
                    let isSelected = selection.contains(option)
                    let color = colorProvider?(option) ?? themeAccent

                    ChipButton(
                        label: option.rawValue,
                        icon: iconProvider?(option),
                        isSelected: isSelected,
                        selectedColor: color
                    ) {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                            if isSelected {
                                selection.removeAll { $0 == option }
                            } else {
                                selection.append(option)
                            }
                        }
                    }
                }
            }
        }
    }
}

/// Individual chip button
struct ChipButton: View {
    @Environment(\.themeAccent) private var defaultAccent

    let label: String
    var icon: String? = nil
    let isSelected: Bool
    var selectedColor: Color? = nil
    let action: () -> Void

    private var effectiveColor: Color {
        selectedColor ?? defaultAccent
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 13))
                }

                Text(label)
                    .font(.system(size: 14, weight: isSelected ? .semibold : .medium))

                if isSelected {
                    Image(systemName: "checkmark")
                        .font(.system(size: 11, weight: .bold))
                }
            }
            .foregroundColor(isSelected ? effectiveColor : .primary)
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(isSelected ? effectiveColor.opacity(0.12) : Color(white: 0.95))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(isSelected ? effectiveColor.opacity(0.3) : Color.clear, lineWidth: 1)
            )
            .scaleEffect(isSelected ? 1.0 : 0.98)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    VStack(spacing: 24) {
        ChipSelectionView(
            title: "Flower Style",
            options: FlowerStyle.allCases,
            selection: .constant(.modern),
            iconProvider: { $0.icon }
        )

        MultiChipSelectionView(
            title: "Preferred Moods",
            options: MoodPreference.allCases,
            selection: .constant([.romantic, .elegant]),
            iconProvider: { $0.icon },
            colorProvider: { $0.color }
        )
    }
    .padding()
}
