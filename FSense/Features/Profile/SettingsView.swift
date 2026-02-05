import SwiftUI

/// Settings screen for user preferences
/// Currently supports city/region selection for flower search
struct SettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.themeAccent) private var themeAccent

    @State private var selectedRegion: String = UserSettings.selectedRegion
    @State private var selectedCity: String = UserSettings.selectedCity
    @State private var selectedLanguage: AppLanguage = LanguageManager.shared.currentLanguage
    @State private var showRestartAlert = false

    var body: some View {
        ScrollView {
            VStack(spacing: 0) {
                // MARK: - Header
                Text("Settings")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                    .padding(.top, 60)
                    .padding(.bottom, 40)

                // MARK: - Appearance Settings
                ThemeSelectionSection()
                    .padding(.bottom, 24)

                // MARK: - Language Settings
                languageSection
                    .padding(.bottom, 24)

                // MARK: - Location Settings
                VStack(alignment: .leading, spacing: 0) {
                    Text("Location")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.secondary)
                        .textCase(.uppercase)
                        .padding(.horizontal, 16)
                        .padding(.bottom, 8)

                    VStack(spacing: 0) {
                        // Region Picker
                        HStack {
                            Image(systemName: "globe")
                                .font(.system(size: 20))
                                .foregroundColor(themeAccent)
                                .frame(width: 32)

                            Text("Country")
                                .font(.system(size: 17))

                            Spacer()

                            Picker("", selection: $selectedRegion) {
                                ForEach(UserSettings.supportedRegions) { region in
                                    Text(region.name).tag(region.code)
                                }
                            }
                            .pickerStyle(.menu)
                            .tint(themeAccent)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)

                        Divider()
                            .padding(.leading, 64)

                        // City Picker
                        HStack {
                            Image(systemName: "building.2")
                                .font(.system(size: 20))
                                .foregroundColor(themeAccent)
                                .frame(width: 32)

                            Text("City")
                                .font(.system(size: 17))

                            Spacer()

                            Picker("", selection: $selectedCity) {
                                ForEach(availableCities, id: \.self) { city in
                                    Text(city).tag(city)
                                }
                            }
                            .pickerStyle(.menu)
                            .tint(themeAccent)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                    }
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding(.horizontal, 16)
                }

                // MARK: - Info Text
                Text("Your location is used to find flower shops near you.")
                    .font(.system(size: 13))
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 32)
                    .padding(.top, 12)
                    .padding(.bottom, 40)
                    .multilineTextAlignment(.center)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
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
        }
        .onChange(of: selectedRegion) { _, newRegion in
            // Reset city to first available when region changes
            let cities = UserSettings.cities(for: newRegion)
            if !cities.contains(selectedCity), let firstCity = cities.first {
                selectedCity = firstCity
            }
            saveSettings()
        }
        .onChange(of: selectedCity) { _, _ in
            saveSettings()
        }
        .onChange(of: selectedLanguage) { _, newLanguage in
            LanguageManager.shared.currentLanguage = newLanguage
            showRestartAlert = true
        }
        .alert("Language Changed", isPresented: $showRestartAlert) {
            Button("OK") {
                LanguageManager.shared.clearRestartFlag()
            }
        } message: {
            Text("The interface language has been changed. Some text may update after restarting the app.")
        }
    }

    // MARK: - Language Section

    private var languageSection: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("Language")
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.secondary)
                .textCase(.uppercase)
                .padding(.horizontal, 16)
                .padding(.bottom, 8)

            VStack(spacing: 0) {
                HStack {
                    Image(systemName: "globe")
                        .font(.system(size: 20))
                        .foregroundColor(themeAccent)
                        .frame(width: 32)

                    Text("App Language")
                        .font(.system(size: 17))

                    Spacer()

                    Picker("", selection: $selectedLanguage) {
                        ForEach(AppLanguage.allCases) { language in
                            HStack {
                                Image(systemName: language.icon)
                                Text(language.nativeName)
                            }
                            .tag(language)
                        }
                    }
                    .pickerStyle(.menu)
                    .tint(themeAccent)
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 16)

            Text("Choose the language for the app interface.")
                .font(.system(size: 13))
                .foregroundColor(.secondary)
                .padding(.horizontal, 32)
                .padding(.top, 8)
        }
    }

    // MARK: - Computed Properties

    private var availableCities: [String] {
        UserSettings.cities(for: selectedRegion)
    }

    // MARK: - Private Methods

    private func saveSettings() {
        UserSettings.selectedRegion = selectedRegion
        UserSettings.selectedCity = selectedCity
    }
}

#Preview {
    NavigationStack {
        SettingsView()
    }
}
