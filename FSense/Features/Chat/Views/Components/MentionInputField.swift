import SwiftUI

/// TextField with @mention picker that slides up from input
struct MentionInputField: View {
    @Binding var text: String
    let placeholder: String
    var isEnabled: Bool = true
    let onSend: () -> Void

    @State private var mentionQuery: String?
    @FocusState private var isFocused: Bool
    @StateObject private var profilesService = LovedOnesService.shared

    private var showMentions: Bool {
        mentionQuery != nil && isFocused
    }

    private var matchingProfiles: [LovedOneProfile] {
        guard let query = mentionQuery else { return [] }
        return profilesService.profilesMatching(mention: query)
    }

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Mentions list - appears ABOVE input
            if showMentions {
                mentionsList
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            // Input bar - always at bottom
            inputBar
        }
        .animation(.spring(response: 0.3, dampingFraction: 0.8), value: showMentions)
        .onChange(of: text) { _, newValue in
            mentionQuery = extractMentionQuery(from: newValue)
        }
    }

    // MARK: - Mentions List

    private var mentionsList: some View {
        VStack(spacing: 12) {
            if matchingProfiles.isEmpty {
                emptyState
            } else {
                ForEach(matchingProfiles.prefix(5)) { profile in
                    Button {
                        selectProfile(profile)
                    } label: {
                        mentionRow(profile)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity)
        .background(Color(red: 0.976, green: 0.976, blue: 0.976))
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(Color.white, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
        .padding(.horizontal, 20)
        .padding(.bottom, 8)
    }

    private func mentionRow(_ profile: LovedOneProfile) -> some View {
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

    private var emptyState: some View {
        HStack(spacing: 10) {
            Image(systemName: profilesService.profiles.isEmpty ? "person.badge.plus" : "magnifyingglass")
                .font(.system(size: 16))
                .foregroundColor(.secondary)

            Text(profilesService.profiles.isEmpty ? "No users yet" : "No matches")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.secondary)

            Spacer()
        }
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        HStack(spacing: 8) {
            TextField(placeholder, text: $text)
                .font(.system(size: 16))
                .focused($isFocused)
                .disabled(!isEnabled)
                .submitLabel(.send)
                .onSubmit {
                    if canSend { onSend() }
                }

            sendButton
        }
        .padding(.leading, 16)
        .padding(.trailing, 10)
        .padding(.vertical, 12)
        .background(Color(red: 0.976, green: 0.976, blue: 0.976))
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(Color.white, lineWidth: 1)
        )
        .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
        .padding(.horizontal, 20)
    }

    private var sendButton: some View {
        Button(action: onSend) {
            Image(systemName: "arrow.up")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)
                .frame(width: 30, height: 30)
                .background(
                    Circle().fill(
                        LinearGradient(
                            colors: [
                                Color(red: 0.55, green: 0, blue: 0.92),
                                Color(red: 0.91, green: 0.04, blue: 0.79)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                )
        }
        .disabled(!canSend)
        .opacity(canSend ? 1 : 0.5)
    }

    private var canSend: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && isEnabled
    }

    // MARK: - Mention Logic

    private func extractMentionQuery(from text: String) -> String? {
        guard let atIndex = text.lastIndex(of: "@") else { return nil }
        let afterAt = text[text.index(after: atIndex)...]
        if afterAt.contains(" ") { return nil }
        return String(afterAt)
    }

    private func selectProfile(_ profile: LovedOneProfile) {
        guard let atIndex = text.lastIndex(of: "@") else { return }
        let beforeAt = String(text[..<atIndex])
        text = "\(beforeAt)@\(profile.displayName) "
        mentionQuery = nil
    }
}

// MARK: - Preview

#Preview("With mentions") {
    MentionInputField(
        text: .constant("@An"),
        placeholder: "Ask me about...",
        onSend: { }
    )
    .background(Color(white: 0.97))
}

#Preview("Empty") {
    MentionInputField(
        text: .constant(""),
        placeholder: "Ask me about...",
        onSend: { }
    )
    .background(Color(white: 0.97))
}
