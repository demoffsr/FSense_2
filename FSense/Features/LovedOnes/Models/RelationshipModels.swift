import SwiftUI

// MARK: - Relationship Category

enum RelationshipCategory: String, Codable, CaseIterable, Identifiable {
    case family = "Family"
    case romance = "Romance"
    case friends = "Friends"
    case professional = "Professional"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .family: return "house.fill"
        case .romance: return "heart.fill"
        case .friends: return "person.2.fill"
        case .professional: return "briefcase.fill"
        }
    }

    var color: Color {
        switch self {
        case .family: return .orange
        case .romance: return Color("AccentPink")
        case .friends: return .blue
        case .professional: return .gray
        }
    }

    var relationships: [Relationship] {
        switch self {
        case .family:
            return [.mom, .dad, .sister, .brother, .grandparent, .aunt, .uncle, .cousin, .child]
        case .romance:
            return [.girlfriend, .boyfriend, .wife, .husband, .partner, .fiance]
        case .friends:
            return [.closeFriend, .friend, .colleague, .neighbor, .mentor]
        case .professional:
            return [.boss, .client, .employee]
        }
    }
}

// MARK: - Relationship

enum Relationship: String, Codable, CaseIterable, Identifiable {
    // Family
    case mom = "Mom"
    case dad = "Dad"
    case sister = "Sister"
    case brother = "Brother"
    case grandparent = "Grandparent"
    case aunt = "Aunt"
    case uncle = "Uncle"
    case cousin = "Cousin"
    case child = "Child"

    // Romance
    case girlfriend = "Girlfriend"
    case boyfriend = "Boyfriend"
    case wife = "Wife"
    case husband = "Husband"
    case partner = "Partner"
    case fiance = "Fiance"

    // Friends
    case closeFriend = "Close Friend"
    case friend = "Friend"
    case colleague = "Colleague"
    case neighbor = "Neighbor"
    case mentor = "Mentor"

    // Professional
    case boss = "Boss"
    case client = "Client"
    case employee = "Employee"

    var id: String { rawValue }

    var category: RelationshipCategory {
        switch self {
        case .mom, .dad, .sister, .brother, .grandparent, .aunt, .uncle, .cousin, .child:
            return .family
        case .girlfriend, .boyfriend, .wife, .husband, .partner, .fiance:
            return .romance
        case .closeFriend, .friend, .colleague, .neighbor, .mentor:
            return .friends
        case .boss, .client, .employee:
            return .professional
        }
    }
}

// MARK: - Important Date

struct ImportantDate: Identifiable, Codable, Equatable {
    let id: UUID
    var title: String
    var date: Date
    var type: DateType
    var notificationEnabled: Bool
    var notificationDaysBefore: Int

    init(
        id: UUID = UUID(),
        title: String,
        date: Date,
        type: DateType,
        notificationEnabled: Bool = true,
        notificationDaysBefore: Int = 1
    ) {
        self.id = id
        self.title = title
        self.date = date
        self.type = type
        self.notificationEnabled = notificationEnabled
        self.notificationDaysBefore = notificationDaysBefore
    }

    /// Calculate days until next occurrence of this date
    var daysUntilNext: Int {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())

        // Get this year's occurrence
        var components = calendar.dateComponents([.month, .day], from: date)
        components.year = calendar.component(.year, from: today)

        guard let thisYearDate = calendar.date(from: components) else { return 0 }

        let targetDate: Date
        if thisYearDate >= today {
            targetDate = thisYearDate
        } else {
            // Next year
            components.year = calendar.component(.year, from: today) + 1
            targetDate = calendar.date(from: components) ?? thisYearDate
        }

        return calendar.dateComponents([.day], from: today, to: targetDate).day ?? 0
    }

    /// Formatted countdown text
    var countdownText: String {
        let days = daysUntilNext
        if days == 0 {
            return "Today!"
        } else if days == 1 {
            return "Tomorrow"
        } else {
            return "in \(days) days"
        }
    }
}

enum DateType: String, Codable, CaseIterable {
    case birthday = "Birthday"
    case anniversary = "Anniversary"
    case custom = "Custom"

    var icon: String {
        switch self {
        case .birthday: return "gift.fill"
        case .anniversary: return "heart.circle.fill"
        case .custom: return "calendar.badge.plus"
        }
    }
}
