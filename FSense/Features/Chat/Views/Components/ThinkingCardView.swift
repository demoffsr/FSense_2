import SwiftUI

/// Real-time pipeline progress card
struct ThinkingCardView: View {

    @ObservedObject var eventService = PipelineEventService.shared

    let isExpanded: Bool
    let onToggle: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerView

            // Expandable content with real-time steps
            if isExpanded {
                expandedContent
            }
        }
        .padding(.vertical, 12)
        .padding(.horizontal, 14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(white: 0.96))
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
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

    private var expandedContent: some View {
        VStack(alignment: .leading, spacing: 6) {
            Divider()
                .padding(.vertical, 10)

            // Directly observe eventService.steps
            ForEach(eventService.steps) { step in
                ProgressStepRow(step: step)
            }
        }
    }
}

// MARK: - Individual Step Row

struct ProgressStepRow: View {

    let step: ProgressStep

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
        .animation(.easeInOut(duration: 0.15), value: step.status)
    }

    @ViewBuilder
    private var statusIcon: some View {
        switch step.status {
        case .pending:
            Circle()
                .fill(Color.gray.opacity(0.2))
                .frame(width: 8, height: 8)

        case .active:
            // Pulsing animation for active
            Circle()
                .fill(Color.purple)
                .frame(width: 8, height: 8)
                .overlay(
                    Circle()
                        .stroke(Color.purple.opacity(0.5), lineWidth: 2)
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
        case .pending: return .gray.opacity(0.5)
        case .active: return .black
        case .completed: return .black.opacity(0.7)
        }
    }
}

#Preview {
    ThinkingCardView(
        isExpanded: true,
        onToggle: {}
    )
    .padding()
}
