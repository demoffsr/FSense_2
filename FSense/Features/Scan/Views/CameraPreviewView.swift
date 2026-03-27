import SwiftUI
import AVFoundation

/// UIViewRepresentable wrapper for AVCaptureSession camera preview
struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> CameraPreviewUIView {
        let view = CameraPreviewUIView()
        view.session = session
        return view
    }

    func updateUIView(_ uiView: CameraPreviewUIView, context: Context) {
        // No updates needed - session is managed by CameraManager
    }
}

/// UIView subclass for camera preview layer
final class CameraPreviewUIView: UIView {
    var session: AVCaptureSession? {
        didSet {
            guard let session = session else { return }
            previewLayer.session = session
        }
    }

    private var previewLayer: AVCaptureVideoPreviewLayer {
        layer as! AVCaptureVideoPreviewLayer
    }

    override class var layerClass: AnyClass {
        AVCaptureVideoPreviewLayer.self
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupPreviewLayer()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupPreviewLayer()
    }

    private func setupPreviewLayer() {
        previewLayer.videoGravity = .resizeAspectFill
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        previewLayer.frame = bounds
    }
}

// MARK: - Camera Manager

@MainActor
final class CameraManager: ObservableObject {
    @Published var isSessionRunning = false
    @Published var capturedImage: UIImage?
    @Published var errorMessage: String?

    let session = AVCaptureSession()
    private let photoOutput = AVCapturePhotoOutput()
    private var photoDelegate: PhotoCaptureDelegate?

    var isFlashAvailable: Bool {
        guard let device = AVCaptureDevice.default(for: .video) else { return false }
        return device.hasFlash
    }

    func checkPermissions() async -> Bool {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            return true
        case .notDetermined:
            return await AVCaptureDevice.requestAccess(for: .video)
        case .denied, .restricted:
            return false
        @unknown default:
            return false
        }
    }

    func setupSession() async {
        guard await checkPermissions() else {
            errorMessage = "Camera access denied. Please enable in Settings."
            return
        }

        session.beginConfiguration()
        session.sessionPreset = .photo

        // Add video input
        guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
              let videoInput = try? AVCaptureDeviceInput(device: videoDevice),
              session.canAddInput(videoInput) else {
            errorMessage = "Failed to setup camera"
            session.commitConfiguration()
            return
        }
        session.addInput(videoInput)

        // Add photo output
        guard session.canAddOutput(photoOutput) else {
            errorMessage = "Failed to setup photo output"
            session.commitConfiguration()
            return
        }
        session.addOutput(photoOutput)

        // Configure max photo dimensions (replaces deprecated isHighResolutionCaptureEnabled)
        if let maxDimensions = videoDevice.activeFormat.supportedMaxPhotoDimensions.max(by: { $0.width < $1.width }) {
            photoOutput.maxPhotoDimensions = maxDimensions
        }

        session.commitConfiguration()
    }

    func startSession() {
        guard !session.isRunning else { return }
        isSessionRunning = true
        let captureSession = session
        DispatchQueue.global(qos: .userInitiated).async {
            captureSession.startRunning()
        }
    }

    func stopSession() {
        guard session.isRunning else { return }
        isSessionRunning = false
        let captureSession = session
        DispatchQueue.global(qos: .userInitiated).async {
            captureSession.stopRunning()
        }
    }

    func capturePhoto(flashMode: AVCaptureDevice.FlashMode = .off) async -> UIImage? {
        let settings = AVCapturePhotoSettings()
        settings.flashMode = flashMode

        return await withCheckedContinuation { continuation in
            let delegate = PhotoCaptureDelegate { image in
                continuation.resume(returning: image)
            }
            self.photoDelegate = delegate
            photoOutput.capturePhoto(with: settings, delegate: delegate)
        }
    }

    func setFlash(_ isOn: Bool) {
        guard let device = AVCaptureDevice.default(for: .video),
              device.hasFlash,
              device.isTorchAvailable else { return }

        do {
            try device.lockForConfiguration()
            device.torchMode = isOn ? .on : .off
            device.unlockForConfiguration()
        } catch {
            print("Failed to set flash: \(error)")
        }
    }
}

// MARK: - Photo Capture Delegate

private final class PhotoCaptureDelegate: NSObject, AVCapturePhotoCaptureDelegate {
    private let completion: (UIImage?) -> Void

    init(completion: @escaping (UIImage?) -> Void) {
        self.completion = completion
    }

    func photoOutput(_ output: AVCapturePhotoOutput, didFinishProcessingPhoto photo: AVCapturePhoto, error: Error?) {
        if let error = error {
            print("Photo capture error: \(error)")
            completion(nil)
            return
        }

        guard let data = photo.fileDataRepresentation(),
              let image = UIImage(data: data) else {
            completion(nil)
            return
        }

        completion(image)
    }
}
