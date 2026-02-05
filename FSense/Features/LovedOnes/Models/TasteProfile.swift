import SwiftUI

// MARK: - Localized Displayable Protocol

/// Protocol for enums that provide localized display names
protocol LocalizedDisplayable {
    var displayName: LocalizedStringKey { get }
}

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

enum FlowerStyle: String, Codable, CaseIterable, Identifiable, LocalizedDisplayable {
    case minimal, classic, modern, lush, wildflower

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .minimal: return "Minimal"
        case .classic: return "Classic"
        case .modern: return "Modern"
        case .lush: return "Lush"
        case .wildflower: return "Wildflower"
        }
    }

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

enum BudgetRange: String, Codable, CaseIterable, Identifiable, LocalizedDisplayable {
    case budget, moderate, premium, luxury

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .budget: return "Budget"
        case .moderate: return "Moderate"
        case .premium: return "Premium"
        case .luxury: return "Luxury"
        }
    }

    var priceRange: String {
        switch self {
        case .budget: return "$20-40"
        case .moderate: return "$40-80"
        case .premium: return "$80-150"
        case .luxury: return "$150+"
        }
    }
}

// MARK: - Mood Preference

enum MoodPreference: String, Codable, CaseIterable, Identifiable, LocalizedDisplayable {
    case romantic, cheerful, elegant, playful, calming, dramatic

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .romantic: return "Romantic"
        case .cheerful: return "Cheerful"
        case .elegant: return "Elegant"
        case .playful: return "Playful"
        case .calming: return "Calming"
        case .dramatic: return "Dramatic"
        }
    }

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

enum ColorPreference: String, Codable, CaseIterable, Identifiable, LocalizedDisplayable {
    case red, pink, white, yellow, orange, purple, blue, green, mixed

    var id: String { rawValue }

    var displayName: LocalizedStringKey {
        switch self {
        case .red: return "Red"
        case .pink: return "Pink"
        case .white: return "White"
        case .yellow: return "Yellow"
        case .orange: return "Orange"
        case .purple: return "Purple"
        case .blue: return "Blue"
        case .green: return "Green"
        case .mixed: return "Mixed"
        }
    }

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
