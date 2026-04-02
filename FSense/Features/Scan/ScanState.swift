import SwiftUI

// MARK: - Scan Phase

enum ScanPhase: Equatable {
    case camera
    case capturing
    case analyzing
    case quickResult
    case loadingDetail
    case detail
    case error(String)

    var isLoading: Bool {
        switch self {
        case .capturing, .analyzing, .loadingDetail:
            return true
        default:
            return false
        }
    }

    var showsCamera: Bool {
        switch self {
        case .camera, .capturing:
            return true
        default:
            return false
        }
    }
}

// MARK: - Scan State

struct ScanState: Equatable {
    var phase: ScanPhase = .camera
    var scanMode: ScanMode = .flower
    var capturedImage: UIImage?
    var quickResult: QuickScanResult?
    var detailResult: ScanDetailResult?
    var isFlashOn: Bool = false
    var selectedFlowerIndex: Int = 0

    // Computed
    var primaryFlower: DetectedFlower? {
        quickResult?.primaryFlower
    }

    var allDetectedFlowers: [DetectedFlower] {
        guard let result = quickResult else { return [] }
        return [result.primaryFlower] + result.additionalFlowers
    }

    var selectedFlower: DetectedFlower? {
        let flowers = allDetectedFlowers
        guard selectedFlowerIndex < flowers.count else { return flowers.first }
        return flowers[selectedFlowerIndex]
    }

    var errorMessage: String? {
        if case .error(let message) = phase {
            return message
        }
        return nil
    }

    // Equatable conformance for UIImage
    static func == (lhs: ScanState, rhs: ScanState) -> Bool {
        lhs.phase == rhs.phase &&
        lhs.scanMode == rhs.scanMode &&
        lhs.quickResult?.requestId == rhs.quickResult?.requestId &&
        lhs.detailResult?.requestId == rhs.detailResult?.requestId &&
        lhs.isFlashOn == rhs.isFlashOn &&
        lhs.selectedFlowerIndex == rhs.selectedFlowerIndex
        // Note: Intentionally not comparing capturedImage for performance
    }
}
