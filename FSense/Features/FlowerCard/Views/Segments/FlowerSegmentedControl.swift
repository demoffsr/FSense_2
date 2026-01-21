import SwiftUI

/// Segmented control for switching between Meaning / Gifting / Context
/// Native iOS segmented control with glass effect
struct FlowerSegmentedControl: View {
    
    @Binding var selectedSegment: FlowerCardSegment
    
    var body: some View {
        Picker("Segment", selection: $selectedSegment) {
            ForEach(FlowerCardSegment.allCases) { segment in
                Text(segment.rawValue)
                    .tag(segment)
            }
        }
        .pickerStyle(.segmented)
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 20) {
        FlowerSegmentedControl(selectedSegment: .constant(.meaning))
        FlowerSegmentedControl(selectedSegment: .constant(.gifting))
        FlowerSegmentedControl(selectedSegment: .constant(.context))
    }
    .padding()
}
