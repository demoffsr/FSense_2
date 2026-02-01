import Foundation
import SwiftUI

/// Service for managing loved ones profiles with persistence
@MainActor
final class LovedOnesService: ObservableObject {

    static let shared = LovedOnesService()

    @Published private(set) var profiles: [LovedOneProfile] = []

    private let userDefaultsKey = "LovedOnesProfiles"
    private let photoDirectoryName = "LovedOnesPhotos"

    private init() {
        Task { @MainActor in
            await loadProfilesAsync()
        }
    }

    // MARK: - Statistics

    var profileCount: Int {
        profiles.count
    }

    func profileCount(in category: RelationshipCategory) -> Int {
        profiles.filter { $0.category == category }.count
    }

    // MARK: - CRUD Operations

    /// Create a new profile
    func createProfile(_ profile: LovedOneProfile) {
        profiles.insert(profile, at: 0)
        saveProfiles()
        print("[LovedOnes] Created profile: \(profile.name)")
    }

    /// Update an existing profile
    func updateProfile(_ profile: LovedOneProfile) {
        if let index = profiles.firstIndex(where: { $0.id == profile.id }) {
            var updated = profile
            updated.update()
            profiles[index] = updated
            saveProfiles()
            print("[LovedOnes] Updated profile: \(profile.name)")
        }
    }

    /// Delete a profile
    func deleteProfile(_ profile: LovedOneProfile) {
        if let index = profiles.firstIndex(where: { $0.id == profile.id }) {
            // Delete photo if exists
            if let photoPath = profile.photoPath {
                deletePhoto(path: photoPath)
            }
            profiles.remove(at: index)
            saveProfiles()
            print("[LovedOnes] Deleted profile: \(profile.name)")
        }
    }

    /// Delete profiles at offsets (for swipe-to-delete)
    func deleteProfiles(at offsets: IndexSet, in filteredProfiles: [LovedOneProfile]) {
        for index in offsets {
            let profile = filteredProfiles[index]
            deleteProfile(profile)
        }
    }

    /// Mark profile as used (updates lastUsedAt)
    func markProfileAsUsed(_ profile: LovedOneProfile) {
        if let index = profiles.firstIndex(where: { $0.id == profile.id }) {
            profiles[index].markAsUsed()
            saveProfiles()
        }
    }

    // MARK: - Query Methods

    /// Get profiles filtered by category
    func profiles(in category: RelationshipCategory) -> [LovedOneProfile] {
        profiles.filter { $0.category == category }
    }

    /// Search profiles by name or nickname
    func search(query: String) -> [LovedOneProfile] {
        guard !query.isEmpty else { return profiles }

        let lowercasedQuery = query.lowercased()
        return profiles.filter { profile in
            profile.name.lowercased().contains(lowercasedQuery) ||
            (profile.nickname?.lowercased().contains(lowercasedQuery) ?? false)
        }
    }

    /// Find profile for @mention (matches name or nickname)
    func profile(forMention text: String) -> LovedOneProfile? {
        let cleanText = text.lowercased().trimmingCharacters(in: .whitespaces)
        return profiles.first { profile in
            profile.name.lowercased() == cleanText ||
            profile.nickname?.lowercased() == cleanText ||
            profile.displayName.lowercased().replacingOccurrences(of: " ", with: "") == cleanText
        }
    }

    /// Get profiles matching partial mention text (for autocomplete)
    func profilesMatching(mention text: String) -> [LovedOneProfile] {
        guard !text.isEmpty else { return profiles }

        let cleanText = text.lowercased()
        return profiles.filter { profile in
            profile.name.lowercased().contains(cleanText) ||
            (profile.nickname?.lowercased().contains(cleanText) ?? false)
        }
    }

    /// Get profiles with upcoming events within specified days
    func profilesWithUpcomingEvents(within days: Int = 30) -> [(LovedOneProfile, ImportantDate)] {
        var results: [(LovedOneProfile, ImportantDate)] = []

        for profile in profiles {
            for date in profile.upcomingDates where date.daysUntilNext <= days {
                results.append((profile, date))
            }
        }

        return results.sorted { $0.1.daysUntilNext < $1.1.daysUntilNext }
    }

    // MARK: - Photo Management

    /// Save photo for profile
    func savePhoto(_ image: UIImage, for profileId: UUID) -> String? {
        guard let data = image.jpegData(compressionQuality: 0.8) else {
            print("[LovedOnes] Failed to compress image")
            return nil
        }

        let fileName = "\(profileId.uuidString).jpg"
        let url = photoDirectoryURL.appendingPathComponent(fileName)

        do {
            try FileManager.default.createDirectory(
                at: photoDirectoryURL,
                withIntermediateDirectories: true
            )
            try data.write(to: url)
            print("[LovedOnes] Saved photo: \(fileName)")
            return fileName
        } catch {
            print("[LovedOnes] Failed to save photo: \(error)")
            return nil
        }
    }

    /// Load photo from path
    func loadPhoto(path: String) -> UIImage? {
        let url = photoDirectoryURL.appendingPathComponent(path)
        guard let data = try? Data(contentsOf: url) else { return nil }
        return UIImage(data: data)
    }

    /// Delete photo at path
    func deletePhoto(path: String) {
        let url = photoDirectoryURL.appendingPathComponent(path)
        try? FileManager.default.removeItem(at: url)
        print("[LovedOnes] Deleted photo: \(path)")
    }

    private var photoDirectoryURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(photoDirectoryName)
    }

    // MARK: - Persistence

    private func saveProfiles() {
        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(profiles)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            print("[LovedOnes] Failed to save: \(error)")
        }
    }

    private func loadProfilesAsync() async {
        let key = userDefaultsKey

        let decoded = await Task.detached(priority: .userInitiated) {
            guard let data = UserDefaults.standard.data(forKey: key) else {
                return [LovedOneProfile]()
            }

            do {
                let decoder = JSONDecoder()
                return try decoder.decode([LovedOneProfile].self, from: data)
            } catch {
                print("[LovedOnes] Failed to decode: \(error)")
                return [LovedOneProfile]()
            }
        }.value

        profiles = decoded
        print("[LovedOnes] Loaded \(profiles.count) profiles")
    }
}
