import Foundation

/// Service for saving and loading flower recommendations to archive
@MainActor
final class FlowerArchiveService: ObservableObject {

    static let shared = FlowerArchiveService()

    @Published private(set) var archivedFlowers: [ArchivedFlower] = []

    private let userDefaultsKey = "FlowerArchive"

    private init() {
        // Load archive asynchronously to avoid blocking main thread at startup
        Task { @MainActor in
            await loadArchiveAsync()
        }
    }

    // MARK: - Archive Statistics

    var flowerCount: Int {
        archivedFlowers.count
    }

    // MARK: - Archive Management

    /// Save a flower to the archive (or update if already exists)
    func archiveFlower(_ flower: Flower) {
        // Check if flower already exists (by name)
        if let existingIndex = archivedFlowers.firstIndex(where: { $0.flower.name == flower.name }) {
            // Update existing entry: move to top and update timestamp
            var updated = archivedFlowers[existingIndex]
            updated.lastViewedAt = Date()

            archivedFlowers.remove(at: existingIndex)
            archivedFlowers.insert(updated, at: 0)

            saveArchive()
            print("[Archive] Updated flower: \(flower.name)")
        } else {
            // Create new entry
            let archived = ArchivedFlower(
                id: UUID(),
                flower: flower,
                archivedAt: Date(),
                lastViewedAt: Date()
            )

            archivedFlowers.insert(archived, at: 0)
            saveArchive()
            print("[Archive] Saved new flower: \(flower.name)")
        }
    }

    /// Remove a flower from archive
    func removeFlower(at offsets: IndexSet) {
        archivedFlowers.remove(atOffsets: offsets)
        saveArchive()
    }

    /// Clear all archived flowers
    func clearArchive() {
        archivedFlowers.removeAll()
        saveArchive()
    }

    // MARK: - Persistence

    private func saveArchive() {
        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(archivedFlowers)
            UserDefaults.standard.set(data, forKey: userDefaultsKey)
        } catch {
            print("[Archive] Failed to save: \(error)")
        }
    }

    /// Load archive asynchronously to prevent blocking main thread
    private func loadArchiveAsync() async {
        let key = userDefaultsKey

        // Read AND decode on background thread to fully avoid blocking UI
        let decoded = await Task.detached(priority: .userInitiated) {
            guard let data = UserDefaults.standard.data(forKey: key) else {
                return [ArchivedFlower]()
            }

            do {
                let decoder = JSONDecoder()
                return try decoder.decode([ArchivedFlower].self, from: data)
            } catch {
                print("[Archive] Failed to decode: \(error)")
                return [ArchivedFlower]()
            }
        }.value

        archivedFlowers = decoded
        print("[Archive] Loaded \(archivedFlowers.count) flowers")
    }
}

// MARK: - Archived Flower Model

struct ArchivedFlower: Identifiable, Codable {
    let id: UUID
    let flower: Flower
    let archivedAt: Date // First time added to archive
    var lastViewedAt: Date // Last time viewed (updated on each open)
}

// MARK: - Flower Codable Extension

extension Flower: Codable {
    enum CodingKeys: String, CodingKey {
        case id, name, imageAsset, imageURL, imageCacheKey
        case meanings, symbolismText, whyThisFlowerText, moodIntensityValue
        case giftingInfo, contextInfo, alternatives
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        id = try container.decode(UUID.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        imageAsset = try container.decodeIfPresent(String.self, forKey: .imageAsset)

        if let urlString = try container.decodeIfPresent(String.self, forKey: .imageURL) {
            imageURL = URL(string: urlString)
        } else {
            imageURL = nil
        }

        imageCacheKey = try container.decodeIfPresent(String.self, forKey: .imageCacheKey)

        meanings = try container.decode([String].self, forKey: .meanings)
        symbolismText = try container.decode(String.self, forKey: .symbolismText)
        whyThisFlowerText = try container.decode(String.self, forKey: .whyThisFlowerText)
        moodIntensityValue = try container.decode(Double.self, forKey: .moodIntensityValue)

        giftingInfo = try container.decodeIfPresent(GiftingInfo.self, forKey: .giftingInfo)
        contextInfo = try container.decodeIfPresent(ContextInfo.self, forKey: .contextInfo)
        alternatives = try container.decodeIfPresent([AlternativeFlower].self, forKey: .alternatives) ?? []
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)

        try container.encode(id, forKey: .id)
        try container.encode(name, forKey: .name)
        try container.encodeIfPresent(imageAsset, forKey: .imageAsset)
        try container.encodeIfPresent(imageURL?.absoluteString, forKey: .imageURL)
        try container.encodeIfPresent(imageCacheKey, forKey: .imageCacheKey)
        try container.encode(meanings, forKey: .meanings)
        try container.encode(symbolismText, forKey: .symbolismText)
        try container.encode(whyThisFlowerText, forKey: .whyThisFlowerText)
        try container.encode(moodIntensityValue, forKey: .moodIntensityValue)
        try container.encodeIfPresent(giftingInfo, forKey: .giftingInfo)
        try container.encodeIfPresent(contextInfo, forKey: .contextInfo)
        try container.encode(alternatives, forKey: .alternatives)
    }
}
