import SwiftUI

struct UsersView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.themeAccent) private var themeAccent
    @StateObject private var service = LovedOnesService.shared

    @State private var searchText = ""
    @State private var expandedCategories: Set<RelationshipCategory> = Set(RelationshipCategory.allCases)
    @State private var showingAddSheet = false
    @State private var selectedProfile: LovedOneProfile?

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // Search bar
                searchBar
                    .padding(.horizontal, 16)
                    .padding(.top, 8)
                    .padding(.bottom, 16)

                if filteredProfiles.isEmpty && !searchText.isEmpty {
                    emptySearchState
                } else if service.profiles.isEmpty {
                    emptyState
                } else {
                    categorySections
                }
            }
            .padding(.bottom, 100)
        }
        .background(Color(white: 0.96))
        .navigationTitle("Users")
        .navigationBarTitleDisplayMode(.large)
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
                    showingAddSheet = true
                } label: {
                    Image(systemName: "plus")
                        .font(.system(size: 17, weight: .semibold))
                }
            }
        }
        .sheet(isPresented: $showingAddSheet) {
            NavigationStack {
                LovedOneEditView(mode: .create)
            }
        }
        .navigationDestination(item: $selectedProfile) { profile in
            LovedOneDetailView(profile: profile)
        }
    }

    // MARK: - Computed Properties

    private var filteredProfiles: [LovedOneProfile] {
        if searchText.isEmpty {
            return service.profiles
        }
        return service.search(query: searchText)
    }

    private func profiles(in category: RelationshipCategory) -> [LovedOneProfile] {
        filteredProfiles.filter { $0.category == category }
    }

    // MARK: - Search Bar

    private var searchBar: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 16))
                .foregroundColor(.secondary)

            TextField("Search by name...", text: $searchText)
                .font(.system(size: 16))
                .autocorrectionDisabled()

            if !searchText.isEmpty {
                Button {
                    searchText = ""
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 16))
                        .foregroundColor(.secondary.opacity(0.6))
                }
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(Color.white)
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
    }

    // MARK: - Category Sections

    private var categorySections: some View {
        VStack(spacing: 20) {
            ForEach(RelationshipCategory.allCases) { category in
                let categoryProfiles = profiles(in: category)

                if !categoryProfiles.isEmpty || searchText.isEmpty {
                    UsersCategorySection(
                        category: category,
                        profiles: categoryProfiles,
                        isExpanded: expandedCategories.contains(category),
                        onToggle: {
                            withAnimation(.spring(response: 0.35, dampingFraction: 0.85)) {
                                if expandedCategories.contains(category) {
                                    expandedCategories.remove(category)
                                } else {
                                    expandedCategories.insert(category)
                                }
                            }
                        },
                        onSelect: { profile in
                            selectedProfile = profile
                        },
                        onDelete: { profile in
                            service.deleteProfile(profile)
                        }
                    )
                }
            }
        }
        .padding(.horizontal, 16)
    }

    // MARK: - Empty States

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.2.circle")
                .font(.system(size: 56))
                .foregroundColor(themeAccent.opacity(0.4))

            Text("No users yet")
                .font(.system(size: 20, weight: .semibold))
                .foregroundColor(.primary)

            Text("Add people you care about to get\npersonalized flower recommendations")
                .font(.system(size: 15))
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)

            Button {
                showingAddSheet = true
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "plus")
                    Text("Add First User")
                }
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.white)
                .padding(.horizontal, 24)
                .padding(.vertical, 14)
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
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
            }
            .padding(.top, 8)
        }
        .padding(.top, 80)
        .padding(.horizontal, 32)
    }

    private var emptySearchState: some View {
        VStack(spacing: 12) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 40))
                .foregroundColor(.secondary.opacity(0.4))

            Text("No matches")
                .font(.system(size: 18, weight: .semibold))
                .foregroundColor(.primary)

            Text("Try a different name")
                .font(.system(size: 15))
                .foregroundColor(.secondary)
        }
        .padding(.top, 60)
    }
}

// MARK: - Category Section

private struct UsersCategorySection: View {
    let category: RelationshipCategory
    let profiles: [LovedOneProfile]
    let isExpanded: Bool
    let onToggle: () -> Void
    let onSelect: (LovedOneProfile) -> Void
    let onDelete: (LovedOneProfile) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Button(action: onToggle) {
                HStack {
                    HStack(spacing: 10) {
                        Image(systemName: category.icon)
                            .font(.system(size: 16))
                            .foregroundColor(category.color)

                        Text(category.rawValue)
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(.primary)

                        Text("(\(profiles.count))")
                            .font(.system(size: 15))
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    Image(systemName: "chevron.down")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.secondary.opacity(0.5))
                        .rotationEffect(.degrees(isExpanded ? 0 : -90))
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            if isExpanded {
                if profiles.isEmpty {
                    Text("Tap + to add someone")
                        .font(.system(size: 14))
                        .foregroundColor(.secondary.opacity(0.7))
                        .padding(.vertical, 16)
                        .frame(maxWidth: .infinity)
                } else {
                    VStack(spacing: 10) {
                        ForEach(Array(profiles.enumerated()), id: \.element.id) { index, profile in
                            Button {
                                onSelect(profile)
                            } label: {
                                LovedOneRowView(profile: profile)
                            }
                            .buttonStyle(CardPressStyle())
                            .cardAppearAnimation(delay: Double(index) * 0.05)
                            .swipeActions(edge: .trailing, allowsFullSwipe: true) {
                                Button(role: .destructive) {
                                    onDelete(profile)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                            .contextMenu {
                                Button(role: .destructive) {
                                    onDelete(profile)
                                } label: {
                                    Label("Delete", systemImage: "trash")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        UsersView()
    }
}
