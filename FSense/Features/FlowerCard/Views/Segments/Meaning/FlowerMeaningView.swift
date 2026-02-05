import SwiftUI

struct FlowerMeaningView: View {

    let data: MeaningSegmentData
    let alternatives: [AlternativeFlower]
    var onAlternativeTap: ((AlternativeFlower) -> Void)?

    var body: some View {
        VStack(spacing: 16) {
            WhyThisFlowerCard(text: data.whyThisFlowerText)
            SymbolismCard(text: data.symbolismText)
            MeaningsChipsView(meanings: data.meanings)
            MoodIntensityView(value: data.moodIntensityValue, level: data.moodIntensityLevel)

            // Alternative flowers section
            AlternativesSection(alternatives: alternatives) { flower in
                onAlternativeTap?(flower)
            }
        }
    }
}

#Preview {
    ScrollView {
        FlowerMeaningView(
            data: MeaningSegmentData(
                whyThisFlowerText: "This flower is traditionally given when one wants to express apology.",
                symbolismText: "In Western cultures, associated with romantic love. In Victorian England, used to convey messages that couldn't be spoken aloud.",
                meanings: ["Love", "Passion", "Romance", "Desire", "Beauty"],
                moodIntensityValue: 0.85,
                moodIntensityLevel: .veryHigh
            ),
            alternatives: AlternativeFlower.mocks
        ) { flower in
            print("Tapped: \(flower.name)")
        }
        .padding()
    }
    .background(Color(.systemGray6))
}
