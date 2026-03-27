import SwiftUI

/// Autocomplete overlay for @mentions in chat input
struct MentionAutocompleteView: View {
    let searchText: String
    let onSelect: (LovedOneProfile) -> Void

    @StateObject private var service = LovedOnesService.shared

    private var matchingProfiles: [LovedOneProfile] {
        service.profilesMatching(mention: searchText)
    }

    var body: some View {
        VStack(spacing: 0) {
            if matchingProfiles.isEmpty {
                // Empty state - no profiles or no matches
                HStack(spacing: 12) {
                    Image(systemName: service.profiles.isEmpty ? "person.badge.plus" : "magnifyingglass")
                        .font(.system(size: 20))
                        .foregroundColor(.secondary)

                    VStack(alignment: .leading, spacing: 2) {
                        Text(service.profiles.isEmpty ? "No users yet" : "No matches")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(.primary)

                        Text(service.profiles.isEmpty ? "Add users in the Users screen" : "Try a different name")
                            .font(.system(size: 13))
                            .foregroundColor(.secondary)
                    }

                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 14)
            } else {
                VStack(spacing: 12) {
                    ForEach(matchingProfiles.prefix(5)) { profile in
                        Button {
                            onSelect(profile)
                        } label: {
                            MentionAutocompleteRow(profile: profile)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
        .padding(14)
        .background(Color(red: 0.976, green: 0.976, blue: 0.976))
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(Color.white, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
    }
}

/// Individual row in the autocomplete list - simple avatar + name design
struct MentionAutocompleteRow: View {
    let profile: LovedOneProfile

    var body: some View {
        HStack(spacing: 10) {
            CompactProfileAvatarView(profile: profile, size: 32)

            Text(profile.displayName)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.black)
                .tracking(-0.08)

            Spacer()
        }
        .contentShape(Rectangle())
    }
}

/// Mention token displayed in the input field
struct MentionTokenView: View {
    let profile: LovedOneProfile
    let onRemove: () -> Void

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: profile.category.icon)
                .font(.system(size: 11))

            Text(profile.displayName)
                .font(.system(size: 14, weight: .medium))

            Button(action: onRemove) {
                Image(systemName: "xmark")
                    .font(.system(size: 9, weight: .bold))
            }
        }
        .foregroundColor(profile.category.color)
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(profile.category.color.opacity(0.12))
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }
}

// MARK: - Mention Parser

/// Utility for parsing @mentions from text
struct MentionParser {
    /// Extract mention text being typed (text after last @)
    static func extractMentionQuery(from text: String) -> String? {
        guard let atIndex = text.lastIndex(of: "@") else { return nil }

        let afterAt = text[text.index(after: atIndex)...]

        // If there's a space after the @, no active mention
        if afterAt.contains(" ") { return nil }

        return String(afterAt)
    }

    /// Check if user is currently typing a mention
    static func isTypingMention(in text: String) -> Bool {
        extractMentionQuery(from: text) != nil
    }

    /// Replace the current mention being typed with the selected profile
    static func replaceMention(in text: String, with profile: LovedOneProfile) -> String {
        guard let atIndex = text.lastIndex(of: "@") else { return text }

        let beforeAt = String(text[..<atIndex])
        return "\(beforeAt)@\(profile.displayName) "
    }
}

#Preview {
    VStack {
        Spacer()

        MentionAutocompleteView(
            searchText: "sar",
            onSelect: { profile in
                print("Selected: \(profile.name)")
            }
        )

        HStack {
            MentionTokenView(
                profile: LovedOneProfile(
                    name: "Sarah",
                    relationship: .girlfriend
                ),
                onRemove: { }
            )

            Text("what flowers should I get?")
                .font(.system(size: 15))
        }
        .padding()
        .background(Color(white: 0.96))
    }
}
