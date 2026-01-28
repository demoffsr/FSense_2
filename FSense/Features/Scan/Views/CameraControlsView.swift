import SwiftUI
import PhotosUI

/// Camera controls overlay with Liquid Glass design
/// Features glass circular buttons, mode toggle, and capture controls
struct CameraControlsView: View {
    let isFlashOn: Bool
    @Binding var scanMode: ScanMode
    let onCapture: () -> Void
    let onToggleFlash: () -> Void
    let onGalleryImage: (UIImage) -> Void
    let onClose: () -> Void
    let onHelp: () -> Void

    @State private var selectedItem: PhotosPickerItem?

    var body: some View {
        VStack(spacing: 0) {
            // Top controls
            topControls
                .padding(.top, 16)

            Spacer()

            // Mode toggle
            GlassModeToggle(mode: $scanMode)
                .padding(.bottom, 24)

            // Flash toggle (centered, small)
            flashButton
                .padding(.bottom, 20)

            // Bottom controls
            bottomControls
                .padding(.bottom, 32)
        }
        .padding(.horizontal, 24)
    }

    // MARK: - Top Controls

    private var topControls: some View {
        HStack {
            // Close button (large glass circle)
            GlassCircleButton(
                icon: "xmark",
                size: 56,
                action: onClose
            )

            Spacer()

            // Help button (large glass circle)
            GlassCircleButton(
                icon: "questionmark",
                size: 56,
                action: onHelp
            )
        }
    }

    // MARK: - Flash Button

    private var flashButton: some View {
        GlassCircleButton(
            icon: isFlashOn ? "bolt.fill" : "bolt.slash",
            size: 44,
            iconColor: isFlashOn ? .yellow : .primary,
            action: onToggleFlash
        )
    }

    // MARK: - Bottom Controls

    private var bottomControls: some View {
        HStack(alignment: .center, spacing: 0) {
            // Gallery picker (glass circle)
            galleryPicker
                .frame(maxWidth: .infinity)

            // Capture button (large white with glass ring)
            captureButton
                .frame(maxWidth: .infinity)

            // Info button (glass circle)
            GlassCircleButton(
                icon: "info",
                size: 56,
                action: onHelp
            )
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: - Gallery Picker

    @ViewBuilder
    private var galleryPicker: some View {
        PhotosPicker(selection: $selectedItem, matching: .images) {
            if #available(iOS 26, *) {
                Image(systemName: "photo.on.rectangle")
                    .font(.system(size: 56 * 0.38, weight: .medium))
                    .foregroundStyle(.primary)
                    .frame(width: 56, height: 56)
                    .contentShape(Circle())
                    .glassEffect(.regular.interactive(), in: .circle)
            } else {
                Image(systemName: "photo.on.rectangle")
                    .font(.system(size: 56 * 0.38, weight: .medium))
                    .foregroundStyle(.primary)
                    .frame(width: 56, height: 56)
                    .background(.ultraThinMaterial, in: Circle())
            }
        }
        .onChange(of: selectedItem) { _, newItem in
            Task {
                if let data = try? await newItem?.loadTransferable(type: Data.self),
                   let image = UIImage(data: data) {
                    onGalleryImage(image)
                }
            }
        }
    }

    // MARK: - Capture Button

    private var captureButton: some View {
        Button(action: onCapture) {
            ZStack {
                // Outer glass ring
                if #available(iOS 26, *) {
                    Circle()
                        .fill(.clear)
                        .frame(width: 80, height: 80)
                        .glassEffect(.regular, in: .circle)
                } else {
                    Circle()
                        .fill(.ultraThinMaterial)
                        .frame(width: 80, height: 80)
                }

                // Inner white capture circle
                Circle()
                    .fill(.white)
                    .frame(width: 64, height: 64)
            }
        }
        .buttonStyle(CaptureButtonStyle())
    }
}

// MARK: - Glass Circle Button

/// Reusable glass circular button for camera controls
struct GlassCircleButton: View {
    let icon: String
    let size: CGFloat
    var iconColor: Color = .primary
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            buttonContent
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private var buttonContent: some View {
        if #available(iOS 26, *) {
            Image(systemName: icon)
                .font(.system(size: size * 0.36, weight: .medium))
                .foregroundStyle(iconColor)
                .frame(width: size, height: size)
                .contentShape(Circle())
                .glassEffect(.regular.interactive(), in: .circle)
        } else {
            Image(systemName: icon)
                .font(.system(size: size * 0.36, weight: .medium))
                .foregroundStyle(iconColor)
                .frame(width: size, height: size)
                .background(.ultraThinMaterial, in: Circle())
        }
    }
}

// MARK: - Capture Button Style

/// Custom button style for capture button with scale animation
struct CaptureButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.92 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        Color.black.ignoresSafeArea()

        CameraControlsView(
            isFlashOn: false,
            scanMode: .constant(.single),
            onCapture: {},
            onToggleFlash: {},
            onGalleryImage: { _ in },
            onClose: {},
            onHelp: {}
        )
    }
}
