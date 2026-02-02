import Foundation

// MARK: - Mood Intensity Level

enum MoodIntensityLevel: String, CaseIterable, Identifiable {
    case veryLow = "Very Low"
    case low = "Low"
    case balanced = "Balanced"
    case high = "High"
    case veryHigh = "Very High"
    
    var id: String { rawValue }
    
    /// Numeric range for each level (0.0 - 1.0)
    var range: ClosedRange<Double> {
        switch self {
        case .veryLow: return 0.0...0.2
        case .low: return 0.2...0.4
        case .balanced: return 0.4...0.6
        case .high: return 0.6...0.8
        case .veryHigh: return 0.8...1.0
        }
    }
    
    init(from value: Double) {
        switch value {
        case 0.0..<0.2: self = .veryLow
        case 0.2..<0.4: self = .low
        case 0.4..<0.6: self = .balanced
        case 0.6..<0.8: self = .high
        default: self = .veryHigh
        }
    }
}

// MARK: - Flower Model

struct Flower: Identifiable, Equatable, Hashable {
    let id: UUID
    let name: String
    let imageAsset: String?
    let imageURL: URL?
    let imageCacheKey: String?

    // Meaning data
    let meanings: [String]
    let symbolismText: String
    let whyThisFlowerText: String
    let moodIntensityValue: Double
    
    // Computed
    var moodIntensityLevel: MoodIntensityLevel {
        MoodIntensityLevel(from: moodIntensityValue)
    }
    
    // Related data (loaded separately or embedded)
    var giftingInfo: GiftingInfo?
    var contextInfo: ContextInfo?
    
    init(
        id: UUID = UUID(),
        name: String,
        imageAsset: String? = nil,
        imageURL: URL? = nil,
        imageCacheKey: String? = nil,
        meanings: [String] = [],
        symbolismText: String = "",
        whyThisFlowerText: String = "",
        moodIntensityValue: Double = 0.5,
        giftingInfo: GiftingInfo? = nil,
        contextInfo: ContextInfo? = nil
    ) {
        self.id = id
        self.name = name
        self.imageAsset = imageAsset
        self.imageURL = imageURL
        self.imageCacheKey = imageCacheKey
        self.meanings = meanings
        self.symbolismText = symbolismText
        self.whyThisFlowerText = whyThisFlowerText
        self.moodIntensityValue = moodIntensityValue
        self.giftingInfo = giftingInfo
        self.contextInfo = contextInfo
    }
    
    // MARK: - Hashable (only by ID for navigation)
    
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

// MARK: - Preview / Mock Data

extension Flower {
    static let mock = Flower(
        name: "Red Rose",
        imageAsset: "rose_image",
        meanings: ["Love", "Passion", "Romance", "Desire", "Beauty"],
        symbolismText: "The red rose has been a symbol of love and passion for centuries, representing deep emotional connection and romantic devotion.",
        whyThisFlowerText: "Perfect for expressing deep romantic feelings. The red rose speaks the universal language of love.",
        moodIntensityValue: 0.85,
        giftingInfo: .mock,
        contextInfo: .mock
    )
}
