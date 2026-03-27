import SwiftUI
import Foundation

/// Manages scan history persistence and retrieval
@MainActor
final class ScanHistoryManager: ObservableObject {

    // MARK: - Singleton

    static let shared = ScanHistoryManager()

    // MARK: - Published State

    @Published private(set) var sessions: [ScanSession] = []

    // MARK: - Private Properties

    private let userDefaults = UserDefaults.standard
    private let sessionsKey = "scan_sessions"
    private let maxSessions = 50

    // MARK: - Initialization

    private init() {
        loadSessions()
    }

    // MARK: - Public API

    /// Save a scan session from a quick scan result
    func saveSession(_ result: QuickScanResult, image: UIImage?) {
        let session = ScanSession(
            id: UUID(),
            flowerName: result.primaryFlower.name,
            scientificName: result.primaryFlower.scientificName,
            confidence: result.primaryFlower.confidence,
            color: result.primaryFlower.color,
            imagePath: saveImage(image),
            scannedAt: Date(),
            scanMode: ScanMode(rawValue: result.scanMode) ?? .flower,
            requestId: result.requestId,
            additionalFlowerCount: result.additionalFlowers.count
        )

        sessions.insert(session, at: 0)

        // Trim to max sessions
        if sessions.count > maxSessions {
            let removed = sessions.removeLast()
            deleteImage(at: removed.imagePath)
        }

        saveSessions()
    }

    /// Delete a scan session
    func deleteSession(_ id: UUID) {
        if let index = sessions.firstIndex(where: { $0.id == id }) {
            let session = sessions[index]
            deleteImage(at: session.imagePath)
            sessions.remove(at: index)
            saveSessions()
        }
    }

    /// Clear all scan history
    func clearHistory() {
        for session in sessions {
            deleteImage(at: session.imagePath)
        }
        sessions.removeAll()
        saveSessions()
    }

    // MARK: - Private Methods

    private func loadSessions() {
        guard let data = userDefaults.data(forKey: sessionsKey) else { return }
        do {
            sessions = try JSONDecoder().decode([ScanSession].self, from: data)
        } catch {
            print("[ScanHistoryManager] Failed to load sessions: \(error)")
        }
    }

    private func saveSessions() {
        do {
            let data = try JSONEncoder().encode(sessions)
            userDefaults.set(data, forKey: sessionsKey)
        } catch {
            print("[ScanHistoryManager] Failed to save sessions: \(error)")
        }
    }

    private func saveImage(_ image: UIImage?) -> String? {
        guard let image = image,
              let data = image.jpegData(compressionQuality: 0.7) else {
            return nil
        }

        let filename = UUID().uuidString + ".jpg"
        let url = getDocumentsDirectory().appendingPathComponent("scan_images/\(filename)")

        // Create directory if needed
        try? FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )

        do {
            try data.write(to: url)
            return filename
        } catch {
            print("[ScanHistoryManager] Failed to save image: \(error)")
            return nil
        }
    }

    private func deleteImage(at path: String?) {
        guard let path = path else { return }
        let url = getDocumentsDirectory().appendingPathComponent("scan_images/\(path)")
        try? FileManager.default.removeItem(at: url)
    }

    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

// MARK: - Scan Session Model

struct ScanSession: Identifiable, Codable {
    let id: UUID
    let flowerName: String
    let scientificName: String?
    let confidence: Double
    let color: String?
    let imagePath: String?
    let scannedAt: Date
    let scanMode: ScanMode
    let requestId: String
    let additionalFlowerCount: Int

    var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: scannedAt)
    }

    var relativeDate: String {
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: scannedAt, relativeTo: Date())
    }

    var confidencePercentage: Int {
        Int(confidence * 100)
    }
}

// MARK: - Helper Extensions

extension ScanSession {
    /// Load the thumbnail image if available
    func loadImage() -> UIImage? {
        guard let path = imagePath else { return nil }
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("scan_images/\(path)")
        return UIImage(contentsOfFile: url.path)
    }
}
