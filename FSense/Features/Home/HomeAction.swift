import Foundation

/// Actions for Home screen
/// Responsibility: Defines all user interactions on Home screen
enum HomeAction {
    case onAppear
    case avatarTapped
    case searchTextChanged(String)
    case settingsTapped
    case bannerTapped
    case scanTapped
    case seeAllTapped
    case tabChanged(RecentTab)
    case chatSessionTapped(ChatSession)
    case deleteChat(ChatSession)
    case plusTapped
    case inputChanged(String)
    case sendTapped
}
