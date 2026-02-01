import SwiftUI

/// ViewModel for Home screen
/// Responsibility: Handles state and actions for Home feature
@MainActor
final class HomeViewModel: ObservableObject {

    @Published var state = HomeState()

    /// Access to chat history
    let chatHistory = ChatHistoryManager.shared

    /// Access to scan history
    let scanHistory = ScanHistoryManager.shared

    /// Per-session view models (granular dependencies for performance)
    @Published private(set) var sessionViewModels: [UUID: ChatSessionViewModel] = [:] {
        didSet {
            // Recompute sorted cache only when dictionary changes
            _cachedSortedViewModels = Array(sessionViewModels.values)
                .sorted { $0.updatedAt > $1.updatedAt }
        }
    }

    /// Cached sorted array - O(1) access, O(n log n) only on mutation
    private var _cachedSortedViewModels: [ChatSessionViewModel] = []

    /// Sorted recent chat view models (cached, O(1) access)
    var recentChatViewModels: [ChatSessionViewModel] {
        _cachedSortedViewModels
    }

    /// Legacy accessor for compatibility (TODO: remove after migration)
    @Published var recentChats: [ChatSession] = []

    /// Recent scan items from ScanHistoryManager
    var recentScans: [RecentScanItem] {
        scanHistory.sessions.prefix(10).map { session in
            RecentScanItem(
                id: session.id,
                flowerName: session.flowerName,
                subtitle: session.scientificName ?? session.relativeDate,
                imageAsset: nil,
                imagePath: session.imagePath,
                scannedAt: session.scannedAt,
                confidence: session.confidence,
                requestId: session.requestId
            )
        }
    }

    /// Task for observing chat history changes (replaces Combine subscription)
    private var observationTask: Task<Void, Never>?
    private var isSetup = false

    init() {
        // Defer setup to avoid blocking app launch
        // Will be triggered on first onAppear
    }

    deinit {
        observationTask?.cancel()
    }

    /// Setup async observation - called lazily on first onAppear
    private func setupBindingsIfNeeded() {
        guard !isSetup else { return }
        isSetup = true

        // Observe chat history changes using async/await
        observationTask = Task { [weak self] in
            guard let self = self else { return }

            // Use .values to convert Combine publisher to AsyncSequence
            for await sessions in chatHistory.$sessions.values {
                guard !Task.isCancelled else { break }
                self.handleSessionsUpdate(sessions)
            }
        }
    }

    /// Handle sessions update from async observation
    private func handleSessionsUpdate(_ sessions: [ChatSession]) {
        // Filter sessions with user messages
        let validSessions = sessions.filter { session in
            session.messages.contains { $0.sender == .user }
        }

        // Update view models dictionary (granular updates)
        // Only affected sessions will trigger SwiftUI updates
        var newViewModels: [UUID: ChatSessionViewModel] = [:]

        for session in validSessions {
            if let existing = sessionViewModels[session.id] {
                // Update existing view model (only this row updates)
                existing.update(from: session)
                newViewModels[session.id] = existing
            } else {
                // Create new view model
                newViewModels[session.id] = ChatSessionViewModel(from: session)
            }
        }

        sessionViewModels = newViewModels

        // Keep legacy array for compatibility
        recentChats = validSessions
    }
    
    func send(_ action: HomeAction) {
        switch action {
        case .onAppear:
            // Refresh data when view appears
            refreshData()
            
        case .avatarTapped:
            // Navigate to profile
            break
            
        case .searchTextChanged(let text):
            state.searchText = text
            
        case .settingsTapped:
            // Navigate to settings
            break
            
        case .bannerTapped:
            // Handle banner tap
            break
            
        case .scanTapped:
            // Open scanner
            break
            
        case .seeAllTapped:
            // Navigate to see all
            break
            
        case .tabChanged(let tab):
            state.selectedTab = tab
            
        case .chatSessionTapped:
            // Handled by view directly
            break
            
        case .deleteChat(let session):
            chatHistory.deleteSession(session)

        case .renameChat(let session, let newTitle):
            chatHistory.renameSession(session, newTitle: newTitle)

        case .plusTapped:
            // Start new chat
            break
            
        case .inputChanged(let text):
            state.inputText = text
            
        case .sendTapped:
            // Send message
            break
        }
    }
    
    private func refreshData() {
        // Setup bindings on first refresh (lazy initialization)
        setupBindingsIfNeeded()

        // Force refresh recent chats (triggers Combine pipeline)
        let sessions = chatHistory.chatSessions.filter { session in
            session.messages.contains { $0.sender == .user }
        }

        // Update view models
        var newViewModels: [UUID: ChatSessionViewModel] = [:]
        for session in sessions {
            if let existing = sessionViewModels[session.id] {
                existing.update(from: session)
                newViewModels[session.id] = existing
            } else {
                newViewModels[session.id] = ChatSessionViewModel(from: session)
            }
        }

        sessionViewModels = newViewModels
        recentChats = sessions
    }
}
