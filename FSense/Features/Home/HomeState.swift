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
struct RecentScanItem: Identifiable {
    let id: UUID
    let flowerName: String
    let subtitle: String
    let imageAsset: String?
    let scannedAt: Date
    
    init(
        id: UUID = UUID(),
        flowerName: String,
        subtitle: String,
        imageAsset: String? = nil,
        scannedAt: Date = Date()
    ) {
        self.id = id
        self.flowerName = flowerName
        self.subtitle = subtitle
        self.imageAsset = imageAsset
        self.scannedAt = scannedAt
    }
}
