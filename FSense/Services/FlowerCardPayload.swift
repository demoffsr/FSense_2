import Foundation

// MARK: - FlowerCardPayload (API Response DTO)

/// Root payload from the FSense backend API
/// Maps to: backend/schemas/flower_card_payload.py
struct FlowerCardPayload: Decodable, Equatable {
    let header: FlowerHeader
    let meaning: MeaningTab
    let gifting: GiftingTabPayload
    let context: ContextTabPayload
    let askAi: AskAIMetadata
    let pipelineVersion: String
    let requestId: String
}

// MARK: - Header

struct FlowerHeader: Decodable, Equatable {
    let flowerId: String
    let name: String
    let imageUrl: String?
    let imageAsset: String?
    let imageCacheKey: String?
}

// MARK: - Meaning Tab

struct MeaningTab: Decodable, Equatable {
    let meanings: [String]
    let symbolism: SymbolismPayload
    let whyThisFlower: WhyThisFlowerPayload
    let moodIntensity: MoodIntensityPayload
}

struct SymbolismPayload: Decodable, Equatable {
    let title: String
    let text: String
}

struct WhyThisFlowerPayload: Decodable, Equatable {
    let title: String
    let text: String
    let bannerImageAsset: String?
}

struct MoodIntensityPayload: Decodable, Equatable {
    let value: Double
    let label: String
}

// MARK: - Gifting Tab

struct GiftingTabPayload: Decodable, Equatable {
    let suitability: GiftSuitabilityPayload
    let emotionalRisk: EmotionalRiskPayload
    let recipientFits: [RecipientFitItem]
    let whenToGift: [GiftingOccasionItem]
    let whenToAvoid: [GiftingOccasionItem]
}

struct GiftSuitabilityPayload: Decodable, Equatable {
    let level: String
    let description: String
}

struct EmotionalRiskPayload: Decodable, Equatable {
    let level: String
    let description: String
}

struct RecipientFitItem: Decodable, Equatable {
    let recipientType: String
    let fitLevel: String
    let note: String?
}

struct GiftingOccasionItem: Decodable, Equatable {
    let occasion: String
    let suitability: String
    let description: String?
}

// MARK: - Context Tab

struct ContextTabPayload: Decodable, Equatable {
    let summary: ContextSummary
    let culturalInterpretations: [CulturalInterpretationItem]
    let relationshipContexts: [RelationshipContextItem]
    let timingSensitivities: [TimingSensitivityItem]
    let commonMisinterpretations: [CommonMisinterpretationItem]
}

struct ContextSummary: Decodable, Equatable {
    let text: String
}

struct CulturalInterpretationItem: Decodable, Equatable {
    let emoji: String
    let culture: String
    let interpretation: String
    let sentiment: String
}

struct RelationshipContextItem: Decodable, Equatable {
    let relationshipType: String
    let appropriateness: String
    let guidance: String
}

struct TimingSensitivityItem: Decodable, Equatable {
    let timing: String
    let sensitivity: String
    let note: String
}

struct CommonMisinterpretationItem: Decodable, Equatable {
    let misinterpretation: String
    let clarification: String
}

// MARK: - Ask AI

struct AskAIMetadata: Decodable, Equatable {
    let enabled: Bool
    let suggestedQuestions: [String]
}

// MARK: - Conversion to Domain Models

extension FlowerCardPayload {

    /// Convert API payload to domain Flower model
    func toFlower() -> Flower {
        let giftingData = toGiftingInfo()
        let contextData = toContextInfo()

        print("[toFlower] Converting payload for: \(header.name)")
        print("[toFlower] meanings: \(meaning.meanings)")
        print("[toFlower] giftingInfo.suitability: \(giftingData.overallSuitability)")
        print("[toFlower] giftingInfo.whenToGift: \(giftingData.whenToGiftItems)")
        print("[toFlower] contextInfo.culturalCount: \(contextData.culturalInterpretations.count)")

        return Flower(
            name: header.name,
            imageAsset: header.imageAsset,
            imageURL: header.imageUrl.flatMap { URL(string: $0) },
            imageCacheKey: header.imageCacheKey,
            meanings: meaning.meanings,
            symbolismText: meaning.symbolism.text,
            whyThisFlowerText: meaning.whyThisFlower.text,
            moodIntensityValue: meaning.moodIntensity.value,
            giftingInfo: giftingData,
            contextInfo: contextData
        )
    }

    /// Convert to FlowerRecommendation for chat display
    func toFlowerRecommendation() -> FlowerRecommendation {
        FlowerRecommendation(
            flowerName: header.name,
            imageAsset: header.imageAsset,
            imageUrl: header.imageUrl,
            imageCacheKey: header.imageCacheKey,
            meaning: meaning.meanings.joined(separator: ", "),
            explanation: meaning.whyThisFlower.text,
            confidence: gifting.suitability.level.capitalized
        )
    }

    private func toGiftingInfo() -> GiftingInfo {
        print("[toGiftingInfo] Creating GiftingInfo...")
        print("[toGiftingInfo] suitability.level: \(gifting.suitability.level)")
        print("[toGiftingInfo] whenToGift count: \(gifting.whenToGift.count)")
        print("[toGiftingInfo] recipientFits count: \(gifting.recipientFits.count)")

        let result = GiftingInfo(
            overallSuitability: mapSuitability(gifting.suitability.level),
            suitabilityDescription: gifting.suitability.description,
            emotionalRisk: mapRiskLevel(gifting.emotionalRisk.level),
            emotionalRiskDescription: gifting.emotionalRisk.description,
            whenToGiftItems: gifting.whenToGift.map { $0.occasion },
            whenToAvoidItems: gifting.whenToAvoid.map { $0.occasion },
            recipientFits: gifting.recipientFits.map { item in
                RecipientFit(
                    recipientType: item.recipientType,
                    fitLevel: mapSuitability(item.fitLevel),
                    note: item.note
                )
            }
        )
        print("[toGiftingInfo] Created successfully")
        return result
    }

    private func toContextInfo() -> ContextInfo {
        ContextInfo(
            summaryText: context.summary.text,
            culturalInterpretations: context.culturalInterpretations.map { item in
                CulturalInterpretation(
                    emoji: item.emoji,
                    culture: item.culture,
                    interpretation: item.interpretation,
                    sentiment: mapSentiment(item.sentiment)
                )
            },
            relationshipContexts: context.relationshipContexts.map { item in
                RelationshipContext(
                    relationshipType: item.relationshipType,
                    appropriateness: mapAppropriateness(item.appropriateness),
                    guidance: item.guidance
                )
            },
            timingSensitivities: context.timingSensitivities.map { item in
                TimingSensitivity(
                    timing: item.timing,
                    sensitivity: mapSensitivity(item.sensitivity),
                    note: item.note
                )
            },
            commonMisinterpretations: context.commonMisinterpretations.map { item in
                CommonMisinterpretation(
                    misinterpretation: item.misinterpretation,
                    clarification: item.clarification
                )
            }
        )
    }

    // MARK: - Mapping Helpers

    private func mapSuitability(_ level: String) -> GiftSuitability {
        switch level.lowercased() {
        case "excellent": return .excellent
        case "good": return .good
        case "moderate": return .moderate
        case "risky": return .risky
        case "not_recommended", "notrecommended": return .notRecommended
        default: return .moderate
        }
    }

    private func mapRiskLevel(_ level: String) -> EmotionalRiskLevel {
        switch level.lowercased() {
        case "none": return .none
        case "low": return .low
        case "moderate": return .moderate
        case "high": return .high
        case "very_high", "veryhigh": return .veryHigh
        default: return .moderate
        }
    }

    private func mapSentiment(_ sentiment: String) -> ContextSentiment {
        switch sentiment.lowercased() {
        case "positive": return .positive
        case "negative": return .negative
        case "mixed": return .mixed
        default: return .neutral
        }
    }

    private func mapAppropriateness(_ level: String) -> ContextAppropriatenessLevel {
        switch level.lowercased() {
        case "highly_appropriate", "highlyappropriate": return .highlyAppropriate
        case "appropriate": return .appropriate
        case "neutral": return .neutral
        case "inappropriate": return .inappropriate
        case "highly_inappropriate", "highlyinappropriate": return .highlyInappropriate
        default: return .neutral
        }
    }

    private func mapSensitivity(_ level: String) -> ContextSensitivityLevel {
        switch level.lowercased() {
        case "low": return .low
        case "moderate": return .moderate
        case "high": return .high
        case "critical": return .critical
        default: return .moderate
        }
    }
}
