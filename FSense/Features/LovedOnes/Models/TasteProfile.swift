import SwiftUI

// MARK: - Taste Profile

struct TasteProfile: Codable, Equatable {
    var flowerStyle: FlowerStyle?
    var budgetRange: BudgetRange?
    var preferredMoods: [MoodPreference]
    var favoriteFlowers: [String]
    var dislikedFlowers: [String]
    var allergies: [String]
    var notes: String?

    init(
        flowerStyle: FlowerStyle? = nil,
        budgetRange: BudgetRange? = nil,
        preferredMoods: [MoodPreference] = [],
        favoriteFlowers: [String] = [],
        dislikedFlowers: [String] = [],
        allergies: [String] = [],
        notes: String? = nil
    ) {
        self.flowerStyle = flowerStyle
        self.budgetRange = budgetRange
        self.preferredMoods = preferredMoods
        self.favoriteFlowers = favoriteFlowers
        self.dislikedFlowers = dislikedFlowers
        self.allergies = allergies
        self.notes = notes
    }

    /// Check if profile has any preferences set
    var hasPreferences: Bool {
        flowerStyle != nil ||
        budgetRange != nil ||
        !preferredMoods.isEmpty ||
        !favoriteFlowers.isEmpty ||
        !dislikedFlowers.isEmpty ||
        !allergies.isEmpty ||
        (notes != nil && !notes!.isEmpty)
    }
}

// MARK: - Flower Style

enum FlowerStyle: String, Codable, CaseIterable, Identifiable {
    case minimal = "Minimal"
    case classic = "Classic"
    case modern = "Modern"
    case lush = "Lush"
    case wildflower = "Wildflower"

    var id: String { rawValue }

    var description: String {
        switch self {
        case .minimal: return "Simple, elegant arrangements"
        case .classic: return "Traditional, timeless bouquets"
        case .modern: return "Contemporary, artistic designs"
        case .lush: return "Full, abundant arrangements"
        case .wildflower: return "Natural, garden-style blooms"
        }
    }

    var icon: String {
        switch self {
        case .minimal: return "leaf"
        case .classic: return "rosette"
        case .modern: return "sparkles"
        case .lush: return "leaf.fill"
        case .wildflower: return "camera.macro"
        }
    }
}

// MARK: - Budget Range

enum BudgetRange: String, Codable, CaseIterable, Identifiable {
    case budget = "Budget"
    case moderate = "Moderate"
    case premium = "Premium"
    case luxury = "Luxury"

    var id: String { rawValue }

    var priceRange: String {
        switch self {
        case .budget: return "$20-40"
        case .moderate: return "$40-80"
        case .premium: return "$80-150"
        case .luxury: return "$150+"
        }
    }

    var displayText: String {
        "\(rawValue) (\(priceRange))"
    }
}

// MARK: - Mood Preference

enum MoodPreference: String, Codable, CaseIterable, Identifiable {
    case romantic = "Romantic"
    case cheerful = "Cheerful"
    case elegant = "Elegant"
    case playful = "Playful"
    case calming = "Calming"
    case dramatic = "Dramatic"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .romantic: return "heart"
        case .cheerful: return "sun.max"
        case .elegant: return "crown"
        case .playful: return "face.smiling"
        case .calming: return "leaf"
        case .dramatic: return "theatermasks"
        }
    }

    var color: Color {
        switch self {
        case .romantic: return .pink
        case .cheerful: return .yellow
        case .elegant: return .purple
        case .playful: return .orange
        case .calming: return .mint
        case .dramatic: return .red
        }
    }
}

// MARK: - Color Preference

enum ColorPreference: String, Codable, CaseIterable, Identifiable {
    case red = "Red"
    case pink = "Pink"
    case white = "White"
    case yellow = "Yellow"
    case orange = "Orange"
    case purple = "Purple"
    case blue = "Blue"
    case green = "Green"
    case mixed = "Mixed"

    var id: String { rawValue }

    var color: Color {
        switch self {
        case .red: return .red
        case .pink: return .pink
        case .white: return Color(white: 0.95)
        case .yellow: return .yellow
        case .orange: return .orange
        case .purple: return .purple
        case .blue: return .blue
        case .green: return .green
        case .mixed: return Color("AccentPurple")
        }
    }
}
