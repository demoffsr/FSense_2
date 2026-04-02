import SwiftUI

/// Row component for displaying a loved one in the list
struct LovedOneRowView: View {
    let profile: LovedOneProfile

    var body: some View {
        HStack(spacing: 12) {
            ProfileAvatarView(profile: profile, size: 46, showBorder: false)

            VStack(alignment: .leading, spacing: 3) {
                Text(profile.displayName)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.primary)
                    .lineLimit(1)

                HStack(spacing: 6) {
                    Text(profile.relationship.rawValue)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)

                    if let nextDate = profile.nextDate {
                        Text("•")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary.opacity(0.5))

                        HStack(spacing: 4) {
                            Image(systemName: nextDate.type.icon)
                                .font(.system(size: 11))
                            Text(nextDate.countdownText)
                        }
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(nextDate.daysUntilNext <= 7 ? .orange : .secondary)
                    }
                }
            }

            Spacer()

            // Allergy indicator
            if profile.hasAllergies {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 14))
                    .foregroundColor(.orange)
            }

            Image(systemName: "chevron.right")
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(.secondary.opacity(0.4))
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
        .shadow(color: .black.opacity(0.06), radius: 8, x: 0, y: 2)
    }
}

#Preview {
    VStack(spacing: 12) {
        LovedOneRowView(
            profile: LovedOneProfile(
                name: "Sarah Johnson",
                nickname: "Sarah",
                relationship: .girlfriend,
                birthday: ImportantDate(
                    title: "Birthday",
                    date: Calendar.current.date(byAdding: .day, value: 23, to: Date())!,
                    type: .birthday
                ),
                tasteProfile: TasteProfile(allergies: ["Lilies"])
            )
        )

        LovedOneRowView(
            profile: LovedOneProfile(
                name: "Mom",
                relationship: .mom
            )
        )

        LovedOneRowView(
            profile: LovedOneProfile(
                name: "Alex Thompson",
                relationship: .closeFriend,
                anniversary: ImportantDate(
                    title: "Friendship Day",
                    date: Calendar.current.date(byAdding: .day, value: 3, to: Date())!,
                    type: .custom
                )
            )
        )
    }
    .padding()
    .background(Color(white: 0.95))
}
