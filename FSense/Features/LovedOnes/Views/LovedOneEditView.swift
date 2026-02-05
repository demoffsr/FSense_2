import SwiftUI
import PhotosUI

enum LovedOneEditMode: Equatable {
    case create
    case edit(LovedOneProfile)

    static func == (lhs: LovedOneEditMode, rhs: LovedOneEditMode) -> Bool {
        switch (lhs, rhs) {
        case (.create, .create):
            return true
        case let (.edit(l), .edit(r)):
            return l.id == r.id
        default:
            return false
        }
    }
}

struct LovedOneEditView: View {
    let mode: LovedOneEditMode

    @Environment(\.dismiss) private var dismiss
    @Environment(\.themeAccent) private var themeAccent
    @StateObject private var service = LovedOnesService.shared

    // Basic Info
    @State private var name: String = ""
    @State private var nickname: String = ""
    @State private var selectedRelationship: Relationship?
    @State private var expandedCategory: RelationshipCategory?

    // Photo
    @State private var selectedPhoto: UIImage?
    @State private var showingPhotoPicker = false
    @State private var photoPickerItem: PhotosPickerItem?

    // Important Dates
    @State private var hasBirthday = false
    @State private var birthdayDate = Date()
    @State private var hasAnniversary = false
    @State private var anniversaryDate = Date()
    @State private var customDates: [ImportantDate] = []
    @State private var showingAddCustomDate = false

    // Taste Profile
    @State private var flowerStyle: FlowerStyle?
    @State private var budgetRange: BudgetRange?
    @State private var preferredMoods: [MoodPreference] = []
    @State private var favoriteFlowers: [String] = []
    @State private var dislikedFlowers: [String] = []
    @State private var allergies: [String] = []
    @State private var notes: String = ""

    // Validation
    @State private var showingValidationError = false

    var body: some View {
        ScrollView {
            VStack(spacing: 24) {
                // Photo section
                photoSection
                    .padding(.top, 16)

                // Basic info section
                basicInfoSection

                // Important dates section
                importantDatesSection

                // Taste profile section
                tasteProfileSection

                // Favorites & dislikes
                favoritesSection

                // Notes section
                notesSection
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 100)
        }
        .background(Color(white: 0.96))
        .navigationTitle(mode == .create ? "Add Profile" : "Edit Profile")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    dismiss()
                } label: {
                    Text("Cancel", comment: "Button to dismiss without saving")
                }
            }

            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    saveProfile()
                } label: {
                    Text("Save", comment: "Button to save loved one profile")
                }
                .font(.system(size: 16, weight: .semibold))
                .disabled(!isValid)
            }
        }
        .onAppear {
            loadExistingProfile()
        }
        .alert("Missing Information", isPresented: $showingValidationError) {
            Button("OK", role: .cancel) { }
        } message: {
            Text("Please enter a name and select a relationship.")
        }
    }

    // MARK: - Photo Section

    private var photoSection: some View {
        VStack(spacing: 12) {
            PhotosPicker(selection: $photoPickerItem, matching: .images) {
                if let photo = selectedPhoto {
                    Image(uiImage: photo)
                        .resizable()
                        .scaledToFill()
                        .frame(width: 100, height: 100)
                        .clipShape(Circle())
                        .overlay(
                            Circle()
                                .stroke(Color.white, lineWidth: 3)
                        )
                        .shadow(color: .black.opacity(0.1), radius: 6, x: 0, y: 3)
                        .overlay(alignment: .bottomTrailing) {
                            Image(systemName: "pencil.circle.fill")
                                .font(.system(size: 28))
                                .foregroundColor(themeAccent)
                                .background(Circle().fill(.white).padding(6))
                        }
                } else {
                    ZStack {
                        Circle()
                            .fill(Color(white: 0.92))
                            .frame(width: 100, height: 100)

                        VStack(spacing: 6) {
                            Image(systemName: "camera.fill")
                                .font(.system(size: 24))
                                .foregroundColor(.secondary)

                            Text("Add Photo")
                                .font(.system(size: 12))
                                .foregroundColor(.secondary)
                        }
                    }
                }
            }
            .onChange(of: photoPickerItem) { _, newItem in
                Task { @MainActor in
                    if let data = try? await newItem?.loadTransferable(type: Data.self),
                       let image = UIImage(data: data) {
                        selectedPhoto = image
                    }
                }
            }

            if selectedPhoto != nil {
                Button("Remove Photo") {
                    selectedPhoto = nil
                    photoPickerItem = nil
                }
                .font(.system(size: 14))
                .foregroundColor(.red)
            }
        }
    }

    // MARK: - Basic Info Section

    private var basicInfoSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader("Basic Info")

            VStack(spacing: 0) {
                // Name field
                textFieldRow(
                    icon: "person.fill",
                    placeholder: "Name *",
                    text: $name
                )

                Divider().padding(.leading, 44)

                // Nickname field
                textFieldRow(
                    icon: "tag.fill",
                    placeholder: "Nickname (optional)",
                    text: $nickname
                )

                Divider().padding(.leading, 44)

                // Relationship picker
                relationshipPicker
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
    }

    private func textFieldRow(icon: String, placeholder: String, text: Binding<String>) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(themeAccent)
                .frame(width: 24)

            TextField(placeholder, text: text)
                .font(.system(size: 16))
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 14)
    }

    private var relationshipPicker: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Image(systemName: "heart.fill")
                    .font(.system(size: 16))
                    .foregroundColor(themeAccent)
                    .frame(width: 24)

                Text(selectedRelationship?.displayName ?? "Relationship *")
                    .font(.system(size: 16))
                    .foregroundColor(selectedRelationship == nil ? .secondary : .primary)

                Spacer()

                Image(systemName: "chevron.down")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.secondary.opacity(0.5))
                    .rotationEffect(.degrees(expandedCategory != nil ? 180 : 0))
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)
            .contentShape(Rectangle())
            .onTapGesture {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                    if expandedCategory != nil {
                        expandedCategory = nil
                    } else {
                        expandedCategory = .romance
                    }
                }
            }

            // Category picker
            if expandedCategory != nil {
                VStack(spacing: 0) {
                    Divider().padding(.leading, 44)

                    ForEach(RelationshipCategory.allCases) { category in
                        VStack(spacing: 0) {
                            // Category header
                            Button {
                                withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                                    expandedCategory = expandedCategory == category ? nil : category
                                }
                            } label: {
                                HStack {
                                    Image(systemName: category.icon)
                                        .font(.system(size: 14))
                                        .foregroundColor(category.color)
                                        .frame(width: 24)

                                    Text(category.displayName)
                                        .font(.system(size: 15, weight: .medium))
                                        .foregroundColor(.primary)

                                    Spacer()

                                    Image(systemName: "chevron.right")
                                        .font(.system(size: 12, weight: .semibold))
                                        .foregroundColor(.secondary.opacity(0.4))
                                        .rotationEffect(.degrees(expandedCategory == category ? 90 : 0))
                                }
                                .padding(.horizontal, 14)
                                .padding(.vertical, 12)
                                .background(expandedCategory == category ? Color(white: 0.97) : .clear)
                            }
                            .buttonStyle(.plain)

                            // Relationships in category
                            if expandedCategory == category {
                                ForEach(category.relationships) { relationship in
                                    Button {
                                        selectedRelationship = relationship
                                        withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                                            expandedCategory = nil
                                        }
                                    } label: {
                                        HStack {
                                            Text(relationship.displayName)
                                                .font(.system(size: 15))
                                                .foregroundColor(.primary)

                                            Spacer()

                                            if selectedRelationship == relationship {
                                                Image(systemName: "checkmark")
                                                    .font(.system(size: 14, weight: .semibold))
                                                    .foregroundColor(themeAccent)
                                            }
                                        }
                                        .padding(.leading, 52)
                                        .padding(.trailing, 14)
                                        .padding(.vertical, 10)
                                        .background(selectedRelationship == relationship ? themeAccent.opacity(0.06) : .clear)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // MARK: - Important Dates Section

    private var importantDatesSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader("Important Dates")

            VStack(spacing: 0) {
                // Birthday
                dateToggleRow(
                    icon: "gift.fill",
                    title: "Birthday",
                    isEnabled: $hasBirthday,
                    date: $birthdayDate
                )

                Divider().padding(.leading, 44)

                // Anniversary
                dateToggleRow(
                    icon: "heart.circle.fill",
                    title: "Anniversary",
                    isEnabled: $hasAnniversary,
                    date: $anniversaryDate
                )

                // Custom dates
                ForEach(customDates) { customDate in
                    Divider().padding(.leading, 44)
                    customDateRow(customDate)
                }

                Divider().padding(.leading, 44)

                // Add custom date button
                Button {
                    showingAddCustomDate = true
                } label: {
                    HStack(spacing: 12) {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(themeAccent)
                            .frame(width: 24)

                        Text("Add Custom Date")
                            .font(.system(size: 16))
                            .foregroundColor(themeAccent)

                        Spacer()
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 14)
                }
                .buttonStyle(.plain)
            }
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
        .sheet(isPresented: $showingAddCustomDate) {
            CustomDateSheet(onSave: { newDate in
                customDates.append(newDate)
            })
        }
    }

    private func dateToggleRow(icon: String, title: String, isEnabled: Binding<Bool>, date: Binding<Date>) -> some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                Image(systemName: icon)
                    .font(.system(size: 16))
                    .foregroundColor(themeAccent)
                    .frame(width: 24)

                Text(title)
                    .font(.system(size: 16))
                    .foregroundColor(.primary)

                Spacer()

                Toggle("", isOn: isEnabled)
                    .labelsHidden()
                    .tint(themeAccent)
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 14)

            if isEnabled.wrappedValue {
                DatePicker(
                    "",
                    selection: date,
                    displayedComponents: .date
                )
                .datePickerStyle(.graphical)
                .padding(.horizontal, 14)
                .padding(.bottom, 14)
            }
        }
    }

    private func customDateRow(_ date: ImportantDate) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "calendar")
                .font(.system(size: 16))
                .foregroundColor(themeAccent)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(date.title)
                    .font(.system(size: 16))
                    .foregroundColor(.primary)

                Text(formatDate(date.date))
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
            }

            Spacer()

            Button {
                customDates.removeAll { $0.id == date.id }
            } label: {
                Image(systemName: "trash")
                    .font(.system(size: 14))
                    .foregroundColor(.red)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
    }

    // MARK: - Taste Profile Section

    private var tasteProfileSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader("Taste Profile")

            VStack(spacing: 20) {
                ChipSelectionView(
                    title: "Flower Style",
                    options: FlowerStyle.allCases,
                    selection: $flowerStyle,
                    iconProvider: { $0.icon }
                )

                ChipSelectionView(
                    title: "Budget Range",
                    options: BudgetRange.allCases,
                    selection: $budgetRange
                )

                MultiChipSelectionView(
                    title: "Preferred Moods",
                    options: MoodPreference.allCases,
                    selection: $preferredMoods,
                    iconProvider: { $0.icon },
                    colorProvider: { $0.color }
                )
            }
            .padding(16)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
    }

    // MARK: - Favorites Section

    private var favoritesSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader("Favorites & Restrictions")

            VStack(spacing: 20) {
                TagInputView(
                    title: "Favorite Flowers",
                    tags: $favoriteFlowers,
                    placeholder: "Add favorite...",
                    tagColor: .pink
                )

                TagInputView(
                    title: "Dislikes",
                    tags: $dislikedFlowers,
                    placeholder: "Add dislike...",
                    tagColor: .gray
                )

                TagInputView(
                    title: "Allergies",
                    tags: $allergies,
                    placeholder: "Add allergy...",
                    tagColor: .orange,
                    showWarning: true
                )
            }
            .padding(16)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
        }
    }

    // MARK: - Notes Section

    private var notesSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            sectionHeader("Notes")

            TextEditor(text: $notes)
                .font(.system(size: 15))
                .frame(minHeight: 100)
                .padding(12)
                .background(Color.white)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: .black.opacity(0.04), radius: 6, x: 0, y: 2)
                .overlay(alignment: .topLeading) {
                    if notes.isEmpty {
                        Text("Add any notes about their preferences...")
                            .font(.system(size: 15))
                            .foregroundColor(.secondary.opacity(0.5))
                            .padding(.horizontal, 16)
                            .padding(.vertical, 20)
                            .allowsHitTesting(false)
                    }
                }
        }
    }

    // MARK: - Helper Views

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 18, weight: .semibold))
            .foregroundColor(.primary)
    }

    // MARK: - Computed Properties

    private var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty && selectedRelationship != nil
    }

    // MARK: - Methods

    private func loadExistingProfile() {
        guard case let .edit(profile) = mode else { return }

        name = profile.name
        nickname = profile.nickname ?? ""
        selectedRelationship = profile.relationship

        // Load photo
        if let photoPath = profile.photoPath {
            selectedPhoto = service.loadPhoto(path: photoPath)
        }

        // Load dates
        if let birthday = profile.birthday {
            hasBirthday = true
            birthdayDate = birthday.date
        }
        if let anniversary = profile.anniversary {
            hasAnniversary = true
            anniversaryDate = anniversary.date
        }
        customDates = profile.customDates

        // Load taste profile
        flowerStyle = profile.tasteProfile.flowerStyle
        budgetRange = profile.tasteProfile.budgetRange
        preferredMoods = profile.tasteProfile.preferredMoods
        favoriteFlowers = profile.tasteProfile.favoriteFlowers
        dislikedFlowers = profile.tasteProfile.dislikedFlowers
        allergies = profile.tasteProfile.allergies
        notes = profile.tasteProfile.notes ?? ""
    }

    private func saveProfile() {
        guard isValid, let relationship = selectedRelationship else {
            showingValidationError = true
            return
        }

        let trimmedName = name.trimmingCharacters(in: .whitespaces)
        let trimmedNickname = nickname.trimmingCharacters(in: .whitespaces)

        // Save photo if new
        var photoPath: String?
        let profileId: UUID

        if case let .edit(existingProfile) = mode {
            profileId = existingProfile.id
            photoPath = existingProfile.photoPath

            // Update photo if changed
            if let newPhoto = selectedPhoto {
                if let existingPath = existingProfile.photoPath {
                    service.deletePhoto(path: existingPath)
                }
                photoPath = service.savePhoto(newPhoto, for: profileId)
            } else if existingProfile.photoPath != nil && selectedPhoto == nil {
                // Photo was removed
                service.deletePhoto(path: existingProfile.photoPath!)
                photoPath = nil
            }
        } else {
            profileId = UUID()
            if let photo = selectedPhoto {
                photoPath = service.savePhoto(photo, for: profileId)
            }
        }

        // Build dates
        var birthday: ImportantDate? = nil
        if hasBirthday {
            birthday = ImportantDate(
                title: "Birthday",
                date: birthdayDate,
                type: .birthday
            )
        }

        var anniversary: ImportantDate? = nil
        if hasAnniversary {
            anniversary = ImportantDate(
                title: "Anniversary",
                date: anniversaryDate,
                type: .anniversary
            )
        }

        // Build taste profile
        let tasteProfile = TasteProfile(
            flowerStyle: flowerStyle,
            budgetRange: budgetRange,
            preferredMoods: preferredMoods,
            favoriteFlowers: favoriteFlowers,
            dislikedFlowers: dislikedFlowers,
            allergies: allergies,
            notes: notes.isEmpty ? nil : notes
        )

        // Create/update profile
        if case let .edit(existingProfile) = mode {
            var updatedProfile = existingProfile
            updatedProfile.name = trimmedName
            updatedProfile.nickname = trimmedNickname.isEmpty ? nil : trimmedNickname
            updatedProfile.photoPath = photoPath
            updatedProfile.relationship = relationship
            updatedProfile.birthday = birthday
            updatedProfile.anniversary = anniversary
            updatedProfile.customDates = customDates
            updatedProfile.tasteProfile = tasteProfile
            service.updateProfile(updatedProfile)
        } else {
            let newProfile = LovedOneProfile(
                id: profileId,
                name: trimmedName,
                nickname: trimmedNickname.isEmpty ? nil : trimmedNickname,
                photoPath: photoPath,
                relationship: relationship,
                birthday: birthday,
                anniversary: anniversary,
                customDates: customDates,
                tasteProfile: tasteProfile
            )
            service.createProfile(newProfile)
        }

        dismiss()
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d, yyyy"
        return formatter.string(from: date)
    }
}

// MARK: - Custom Date Sheet

private struct CustomDateSheet: View {
    @Environment(\.dismiss) private var dismiss
    let onSave: (ImportantDate) -> Void

    @State private var title = ""
    @State private var date = Date()

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                TextField("Event name", text: $title)
                    .font(.system(size: 16))
                    .padding(14)
                    .background(Color(white: 0.96))
                    .clipShape(RoundedRectangle(cornerRadius: 12))

                DatePicker("Date", selection: $date, displayedComponents: .date)
                    .datePickerStyle(.graphical)

                Spacer()
            }
            .padding()
            .navigationTitle("Add Custom Date")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Add") {
                        let newDate = ImportantDate(
                            title: title.isEmpty ? "Custom Event" : title,
                            date: date,
                            type: .custom
                        )
                        onSave(newDate)
                        dismiss()
                    }
                    .font(.system(size: 16, weight: .semibold))
                }
            }
        }
        .presentationDetents([.medium])
    }
}

#Preview {
    NavigationStack {
        LovedOneEditView(mode: .create)
    }
}
