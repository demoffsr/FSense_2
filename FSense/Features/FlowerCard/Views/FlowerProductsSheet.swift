import SwiftUI

/// Bottom sheet displaying flower product search results
struct FlowerProductsSheet: View {
    let products: [FlowerProduct]
    let flowerName: String
    @Binding var isPresented: Bool
    var onFindMore: (() -> Void)?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            sheetHeader
                .padding(.top, 12)
                .padding(.bottom, 16)

            // Content
            if products.isEmpty {
                emptyStateView
            } else {
                productListView
            }
        }
        .background(Color(.systemGray6))
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
        .presentationCornerRadius(20)
    }

    // MARK: - Header

    private var sheetHeader: some View {
        HStack {
            Text(flowerName)
                .font(.system(size: 22, weight: .semibold))
                .foregroundColor(.primary)

            Spacer()
        }
        .padding(.horizontal, 20)
    }

    // MARK: - Product List

    private var productListView: some View {
        ScrollView {
            VStack(spacing: 20) {
                ForEach(products) { product in
                    ShopProductCard(product: product)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 4)
            .padding(.bottom, 100) // Space for button
        }
        .safeAreaInset(edge: .bottom) {
            findMoreButton
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
                .background(Color(.systemGray6))
        }
    }

    private var findMoreButton: some View {
        Button {
            onFindMore?()
        } label: {
            Text("Find more")
                .font(.system(size: 17, weight: .medium))
                .foregroundColor(.primary)
                .frame(maxWidth: .infinity)
                .frame(minHeight: 50, maxHeight: 50)
                .background(Color(red: 0.98, green: 0.98, blue: 0.98))
                .cornerRadius(16)
                .shadow(color: .black.opacity(0.15), radius: 16, x: 0, y: 0)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .inset(by: 0.5)
                        .stroke(.white, lineWidth: 1)
                )
        }
    }

    // MARK: - Empty State

    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Spacer()

            Image(systemName: "magnifyingglass")
                .font(.system(size: 48))
                .foregroundColor(.gray)

            Text("No products found")
                .font(.headline)
                .foregroundColor(.primary)

            Text("We couldn't find any \(flowerName.lowercased()) for sale right now.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

// MARK: - Product Card

struct ShopProductCard: View {
    let product: FlowerProduct

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            // Product Image
            productImage

            // Product Details
            VStack(alignment: .leading, spacing: 0) {
                // Title - Callout (med)
                Text(product.name)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.black)
                    .frame(maxWidth: .infinity, minHeight: 44, maxHeight: 44, alignment: .topLeading)
                    .lineLimit(2)

                // Website - Subheadline (reg)
                Text(extractDomain(from: product.buyUrl))
                    .font(.system(size: 15))
                    .foregroundColor(.black.opacity(0.5))

                // Price and Open button row
                HStack(alignment: .center) {
                    // Price - Title3 (semibold)
                    if !product.price.isEmpty {
                        Text(product.price)
                            .font(.system(size: 20, weight: .semibold))
                            .foregroundColor(.black)
                    }

                    Spacer()

                    // Open Button
                    Button {
                        openProductLink()
                    } label: {
                        Text("Open")
                            .font(.system(size: 15, weight: .medium))
                            .foregroundColor(.black)
                            .padding(.horizontal, 0)
                            .padding(.vertical, 4)
                            .frame(width: 60, alignment: .center)
                            .background(Color(red: 0.98, green: 0.98, blue: 0.98))
                            .cornerRadius(100)
                            .shadow(color: .black.opacity(0.1), radius: 10.9, x: 0, y: 2)
                            .overlay(
                                RoundedRectangle(cornerRadius: 100)
                                    .inset(by: 0.5)
                                    .stroke(.white, lineWidth: 1)
                            )
                    }
                }
                .padding(.top, 8)
            }
        }
    }

    // MARK: - Product Image

    private var productImage: some View {
        Group {
            if let imageURL = product.imageURL {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .empty:
                        imagePlaceholder
                            .overlay(ProgressView().scaleEffect(0.8))
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
        .frame(width: 44, height: 44)
        .clipped()
        .cornerRadius(8)
    }

    private var imagePlaceholder: some View {
        Rectangle()
            .fill(Color.gray.opacity(0.2))
            .overlay(
                Image(systemName: "photo")
                    .font(.system(size: 16))
                    .foregroundColor(.gray.opacity(0.5))
            )
    }

    // MARK: - Helpers

    private func extractDomain(from urlString: String) -> String {
        guard let url = URL(string: urlString),
              let host = url.host else {
            return product.vendor
        }
        // Remove "www." prefix if present
        return host.hasPrefix("www.") ? String(host.dropFirst(4)) : host
    }

    private func openProductLink() {
        guard let url = product.purchaseURL else { return }
        UIApplication.shared.open(url)
    }
}

// MARK: - Previews

#Preview("With Products") {
    FlowerProductsSheet(
        products: FlowerProduct.mockProducts,
        flowerName: "Red Rose",
        isPresented: .constant(true)
    )
}

#Preview("Empty State") {
    FlowerProductsSheet(
        products: [],
        flowerName: "Orchids",
        isPresented: .constant(true)
    )
}
