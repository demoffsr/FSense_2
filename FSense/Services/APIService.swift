import Foundation
import UIKit

/// API Service for communicating with FSense backend
actor APIService {

    // MARK: - Singleton

    static let shared = APIService()

    // MARK: - Configuration

    /// Centralized base URL - single source of truth for all services
    /// Use this static property from other services to avoid hardcoding URLs
    static let baseURL: String = {
        #if DEBUG
        return "http://192.168.1.16:8000"  // Use Mac's IP for real device testing
        // Use "http://localhost:8000" if running on iOS Simulator
        #else
        return "http://localhost:8000" // TODO: Replace with production URL
        #endif
    }()

    /// Instance base URL (uses static property)
    private let baseURL = APIService.baseURL

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

    // MARK: - V2 API with Clarification Support

    /// Classify intent to determine if progress bar should be shown
    /// - Parameters:
    ///   - prompt: User's message
    ///   - context: Extended context with conversation history
    /// - Returns: IntentClassification with shouldShowProgress flag
    func classifyIntent(
        prompt: String,
        context: ChatContextV2? = nil
    ) async throws -> IntentClassification {
        let endpoint = "\(baseURL)/api/chat/classify"

        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ChatRequestV2Extended(
            prompt: prompt,
            region: context?.region ?? "US",
            imageBase64: nil,
            context: context
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            return try decoder.decode(IntentClassification.self, from: data)

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

    /// Send a message to the chat API (v2)
    /// Supports both flower recommendations and clarification text responses
    /// - Parameters:
    ///   - prompt: User's message
    ///   - context: Extended context with conversation history
    ///   - region: Geographic region
    ///   - image: Optional image
    /// - Returns: ChatResponse which can be either recommendation or text
    func sendMessage(
        prompt: String,
        context: ChatContextV2? = nil,
        region: String = "US",
        image: UIImage? = nil
    ) async throws -> ChatResponse {
        let endpoint = "\(baseURL)/api/chat"

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

        let body = ChatRequestV2Extended(
            prompt: prompt,
            region: region,
            imageBase64: imageBase64,
            context: context
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            let result = try decoder.decode(ChatResponseRaw.self, from: data)

            if !result.success {
                throw APIError.serverError(result.error ?? "Unknown error")
            }

            return ChatResponse(
                type: result.type,
                recommendation: result.type == .recommendation ? result.recommendationData : nil,
                textMessage: result.type == .text ? result.textData?.message : nil
            )

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

    /// Send a simple chat message (Ask mode) - no flower pipeline
    /// Uses gpt-4o-mini for fast responses
    /// - Parameters:
    ///   - prompt: User's message
    ///   - context: Optional conversation context
    ///   - image: Optional image attachment
    /// - Returns: Text response from AI
    func sendAskMessage(
        prompt: String,
        context: ChatContextV2? = nil,
        image: UIImage? = nil
    ) async throws -> String {
        let endpoint = "\(baseURL)/api/ask"

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

        let body = AskRequest(
            prompt: prompt,
            region: context?.region ?? "US",
            imageBase64: imageBase64,
            context: context
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            let result = try decoder.decode(AskResponse.self, from: data)
            if !result.success {
                throw APIError.serverError(result.error ?? "Unknown error")
            }
            return result.message

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

// MARK: - Ask API Models

private struct AskRequest: Encodable {
    let prompt: String
    let region: String
    let imageBase64: String?
    let context: ChatContextV2?

    enum CodingKeys: String, CodingKey {
        case prompt
        case region
        case imageBase64 = "image_base64"
        case context
    }
}

private struct AskResponse: Decodable {
    let success: Bool
    let message: String
    let error: String?
}

// MARK: - V2 API Models

/// Context from previous chat interaction (legacy, kept for backwards compatibility)
struct ChatContext: Codable {
    let lastFlowerName: String?
    let lastEmotion: String?
    let region: String

    init(lastFlowerName: String? = nil, lastEmotion: String? = nil, region: String = "US") {
        self.lastFlowerName = lastFlowerName
        self.lastEmotion = lastEmotion
        self.region = region
    }
}

// MARK: - V2 Extended Context Models

/// A single message in conversation history
struct ConversationMessage: Codable {
    let role: String           // "user" or "assistant"
    let content: String        // Message text
    let messageType: String?   // "text" or "recommendation"
    let flowerName: String?    // Flower name if recommendation

    init(role: String, content: String, messageType: String? = nil, flowerName: String? = nil) {
        self.role = role
        self.content = content
        self.messageType = messageType
        self.flowerName = flowerName
    }
}

/// Extended context with full conversation history
struct ChatContextV2: Codable {
    let conversationHistory: [ConversationMessage]
    let lastFlowerName: String?
    let lastEmotion: String?
    let region: String

    init(
        conversationHistory: [ConversationMessage] = [],
        lastFlowerName: String? = nil,
        lastEmotion: String? = nil,
        region: String = "US"
    ) {
        self.conversationHistory = conversationHistory
        self.lastFlowerName = lastFlowerName
        self.lastEmotion = lastEmotion
        self.region = region
    }
}

/// Response from intent classification endpoint
struct IntentClassification: Decodable {
    let intent: String
    let shouldShowProgress: Bool
}

/// Response type from v2 API
enum ChatResponseType: String, Codable {
    case recommendation
    case text
}

/// Unified chat response
struct ChatResponse {
    let type: ChatResponseType
    let recommendation: FlowerCardPayload?
    let textMessage: String?

    var isRecommendation: Bool { type == .recommendation }
    var isText: Bool { type == .text }
}

private struct ChatRequestV2Extended: Encodable {
    let prompt: String
    let region: String
    let imageBase64: String?
    let context: ChatContextV2?

    enum CodingKeys: String, CodingKey {
        case prompt
        case region
        case imageBase64 = "image_base64"
        case context
    }
}

private struct TextResponseData: Decodable {
    let message: String
}

private struct ChatResponseRaw: Decodable {
    let success: Bool
    let type: ChatResponseType
    let error: String?

    // For recommendation type
    let recommendationData: FlowerCardPayload?

    // For text type
    let textData: TextResponseData?

    enum CodingKeys: String, CodingKey {
        case success, type, error, data
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        success = try container.decode(Bool.self, forKey: .success)
        type = try container.decode(ChatResponseType.self, forKey: .type)
        error = try container.decodeIfPresent(String.self, forKey: .error)

        // Decode data based on type
        if type == .recommendation {
            recommendationData = try container.decodeIfPresent(FlowerCardPayload.self, forKey: .data)
            textData = nil
        } else {
            recommendationData = nil
            textData = try container.decodeIfPresent(TextResponseData.self, forKey: .data)
        }
    }
}

// MARK: - API Errors

// MARK: - Scan API

extension APIService {

    /// Scan a flower image and get quick identification
    /// - Parameters:
    ///   - image: UIImage to analyze
    ///   - mode: Single flower or bouquet mode
    /// - Returns: QuickScanResult with flower identification
    func scanFlower(image: UIImage, mode: ScanMode) async throws -> QuickScanResult {
        let endpoint = "\(apiBaseURL)/api/scan"

        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        guard let imageBase64 = imageToBase64(image) else {
            throw APIError.serverError("Failed to encode image")
        }

        let body = ScanRequestBody(
            imageBase64: imageBase64,
            scanMode: mode.rawValue,
            region: "US"
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            let result = try decoder.decode(QuickScanResponse.self, from: data)
            guard let scanData = result.data else {
                throw APIError.serverError(result.error ?? "No scan data returned")
            }
            return scanData

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

    /// Get detailed scan information
    /// - Parameters:
    ///   - requestId: Request ID from quick scan
    ///   - flowerId: Flower ID to get details for
    /// - Returns: ScanDetailResult with full flower information
    func getScanDetail(requestId: String, flowerId: String) async throws -> ScanDetailResult {
        let endpoint = "\(apiBaseURL)/api/scan/detail"

        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = ScanDetailRequestBody(requestId: requestId, flowerId: flowerId)
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            let result = try decoder.decode(ScanDetailResponse.self, from: data)
            guard let detailData = result.data else {
                throw APIError.serverError(result.error ?? "No detail data returned")
            }
            return detailData

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
}

// MARK: - Scan Request Bodies

private struct ScanRequestBody: Encodable {
    let imageBase64: String
    let scanMode: String
    let region: String

    enum CodingKeys: String, CodingKey {
        case imageBase64 = "image_base64"
        case scanMode = "scan_mode"
        case region
    }
}

private struct ScanDetailRequestBody: Encodable {
    let requestId: String
    let flowerId: String

    enum CodingKeys: String, CodingKey {
        case requestId = "request_id"
        case flowerId = "flower_id"
    }
}

// MARK: - Flower Product Search API

extension APIService {

    /// Search for flower products online
    /// - Parameters:
    ///   - flowerName: Name of flower to search
    ///   - city: City for delivery/search
    ///   - region: Geographic region (US, CA, RU)
    ///   - maxResults: Maximum products to return
    /// - Returns: FlowerSearchResponse with products
    func searchFlowerProducts(
        flowerName: String,
        city: String,
        region: String = "US",
        maxResults: Int = 10
    ) async throws -> FlowerSearchResponse {
        let endpoint = "\(apiBaseURL)/api/flowers/search"

        guard let url = URL(string: endpoint) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body = FlowerSearchRequestBody(
            flowerName: flowerName,
            city: city,
            region: region,
            maxResults: maxResults
        )
        request.httpBody = try JSONEncoder().encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200..<300:
            return try decoder.decode(FlowerSearchResponse.self, from: data)

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
}

private struct FlowerSearchRequestBody: Encodable {
    let flowerName: String
    let city: String
    let region: String
    let maxResults: Int

    enum CodingKeys: String, CodingKey {
        case flowerName = "flower_name"
        case city
        case region
        case maxResults = "max_results"
    }
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
