import SwiftUI
import PhotosUI

/// Camera controls overlay with Liquid Glass effects
/// Layout matches Figma specs: top bar (62px), bottom sheet (238px)
struct CameraControlsView: View {
    let isFlashOn: Bool
    @Binding var scanMode: ScanMode
    let onCapture: () -> Void
    let onToggleFlash: () -> Void
    let onGalleryImage: (UIImage) -> Void
    let onClose: () -> Void

    @State private var selectedItem: PhotosPickerItem?
    @State private var isCapturing = false

    // Figma specs
    private let topButtonSize: CGFloat = 44
    private let galleryButtonSize: CGFloat = 50
    private let captureOuterSize: CGFloat = 66
    private let captureInnerSize: CGFloat = 56

    var body: some View {
        GeometryReader { geometry in
            ZStack(alignment: .bottom) {
                // Top bar
                VStack {
                    topBar
                        .padding(.top, geometry.safeAreaInsets.top + 16)
                        .padding(.horizontal, 16)
                    Spacer()
                }

                // Bottom sheet with glass effect
                bottomSheet(safeArea: geometry.safeAreaInsets.bottom)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    // MARK: - Top Bar

    @ViewBuilder
    private var topBar: some View {
        if #available(iOS 26, *) {
            GlassEffectContainer(spacing: 16) {
                HStack {
                    Button(action: onClose) {
                        Image(systemName: "chevron.left")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: topButtonSize, height: topButtonSize)
                            .glassEffect(
                                .clear.tint(.black.opacity(0.12)).interactive(),
                                in: .circle
                            )
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Button(action: onToggleFlash) {
                        Image(systemName: isFlashOn ? "bolt.fill" : "bolt")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundStyle(isFlashOn ? .yellow : .white)
                            .frame(width: topButtonSize, height: topButtonSize)
                            .glassEffect(
                                .clear.tint(.black.opacity(0.12)).interactive(),
                                in: .circle
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        } else {
            HStack {
                Button(action: onClose) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(.white)
                        .frame(width: topButtonSize, height: topButtonSize)
                        .background(.ultraThinMaterial, in: Circle())
                }
                .buttonStyle(.plain)

                Spacer()

                Button(action: onToggleFlash) {
                    Image(systemName: isFlashOn ? "bolt.fill" : "bolt")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(isFlashOn ? .yellow : .white)
                        .frame(width: topButtonSize, height: topButtonSize)
                        .background(.ultraThinMaterial, in: Circle())
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: - Bottom Sheet

    @ViewBuilder
    private func bottomSheet(safeArea: CGFloat) -> some View {
        if #available(iOS 26, *) {
            VStack(spacing: 24) {
                // Mode toggle
                GlassModeToggle(mode: $scanMode)
                    .padding(.top, 24)

                // Bottom controls
                bottomControls
                    .padding(.bottom, safeArea + 24)
            }
            .frame(maxWidth: .infinity)
            .background {
                // Glass background that extends beyond screen edges to hide borders
                // Screen itself clips the sides, preserving corner radius
                Rectangle()
                    .fill(.clear)
                    .glassEffect(
                        .clear.tint(.black.opacity(0.06)).interactive(),
                        in: UnevenRoundedRectangle(
                            topLeadingRadius: 34,
                            bottomLeadingRadius: 0,
                            bottomTrailingRadius: 0,
                            topTrailingRadius: 34
                        )
                    )
                    .padding(.horizontal, -20) // Extend beyond sides - screen clips
                    .padding(.bottom, -100) // Extend below visible area
            }
            // No .clipped() - screen naturally clips sides while preserving corner radius
        } else {
            VStack(spacing: 24) {
                GlassModeToggle(mode: $scanMode)
                    .padding(.top, 24)

                bottomControls
                    .padding(.bottom, safeArea + 24)
            }
            .frame(maxWidth: .infinity)
            .background(
                .ultraThinMaterial,
                in: UnevenRoundedRectangle(
                    topLeadingRadius: 34,
                    bottomLeadingRadius: 0,
                    bottomTrailingRadius: 0,
                    topTrailingRadius: 34
                )
            )
        }
    }

    // MARK: - Bottom Controls

    private var bottomControls: some View {
        HStack(alignment: .center, spacing: 0) {
            // Gallery button - left aligned
            galleryPicker
                .frame(maxWidth: .infinity, alignment: .center)

            // Capture button - center
            captureButton
                .frame(maxWidth: .infinity, alignment: .center)

            // Placeholder for symmetry (hidden)
            Color.clear
                .frame(width: galleryButtonSize, height: galleryButtonSize)
                .frame(maxWidth: .infinity, alignment: .center)
        }
        .padding(.horizontal, 32)
    }

    // MARK: - Gallery Picker

    @ViewBuilder
    private var galleryPicker: some View {
        if #available(iOS 26, *) {
            PhotosPicker(selection: $selectedItem, matching: .images) {
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(.white)
                    .frame(width: galleryButtonSize, height: galleryButtonSize)
                    .glassEffect(
                        .regular.tint(.white.opacity(0.1)).interactive(),
                        in: .circle
                    )
            }
            .buttonStyle(.plain)
            .onChange(of: selectedItem) { _, newItem in
                loadImage(from: newItem)
            }
        } else {
            PhotosPicker(selection: $selectedItem, matching: .images) {
                Image(systemName: "photo.on.rectangle.angled")
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(.white)
                    .frame(width: galleryButtonSize, height: galleryButtonSize)
                    .background(.ultraThinMaterial, in: Circle())
            }
            .buttonStyle(.plain)
            .onChange(of: selectedItem) { _, newItem in
                loadImage(from: newItem)
            }
        }
    }

    private func loadImage(from item: PhotosPickerItem?) {
        Task {
            if let data = try? await item?.loadTransferable(type: Data.self),
               let image = UIImage(data: data) {
                onGalleryImage(image)
            }
        }
    }

    // MARK: - Capture Button

    @ViewBuilder
    private var captureButton: some View {
        if #available(iOS 26, *) {
            Button {
                triggerCapture()
            } label: {
                ZStack {
                    // Outer glass ring
                    Circle()
                        .fill(.clear)
                        .frame(width: captureOuterSize, height: captureOuterSize)
                        .glassEffect(
                            .regular.tint(.white.opacity(0.15)).interactive(),
                            in: .circle
                        )

                    // Inner white circle
                    Circle()
                        .fill(.white)
                        .frame(width: captureInnerSize, height: captureInnerSize)
                        .scaleEffect(isCapturing ? 0.88 : 1.0)
                }
            }
            .buttonStyle(.plain)
        } else {
            Button {
                triggerCapture()
            } label: {
                ZStack {
                    Circle()
                        .fill(.clear)
                        .frame(width: captureOuterSize, height: captureOuterSize)
                        .background(.ultraThinMaterial, in: Circle())

                    Circle()
                        .fill(.white)
                        .frame(width: captureInnerSize, height: captureInnerSize)
                        .scaleEffect(isCapturing ? 0.88 : 1.0)
                }
            }
            .buttonStyle(.plain)
        }
    }

    private func triggerCapture() {
        withAnimation(.easeInOut(duration: 0.1)) {
            isCapturing = true
        }
        onCapture()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
            withAnimation(.easeInOut(duration: 0.1)) {
                isCapturing = false
            }
        }
    }
}

// MARK: - Glass Circle Button (for other views)

struct GlassCircleButton: View {
    let icon: String
    let size: CGFloat
    var iconColor: Color = .white
    let action: () -> Void

    var body: some View {
        if #available(iOS 26, *) {
            Button(action: action) {
                Image(systemName: icon)
                    .font(.system(size: size * 0.4, weight: .semibold))
                    .foregroundStyle(iconColor)
                    .frame(width: size, height: size)
                    .glassEffect(
                        .clear.tint(.black.opacity(0.12)).interactive(),
                        in: .circle
                    )
            }
            .buttonStyle(.plain)
        } else {
            Button(action: action) {
                Image(systemName: icon)
                    .font(.system(size: size * 0.4, weight: .semibold))
                    .foregroundStyle(iconColor)
                    .frame(width: size, height: size)
                    .background(.ultraThinMaterial, in: Circle())
            }
            .buttonStyle(.plain)
        }
    }
}

// MARK: - Preview

#Preview {
    ZStack {
        LinearGradient(
            colors: [
                Color(red: 0, green: 0.11, blue: 0.92),
                Color(red: 0.55, green: 0, blue: 0.92),
                Color(red: 0.91, green: 0, blue: 0.89)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()

        CameraControlsView(
            isFlashOn: false,
            scanMode: .constant(.flower),
            onCapture: {},
            onToggleFlash: {},
            onGalleryImage: { _ in },
            onClose: {}
        )
    }
}
