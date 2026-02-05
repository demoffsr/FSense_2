import SwiftUI

// MARK: - Gradient Theme Colors

/// Represents the colors for a 4-blob animated gradient background
struct GradientThemeColors {
    let blobA: Color  // Top-left
    let blobB: Color  // Top-right
    let blobC: Color  // Center-left
    let blobD: Color  // Center-right
}

// MARK: - Gradient Theme

/// Available gradient themes for the home screen background
enum GradientTheme: String, CaseIterable, Identifiable {
    case aurora = "aurora"
    case noir = "noir"
    case ocean = "ocean"
    case sunset = "sunset"
    case blossom = "blossom"

    var id: String { rawValue }

    // MARK: - Display Properties

    var displayName: String {
        switch self {
        case .aurora: return "Aurora"
        case .noir: return "Noir"
        case .ocean: return "Ocean"
        case .sunset: return "Sunset"
        case .blossom: return "Blossom"
        }
    }

    // MARK: - Theme Colors

    var colors: GradientThemeColors {
        switch self {
        case .aurora:
            return GradientThemeColors(
                blobA: Color("GradientBlobBlue"),
                blobB: Color("GradientBlobPurple"),
                blobC: Color("GradientBlobMagenta"),
                blobD: Color("GradientBlobOrange")
            )
        case .noir:
            return GradientThemeColors(
                blobA: Color("GradientNoirA"),
                blobB: Color("GradientNoirB"),
                blobC: Color("GradientNoirC"),
                blobD: Color("GradientNoirD")
            )
        case .ocean:
            return GradientThemeColors(
                blobA: Color("GradientOceanA"),
                blobB: Color("GradientOceanB"),
                blobC: Color("GradientOceanC"),
                blobD: Color("GradientOceanD")
            )
        case .sunset:
            return GradientThemeColors(
                blobA: Color("GradientSunsetA"),
                blobB: Color("GradientSunsetB"),
                blobC: Color("GradientSunsetC"),
                blobD: Color("GradientSunsetD")
            )
        case .blossom:
            return GradientThemeColors(
                blobA: Color("GradientBlossomA"),
                blobB: Color("GradientBlossomB"),
                blobC: Color("GradientBlossomC"),
                blobD: Color("GradientBlossomD")
            )
        }
    }

    /// Preview colors for theme selector cards
    var previewColors: [Color] {
        [colors.blobA, colors.blobB, colors.blobC, colors.blobD]
    }

    /// Accent color for UI elements (buttons, icons, tints)
    var accentColor: Color {
        switch self {
        case .aurora:
            return .purple
        case .noir:
            return Color("GradientNoirD")  // Light gray
        case .ocean:
            return Color("GradientOceanB") // Bright blue
        case .sunset:
            return Color("GradientSunsetB") // Orange
        case .blossom:
            return Color("GradientBlossomD") // Pink
        }
    }
}
