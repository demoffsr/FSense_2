import SwiftUI

struct FlowerArchiveView: View {

    @Environment(\.themeAccent) private var themeAccent
    @StateObject private var archiveService = FlowerArchiveService.shared
    @State private var selectedFlower: Flower?
    @State private var navigateToDetail = false

    // Pagination
    @State private var displayedCount: Int = 20
    private let batchSize: Int = 20

    var body: some View {
        ZStack {
            if archiveService.archivedFlowers.isEmpty {
                emptyState
            } else {
                flowerList
            }
        }
        .navigationTitle("Flower Archive")
        .navigationBarTitleDisplayMode(.large)
        .navigationDestination(isPresented: $navigateToDetail) {
            if let flower = selectedFlower {
                FlowerCardView(flower: flower)
                    .id(flower.id)
            }
        }
        .toolbar {
            if !archiveService.archivedFlowers.isEmpty {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(role: .destructive) {
                        archiveService.clearArchive()
                        displayedCount = batchSize
                    } label: {
                        Text("Clear All")
                            .foregroundColor(.red)
                    }
                }
            }
        }
        .onChange(of: archiveService.archivedFlowers.count) { oldCount, newCount in
            // Reset pagination if archive was cleared or significantly changed
            if newCount < oldCount {
                displayedCount = min(displayedCount, max(newCount, batchSize))
            }
        }
    }

    // MARK: - Flower List

    private var displayedFlowers: [ArchivedFlower] {
        Array(archiveService.archivedFlowers.prefix(displayedCount))
    }

    private var hasMoreToLoad: Bool {
        displayedCount < archiveService.archivedFlowers.count
    }

    private var flowerList: some View {
        List {
            ForEach(displayedFlowers) { archivedItem in
                FlowerArchiveRow(
                    flower: archivedItem.flower,
                    lastViewedAt: archivedItem.lastViewedAt
                )
                .contentShape(Rectangle())
                .onTapGesture {
                    selectedFlower = archivedItem.flower
                    navigateToDetail = true
                }
            }
            .onDelete { indexSet in
                archiveService.removeFlower(at: indexSet)
            }

            // Load more trigger
            if hasMoreToLoad {
                Color.clear
                    .frame(height: 1)
                    .onAppear {
                        displayedCount += batchSize
                    }
            }
        }
        .listStyle(.plain)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "leaf.fill")
                .font(.system(size: 64))
                .foregroundColor(.secondary.opacity(0.5))

            Text("No Flowers Yet")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Explore flowers to build your collection")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
    }
}

// MARK: - Archive Row

struct FlowerArchiveRow: View {

    @Environment(\.themeAccent) private var themeAccent

    let flower: Flower
    let lastViewedAt: Date

    var body: some View {
        HStack(spacing: 16) {
            // Flower Image
            flowerImage
                .frame(width: 80, height: 80)
                .clipShape(RoundedRectangle(cornerRadius: 12))

            // Flower Info
            VStack(alignment: .leading, spacing: 6) {
                Text(flower.name)
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.primary)

                Text(flower.meanings.prefix(3).joined(separator: " · "))
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
                    .lineLimit(1)

                Text("Last viewed \(formattedDate)")
                    .font(.system(size: 12))
                    .foregroundColor(.secondary.opacity(0.7))
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.secondary.opacity(0.5))
        }
        .padding(.vertical, 8)
    }

    // MARK: - Flower Image

    @ViewBuilder
    private var flowerImage: some View {
        if let imageURL = flower.imageURL {
            CachedAsyncImage(url: imageURL) { image in
                image
                    .resizable()
                    .aspectRatio(contentMode: .fill)
            } placeholder: {
                fallbackImage
            }
        } else if let asset = flower.imageAsset {
            Image(asset)
                .resizable()
                .aspectRatio(contentMode: .fill)
        } else {
            fallbackImage
        }
    }

    private var fallbackImage: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [Color.pink.opacity(0.3), themeAccent.opacity(0.2)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
            .overlay(
                Image(systemName: "leaf.fill")
                    .font(.system(size: 28))
                    .foregroundColor(.white.opacity(0.8))
            )
    }

    // MARK: - Date Formatting

    private var formattedDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: lastViewedAt, relativeTo: Date())
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        FlowerArchiveView()
    }
}
