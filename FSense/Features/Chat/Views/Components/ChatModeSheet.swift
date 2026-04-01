import SwiftUI
import Photos

// MARK: - Chat Mode Sheet

/// Bottom sheet for selecting chat mode and attaching photos
struct ChatModeSheet: View {
    @ObservedObject var viewModel: ChatViewModel
    @Binding var isPresented: Bool

    @State private var recentPhotos: [PHAsset] = []
    @State private var showImagePicker = false
    @State private var imageSource: ImageSource = .photoLibrary

    // Photo library authorization
    @State private var photoAuthStatus: PHAuthorizationStatus = .notDetermined

    private static let lightShadowColor = Color.black.opacity(0.08)

    var body: some View {
        VStack(spacing: 0) {
            // Header
            headerSection

            // Photo picker section
            photoSection
                .padding(.top, 16)

            // Divider
            Divider()
                .padding(.vertical, 16)

            // Mode selection
            modeSection

            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.top, 20)
        .presentationDetents([.height(360)])
        .presentationDragIndicator(.visible)
        .presentationCornerRadius(24)
        .onAppear {
            checkPhotoAuthorization()
        }
        .sheet(isPresented: $showImagePicker) {
            ImagePickerView(source: imageSource, selectedImage: attachmentBinding)
        }
    }

    // MARK: - Header Section

    private var headerSection: some View {
        HStack {
            Text("FSense")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(.black)

            Spacer()

            if photoAuthStatus == .authorized || photoAuthStatus == .limited {
                Button {
                    imageSource = .photoLibrary
                    showImagePicker = true
                } label: {
                    HStack(spacing: 4) {
                        Text("All Photos")
                            .font(.system(size: 14, weight: .medium))
                        Image(systemName: "chevron.right")
                            .font(.system(size: 12, weight: .medium))
                    }
                    .foregroundStyle(ChatDesign.Colors.accentPurple)
                }
            }
        }
    }

    // MARK: - Photo Section

    private var photoSection: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            LazyHStack(spacing: 12) {
                // Camera button
                cameraButton

                // Recent photos - LazyHStack ensures only visible items render
                ForEach(recentPhotos.prefix(8), id: \.localIdentifier) { asset in
                    RecentPhotoThumbnail(asset: asset, onSelect: handlePhotoSelected)
                }
            }
            .padding(.horizontal, 1)  // Prevent shadow clipping
        }
        .frame(height: 90)
    }

    // Extracted closure to avoid recreation in ForEach
    private func handlePhotoSelected(_ image: UIImage) {
        viewModel.send(.attachImage(image))
        isPresented = false
    }

    private var cameraButton: some View {
        Button {
            imageSource = .camera
            showImagePicker = true
        } label: {
            VStack(alignment: .center, spacing: 10) {
                Image(systemName: "camera.fill")
                    .font(.system(size: 22))
                    .foregroundStyle(.black.opacity(0.7))
                Text("Camera")
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(.black.opacity(0.6))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .frame(width: 90, height: 90, alignment: .center)
            .background(.white)
            .cornerRadius(16)
            .compositingGroup()  // Performance: rasterize shadow
            .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Mode Section

    private var modeSection: some View {
        VStack(spacing: 12) {
            ModeButton(
                mode: .ask,
                isSelected: viewModel.chatMode == .ask
            ) {
                viewModel.send(.toggleMode(.ask))
            }

            ModeButton(
                mode: .find,
                isSelected: viewModel.chatMode == .find
            ) {
                viewModel.send(.toggleMode(.find))
            }
        }
    }

    // MARK: - Helpers

    private var attachmentBinding: Binding<UIImage?> {
        Binding(
            get: { viewModel.attachedImage },
            set: { image in
                if let image = image {
                    viewModel.send(.attachImage(image))
                    isPresented = false
                }
            }
        )
    }

    private func checkPhotoAuthorization() {
        photoAuthStatus = PHPhotoLibrary.authorizationStatus(for: .readWrite)

        switch photoAuthStatus {
        case .authorized, .limited:
            loadRecentPhotos()
        case .notDetermined:
            PHPhotoLibrary.requestAuthorization(for: .readWrite) { status in
                DispatchQueue.main.async {
                    photoAuthStatus = status
                    if status == .authorized || status == .limited {
                        loadRecentPhotos()
                    }
                }
            }
        default:
            break
        }
    }

    private func loadRecentPhotos() {
        // Move synchronous fetch off main thread to prevent hitches
        Task.detached(priority: .userInitiated) { @Sendable in
            let options = PHFetchOptions()
            options.sortDescriptors = [NSSortDescriptor(key: "creationDate", ascending: false)]
            options.fetchLimit = 10

            let result = PHAsset.fetchAssets(with: .image, options: options)
            // Use nonisolated local variable to avoid capture warning
            let fetchedAssets: [PHAsset] = {
                var assets: [PHAsset] = []
                assets.reserveCapacity(result.count)
                result.enumerateObjects { asset, _, _ in
                    assets.append(asset)
                }
                return assets
            }()

            await MainActor.run {
                self.recentPhotos = fetchedAssets
            }
        }
    }
}

// MARK: - Mode Button

private struct ModeButton: View {
    let mode: ChatMode
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(alignment: .center, spacing: 10) {
                // Icon
                Image(systemName: mode.iconName)
                    .font(.system(size: 20, weight: .medium))
                    .foregroundStyle(isSelected ? ChatDesign.Colors.accentPurple : .black.opacity(0.7))
                    .frame(width: 32)

                // Text
                VStack(alignment: .leading, spacing: 2) {
                    Text(mode.displayName)
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(.black)
                    Text(mode.subtitle)
                        .font(.system(size: 13))
                        .foregroundStyle(.black.opacity(0.5))
                }

                Spacer()

                // Selection indicator
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 22))
                        .foregroundStyle(ChatDesign.Colors.accentPurple)
                }
            }
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.white)
            .cornerRadius(16)
            .compositingGroup()  // Performance: rasterize shadow
            .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Recent Photo Thumbnail

private struct RecentPhotoThumbnail: View {
    let asset: PHAsset
    let onSelect: (UIImage) -> Void

    @State private var thumbnail: UIImage?

    // MARK: - Cached Request Options (Performance: avoid recreating per-request)
    private static let thumbnailOptions: PHImageRequestOptions = {
        let options = PHImageRequestOptions()
        options.deliveryMode = .opportunistic
        options.isNetworkAccessAllowed = true
        return options
    }()

    private static let fullImageOptions: PHImageRequestOptions = {
        let options = PHImageRequestOptions()
        options.deliveryMode = .highQualityFormat
        options.isNetworkAccessAllowed = true
        options.isSynchronous = false
        return options
    }()

    private static let thumbnailSize = CGSize(width: 180, height: 180)  // 2x for retina
    private static let fullImageSize = CGSize(width: 1024, height: 1024)

    var body: some View {
        Button {
            loadFullImage()
        } label: {
            thumbnailContent
        }
        .buttonStyle(.plain)
        .task {
            await loadThumbnailAsync()
        }
    }

    // Extracted to separate view for body simplicity
    @ViewBuilder
    private var thumbnailContent: some View {
        if let thumbnail {
            Image(uiImage: thumbnail)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(width: 90, height: 90)
                .clipShape(RoundedRectangle(cornerRadius: 16))
        } else {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(white: 0.9))
                .frame(width: 90, height: 90)
        }
    }

    @MainActor
    private func loadThumbnailAsync() async {
        guard thumbnail == nil else { return }

        let loadedImage = await withCheckedContinuation { continuation in
            PHImageManager.default().requestImage(
                for: asset,
                targetSize: Self.thumbnailSize,
                contentMode: .aspectFill,
                options: Self.thumbnailOptions
            ) { image, info in
                // Only continue if this is the final image (not degraded placeholder)
                let isDegraded = (info?[PHImageResultIsDegradedKey] as? Bool) ?? false
                if !isDegraded {
                    continuation.resume(returning: image)
                }
            }
        }

        thumbnail = loadedImage
    }

    private func loadFullImage() {
        PHImageManager.default().requestImage(
            for: asset,
            targetSize: Self.fullImageSize,
            contentMode: .aspectFit,
            options: Self.fullImageOptions
        ) { image, _ in
            if let image {
                DispatchQueue.main.async {
                    onSelect(image)
                }
            }
        }
    }
}
