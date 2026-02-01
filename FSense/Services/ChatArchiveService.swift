import Foundation

/// Service for archiving chat sessions
@MainActor
final class ChatArchiveService: ObservableObject {

    static let shared = ChatArchiveService()

    @Published private(set) var archivedSessions: [ArchivedChatSession] = []

    private let storageKey = "archived_chat_sessions"

    private init() {
        // Load archive asynchronously to avoid blocking main thread at startup
        Task { @MainActor in
            await loadArchiveAsync()
        }
    }

    // MARK: - Archive Statistics

    var sessionCount: Int {
        archivedSessions.count
    }

    // MARK: - Archive Management

    /// Archive a chat session
    func archiveSession(_ session: ChatSession) {
        // Check if session already exists (by ID)
        if let existingIndex = archivedSessions.firstIndex(where: { $0.session.id == session.id }) {
            // Update existing entry: move to top and update timestamp
            var updated = archivedSessions[existingIndex]
            updated = ArchivedChatSession(
                id: updated.id,
                session: session,
                archivedAt: updated.archivedAt
            )

            archivedSessions.remove(at: existingIndex)
            archivedSessions.insert(updated, at: 0)

            saveArchive()
            print("[ChatArchive] Updated session: \(session.title)")
        } else {
            // Create new entry
            let archived = ArchivedChatSession(
                id: UUID(),
                session: session,
                archivedAt: Date()
            )

            archivedSessions.insert(archived, at: 0)
            saveArchive()
            print("[ChatArchive] Archived session: \(session.title)")
        }
    }

    /// Remove a session from archive
    func removeSession(at offsets: IndexSet) {
        archivedSessions.remove(atOffsets: offsets)
        saveArchive()
    }

    /// Clear all archived sessions
    func clearArchive() {
        archivedSessions.removeAll()
        saveArchive()
    }

    // MARK: - Persistence

    private func saveArchive() {
        do {
            let encoder = JSONEncoder()
            let data = try encoder.encode(archivedSessions)
            UserDefaults.standard.set(data, forKey: storageKey)
        } catch {
            print("[ChatArchive] Failed to save: \(error)")
        }
    }

    /// Load archive asynchronously to prevent blocking main thread
    private func loadArchiveAsync() async {
        let key = storageKey

        // Read AND decode on background thread to fully avoid blocking UI
        let decoded = await Task.detached(priority: .userInitiated) {
            guard let data = UserDefaults.standard.data(forKey: key) else {
                return [ArchivedChatSession]()
            }

            do {
                let decoder = JSONDecoder()
                return try decoder.decode([ArchivedChatSession].self, from: data)
            } catch {
                print("[ChatArchive] Failed to decode: \(error)")
                return [ArchivedChatSession]()
            }
        }.value

        archivedSessions = decoded
        print("[ChatArchive] Loaded \(archivedSessions.count) sessions")
    }
}

// MARK: - Archived Chat Session Model

struct ArchivedChatSession: Identifiable, Codable {
    let id: UUID
    let session: ChatSession
    let archivedAt: Date
}
