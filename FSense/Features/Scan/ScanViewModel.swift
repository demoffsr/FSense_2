import SwiftUI
import CoreImage
import CoreImage.CIFilterBuiltins

/// ViewModel for Flower Scan screen
/// Handles camera capture, image analysis, and result presentation
@MainActor
final class ScanViewModel: ObservableObject {

    // MARK: - Published State

    @Published private(set) var state = ScanState()

    /// Pre-computed blurred background image for performance
    @Published private(set) var blurredBackground: UIImage?

    // MARK: - Dependencies

    private let apiService = APIService.shared

    // MARK: - Action Handler

    func send(_ action: ScanAction) {
        switch action {
        case .capturePhoto(let image):
            handleCapturePhoto(image)

        case .imageFromGallery(let image):
            handleImageFromGallery(image)

        case .toggleScanMode:
            state.scanMode = state.scanMode == .flower ? .bouquet : .flower

        case .toggleFlash:
            state.isFlashOn.toggle()

        case .retake:
            handleRetake()

        case .analyzeImage:
            Task { await analyzeImage() }

        case .quickScanReceived(let result):
            handleQuickScanReceived(result)

        case .quickScanFailed(let error):
            state.phase = .error(error)

        case .requestDetail:
            Task { await requestDetail() }

        case .detailReceived(let result):
            state.detailResult = result
            state.phase = .detail

        case .detailFailed(let error):
            state.phase = .error(error)

        case .selectFlower(let index):
            state.selectedFlowerIndex = index

        case .dismiss:
            // Handled by parent view
            break

        case .askAI(let question):
            handleAskAI(question)

        case .onAppear:
            // Camera setup handled by CameraPreviewView
            break

        case .onDisappear:
            // Cleanup handled automatically
            break
        }
    }

    // MARK: - Computed Properties

    var phase: ScanPhase { state.phase }
    var scanMode: ScanMode {
        get { state.scanMode }
        set { state.scanMode = newValue }
    }
    var isFlashOn: Bool { state.isFlashOn }
    var capturedImage: UIImage? { state.capturedImage }
    var quickResult: QuickScanResult? { state.quickResult }
    var detailResult: ScanDetailResult? { state.detailResult }
    var primaryFlower: DetectedFlower? { state.primaryFlower }
    var allDetectedFlowers: [DetectedFlower] { state.allDetectedFlowers }
    var selectedFlower: DetectedFlower? { state.selectedFlower }
    var selectedFlowerIndex: Int { state.selectedFlowerIndex }

    // MARK: - Private Handlers

    private func handleCapturePhoto(_ image: UIImage) {
        state.capturedImage = image
        state.phase = .capturing

        // Pre-compute blurred background off main thread
        computeBlurredBackground(from: image)

        // Immediately start analysis
        Task { await analyzeImage() }
    }

    private func handleImageFromGallery(_ image: UIImage) {
        state.capturedImage = image
        state.phase = .capturing

        // Pre-compute blurred background off main thread
        computeBlurredBackground(from: image)

        Task { await analyzeImage() }
    }

    private func handleRetake() {
        state.capturedImage = nil
        state.quickResult = nil
        state.detailResult = nil
        state.selectedFlowerIndex = 0
        blurredBackground = nil
        state.phase = .camera
    }

    /// Computes blurred background image on a background thread
    private func computeBlurredBackground(from image: UIImage) {
        Task.detached(priority: .userInitiated) { [weak self] in
            guard let blurred = ScanViewModel.createBlurredImage(image, radius: 10) else { return }
            await MainActor.run { [weak self] in
                self?.blurredBackground = blurred
            }
        }
    }

    /// Creates a blurred version of the image using CIFilter (thread-safe)
    /// Marked nonisolated to allow calling from detached tasks
    nonisolated private static func createBlurredImage(_ image: UIImage, radius: CGFloat) -> UIImage? {
        guard let ciImage = CIImage(image: image) else { return nil }

        let filter = CIFilter.gaussianBlur()
        filter.inputImage = ciImage
        filter.radius = Float(radius)

        guard let outputImage = filter.outputImage else { return nil }

        // Crop to original bounds (blur extends beyond edges)
        let croppedImage = outputImage.cropped(to: ciImage.extent)

        let context = CIContext(options: [.useSoftwareRenderer: false])
        guard let cgImage = context.createCGImage(croppedImage, from: croppedImage.extent) else {
            return nil
        }

        return UIImage(cgImage: cgImage, scale: image.scale, orientation: image.imageOrientation)
    }

    private func handleQuickScanReceived(_ result: QuickScanResult) {
        state.quickResult = result
        state.phase = .quickResult

        // Save to history
        ScanHistoryManager.shared.saveSession(result, image: state.capturedImage)
    }

    private func handleAskAI(_ question: String) {
        // TODO: Navigate to chat with context
        print("[ScanViewModel] Ask AI: \(question)")
    }

    // MARK: - API Calls

    private func analyzeImage() async {
        guard let image = state.capturedImage else {
            state.phase = .error("No image captured")
            return
        }

        state.phase = .analyzing

        do {
            let result = try await apiService.scanFlower(
                image: image,
                mode: state.scanMode
            )
            send(.quickScanReceived(result))
        } catch {
            send(.quickScanFailed(error.localizedDescription))
        }
    }

    private func requestDetail() async {
        guard let quickResult = state.quickResult else {
            state.phase = .error("No scan result available")
            return
        }

        state.phase = .loadingDetail

        do {
            let detail = try await apiService.getScanDetail(
                requestId: quickResult.requestId,
                flowerId: quickResult.primaryFlower.id
            )
            send(.detailReceived(detail))
        } catch {
            send(.detailFailed(error.localizedDescription))
        }
    }
}
