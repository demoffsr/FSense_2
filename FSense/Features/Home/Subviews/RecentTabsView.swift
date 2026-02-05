import SwiftUI

struct RecentTabsView: View {
    @Binding var selectedTab: RecentTab
    
    var body: some View {
        Picker("Recent", selection: $selectedTab) {
            ForEach(RecentTab.allCases, id: \.self) { tab in
                Text(tab.displayName)
                    .tag(tab)
            }
        }
        .pickerStyle(.segmented)
    }
}

#Preview {
    RecentTabsView(selectedTab: .constant(.chats))
        .padding()
}
