import Foundation

// MARK: - Loved One Profile

struct LovedOneProfile: Identifiable, Codable, Equatable {
    let id: UUID
    var name: String
    var nickname: String?
    var photoPath: String?
    var relationship: Relationship
    var birthday: ImportantDate?
    var anniversary: ImportantDate?
    var customDates: [ImportantDate]
    var tasteProfile: TasteProfile
    var createdAt: Date
    var updatedAt: Date
    var lastUsedAt: Date?

    init(
        id: UUID = UUID(),
        name: String,
        nickname: String? = nil,
        photoPath: String? = nil,
        relationship: Relationship,
        birthday: ImportantDate? = nil,
        anniversary: ImportantDate? = nil,
        customDates: [ImportantDate] = [],
        tasteProfile: TasteProfile = TasteProfile(),
        createdAt: Date = Date(),
        updatedAt: Date = Date(),
        lastUsedAt: Date? = nil
    ) {
        self.id = id
        self.name = name
        self.nickname = nickname
        self.photoPath = photoPath
        self.relationship = relationship
        self.birthday = birthday
        self.anniversary = anniversary
        self.customDates = customDates
        self.tasteProfile = tasteProfile
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.lastUsedAt = lastUsedAt
    }

    // MARK: - Computed Properties

    /// Category derived from relationship
    var category: RelationshipCategory {
        relationship.category
    }

    /// Initials for avatar fallback
    var initials: String {
        let components = name.split(separator: " ")
        let first = components.first?.prefix(1) ?? ""
        let last = components.count > 1 ? components.last?.prefix(1) ?? "" : ""
        return "\(first)\(last)".uppercased()
    }

    /// Display name (nickname if available, otherwise name)
    var displayName: String {
        nickname ?? name
    }

    /// Mention handle (for @ mentions in chat)
    var mentionHandle: String {
        "@\(displayName.lowercased().replacingOccurrences(of: " ", with: ""))"
    }

    /// All important dates combined
    var allDates: [ImportantDate] {
        var dates: [ImportantDate] = []
        if let birthday = birthday { dates.append(birthday) }
        if let anniversary = anniversary { dates.append(anniversary) }
        dates.append(contentsOf: customDates)
        return dates
    }

    /// Upcoming dates sorted by days until
    var upcomingDates: [ImportantDate] {
        allDates.sorted { $0.daysUntilNext < $1.daysUntilNext }
    }

    /// Next upcoming date
    var nextDate: ImportantDate? {
        upcomingDates.first
    }

    /// Check if profile has any allergies (important for safety)
    var hasAllergies: Bool {
        !tasteProfile.allergies.isEmpty
    }

    // MARK: - Mutation Methods

    mutating func markAsUsed() {
        lastUsedAt = Date()
        updatedAt = Date()
    }

    mutating func update() {
        updatedAt = Date()
    }
}

// MARK: - Hashable

extension LovedOneProfile: Hashable {
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}
