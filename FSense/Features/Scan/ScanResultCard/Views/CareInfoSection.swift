import SwiftUI

/// Care information section with difficulty, light, water
struct CareInfoSection: View {
    let info: CareInfo

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Care Guide")
                .font(.headline)

            // Care metrics
            HStack(spacing: 16) {
                careMetric(
                    icon: info.difficulty.icon,
                    label: "Care",
                    value: info.difficulty.displayName,
                    color: difficultyColor
                )

                careMetric(
                    icon: info.light.icon,
                    label: "Light",
                    value: info.light.displayName,
                    color: .orange
                )

                careMetric(
                    icon: info.water.icon,
                    label: "Water",
                    value: info.water.displayName,
                    color: .blue
                )
            }

            // Additional info
            if let temp = info.temperatureRange, !temp.isEmpty {
                additionalInfo(icon: "thermometer", text: "Temperature: \(temp)")
            }

            if let humidity = info.humidity, !humidity.isEmpty {
                additionalInfo(icon: "humidity", text: "Humidity: \(humidity)")
            }

            // Care tips
            if !info.tips.isEmpty {
                careTipsSection
            }
        }
    }

    // MARK: - Care Metric

    private func careMetric(icon: String, label: String, value: String, color: Color) -> some View {
        VStack(spacing: 8) {
            ZStack {
                Circle()
                    .fill(color.opacity(0.15))
                    .frame(width: 50, height: 50)

                Image(systemName: icon)
                    .font(.system(size: 20))
                    .foregroundColor(color)
            }

            VStack(spacing: 2) {
                Text(label)
                    .font(.caption)
                    .foregroundColor(.secondary)

                Text(value)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundColor(.primary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Additional Info

    private func additionalInfo(icon: String, text: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.caption)
                .foregroundColor(.secondary)

            Text(text)
                .font(.subheadline)
                .foregroundColor(.primary)
        }
    }

    // MARK: - Care Tips

    private var careTipsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Tips")
                .font(.subheadline)
                .fontWeight(.medium)
                .foregroundColor(.secondary)

            ForEach(info.tips.prefix(5), id: \.self) { tip in
                HStack(alignment: .top, spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.caption)
                        .foregroundColor(.green)

                    Text(tip)
                        .font(.subheadline)
                        .foregroundColor(.primary)
                }
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }

    // MARK: - Helpers

    private var difficultyColor: Color {
        switch info.difficulty {
        case .easy: return .green
        case .moderate: return .orange
        case .hard: return .red
        }
    }
}

// MARK: - Preview

#Preview {
    CareInfoSection(info: CareInfo(
        difficulty: .moderate,
        light: .fullSun,
        water: .moderate,
        temperatureRange: "15-25°C",
        humidity: "Medium",
        tips: [
            "Prune in early spring",
            "Water at the base to prevent disease",
            "Fertilize monthly during growing season"
        ]
    ))
    .padding()
}
