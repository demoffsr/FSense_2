import SwiftUI

struct LovedOneDetailView: View {
    let profile: LovedOneProfile

    @Environment(\.dismiss) private var dismiss
    @Environment(\.themeAccent) private var themeAccent
    @StateObject private var service = LovedOnesService.shared
    @State private var showingEditSheet = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Hero section
                heroSection
                    .padding(.top, 20)

                // Upcoming events
                if !profile.upcomingDates.isEmpty {
                    upcomingEventsSection
                }

                // Preferences section
                if profile.tasteProfile.hasPreferences {
                    preferencesSection
                }

                // Favorites section
                if !profile.tasteProfile.favoriteFlowers.isEmpty {
                    favoritesSection
                }

                // Dislikes section
                if !profile.tasteProfile.dislikedFlowers.isEmpty {
                    dislikesSection
                }

                // Allergies section (with warning)
                if profile.hasAllergies {
                    allergiesSection
                }

                // Notes section
                if let notes = profile.tasteProfile.notes, !notes.isEmpty {
                    notesSection(notes)
                }

                // CTA Button
                ctaButton
                    .padding(.top, 8)
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 100)
        }
        .background(Color(white: 0.96))
        .navigationTitle(profile.displayName)
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    dismiss()
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "chevron.left")
                        Text("Back")
                    }
                }
            }

            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    showingEditSheet = true
                } label: {
                    Text("Edit")
                        .font(.system(size: 16, weight: .medium))
                }
            }
        }
        .sheet(isPresented: $showingEditSheet) {
            NavigationStack {
                LovedOneEditView(mode: .edit(profile))
            }
        }
    }

    // MARK: - Hero Section

    private var heroSection: some View {
        VStack(spacing: 16) {
            ProfileAvatarView(profile: profile, size: 120)

            // Relationship badge
            HStack(spacing: 8) {
                Image(systemName: profile.category.icon)
                    .font(.system(size: 14))
                Text(profile.relationship.rawValue)
                    .font(.system(size: 15, weight: .semibold))
            }
            .foregroundColor(profile.category.color)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(profile.category.color.opacity(0.12))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            if let nickname = profile.nickname, nickname != profile.name {
                Text("aka \(profile.name)")
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
            }
        }
    }

    // MARK: - Upcoming Events Section

    private var upcomingEventsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Upcoming", icon: "calendar")

            VStack(spacing: 10) {
                ForEach(profile.upcomingDates.prefix(3)) { date in
                    UpcomingEventCard(event: date)
                }
            }
        }
    }

    // MARK: - Preferences Section

    private var preferencesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Preferences", icon: "slider.horizontal.3")

            VStack(spacing: 0) {
                if let style = profile.tasteProfile.flowerStyle {
                    preferenceRow(
                        icon: style.icon,
                        label: "Style",
                        value: style.rawValue
                    )
                    Divider().padding(.leading, 44)
                }

                if let budget = profile.tasteProfile.budgetRange {
                    preferenceRow(
                        icon: "dollarsign.circle",
                        label: "Budget",
                        value: budget.displayText
                    )
                    Divider().padding(.leading, 44)
                }

                if !profile.tasteProfile.preferredMoods.isEmpty {
                    moodPreferencesRow
                }
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
    }

    private func preferenceRow(icon: String, label: String, value: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(themeAccent)
                .frame(width: 32)

            Text(label)
                .font(.system(size: 15))
                .foregroundColor(.secondary)

            Spacer()

            Text(value)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(.primary)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 14)
    }

    private var moodPreferencesRow: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: "heart")
                .font(.system(size: 16))
                .foregroundColor(themeAccent)
                .frame(width: 32)
                .padding(.top, 2)

            Text("Moods")
                .font(.system(size: 15))
                .foregroundColor(.secondary)
                .padding(.top, 2)

            Spacer()

            FlowLayout(spacing: 6) {
                ForEach(profile.tasteProfile.preferredMoods) { mood in
                    Text(mood.rawValue)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(mood.color)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(mood.color.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 14)
    }

    // MARK: - Favorites Section

    private var favoritesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Favorites", icon: "heart.fill", color: .pink)

            tagsView(profile.tasteProfile.favoriteFlowers, color: .pink)
        }
    }

    // MARK: - Dislikes Section

    private var dislikesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Dislikes", icon: "hand.thumbsdown.fill", color: .gray)

            tagsView(profile.tasteProfile.dislikedFlowers, color: .gray)
        }
    }

    // MARK: - Allergies Section

    private var allergiesSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 16))
                    .foregroundColor(.orange)

                Text("Allergies")
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.primary)
            }

            tagsView(profile.tasteProfile.allergies, color: .orange)
        }
    }

    // MARK: - Notes Section

    private func notesSection(_ notes: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader("Notes", icon: "note.text")

            Text(notes)
                .font(.system(size: 15))
                .foregroundColor(.primary)
                .padding(14)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
    }

    // MARK: - CTA Button

    private var ctaButton: some View {
        Button {
            // TODO: Open chat with profile context
            service.markProfileAsUsed(profile)
        } label: {
            HStack(spacing: 10) {
                Image(systemName: "sparkles")
                Text("Start a Chat for \(profile.displayName)")
            }
            .font(.system(size: 17, weight: .semibold))
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                LinearGradient(
                    colors: [
                        Color("AccentPurple"),
                        Color("AccentPink")
                    ],
                    startPoint: .leading,
                    endPoint: .trailing
                )
            )
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: themeAccent.opacity(0.3), radius: 8, x: 0, y: 4)
        }
    }

    // MARK: - Helper Views

    private func sectionHeader(_ title: String, icon: String, color: Color? = nil) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color ?? themeAccent)

            Text(title)
                .font(.system(size: 17, weight: .semibold))
                .foregroundColor(.primary)
        }
    }

    private func tagsView(_ tags: [String], color: Color) -> some View {
        FlowLayout(spacing: 8) {
            ForEach(tags, id: \.self) { tag in
                Text(tag)
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(color)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(color.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
        }
    }
}

#Preview {
    NavigationStack {
        LovedOneDetailView(
            profile: LovedOneProfile(
                name: "Sarah Johnson",
                nickname: "Sarah",
                relationship: .girlfriend,
                birthday: ImportantDate(
                    title: "Birthday",
                    date: Calendar.current.date(byAdding: .day, value: 23, to: Date())!,
                    type: .birthday
                ),
                anniversary: ImportantDate(
                    title: "Anniversary",
                    date: Calendar.current.date(byAdding: .day, value: 47, to: Date())!,
                    type: .anniversary
                ),
                tasteProfile: TasteProfile(
                    flowerStyle: .modern,
                    budgetRange: .moderate,
                    preferredMoods: [.romantic, .elegant],
                    favoriteFlowers: ["Roses", "Peonies", "Tulips"],
                    dislikedFlowers: ["Carnations"],
                    allergies: ["Lilies"],
                    notes: "Prefers single stems over large bouquets. Loves pink and white colors."
                )
            )
        )
    }
}
