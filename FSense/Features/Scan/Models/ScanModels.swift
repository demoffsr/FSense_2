import Foundation
import UIKit

// MARK: - Scan Mode

enum ScanMode: String, Codable, CaseIterable {
    case flower
    case bouquet
    case plant

    var displayName: String {
        switch self {
        case .flower: return "Flower"
        case .bouquet: return "Bouquet"
        case .plant: return "Plant"
        }
    }

    var icon: String {
        switch self {
        case .flower: return "camera.macro"
        case .bouquet: return "sparkles"
        case .plant: return "leaf.fill"
        }
    }
}

// MARK: - Detected Flower

struct DetectedFlower: Identifiable, Codable, Equatable {
    let id: String
    let name: String
    let scientificName: String?
    let confidence: Double
    let color: String?
    let thumbnailUrl: String?

    var confidencePercentage: Int {
        Int(confidence * 100)
    }

    var confidenceLabel: String {
        "\(confidencePercentage)%"
    }
}

// MARK: - Quick Scan Result

struct QuickScanResult: Codable {
    let primaryFlower: DetectedFlower
    let additionalFlowers: [DetectedFlower]
    let bouquetDescription: String?
    let scanMode: String
    let requestId: String

    var hasMultipleFlowers: Bool {
        !additionalFlowers.isEmpty
    }
}

// MARK: - Botanical Info

struct BotanicalInfo: Codable, Equatable {
    let family: String
    let nativeRegions: [String]
    let bloomSeasons: [String]
    let lifespan: String?

    var nativeRegionsText: String {
        nativeRegions.joined(separator: ", ")
    }

    var bloomSeasonsText: String {
        bloomSeasons.joined(separator: ", ")
    }
}

// MARK: - Care Info

enum CareDifficulty: String, Codable {
    case easy
    case moderate
    case hard

    var displayName: String {
        rawValue.capitalized
    }

    var icon: String {
        switch self {
        case .easy: return "leaf"
        case .moderate: return "leaf.fill"
        case .hard: return "exclamationmark.triangle"
        }
    }

    var color: String {
        switch self {
        case .easy: return "green"
        case .moderate: return "yellow"
        case .hard: return "red"
        }
    }
}

enum LightRequirement: String, Codable {
    case low
    case medium
    case high
    case fullSun = "full_sun"

    var displayName: String {
        switch self {
        case .low: return "Low Light"
        case .medium: return "Medium Light"
        case .high: return "Bright Light"
        case .fullSun: return "Full Sun"
        }
    }

    var icon: String {
        switch self {
        case .low: return "moon"
        case .medium: return "sun.min"
        case .high: return "sun.max"
        case .fullSun: return "sun.max.fill"
        }
    }
}

enum WaterFrequency: String, Codable {
    case low
    case moderate
    case frequent

    var displayName: String {
        switch self {
        case .low: return "Low"
        case .moderate: return "Moderate"
        case .frequent: return "Frequent"
        }
    }

    var icon: String {
        "drop.fill"
    }
}

struct CareInfo: Codable, Equatable {
    let difficulty: CareDifficulty
    let light: LightRequirement
    let water: WaterFrequency
    let temperatureRange: String?
    let humidity: String?
    let tips: [String]
}

// MARK: - Ask AI Metadata

struct ScanAskAIMetadata: Codable, Equatable {
    let enabled: Bool
    let suggestedQuestions: [String]
}

// MARK: - Scan Result Header

struct ScanResultHeader: Codable, Equatable {
    let flowerId: String
    let name: String
    let scientificName: String?
    let confidence: Double
    let imageUrl: String?

    var confidencePercentage: Int {
        Int(confidence * 100)
    }
}

// MARK: - Scan Detail Result

struct ScanDetailResult: Codable {
    let header: ScanResultHeader
    let botanical: BotanicalInfo
    let meanings: [String]
    let care: CareInfo
    let similarFlowers: [DetectedFlower]
    let askAi: ScanAskAIMetadata
    let requestId: String
    let pipelineVersion: String
}

// MARK: - API Response Wrappers

struct QuickScanResponse: Codable {
    let success: Bool
    let data: QuickScanResult?
    let error: String?
}

struct ScanDetailResponse: Codable {
    let success: Bool
    let data: ScanDetailResult?
    let error: String?
}
