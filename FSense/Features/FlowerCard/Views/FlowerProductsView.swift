import SwiftUI

/// View displaying flower product search results
struct FlowerProductsView: View {
    let products: [FlowerProduct]
    let flowerName: String

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        Group {
            if products.isEmpty {
                emptyStateView
            } else {
                productListView
            }
        }
        .navigationTitle("Buy \(flowerName)")
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button {
                    dismiss()
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.primary)
                }
            }
        }
    }

    // MARK: - Product List

    private var productListView: some View {
        ScrollView {
            LazyVStack(spacing: 12) {
                ForEach(products) { product in
                    FlowerProductCard(product: product)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            .padding(.bottom, 32)
        }
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.gray)

            Text("No products found")
                .font(.headline)
                .foregroundColor(.primary)

            Text("We couldn't find any \(flowerName.lowercased()) for sale right now. Try again later.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button {
                dismiss()
            } label: {
                Text("Go Back")
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.white)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                    .background(Color.accentColor)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }
}

// MARK: - Product Card

struct FlowerProductCard: View {
    let product: FlowerProduct

    var body: some View {
        Button {
            openProductLink()
        } label: {
            HStack(spacing: 12) {
                // Product Image
                productImage

                // Product Details
                VStack(alignment: .leading, spacing: 4) {
                    Text(product.name)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(.primary)
                        .lineLimit(2)
                        .multilineTextAlignment(.leading)

                    Text(product.vendor)
                        .font(.system(size: 13))
                        .foregroundColor(.secondary)

                    HStack {
                        Text(product.price)
                            .font(.system(size: 17, weight: .bold))
                            .foregroundColor(.primary)

                        Spacer()

                        if let city = product.city {
                            HStack(spacing: 2) {
                                Image(systemName: "location.fill")
                                    .font(.system(size: 10))
                                    .foregroundColor(.secondary)
                                Text(city)
                                    .font(.system(size: 12))
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }

                Image(systemName: "arrow.up.right")
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)
            }
            .padding(12)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(Color(.systemBackground))
            )
            .shadow(color: .black.opacity(0.06), radius: 8, x: 0, y: 2)
        }
        .buttonStyle(.plain)
    }

    // MARK: - Product Image

    private var productImage: some View {
        Group {
            if let imageURL = product.imageURL {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .empty:
                        imagePlaceholder
                            .overlay(ProgressView())
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure:
                        imagePlaceholder
                    @unknown default:
                        imagePlaceholder
                    }
                }
            } else {
                imagePlaceholder
            }
        }
        .frame(width: 80, height: 80)
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var imagePlaceholder: some View {
        Rectangle()
            .fill(Color.gray.opacity(0.15))
            .overlay(
                Image(systemName: "photo")
                    .font(.system(size: 24))
                    .foregroundColor(.gray.opacity(0.5))
            )
    }

    // MARK: - Actions

    private func openProductLink() {
        guard let url = product.purchaseURL else { return }
        UIApplication.shared.open(url)
    }
}

// MARK: - Previews

#Preview("With Products") {
    NavigationStack {
        FlowerProductsView(
            products: FlowerProduct.mockProducts,
            flowerName: "Red Roses"
        )
    }
}

#Preview("Empty State") {
    NavigationStack {
        FlowerProductsView(
            products: [],
            flowerName: "Orchids"
        )
    }
}
