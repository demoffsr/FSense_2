import SwiftUI

struct MeaningsChipsView: View {
    
    let meanings: [String]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Meanings")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            VStack(alignment: .leading, spacing: 10) {
                FlowLayout(spacing: 10) {
                    ForEach(meanings, id: \.self) { meaning in
                        Text(meaning)
                            .font(.system(size: 15))
                            .foregroundColor(.black)
                            .padding(.horizontal, 24)
                            .padding(.vertical, 6)
                            .background(Color.white)
                            .cornerRadius(16)
                            .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .topLeading)
        }
        .frame(maxWidth: .infinity, alignment: .topLeading)
    }
}

// MARK: - Flow Layout

struct FlowLayout: Layout {
    var spacing: CGFloat = 10

    // Cache structure to avoid recomputing layout
    struct LayoutCache {
        var size: CGSize = .zero
        var positions: [CGPoint] = []
        var sizes: [CGSize] = []
        var proposalWidth: CGFloat?
    }

    func makeCache(subviews: Subviews) -> LayoutCache {
        LayoutCache()
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout LayoutCache) -> CGSize {
        updateCacheIfNeeded(proposal: proposal, subviews: subviews, cache: &cache)
        return cache.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout LayoutCache) {
        updateCacheIfNeeded(proposal: proposal, subviews: subviews, cache: &cache)

        for (index, subview) in subviews.enumerated() {
            subview.place(
                at: CGPoint(
                    x: bounds.minX + cache.positions[index].x,
                    y: bounds.minY + cache.positions[index].y
                ),
                proposal: ProposedViewSize(cache.sizes[index])
            )
        }
    }

    private func updateCacheIfNeeded(proposal: ProposedViewSize, subviews: Subviews, cache: inout LayoutCache) {
        // Only recompute if proposal changed
        guard cache.proposalWidth != proposal.width else { return }

        let maxWidth = proposal.width ?? .infinity
        cache.proposalWidth = proposal.width
        cache.positions = []
        cache.sizes = []

        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var totalHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            cache.sizes.append(size)

            if currentX + size.width > maxWidth && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }

            cache.positions.append(CGPoint(x: currentX, y: currentY))
            lineHeight = max(lineHeight, size.height)
            currentX += size.width + spacing
            totalHeight = currentY + lineHeight
        }

        cache.size = CGSize(width: maxWidth, height: totalHeight)
    }
}

#Preview {
    MeaningsChipsView(meanings: ["Apology", "Humility", "Reconciliation", "Sincerity", "Peace"])
        .padding()
        .background(Color(.systemGray6))
}
