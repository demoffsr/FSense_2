import Foundation
import SwiftUI

/// Represents the state when opening the chat sheet
enum ActiveChatState {
    /// Fresh chat - no previous session or timed out
    case fresh
    /// Only draft text preserved (no session yet)
    case draftOnly(draftText: String)
    /// Existing session with optional draft
    case existingSession(sessionId: UUID, draftText: String)
}

/// Singleton manager for active chat session state
/// Handles session persistence across sheet open/close cycles with 30-second timeout
@MainActor
final class ActiveChatStateManager: ObservableObject {

    // MARK: - Singleton

    static let shared = ActiveChatStateManager()

    // MARK: - Configuration

    private let inactivityTimeoutSeconds: TimeInterval = 30

    // MARK: - Persisted State (UserDefaults)

    private let activeSessionIdKey = "active_chat_session_id"
    private let draftTextKey = "active_chat_draft_text"
    private let lastInteractionTimeKey = "active_chat_last_interaction"

    // MARK: - Published State

    @Published private(set) var activeSessionId: UUID?
    @Published private(set) var draftText: String = ""

    // MARK: - Private State

    private var lastInteractionTime: Date = Date()

    // MARK: - Initialization

    private init() {
        loadState()
    }

    // MARK: - Public API

    /// Called when the chat sheet is about to open
    /// Determines whether to restore session, draft, or start fresh
    func prepareForSheetOpen() -> ActiveChatState {
        loadState()

        let timeSinceLastInteraction = Date().timeIntervalSince(lastInteractionTime)

        // Check if timed out
        if timeSinceLastInteraction > inactivityTimeoutSeconds {
            // Timeout - clear active state and start fresh
            clearActiveState()
            return .fresh
        }

        // Within timeout window - check what we have
        if let sessionId = activeSessionId {
            return .existingSession(sessionId: sessionId, draftText: draftText)
        } else if !draftText.isEmpty {
            return .draftOnly(draftText: draftText)
        } else {
            return .fresh
        }
    }

    /// Record user interaction to reset the inactivity timer
    func recordInteraction() {
        lastInteractionTime = Date()
        saveState()
    }

    /// Update the draft text (called on every keystroke or text change)
    func updateDraft(_ text: String) {
        draftText = text
        lastInteractionTime = Date()
        saveState()
    }

    /// Set the active session ID (called when first message is sent)
    func setActiveSession(_ sessionId: UUID) {
        activeSessionId = sessionId
        lastInteractionTime = Date()
        saveState()
    }

    /// Called when the chat sheet closes
    /// Saves current draft and session state
    func onSheetClose(currentDraft: String, currentSessionId: UUID?) {
        draftText = currentDraft
        activeSessionId = currentSessionId
        lastInteractionTime = Date()
        saveState()
    }

    /// Clear all active state (called on explicit reset or new chat)
    func clearActiveState() {
        activeSessionId = nil
        draftText = ""
        lastInteractionTime = Date()
        saveState()
    }

    // MARK: - Private Methods

    private func loadState() {
        let defaults = UserDefaults.standard

        // Load session ID
        if let sessionIdString = defaults.string(forKey: activeSessionIdKey),
           let sessionId = UUID(uuidString: sessionIdString) {
            activeSessionId = sessionId
        } else {
            activeSessionId = nil
        }

        // Load draft text
        draftText = defaults.string(forKey: draftTextKey) ?? ""

        // Load last interaction time
        if let timestamp = defaults.object(forKey: lastInteractionTimeKey) as? Date {
            lastInteractionTime = timestamp
        } else {
            lastInteractionTime = Date()
        }
    }

    private func saveState() {
        let defaults = UserDefaults.standard

        // Save session ID
        if let sessionId = activeSessionId {
            defaults.set(sessionId.uuidString, forKey: activeSessionIdKey)
        } else {
            defaults.removeObject(forKey: activeSessionIdKey)
        }

        // Save draft text
        if draftText.isEmpty {
            defaults.removeObject(forKey: draftTextKey)
        } else {
            defaults.set(draftText, forKey: draftTextKey)
        }

        // Save last interaction time
        defaults.set(lastInteractionTime, forKey: lastInteractionTimeKey)
    }
}
