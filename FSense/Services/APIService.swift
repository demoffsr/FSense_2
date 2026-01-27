import Foundation
import UIKit

/// API Service for communicating with FSense backend
actor APIService {

    // MARK: - Singleton

    static let shared = APIService()

    // MARK: - Configuration

    /// Base URL for the API - change this for different environments
    #if DEBUG
    private let baseURL = "http://192.168.1.176:8000"  // Use Mac's IP for real device testing
    // Use "http://localhost:8000" if running on iOS Simulator
    #else
    private let baseURL = "http://localhost:8000" // TODO: Replace with production URL
    #endif

    private let session: URLSession
    private let decoder: JSONDecoder

    // MARK: - Initialization

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 60 // AI calls can take time
        config.timeoutIntervalForResource = 120
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
    }

    // MARK: - Public API

    /// Get the base URL for API requests
    var apiBaseURL: String {
        baseURL
    }

    /// Request a flower recommendation from the backend
    /// - Parameters:
    ///   - prompt: User's message/query
    ///   - region: Geographic region for cultural context (default: "US")
    ///   - image: Optional bouquet image for flower identification
    /// - Returns: FlowerCardPayload containing the recommendation
    func getRecommendation(prompt: String, region: String = "US", image: UIImage? = nil) async throws -> FlowerCardPayload {
        let endpoint = "\(baseURL)/api/recommend"

        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        // Convert image to base64 if provided
        var imageBase64: String? = nil
        if let image = image {
            imageBase64 = imageToBase64(image)
        }

        let body = RecommendRequest(prompt: prompt, region: region, imageBase64: imageBase64)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            let result = try decoder.decode(RecommendResponse.self, from: data)
            return result.data

        case 400..<500:
            if let errorResponse = try? decoder.decode(APIErrorResponse.self, from: data) {
                throw APIError.serverError(errorResponse.detail)
            }
            throw APIError.clientError(httpResponse.statusCode)

        case 500..<600:
            throw APIError.serverError("Server error: \(httpResponse.statusCode)")

        default:
            throw APIError.unknown(httpResponse.statusCode)
        }
    }

    /// Check if the backend is available
    func healthCheck() async -> Bool {
        guard let url = URL(string: "\(baseURL)/health") else {
            return false
        }

        do {
            let (_, response) = try await session.data(from: url)
            if let httpResponse = response as? HTTPURLResponse {
                return httpResponse.statusCode == 200
            }
            return false
        } catch {
            return false
        }
    }
}

// MARK: - Request/Response Models

private struct RecommendRequest: Encodable {
    let prompt: String
    let region: String
    let imageBase64: String?

    enum CodingKeys: String, CodingKey {
        case prompt
        case region
        case imageBase64 = "image_base64"
    }
}

private struct RecommendResponse: Decodable {
    let success: Bool
    let data: FlowerCardPayload
}

private struct APIErrorResponse: Decodable {
    let detail: String
}

// MARK: - API Errors

enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case clientError(Int)
    case serverError(String)
    case decodingError(Error)
    case networkError(Error)
    case unknown(Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .clientError(let code):
            return "Request error: \(code)"
        case .serverError(let message):
            return message
        case .decodingError(let error):
            return "Failed to parse response: \(error.localizedDescription)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .unknown(let code):
            return "Unknown error: \(code)"
        }
    }
}
