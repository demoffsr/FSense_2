import SwiftUI

struct ProfileView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var archiveService = FlowerArchiveService.shared
    @StateObject private var chatArchiveService = ChatArchiveService.shared
    @State private var navigateToArchive = false
    @State private var navigateToChatArchive = false
    @State private var navigateToSettings = false

    var body: some View {
        VStack(spacing: 0) {
            Text("Profile")
                .font(.largeTitle)
                .fontWeight(.bold)
                .padding(.top, 60)
                .padding(.bottom, 40)

            // MARK: - Menu Options
            VStack(spacing: 0) {
                ProfileMenuButton(
                    icon: "archivebox.fill",
                    title: "Flower Archive",
                    subtitle: archiveSubtitle
                ) {
                    navigateToArchive = true
                }

                Divider()
                    .padding(.leading, 60)

                ProfileMenuButton(
                    icon: "bubble.left.and.bubble.right.fill",
                    title: "Chat Archive",
                    subtitle: chatArchiveSubtitle
                ) {
                    navigateToChatArchive = true
                }

                Divider()
                    .padding(.leading, 60)

                ProfileMenuButton(
                    icon: "gearshape.fill",
                    title: "Settings",
                    subtitle: settingsSubtitle
                ) {
                    navigateToSettings = true
                }
            }
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 16)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
        .navigationBarBackButtonHidden(true)
        .navigationDestination(isPresented: $navigateToArchive) {
            FlowerArchiveView()
        }
        .navigationDestination(isPresented: $navigateToChatArchive) {
            ChatArchiveView()
        }
        .navigationDestination(isPresented: $navigateToSettings) {
            SettingsView()
        }
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
        }
    }

    // MARK: - Computed Properties

    private var archiveSubtitle: String {
        let count = archiveService.flowerCount
        if count == 0 {
            return "No flowers yet"
        } else if count == 1 {
            return "1 flower saved"
        } else {
            return "\(count) flowers saved"
        }
    }

    private var chatArchiveSubtitle: String {
        let count = chatArchiveService.sessionCount
        if count == 0 {
            return "No chats yet"
        } else if count == 1 {
            return "1 chat saved"
        } else {
            return "\(count) chats saved"
        }
    }

    private var settingsSubtitle: String {
        "\(UserSettings.selectedCity), \(UserSettings.selectedRegion)"
    }
}

// MARK: - Profile Menu Button

struct ProfileMenuButton: View {
    @Environment(\.themeAccent) private var themeAccent

    let icon: String
    let title: String
    let subtitle: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(themeAccent)
                    .frame(width: 44, height: 44)
                    .background(themeAccent.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                VStack(alignment: .leading, spacing: 2) {
                    Text(title)
                        .font(.system(size: 17, weight: .medium))
                        .foregroundColor(.primary)

                    Text(subtitle)
                        .font(.system(size: 14))
                        .foregroundColor(.secondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.secondary.opacity(0.5))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    NavigationStack {
        ProfileView()
    }
}
