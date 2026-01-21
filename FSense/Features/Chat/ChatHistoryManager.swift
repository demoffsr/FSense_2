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
    
    private let userDefaults = UserDefaults.standard
    private let sessionsKey = "chat_sessions"
    
    // MARK: - Initialization
    
    private init() {
        loadSessions()
    }
    
    // MARK: - Public API
    
    /// Creates a new chat session and returns it
    func createNewSession() -> ChatSession {
        let session = ChatSession()
        sessions.insert(session, at: 0)
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
        saveSessions()
    }
    
    /// Deletes a session by ID
    func deleteSession(by id: UUID) {
        sessions.removeAll { $0.id == id }
        saveSessions()
    }
    
    /// Returns only chat sessions (not scans)
    var chatSessions: [ChatSession] {
        sessions.filter { session in
            // A session is a chat if it has at least one user message
            session.messages.contains { $0.sender == .user }
        }
    }
    
    /// Returns recent sessions (limited)
    func recentSessions(limit: Int = 10) -> [ChatSession] {
        Array(chatSessions.prefix(limit))
    }
    
    // MARK: - Private Methods
    
    private func loadSessions() {
        guard let data = userDefaults.data(forKey: sessionsKey),
              let decoded = try? JSONDecoder().decode([ChatSession].self, from: data) else {
            sessions = []
            return
        }
        sessions = decoded.sorted { $0.updatedAt > $1.updatedAt }
    }
    
    private func saveSessions() {
        guard let encoded = try? JSONEncoder().encode(sessions) else { return }
        userDefaults.set(encoded, forKey: sessionsKey)
    }
}
