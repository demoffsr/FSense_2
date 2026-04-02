import SwiftUI

/// Botanical information section
struct BotanicalInfoSection: View {
    let info: BotanicalInfo

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Botanical Info")
                .font(.headline)

            VStack(spacing: 12) {
                infoRow(icon: "leaf", label: "Family", value: info.family)

                if !info.nativeRegions.isEmpty {
                    infoRow(icon: "globe", label: "Origin", value: info.nativeRegionsText)
                }

                if !info.bloomSeasons.isEmpty {
                    infoRow(icon: "calendar", label: "Blooms", value: info.bloomSeasonsText)
                }

                if let lifespan = info.lifespan, !lifespan.isEmpty {
                    infoRow(icon: "clock", label: "Lifespan", value: lifespan.capitalized)
                }
            }
            .padding(16)
            .background(Color(.secondarySystemBackground))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    private func infoRow(icon: String, label: String, value: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.body)
                .foregroundColor(.accentColor)
                .frame(width: 24)

            Text(label)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(width: 60, alignment: .leading)

            Text(value)
                .font(.subheadline)
                .foregroundColor(.primary)

            Spacer()
        }
    }
}

// MARK: - Preview

#Preview {
    BotanicalInfoSection(info: BotanicalInfo(
        family: "Rosaceae",
        nativeRegions: ["Europe", "Asia", "North America"],
        bloomSeasons: ["Spring", "Summer"],
        lifespan: "perennial"
    ))
    .padding()
}
