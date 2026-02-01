import SwiftUI

/// Card displaying an upcoming event with countdown
struct UpcomingEventCard: View {
    @Environment(\.themeAccent) private var themeAccent

    let event: ImportantDate
    var showFullDate: Bool = true

    var body: some View {
        HStack(spacing: 14) {
            // Event icon
            Image(systemName: event.type.icon)
                .font(.system(size: 20))
                .foregroundColor(iconColor)
                .frame(width: 40, height: 40)
                .background(iconColor.opacity(0.12))
                .clipShape(Circle())

            VStack(alignment: .leading, spacing: 4) {
                // Event title with countdown
                HStack(spacing: 8) {
                    Text(event.title)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(.primary)

                    Text(event.countdownText)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(countdownColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(countdownColor.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                }

                if showFullDate {
                    Text(formattedDate)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            if event.notificationEnabled {
                Image(systemName: "bell.fill")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary.opacity(0.4))
            }
        }
        .padding(14)
        .background(Color.white)
        .overlay(alignment: .leading) {
            LinearGradient(
                colors: [
                    Color("AccentPurple"),
                    Color("AccentPink")
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(width: 5)
        }
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: .black.opacity(0.06), radius: 8, x: 0, y: 2)
    }

    // MARK: - Computed Properties

    private var iconColor: Color {
        switch event.type {
        case .birthday:
            return .orange
        case .anniversary:
            return .pink
        case .custom:
            return themeAccent
        }
    }

    private var countdownColor: Color {
        let days = event.daysUntilNext
        if days == 0 {
            return .green
        } else if days <= 7 {
            return .orange
        } else {
            return .secondary
        }
    }

    private var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d, yyyy"
        return formatter.string(from: event.date)
    }
}

/// Compact event row for list views
struct CompactEventRow: View {
    let event: ImportantDate

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: event.type.icon)
                .font(.system(size: 14))
                .foregroundColor(.secondary)

            Text(event.title)
                .font(.system(size: 14))
                .foregroundColor(.primary)

            Spacer()

            Text(event.countdownText)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(event.daysUntilNext <= 7 ? .orange : .secondary)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        UpcomingEventCard(
            event: ImportantDate(
                title: "Birthday",
                date: Calendar.current.date(byAdding: .day, value: 23, to: Date())!,
                type: .birthday
            )
        )

        UpcomingEventCard(
            event: ImportantDate(
                title: "Anniversary",
                date: Calendar.current.date(byAdding: .day, value: 3, to: Date())!,
                type: .anniversary
            )
        )

        UpcomingEventCard(
            event: ImportantDate(
                title: "Valentine's Day",
                date: Date(),
                type: .custom
            )
        )
    }
    .padding()
    .background(Color(white: 0.95))
}
