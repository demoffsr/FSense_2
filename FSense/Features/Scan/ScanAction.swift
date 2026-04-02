import UIKit

// MARK: - Scan Actions

enum ScanAction {
    // Camera actions
    case capturePhoto(UIImage)
    case imageFromGallery(UIImage)
    case toggleScanMode
    case toggleFlash
    case retake

    // Analysis actions
    case analyzeImage
    case quickScanReceived(QuickScanResult)
    case quickScanFailed(String)

    // Detail actions
    case requestDetail
    case detailReceived(ScanDetailResult)
    case detailFailed(String)

    // Navigation actions
    case selectFlower(Int)
    case dismiss
    case askAI(String)

    // Lifecycle
    case onAppear
    case onDisappear
}
