import SwiftUI

/// Confidence indicator banner
struct ConfidenceBanner: View {
    let confidence: Double

    private var percentage: Int {
        Int(confidence * 100)
    }

    private var color: Color {
        if confidence >= 0.8 {
            return .green
        } else if confidence >= 0.6 {
            return .orange
        } else {
            return .red
        }
    }

    private var label: String {
        if confidence >= 0.8 {
            return "High Confidence"
        } else if confidence >= 0.6 {
            return "Moderate Confidence"
        } else {
            return "Low Confidence"
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            // Progress ring
            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.2), lineWidth: 4)

                Circle()
                    .trim(from: 0, to: confidence)
                    .stroke(color, style: StrokeStyle(lineWidth: 4, lineCap: .round))
                    .rotationEffect(.degrees(-90))

                Text("\(percentage)%")
                    .font(.caption)
                    .fontWeight(.semibold)
            }
            .frame(width: 50, height: 50)

            VStack(alignment: .leading, spacing: 2) {
                Text(label)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundColor(color)

                Text("AI identification accuracy")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding(16)
        .background(color.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 16) {
        ConfidenceBanner(confidence: 0.92)
        ConfidenceBanner(confidence: 0.65)
        ConfidenceBanner(confidence: 0.45)
    }
    .padding()
}
