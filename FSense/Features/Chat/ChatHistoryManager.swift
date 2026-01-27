import Foundation
import SwiftUI

/// Singleton manager for chat history persistence
/// Handles saving, loading, and managing chat sessions
@MainActor
final class ChatHistoryManager: ObservableObject {

    // MARK: - Singleton

    static let shared = ChatHistoryManager()

    // MARK: - Published State

    @Published private(set) var sessions: [ChatSession] = []

    // MARK: - Private Properties

    private let sessionsKey = "chat_sessions"

    /// Debounced save task to prevent excessive UserDefaults writes
    private var saveTask: Task<Void, Never>?

    /// Debounce interval for saving (300ms)
    private let saveDebounceNanoseconds: UInt64 = 300_000_000

    // MARK: - Initialization

    private init() {
        // Load sessions asynchronously to avoid blocking main thread at startup
        Task { @MainActor in
            await loadSessionsAsync()
        }
    }
    
    // MARK: - Public API
    
    /// Creates a new chat session and returns it
    func createNewSession() -> ChatSession {
        let session = ChatSession()
        sessions.insert(session, at: 0)
        updateChatSessionsCache()
        saveSessions()
        return session
    }
    
    /// Updates an existing session with new messages
    func updateSession(_ session: ChatSession) {
        if let index = sessions.firstIndex(where: { $0.id == session.id }) {
            var updated = session
            updated.updatedAt = Date()
            updated.updateTitleFromMessages()
            updated.updateSubtitleFromRecommendation()
            sessions[index] = updated
        } else {
            // Session doesn't exist, add it
            var newSession = session
            newSession.updatedAt = Date()
            newSession.updateTitleFromMessages()
            newSession.updateSubtitleFromRecommendation()
            sessions.insert(newSession, at: 0)
        }
        
        // Sort by most recent
        sessions.sort { $0.updatedAt > $1.updatedAt }
        updateChatSessionsCache()
        saveSessions()
    }

    /// Saves messages to a specific session
    func saveMessages(_ messages: [ChatMessage], to sessionId: UUID) {
        if let index = sessions.firstIndex(where: { $0.id == sessionId }) {
            sessions[index].messages = messages
            sessions[index].updatedAt = Date()
            sessions[index].updateTitleFromMessages()
            sessions[index].updateSubtitleFromRecommendation()

            // Sort by most recent
            sessions.sort { $0.updatedAt > $1.updatedAt }
            updateChatSessionsCache()
            saveSessions()
        }
    }

    /// Gets a session by ID
    func getSession(by id: UUID) -> ChatSession? {
        sessions.first { $0.id == id }
    }

    /// Deletes a session
    func deleteSession(_ session: ChatSession) {
        sessions.removeAll { $0.id == session.id }
        updateChatSessionsCache()
        saveSessions()
    }

    /// Deletes a session by ID
    func deleteSession(by id: UUID) {
        sessions.removeAll { $0.id == id }
        updateChatSessionsCache()
        saveSessions()
    }

    /// Renames a session
    func renameSession(_ session: ChatSession, newTitle: String) {
        if let index = sessions.firstIndex(where: { $0.id == session.id }) {
            sessions[index].title = newTitle
            sessions[index].updatedAt = Date()
            saveSessions()
        }
    }

    /// Cached filtered chat sessions - updated when sessions change
    @Published private(set) var chatSessions: [ChatSession] = []

    /// Update cached chat sessions (call after sessions array changes)
    private func updateChatSessionsCache() {
        chatSessions = sessions.filter { session in
            // A session is a chat if it has at least one user message
            session.messages.contains { $0.sender == .user }
        }
    }
    
    /// Returns recent sessions (limited)
    func recentSessions(limit: Int = 10) -> [ChatSession] {
        Array(chatSessions.prefix(limit))
    }
    
    // MARK: - Private Methods

    private func loadSessionsAsync() async {
        // Read AND decode on background thread to fully avoid blocking UI
        let key = sessionsKey

        let decoded = await Task.detached(priority: .userInitiated) {
            // UserDefaults.standard is thread-safe
            guard let data = UserDefaults.standard.data(forKey: key) else {
                return [ChatSession]()
            }

            do {
                let sessions = try JSONDecoder().decode([ChatSession].self, from: data)
                return sessions.sorted { $0.updatedAt > $1.updatedAt }
            } catch {
                print("[ChatHistory] Failed to decode sessions: \(error)")
                return [ChatSession]()
            }
        }.value

        sessions = decoded
        updateChatSessionsCache()
    }

    /// Save sessions with debounce and background encoding to prevent UI freezes
    private func saveSessions() {
        // Cancel any pending save task
        saveTask?.cancel()

        // Capture values for closure
        let sessionsSnapshot = sessions
        let key = sessionsKey
        let debounceNanos = saveDebounceNanoseconds

        saveTask = Task {
            // Debounce: wait before saving to batch rapid changes
            do {
                try await Task.sleep(nanoseconds: debounceNanos)
            } catch {
                // Task was cancelled, don't save
                return
            }

            guard !Task.isCancelled else { return }

            // Encode on background thread to avoid blocking UI
            let encoded = await Task.detached(priority: .utility) {
                try? JSONEncoder().encode(sessionsSnapshot)
            }.value

            guard !Task.isCancelled, let data = encoded else { return }

            // UserDefaults.standard is thread-safe for set operations
            UserDefaults.standard.set(data, forKey: key)
        }
    }
}
