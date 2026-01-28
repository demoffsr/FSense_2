import SwiftUI

/// Real-time pipeline progress card
struct ThinkingCardView: View {

    let steps: [ProgressStep]
    let isExpanded: Bool
    let onToggle: () -> Void

    // Static shadow color to avoid recreation on each render
    private static let shadowColor = Color.black.opacity(0.1)

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            // Expandable content with real-time steps
            if isExpanded {
                expandedContent
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(16)
        .compositingGroup()
        .shadow(color: Self.shadowColor, radius: 10.9, x: 0, y: 2)
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.easeInOut(duration: 0.2)) {
                onToggle()
            }
        }
    }

    // MARK: - Header

    private var headerView: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 2) {
                Text("Here's how I thought about this")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(.black.opacity(0.8))

                if !isExpanded {
                    Text("Tap to see my reasoning")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            Image(systemName: "chevron.down")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.gray)
                .rotationEffect(.degrees(isExpanded ? 180 : 0))
        }
    }

    // MARK: - Expanded Content

    /// Stable identifier for animation - count of completed/active steps
    private var stepsAnimationKey: Int {
        steps.reduce(0) { acc, step in
            switch step.status {
            case .completed: return acc + 10
            case .active: return acc + 1
            case .pending: return acc
            }
        }
    }

    private var expandedContent: some View {
        VStack(alignment: .leading, spacing: 6) {
            Divider()
                .padding(.vertical, 10)

            ForEach(steps, id: \.id) { step in
                ProgressStepRow(step: step)
            }
        }
        .animation(.easeInOut(duration: 0.15), value: stepsAnimationKey)
    }
}

// MARK: - Individual Step Row

struct ProgressStepRow: View {

    let step: ProgressStep

    // Static colors to avoid recreation on each render
    private static let pendingTextColor = Color.gray.opacity(0.5)
    private static let activeTextColor = Color.black
    private static let completedTextColor = Color.black.opacity(0.7)
    private static let pendingCircleColor = Color.gray.opacity(0.2)
    private static let activePulseColor = Color.purple.opacity(0.5)

    var body: some View {
        HStack(alignment: .center, spacing: 10) {
            // Status indicator
            statusIcon
                .frame(width: 20, height: 20)

            // Emoji + Text
            Text("\(step.emoji) \(step.text)")
                .font(.system(size: 13))
                .foregroundColor(textColor)

            Spacer()
        }
        .padding(.vertical, 3)
    }

    @ViewBuilder
    private var statusIcon: some View {
        switch step.status {
        case .pending:
            Circle()
                .fill(Self.pendingCircleColor)
                .frame(width: 8, height: 8)

        case .active:
            Circle()
                .fill(Color.purple)
                .frame(width: 8, height: 8)
                .overlay(
                    Circle()
                        .stroke(Self.activePulseColor, lineWidth: 2)
                        .scaleEffect(1.5)
                )

        case .completed:
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 14))
                .foregroundColor(.green)
        }
    }

    private var textColor: Color {
        switch step.status {
        case .pending: return Self.pendingTextColor
        case .active: return Self.activeTextColor
        case .completed: return Self.completedTextColor
        }
    }
}

#Preview {
    ThinkingCardView(
        steps: [
            ProgressStep(id: "1", emoji: "🎯", text: "Analyzing intent", status: .completed),
            ProgressStep(id: "2", emoji: "💞", text: "Understanding emotions", status: .active),
            ProgressStep(id: "3", emoji: "🌸", text: "Matching flowers", status: .pending)
        ],
        isExpanded: true,
        onToggle: {}
    )
    .padding()
}
