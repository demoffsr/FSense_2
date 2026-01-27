import Foundation
import Combine

/// Real-time pipeline progress tracking via SSE
@MainActor
final class PipelineEventService: ObservableObject {

    static let shared = PipelineEventService()

    // MARK: - Published State (Direct binding to UI)

    @Published var steps: [ProgressStep] = []
    @Published var isConnected = false
    @Published var pipelineActive = false

    // MARK: - Private

    private var urlSession: URLSession?
    private var dataTask: URLSessionDataTask?
    private var buffer = Data()

    /// Pending data for batch processing
    private var pendingData: [Data] = []
    private var batchTask: Task<Void, Never>?

    /// Batch processing interval (50ms)
    private let batchIntervalNanoseconds: UInt64 = 50_000_000

    private init() {
        setupSteps()
    }

    // MARK: - All Steps Definition

    private let allAgents: [(id: String, emoji: String, text: String)] = [
        ("FIA", "🎯", "Analyzing intent"),
        ("EIA", "💞", "Understanding emotions"),
        ("RIL", "👥", "Processing relationships"),
        ("FMRA", "🌸", "Matching flowers"),
        ("CIA", "🎛️", "Measuring intensity"),
        ("AITB", "🎨", "Building response"),
        ("RFFA", "⚠️", "Assessing fit"),
        ("CRI", "🌍", "Adding cultural context"),
        ("SRFL", "🪞", "Reflecting on choice"),
        ("SFA", "✨", "Creating recommendation")
    ]

    // MARK: - Public API

    func start() {
        stop()
        setupSteps()
        pipelineActive = false
        connect()
    }

    func stop() {
        dataTask?.cancel()
        dataTask = nil
        urlSession?.invalidateAndCancel()
        urlSession = nil
        buffer = Data()
        pendingData = []
        batchTask?.cancel()
        batchTask = nil
        isConnected = false
        pipelineActive = false
        setupSteps()
    }

    private func setupSteps() {
        steps = allAgents.map { agent in
            ProgressStep(
                id: agent.id,
                emoji: agent.emoji,
                text: agent.text,
                status: .pending
            )
        }
    }

    // MARK: - SSE Connection (Using URLSessionDataDelegate for real-time)

    private func connect() {
        guard let baseURL = UserDefaults.standard.string(forKey: "api_base_url") ?? getDefaultBaseURL(),
              let url = URL(string: "\(baseURL)/api/logs/stream") else {
            print("[SSE] Invalid URL")
            return
        }

        print("[SSE] Connecting to: \(url)")

        var request = URLRequest(url: url)
        request.setValue("text/event-stream", forHTTPHeaderField: "Accept")
        request.setValue("no-cache", forHTTPHeaderField: "Cache-Control")
        request.timeoutInterval = 300

        // Create session with delegate for streaming
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalAndRemoteCacheData
        config.timeoutIntervalForRequest = 300
        config.timeoutIntervalForResource = 300

        let delegate = SSEDelegate { [weak self] data in
            Task { @MainActor in
                self?.handleDataBatched(data)
            }
        }

        urlSession = URLSession(configuration: config, delegate: delegate, delegateQueue: nil)
        dataTask = urlSession?.dataTask(with: request)
        dataTask?.resume()

        isConnected = true
    }

    private func getDefaultBaseURL() -> String? {
        // Match APIService configuration for consistency
        #if DEBUG
        return "http://192.168.1.176:8000"  // Use Mac's IP for real device testing
        #else
        return "http://localhost:8000"
        #endif
    }

    // MARK: - Data Handling (Batched)

    /// Queue data for batch processing to reduce Task overhead
    private func handleDataBatched(_ data: Data) {
        pendingData.append(data)

        // Schedule batch processing with debounce
        batchTask?.cancel()
        batchTask = Task { @MainActor [weak self] in
            guard let self = self else { return }

            // Wait for batch interval
            try? await Task.sleep(nanoseconds: self.batchIntervalNanoseconds)
            guard !Task.isCancelled else { return }

            // Process all pending data
            let batch = self.pendingData
            self.pendingData = []

            for data in batch {
                self.processData(data)
            }
        }
    }

    /// Process individual data chunk
    private func processData(_ data: Data) {
        buffer.append(data)

        // Process complete SSE messages (end with \n\n)
        while let range = buffer.range(of: Data("\n\n".utf8)) {
            let messageData = buffer.subdata(in: 0..<range.lowerBound)
            buffer.removeSubrange(0..<range.upperBound)

            if let message = String(data: messageData, encoding: .utf8) {
                processSSEMessage(message)
            }
        }
    }

    private func processSSEMessage(_ message: String) {
        // Parse SSE format: "data: {...}"
        for line in message.components(separatedBy: "\n") {
            if line.hasPrefix("data: ") {
                let json = String(line.dropFirst(6))
                parseEvent(json)
            }
        }
    }

    private func parseEvent(_ json: String) {
        guard let data = json.data(using: .utf8),
              let event = try? JSONDecoder().decode(SSEEvent.self, from: data) else {
            return
        }

        print("[SSE] Event: \(event.type) - \(event.agent ?? "none")")

        switch event.type {
        case "connected":
            print("[SSE] Server confirmed connection")

        case "pipeline_start":
            pipelineActive = true
            // Reset all to pending
            for i in steps.indices {
                steps[i].status = .pending
            }

        case "agent_start":
            if let agent = event.agent,
               let index = steps.firstIndex(where: { $0.id == agent }) {
                steps[index].status = .active
            }

        case "agent_end":
            if let agent = event.agent,
               let index = steps.firstIndex(where: { $0.id == agent }) {
                steps[index].status = .completed
            }

        case "pipeline_end":
            // Mark all remaining as completed
            for i in steps.indices {
                if steps[i].status != .completed {
                    steps[i].status = .completed
                }
            }
            pipelineActive = false

        default:
            break
        }
    }
}

// MARK: - Models

struct ProgressStep: Identifiable, Equatable {
    let id: String
    let emoji: String
    let text: String
    var status: StepStatus

    enum StepStatus: Equatable {
        case pending
        case active
        case completed
    }
}

struct SSEEvent: Decodable {
    let type: String
    let agent: String?
    let message: String?
    let success: Bool?

    enum CodingKeys: String, CodingKey {
        case type, agent, message, success
    }
}

// MARK: - URLSession Delegate for Real-time Streaming

private final class SSEDelegate: NSObject, URLSessionDataDelegate, @unchecked Sendable {
    let onData: @Sendable (Data) -> Void

    init(onData: @escaping @Sendable (Data) -> Void) {
        self.onData = onData
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        // Called immediately when data arrives - no buffering!
        onData(data)
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive response: URLResponse, completionHandler: @escaping (URLSession.ResponseDisposition) -> Void) {
        completionHandler(.allow)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error = error {
            print("[SSE] Connection error: \(error.localizedDescription)")
        }
    }
}
