import Foundation

// MARK: - Gift Suitability

enum GiftSuitability: String, CaseIterable, Identifiable {
    case excellent = "Excellent"
    case good = "Good"
    case moderate = "Moderate"
    case risky = "Risky"
    case notRecommended = "Not Recommended"
    
    var id: String { rawValue }
}

// MARK: - Emotional Risk Level

enum EmotionalRiskLevel: String, CaseIterable, Identifiable {
    case none = "None"
    case low = "Low"
    case moderate = "Moderate"
    case high = "High"
    case veryHigh = "Very High"
    
    var id: String { rawValue }
}

// MARK: - Recipient Type

struct RecipientFit: Identifiable, Equatable, Hashable {
    let id: UUID
    let recipientType: String
    let fitLevel: GiftSuitability
    let note: String?
    
    init(
        id: UUID = UUID(),
        recipientType: String,
        fitLevel: GiftSuitability,
        note: String? = nil
    ) {
        self.id = id
        self.recipientType = recipientType
        self.fitLevel = fitLevel
        self.note = note
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Gifting Occasion

struct GiftingOccasion: Identifiable, Equatable, Hashable {
    let id: UUID
    let occasion: String
    let suitability: GiftSuitability
    let description: String?
    
    init(
        id: UUID = UUID(),
        occasion: String,
        suitability: GiftSuitability,
        description: String? = nil
    ) {
        self.id = id
        self.occasion = occasion
        self.suitability = suitability
        self.description = description
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Gifting Info Model

struct GiftingInfo: Identifiable, Equatable, Hashable {
    let id: UUID
    let overallSuitability: GiftSuitability
    let suitabilityDescription: String
    
    let emotionalRisk: EmotionalRiskLevel
    let emotionalRiskDescription: String
    
    let whenToGiftItems: [String]
    let whenToAvoidItems: [String]
    let recipientFits: [RecipientFit]
    
    init(
        id: UUID = UUID(),
        overallSuitability: GiftSuitability = .good,
        suitabilityDescription: String = "",
        emotionalRisk: EmotionalRiskLevel = .low,
        emotionalRiskDescription: String = "",
        whenToGiftItems: [String] = [],
        whenToAvoidItems: [String] = [],
        recipientFits: [RecipientFit] = []
    ) {
        self.id = id
        self.overallSuitability = overallSuitability
        self.suitabilityDescription = suitabilityDescription
        self.emotionalRisk = emotionalRisk
        self.emotionalRiskDescription = emotionalRiskDescription
        self.whenToGiftItems = whenToGiftItems
        self.whenToAvoidItems = whenToAvoidItems
        self.recipientFits = recipientFits
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Preview / Mock Data

extension GiftingInfo {
    static let mock = GiftingInfo(
        overallSuitability: .excellent,
        suitabilityDescription: "Suitable for sincere apologies and calm reconciliation",
        emotionalRisk: .low,
        emotionalRiskDescription: "Low risk of misinterpretation in delicate situations",
        whenToGiftItems: [
            "Reconciliation",
            "Apology",
            "Anniversary"
        ],
        whenToAvoidItems: [
            "First Date",
            "Business Meeting",
            "Casual Friendship"
        ],
        recipientFits: [
            RecipientFit(recipientType: "Romantic Partner", fitLevel: .excellent, note: "Classic choice"),
            RecipientFit(recipientType: "Spouse", fitLevel: .excellent, note: nil),
            RecipientFit(recipientType: "New Crush", fitLevel: .risky, note: "Consider lighter options first"),
            RecipientFit(recipientType: "Friend", fitLevel: .notRecommended, note: "May send wrong signals"),
            RecipientFit(recipientType: "Family Member", fitLevel: .notRecommended, note: "Choose different color")
        ]
    )
}
