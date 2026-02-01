import Foundation

// MARK: - Cultural Interpretation

struct CulturalInterpretation: Identifiable, Equatable, Hashable, Codable {
    let id: UUID
    let emoji: String
    let culture: String
    let interpretation: String
    let sentiment: ContextSentiment
    
    init(
        id: UUID = UUID(),
        emoji: String = "🌍",
        culture: String,
        interpretation: String,
        sentiment: ContextSentiment = .neutral
    ) {
        self.id = id
        self.emoji = emoji
        self.culture = culture
        self.interpretation = interpretation
        self.sentiment = sentiment
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Relationship Context

struct RelationshipContext: Identifiable, Equatable, Hashable, Codable {
    let id: UUID
    let relationshipType: String
    let appropriateness: ContextAppropriatenessLevel
    let guidance: String
    
    init(
        id: UUID = UUID(),
        relationshipType: String,
        appropriateness: ContextAppropriatenessLevel,
        guidance: String = ""
    ) {
        self.id = id
        self.relationshipType = relationshipType
        self.appropriateness = appropriateness
        self.guidance = guidance
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Timing Sensitivity

struct TimingSensitivity: Identifiable, Equatable, Hashable, Codable {
    let id: UUID
    let timing: String
    let sensitivity: ContextSensitivityLevel
    let note: String
    
    init(
        id: UUID = UUID(),
        timing: String,
        sensitivity: ContextSensitivityLevel,
        note: String = ""
    ) {
        self.id = id
        self.timing = timing
        self.sensitivity = sensitivity
        self.note = note
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Misinterpretation

struct CommonMisinterpretation: Identifiable, Equatable, Hashable, Codable {
    let id: UUID
    let misinterpretation: String
    let clarification: String
    
    init(
        id: UUID = UUID(),
        misinterpretation: String,
        clarification: String
    ) {
        self.id = id
        self.misinterpretation = misinterpretation
        self.clarification = clarification
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Supporting Enums

enum ContextSentiment: String, CaseIterable, Identifiable, Codable {
    case positive = "Positive"
    case neutral = "Neutral"
    case negative = "Negative"
    case mixed = "Mixed"

    var id: String { rawValue }
}

enum ContextAppropriatenessLevel: String, CaseIterable, Identifiable, Codable {
    case highlyAppropriate = "Highly Appropriate"
    case appropriate = "Appropriate"
    case neutral = "Neutral"
    case inappropriate = "Inappropriate"
    case highlyInappropriate = "Highly Inappropriate"

    var id: String { rawValue }
}

enum ContextSensitivityLevel: String, CaseIterable, Identifiable, Codable {
    case low = "Low"
    case moderate = "Moderate"
    case high = "High"
    case critical = "Critical"

    var id: String { rawValue }
}

// MARK: - Context Info Model

struct ContextInfo: Identifiable, Equatable, Hashable, Codable {
    let id: UUID
    let summaryText: String
    
    let culturalInterpretations: [CulturalInterpretation]
    let relationshipContexts: [RelationshipContext]
    let timingSensitivities: [TimingSensitivity]
    let commonMisinterpretations: [CommonMisinterpretation]
    
    init(
        id: UUID = UUID(),
        summaryText: String = "",
        culturalInterpretations: [CulturalInterpretation] = [],
        relationshipContexts: [RelationshipContext] = [],
        timingSensitivities: [TimingSensitivity] = [],
        commonMisinterpretations: [CommonMisinterpretation] = []
    ) {
        self.id = id
        self.summaryText = summaryText
        self.culturalInterpretations = culturalInterpretations
        self.relationshipContexts = relationshipContexts
        self.timingSensitivities = timingSensitivities
        self.commonMisinterpretations = commonMisinterpretations
    }
    
    func hash(into hasher: inout Hasher) { hasher.combine(id) }
}

// MARK: - Preview / Mock Data

extension ContextInfo {
    static let mock = ContextInfo(
        summaryText: "Best suited for emotionally sensitive situations where subtlety and restraint are important.",
        culturalInterpretations: [
            CulturalInterpretation(emoji: "🇯🇵", culture: "Japan", interpretation: "Associated with quiet respect and emotional restraint", sentiment: .positive),
            CulturalInterpretation(emoji: "🇺🇸", culture: "Western", interpretation: "Symbol of romantic love and passion", sentiment: .positive),
            CulturalInterpretation(emoji: "🇸🇦", culture: "Middle Eastern", interpretation: "Symbol of beauty and love, often referenced in poetry", sentiment: .positive)
        ],
        relationshipContexts: [
            RelationshipContext(relationshipType: "New Relationship", appropriateness: .neutral, guidance: "May be too intense for early dating stages"),
            RelationshipContext(relationshipType: "Established Relationship", appropriateness: .highlyAppropriate, guidance: "Perfect expression of ongoing love"),
            RelationshipContext(relationshipType: "Professional", appropriateness: .inappropriate, guidance: "Could be misinterpreted; choose neutral flowers")
        ],
        timingSensitivities: [
            TimingSensitivity(timing: "After an argument", sensitivity: .high, note: "May seem like an easy fix rather than genuine apology"),
            TimingSensitivity(timing: "Unexpected moments", sensitivity: .low, note: "Spontaneous gifts often have the greatest impact"),
            TimingSensitivity(timing: "Public settings", sensitivity: .moderate, note: "Consider if recipient would be comfortable")
        ],
        commonMisinterpretations: [
            CommonMisinterpretation(misinterpretation: "Only for Valentine's Day", clarification: "Appropriate year-round for romantic partners and special moments"),
            CommonMisinterpretation(misinterpretation: "Any number is fine", clarification: "Different quantities carry different meanings in some cultures"),
            CommonMisinterpretation(misinterpretation: "Too cliché to gift", clarification: "Classic choice that remains meaningful when given sincerely")
        ]
    )
}
