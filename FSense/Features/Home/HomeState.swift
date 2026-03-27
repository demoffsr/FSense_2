import Foundation

/// State for Home screen
/// Responsibility: Holds all data displayed on Home screen
struct HomeState {
    var searchText: String = ""
    var selectedTab: RecentTab = .chats
    var inputText: String = ""
}

/// Tab options for Recent section
enum RecentTab: String, CaseIterable {
    case chats = "Chats"
    case scans = "Scans"
}

/// Model for recent scan item (flowers identified via camera)
/// NOTE: Full model with API fields is in ScanHistoryManager.swift
/// This simplified version is for Home screen display
struct RecentScanItem: Identifiable {
    let id: UUID
    let flowerName: String
    let subtitle: String
    let imageAsset: String?
    let imagePath: String?
    let scannedAt: Date
    let confidence: Double?
    let requestId: String?

    init(
        id: UUID = UUID(),
        flowerName: String,
        subtitle: String,
        imageAsset: String? = nil,
        imagePath: String? = nil,
        scannedAt: Date = Date(),
        confidence: Double? = nil,
        requestId: String? = nil
    ) {
        self.id = id
        self.flowerName = flowerName
        self.subtitle = subtitle
        self.imageAsset = imageAsset
        self.imagePath = imagePath
        self.scannedAt = scannedAt
        self.confidence = confidence
        self.requestId = requestId
    }

    var confidenceLabel: String {
        guard let conf = confidence else { return "" }
        return "\(Int(conf * 100))%"
    }

    var relativeDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: scannedAt, relativeTo: Date())
    }
}
