import SwiftUI

/// Tag input with flow layout and add button
struct TagInputView: View {
    let title: String
    @Binding var tags: [String]
    var placeholder: String = "Add..."
    var tagColor: Color = .purple
    var showWarning: Bool = false

    @State private var isAdding = false
    @State private var newTagText = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            // Header
            HStack(spacing: 6) {
                if showWarning {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 14))
                        .foregroundColor(.orange)
                }

                Text(title)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(showWarning ? .orange : .secondary)
            }

            // Tags flow layout
            FlowLayout(spacing: 8) {
                ForEach(tags, id: \.self) { tag in
                    TagView(
                        text: tag,
                        color: tagColor,
                        onDelete: {
                            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                                tags.removeAll { $0 == tag }
                            }
                        }
                    )
                }

                // Add button or input field
                if isAdding {
                    addInputField
                } else {
                    addButton
                }
            }
        }
    }

    private var addButton: some View {
        Button {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                isAdding = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                isInputFocused = true
            }
        } label: {
            HStack(spacing: 4) {
                Image(systemName: "plus")
                    .font(.system(size: 12, weight: .bold))
                Text(placeholder)
                    .font(.system(size: 14, weight: .medium))
            }
            .foregroundColor(tagColor)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(tagColor.opacity(0.08))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(tagColor.opacity(0.2), style: StrokeStyle(lineWidth: 1, dash: [4]))
            )
        }
        .buttonStyle(.plain)
    }

    private var addInputField: some View {
        HStack(spacing: 8) {
            TextField("Enter name...", text: $newTagText)
                .font(.system(size: 14))
                .focused($isInputFocused)
                .submitLabel(.done)
                .onSubmit(addTag)
                .frame(minWidth: 100)

            Button {
                addTag()
            } label: {
                Image(systemName: "checkmark")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(.white)
                    .frame(width: 24, height: 24)
                    .background(tagColor)
                    .clipShape(Circle())
            }
            .disabled(newTagText.trimmingCharacters(in: .whitespaces).isEmpty)

            Button {
                cancelAdd()
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 11, weight: .bold))
                    .foregroundColor(.secondary)
                    .frame(width: 24, height: 24)
                    .background(Color(white: 0.9))
                    .clipShape(Circle())
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .shadow(color: .black.opacity(0.08), radius: 4, x: 0, y: 2)
    }

    private func addTag() {
        let trimmed = newTagText.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }

        // Avoid duplicates
        if !tags.contains(where: { $0.lowercased() == trimmed.lowercased() }) {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                tags.append(trimmed)
            }
        }

        newTagText = ""
        isAdding = false
        isInputFocused = false
    }

    private func cancelAdd() {
        newTagText = ""
        isAdding = false
        isInputFocused = false
    }
}

/// Individual tag with delete button
struct TagView: View {
    let text: String
    var color: Color = .purple
    let onDelete: () -> Void

    var body: some View {
        HStack(spacing: 6) {
            Text(text)
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(color)

            Button(action: onDelete) {
                Image(systemName: "xmark")
                    .font(.system(size: 10, weight: .bold))
                    .foregroundColor(color.opacity(0.6))
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(color.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}

#Preview {
    VStack(spacing: 24) {
        TagInputView(
            title: "Favorite Flowers",
            tags: .constant(["Roses", "Peonies", "Tulips"]),
            tagColor: .pink
        )

        TagInputView(
            title: "Allergies",
            tags: .constant(["Lilies"]),
            placeholder: "Add allergy...",
            tagColor: .orange,
            showWarning: true
        )

        TagInputView(
            title: "Dislikes",
            tags: .constant([]),
            placeholder: "Add flower...",
            tagColor: .gray
        )
    }
    .padding()
    .background(Color(white: 0.96))
}
