import SwiftUI

struct MoodIntensityView: View {

    let value: Double
    let level: MoodIntensityLevel

    // Static shadow color to avoid recreation on each render
    private static let shadowColor = Color.black.opacity(0.1)
    
    // Scale range (0-16)
    private let minValue: Double = 0
    private let maxValue: Double = 16
    
    // Convert 0-1 value to 0-16 scale
    private var displayValue: Double {
        minValue + (value * (maxValue - minValue))
    }
    
    private var progress: CGFloat {
        CGFloat(value)
    }
    
    private var levelColor: Color {
        switch level {
        case .veryLow: return .blue
        case .low: return .green
        case .balanced: return .yellow
        case .high: return .orange
        case .veryHigh: return .red
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            
            // Title
            Text("Mood Intensity")
                .font(.system(size: 16, weight: .medium))
                .foregroundColor(.black)
            
            // Value + Level
            HStack {
                Text(String(format: "%.1f", displayValue))
                    .font(.system(size: 22, weight: .bold))
                    .foregroundColor(Color("TextPrimary"))
                
                Spacer()
                
                Text(level.displayName)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(levelColor)
            }
            
            // Gradient bar + indicator
            ZStack(alignment: .leading) {
                
                RoundedRectangle(cornerRadius: 100)
                    .fill(
                        LinearGradient(
                            colors: [
                                Color(red: 0.00, green: 0.48, blue: 1.00),
                                Color(red: 0.07, green: 0.88, blue: 1.00),
                                Color(red: 0.13, green: 0.93, blue: 0.04),
                                Color(red: 0.92, green: 0.99, blue: 0.00),
                                Color(red: 1.00, green: 0.47, blue: 0.00),
                                Color(red: 1.00, green: 0.00, blue: 0.00)
                            ],
                            startPoint: .leading,
                            endPoint: .trailing
                        )
                    )
                    .frame(height: 24)
                
                GeometryReader { geo in
                    RoundedRectangle(cornerRadius: 3)
                        .fill(Color.gray)
                        .frame(width: 4, height: 32)
                        .offset(x: geo.size.width * progress - 2)
                }
            }
            .frame(height: 32)
            
            // Scale (0 to 16, step 2)
            HStack {
                ForEach([0, 2, 4, 6, 8, 10, 12, 14, 16], id: \.self) { mark in
                    Text("\(mark)")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                    
                    if mark != 16 {
                        Spacer()
                    }
                }
            }
            
            // Legend
            HStack {
                legendDot(color: .blue, text: MoodIntensityLevel.veryLow.displayName)
                Spacer()
                legendDot(color: .green, text: MoodIntensityLevel.low.displayName)
                Spacer()
                legendDot(color: .yellow, text: MoodIntensityLevel.balanced.displayName)
                Spacer()
                legendDot(color: .orange, text: MoodIntensityLevel.high.displayName)
                Spacer()
                legendDot(color: .red, text: MoodIntensityLevel.veryHigh.displayName)
            }
            .frame(maxWidth: .infinity)
        }
        .padding(16)
        .frame(maxWidth: .infinity)
        .background(Color.white)
        .cornerRadius(20)
        .compositingGroup()
        .shadow(color: Self.shadowColor, radius: 10, x: 0, y: 2)
    }

    private func legendDot(color: Color, text: LocalizedStringKey) -> some View {
        HStack(spacing: 4) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)

            Text(text)
                .font(.system(size: 12))
                .foregroundColor(.black)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        MoodIntensityView(value: 0.18, level: .low)
        MoodIntensityView(value: 0.5, level: .balanced)
        MoodIntensityView(value: 0.85, level: .veryHigh)
    }
    .padding()
    .background(Color(.systemGray6))
}
