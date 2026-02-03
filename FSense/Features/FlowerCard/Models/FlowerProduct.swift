import Foundation

/// Product card model for "Find Flowers" search results (maps to ShopCard on backend)
struct FlowerProduct: Identifiable, Codable, Equatable {
    let productId: String
    let name: String
    let price: String
    let priceValue: Double?
    let currency: String?
    let imageUrl: String?
    let vendor: String
    let buyUrl: String
    let city: String?

    var id: String { productId }

    enum CodingKeys: String, CodingKey {
        case productId = "product_id"
        case name
        case price
        case priceValue = "price_value"
        case currency
        case imageUrl = "image_url"
        case vendor
        case buyUrl = "buy_url"
        case city
    }

    var imageURL: URL? {
        guard let imageUrl else { return nil }
        return URL(string: imageUrl)
    }

    var purchaseURL: URL? {
        URL(string: buyUrl)
    }

    /// Currency symbol based on currency code
    var currencySymbol: String {
        switch currency?.uppercased() {
        case "RUB": return "₽"
        case "CAD": return "CA$"
        case "USD", .none: return "$"
        default: return currency ?? "$"
        }
    }
}

/// Response wrapper for product search
struct FlowerSearchResponse: Codable {
    let success: Bool
    let query: String
    let provider: String?
    let products: [FlowerProduct]
    let error: String?
    let cachedAt: String?  // ISO timestamp when results were cached

    enum CodingKeys: String, CodingKey {
        case success
        case query
        case provider
        case products
        case error
        case cachedAt = "cached_at"
    }
}

// MARK: - Mock Data

extension FlowerProduct {
    static let mock = FlowerProduct(
        productId: "mock_001",
        name: "Dozen Red Roses Bouquet",
        price: "$49.99",
        priceValue: 49.99,
        currency: "USD",
        imageUrl: "https://images.unsplash.com/photo-1518882605630-8eb572299d16?w=400",
        vendor: "1-800-Flowers",
        buyUrl: "https://www.1800flowers.com",
        city: "New York"
    )

    static let mockProducts: [FlowerProduct] = [
        FlowerProduct(
            productId: "mock_001",
            name: "Dozen Red Roses Bouquet",
            price: "$49.99",
            priceValue: 49.99,
            currency: "USD",
            imageUrl: "https://images.unsplash.com/photo-1518882605630-8eb572299d16?w=400",
            vendor: "1-800-Flowers",
            buyUrl: "https://www.1800flowers.com",
            city: "New York"
        ),
        FlowerProduct(
            productId: "mock_002",
            name: "Premium Rose Arrangement",
            price: "$79.99",
            priceValue: 79.99,
            currency: "USD",
            imageUrl: "https://images.unsplash.com/photo-1455659817273-f96807779a8a?w=400",
            vendor: "FTD",
            buyUrl: "https://www.ftd.com",
            city: "New York"
        ),
        FlowerProduct(
            productId: "mock_003",
            name: "Red Roses in Vase",
            price: "2500 ₽",
            priceValue: 2500,
            currency: "RUB",
            imageUrl: "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=400",
            vendor: "Флорист.ру",
            buyUrl: "https://www.florist.ru",
            city: "Москва"
        ),
    ]
}
