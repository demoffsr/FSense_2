import SwiftUI
import Combine

/// ViewModel for Home screen
/// Responsibility: Handles state and actions for Home feature
@MainActor
final class HomeViewModel: ObservableObject {
    
    @Published var state = HomeState()
    
    /// Access to chat history
    let chatHistory = ChatHistoryManager.shared
    
    /// Recent chat sessions from history
    @Published var recentChats: [ChatSession] = []
    
    /// Recent scan items (mock for now)
    @Published var recentScans: [RecentScanItem] = []
    
    private var cancellables = Set<AnyCancellable>()
    
    init() {
        // Observe chat history changes
        chatHistory.$sessions
            .receive(on: DispatchQueue.main)
            .sink { [weak self] sessions in
                self?.recentChats = sessions.filter { session in
                    // Only show sessions that have user messages
                    session.messages.contains { $0.sender == .user }
                }
            }
            .store(in: &cancellables)
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
        // Force refresh recent chats
        recentChats = chatHistory.chatSessions
    }
}
