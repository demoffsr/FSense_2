import SwiftUI

// MARK: - Chat Search Bar (Inline in Toolbar)

struct ChatSearchBar: View {
    @Binding var searchText: String
    @Binding var isSearching: Bool
    @FocusState.Binding var isFocused: Bool

    // Match the shadow from input area
    private static let lightShadowColor = Color.black.opacity(0.08)

    var body: some View {
        HStack(spacing: 12) {
            // Search field with glass effect (matching input style)
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundStyle(.secondary)

                TextField("Search", text: $searchText)
                    .font(.system(size: 16))
                    .focused($isFocused)
                    .submitLabel(.search)
            }
            .padding(.leading, 18)
            .padding(.trailing, 10)
            .frame(height: 50)
            .glassEffect(.clear.tint(.white.opacity(0.1)).interactive(), in: Capsule())
            .compositingGroup()
            .shadow(color: Self.lightShadowColor, radius: 12, x: 0, y: 4)

            // Close button (matching plus button style)
            Button {
                withAnimation(.spring(response: 0.35, dampingFraction: 0.9)) {
                    isFocused = false
                    searchText = ""
                    isSearching = false
                }
            } label: {
                Image(systemName: "xmark")
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(.black)
                    .frame(width: 50, height: 50)
                    .glassEffect(.clear.tint(.white.opacity(0.1)).interactive(), in: .circle)
                    .compositingGroup()
                    .shadow(color: Self.lightShadowColor, radius: 12, x: 0, y: 4)
            }
        }
        .padding(.horizontal, 20)
        .transition(.asymmetric(
            insertion: .opacity.combined(with: .scale(scale: 0.95)).animation(.spring(response: 0.35, dampingFraction: 0.85)),
            removal: .opacity.animation(.easeOut(duration: 0.2))
        ))
    }
}

// MARK: - Search Matching Logic

extension ChatMessage {
    /// Check if message matches search query
    func matchesSearch(_ query: String) -> Bool {
        guard !query.isEmpty else { return true }
        let lowercasedQuery = query.lowercased()

        switch content {
        case .text(let text):
            return text.lowercased().contains(lowercasedQuery)

        case .textWithImage(let text, _):
            return text.lowercased().contains(lowercasedQuery)

        case .acknowledgement(let text):
            return text.lowercased().contains(lowercasedQuery)

        case .recommendation(let rec):
            return rec.flowerName.lowercased().contains(lowercasedQuery) ||
                   rec.meaning.lowercased().contains(lowercasedQuery) ||
                   rec.explanation.lowercased().contains(lowercasedQuery)

        case .thinking, .followUp, .typing, .budgetQuestion:
            return false
        }
    }

    /// Get searchable text preview
    var searchableText: String? {
        switch content {
        case .text(let text): return text
        case .textWithImage(let text, _): return text.isEmpty ? nil : text
        case .acknowledgement(let text): return text
        case .recommendation(let rec): return rec.flowerName
        default: return nil
        }
    }
}

// MARK: - Message Highlight Modifier

struct SearchHighlightModifier: ViewModifier {
    let isHighlighted: Bool
    let isSearchActive: Bool
    let matchesSearch: Bool

    func body(content: Content) -> some View {
        content
            .opacity(isSearchActive && !matchesSearch ? 0.3 : 1.0)
            .overlay {
                if isHighlighted {
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(ChatDesign.Colors.accentPurple, lineWidth: 2.5)
                        .padding(-6)
                }
            }
            .animation(.easeInOut(duration: 0.2), value: isHighlighted)
            .animation(.easeInOut(duration: 0.15), value: matchesSearch)
    }
}

extension View {
    func searchHighlight(isHighlighted: Bool, isSearchActive: Bool, matchesSearch: Bool) -> some View {
        modifier(SearchHighlightModifier(
            isHighlighted: isHighlighted,
            isSearchActive: isSearchActive,
            matchesSearch: matchesSearch
        ))
    }
}
