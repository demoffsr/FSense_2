import SwiftUI
import AVFoundation

/// Main scan view with fullscreen camera and Liquid Glass controls
struct ScanView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = ScanViewModel()
    @StateObject private var cameraManager = CameraManager()

    @State private var showingHelp = false

    var body: some View {
        ZStack {
            // Camera preview (always present for smooth transitions)
            cameraLayer

            // Overlays based on state
            switch viewModel.phase {
            case .camera, .capturing:
                cameraOverlay

            case .analyzing:
                AnalyzingOverlay()

            case .quickResult:
                quickResultOverlay

            case .loadingDetail:
                loadingDetailOverlay

            case .detail:
                if let detail = viewModel.detailResult {
                    ScanResultCardView(
                        result: detail,
                        capturedImage: viewModel.capturedImage,
                        onDismiss: { viewModel.send(.retake) },
                        onAskAI: { viewModel.send(.askAI($0)) }
                    )
                }

            case .error(let message):
                errorOverlay(message: message)
            }
        }
        .ignoresSafeArea()
        .statusBarHidden(viewModel.phase.showsCamera)
        .onAppear {
            // Start camera setup immediately on appear (non-blocking)
            Task.detached(priority: .userInitiated) {
                await cameraManager.setupSession()
                await MainActor.run {
                    cameraManager.startSession()
                }
            }
        }
        .onDisappear {
            cameraManager.stopSession()
        }
        .sheet(isPresented: $showingHelp) {
            helpSheet
        }
    }

    // MARK: - Camera Layer

    private var cameraLayer: some View {
        ZStack {
            Color.black

            if cameraManager.isSessionRunning {
                CameraPreviewView(session: cameraManager.session)
            }
        }
    }

    // MARK: - Camera Overlay

    private var cameraOverlay: some View {
        ZStack {
            // Scan frame
            ScanFrameOverlay()

            // Controls with binding for scanMode
            CameraControlsView(
                isFlashOn: viewModel.isFlashOn,
                scanMode: Binding(
                    get: { viewModel.scanMode },
                    set: { viewModel.scanMode = $0 }
                ),
                onCapture: capturePhoto,
                onToggleFlash: { viewModel.send(.toggleFlash) },
                onGalleryImage: { viewModel.send(.imageFromGallery($0)) },
                onClose: { dismiss() }
            )
        }
    }

    // MARK: - Quick Result Overlay

    private var quickResultOverlay: some View {
        VStack {
            // Top bar with close button (glass style)
            HStack {
                GlassCircleButton(
                    icon: "xmark",
                    size: 48,
                    action: { viewModel.send(.retake) }
                )
                Spacer()
            }
            .padding(.horizontal, 24)
            .padding(.top, 60)

            Spacer()

            // Quick info card
            if let result = viewModel.quickResult {
                QuickInfoCardView(
                    result: result,
                    capturedImage: viewModel.capturedImage,
                    onRetake: { viewModel.send(.retake) },
                    onDetails: { viewModel.send(.requestDetail) },
                    onSelectFlower: { viewModel.send(.selectFlower($0)) },
                    selectedFlowerIndex: viewModel.selectedFlowerIndex
                )
            }
        }
        .background(
            // Dimmed captured image
            Group {
                if let image = viewModel.capturedImage {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .blur(radius: 10)
                        .overlay(Color.black.opacity(0.4))
                }
            }
            .ignoresSafeArea()
        )
    }

    // MARK: - Loading Detail Overlay

    private var loadingDetailOverlay: some View {
        ZStack {
            Color.black.opacity(0.5)
                .ignoresSafeArea()

            glassLoadingPill
        }
    }

    @ViewBuilder
    private var glassLoadingPill: some View {
        if #available(iOS 26, *) {
            loadingContent
                .glassEffect(.regular, in: .capsule)
        } else {
            loadingContent
                .background(.ultraThinMaterial, in: Capsule())
        }
    }

    private var loadingContent: some View {
        HStack(spacing: 12) {
            ProgressView()
                .tint(.white)

            Text("Loading details...")
                .font(.headline)
                .foregroundStyle(.white)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 16)
    }

    // MARK: - Error Overlay

    private func errorOverlay(message: String) -> some View {
        ZStack {
            Color.black.opacity(0.6)
                .ignoresSafeArea()

            errorCard(message: message)
        }
    }

    @ViewBuilder
    private func errorCard(message: String) -> some View {
        if #available(iOS 26, *) {
            errorCardContent(message: message)
                .glassEffect(.regular, in: RoundedRectangle(cornerRadius: 24))
        } else {
            errorCardContent(message: message)
                .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 24))
        }
    }

    private func errorCardContent(message: String) -> some View {
        VStack(spacing: 20) {
            // Error icon with glass circle
            errorIcon

            Text(message)
                .font(.headline)
                .foregroundStyle(.primary)
                .multilineTextAlignment(.center)

            // Try again button
            Button {
                viewModel.send(.retake)
            } label: {
                Text("Try Again")
                    .font(.headline)
                    .foregroundStyle(.white)
                    .frame(width: 160, height: 50)
            }
            .buttonStyle(GlassButtonStyle(isProminent: true))
        }
        .padding(32)
    }

    @ViewBuilder
    private var errorIcon: some View {
        if #available(iOS 26, *) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 32, weight: .medium))
                .foregroundStyle(.yellow)
                .frame(width: 64, height: 64)
                .glassEffect(.regular, in: .circle)
        } else {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 32, weight: .medium))
                .foregroundStyle(.yellow)
                .frame(width: 64, height: 64)
                .background(.ultraThinMaterial, in: Circle())
        }
    }

    // MARK: - Help Sheet

    private var helpSheet: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 24) {
                helpItem(
                    icon: "camera",
                    title: "Flower Mode",
                    description: "Point at a single flower to identify it. Works best with clear, well-lit subjects."
                )

                helpItem(
                    icon: "square.stack.3d.up",
                    title: "Bouquet Mode",
                    description: "Scan a bouquet to identify multiple flowers at once. Tap each flower in the results to see details."
                )

                helpItem(
                    icon: "photo",
                    title: "Photo Library",
                    description: "Select an existing photo from your library to identify flowers."
                )

                helpItem(
                    icon: "bolt.fill",
                    title: "Flash",
                    description: "Use the flash in low-light conditions for better results."
                )

                Spacer()
            }
            .padding(24)
            .navigationTitle("How to Scan")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        showingHelp = false
                    }
                }
            }
        }
        .presentationDetents([.medium])
    }

    private func helpItem(icon: String, title: String, description: String) -> some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundColor(.accentColor)
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                Text(description)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    // MARK: - Actions

    private func capturePhoto() {
        Task {
            let flashMode: AVCaptureDevice.FlashMode = viewModel.isFlashOn ? .on : .off
            if let image = await cameraManager.capturePhoto(flashMode: flashMode) {
                viewModel.send(.capturePhoto(image))
            }
        }
    }
}

// MARK: - Preview

#Preview {
    ScanView()
}
