import SwiftUI

// MARK: - Chat Design System
// Single source of truth for chat UI styling, matching Flower Card design language

enum ChatDesign {
    
    // MARK: - Colors
    
    enum Colors {
        /// Primary purple accent
        static let accentPurple = Color("AccentPurple")

        /// Secondary pink accent
        static let accentPink = Color("AccentPink")

        /// Success green
        static let success = Color("Success")

        /// Card background
        static let cardBackground = Color("CardBackground")

        /// Secondary background (for nested elements)
        static let secondaryBackground = Color("SecondaryBackground")

        /// Primary text
        static let textPrimary = Color("TextPrimary")

        /// Secondary text
        static let textSecondary = Color("TextSecondary")

        /// Muted text
        static let textMuted = Color("TextMuted")
        
        /// Accent gradient (static to avoid recreation)
        static let accentGradient = LinearGradient(
            colors: [accentPurple, accentPink],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )

        /// Vertical accent gradient (for bars) - static to avoid recreation
        static let verticalAccentGradient = LinearGradient(
            colors: [accentPurple, accentPink],
            startPoint: .top,
            endPoint: .bottom
        )
        
        /// Soft purple tint for backgrounds
        static let softPurpleTint = accentPurple.opacity(0.06)
        
        /// Soft pink tint for user messages
        static let softPinkTint = accentPink.opacity(0.08)
    }
    
    // MARK: - Typography
    
    enum Typography {
        /// Card title - semibold
        static func title(_ size: CGFloat = 17) -> Font {
            .system(size: size, weight: .semibold)
        }
        
        /// Section header - medium
        static func sectionHeader(_ size: CGFloat = 16) -> Font {
            .system(size: size, weight: .medium)
        }
        
        /// Body text - regular
        static func body(_ size: CGFloat = 15) -> Font {
            .system(size: size, weight: .regular)
        }
        
        /// Caption text - regular, smaller
        static func caption(_ size: CGFloat = 13) -> Font {
            .system(size: size, weight: .regular)
        }
        
        /// Badge text - semibold
        static func badge(_ size: CGFloat = 13) -> Font {
            .system(size: size, weight: .semibold)
        }
    }
    
    // MARK: - Dimensions
    
    enum Dimensions {
        /// Large card corner radius
        static let cardRadius: CGFloat = 24
        
        /// Medium corner radius (for smaller cards)
        static let mediumRadius: CGFloat = 20
        
        /// Badge/chip corner radius
        static let badgeRadius: CGFloat = 14
        
        /// Small corner radius
        static let smallRadius: CGFloat = 12
        
        /// Standard card padding
        static let cardPadding: CGFloat = 16
        
        /// Accent bar width
        static let accentBarWidth: CGFloat = 5
    }
    
    // MARK: - Shadows
    
    enum Shadows {
        /// Standard card shadow
        static func card() -> some View {
            Color.black.opacity(0.1)
        }
        
        static let cardRadius: CGFloat = 10.9
        static let cardX: CGFloat = 0
        static let cardY: CGFloat = 2
        
        /// Elevated shadow
        static let elevatedRadius: CGFloat = 16
        static let elevatedY: CGFloat = 6
    }
}

// MARK: - Card Style Modifier

struct FlowerCardStyle: ViewModifier {
    var hasAccentBar: Bool = false
    var cornerRadius: CGFloat = ChatDesign.Dimensions.cardRadius
    
    func body(content: Content) -> some View {
        content
            .background(ChatDesign.Colors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .stroke(Color.white, lineWidth: 1)
            )
            .shadow(
                color: .black.opacity(0.08),
                radius: ChatDesign.Shadows.cardRadius,
                x: ChatDesign.Shadows.cardX,
                y: ChatDesign.Shadows.cardY
            )
    }
}

extension View {
    func flowerCardStyle(hasAccentBar: Bool = false, cornerRadius: CGFloat = ChatDesign.Dimensions.cardRadius) -> some View {
        modifier(FlowerCardStyle(hasAccentBar: hasAccentBar, cornerRadius: cornerRadius))
    }
}

// MARK: - Accent Bar Card Modifier

struct AccentBarCardStyle: ViewModifier {
    var cornerRadius: CGFloat = ChatDesign.Dimensions.cardRadius
    
    func body(content: Content) -> some View {
        content
            .padding(.leading, ChatDesign.Dimensions.accentBarWidth + 2)
            .background(ChatDesign.Colors.cardBackground)
            .overlay(alignment: .leading) {
                ChatDesign.Colors.verticalAccentGradient
                    .frame(width: ChatDesign.Dimensions.accentBarWidth)
            }
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
            .shadow(
                color: .black.opacity(0.08),
                radius: ChatDesign.Shadows.cardRadius,
                x: ChatDesign.Shadows.cardX,
                y: ChatDesign.Shadows.cardY
            )
    }
}

extension View {
    func accentBarCardStyle(cornerRadius: CGFloat = ChatDesign.Dimensions.cardRadius) -> some View {
        modifier(AccentBarCardStyle(cornerRadius: cornerRadius))
    }
}

// MARK: - Badge Style

struct FlowerBadgeStyle: ViewModifier {
    let color: Color
    
    func body(content: Content) -> some View {
        content
            .font(ChatDesign.Typography.badge())
            .foregroundColor(color)
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(color.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: ChatDesign.Dimensions.badgeRadius, style: .continuous))
    }
}

extension View {
    func flowerBadgeStyle(color: Color) -> some View {
        modifier(FlowerBadgeStyle(color: color))
    }
}

// MARK: - Chip Style

struct FlowerChipStyle: ViewModifier {
    var isSelected: Bool = false
    
    func body(content: Content) -> some View {
        content
            .font(ChatDesign.Typography.body())
            .foregroundColor(ChatDesign.Colors.textPrimary)
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
            .background(ChatDesign.Colors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: ChatDesign.Dimensions.mediumRadius, style: .continuous))
            .shadow(
                color: .black.opacity(0.08),
                radius: ChatDesign.Shadows.cardRadius,
                x: ChatDesign.Shadows.cardX,
                y: ChatDesign.Shadows.cardY
            )
    }
}

extension View {
    func flowerChipStyle(isSelected: Bool = false) -> some View {
        modifier(FlowerChipStyle(isSelected: isSelected))
    }
}

// MARK: - Press Animation Modifier

struct CardPressStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.97 : 1.0)
            .opacity(configuration.isPressed ? 0.9 : 1.0)
            .animation(.easeOut(duration: 0.15), value: configuration.isPressed)
    }
}

// MARK: - Appear Animation Modifier

struct CardAppearAnimation: ViewModifier {
    @State private var appeared = false
    let delay: Double
    
    func body(content: Content) -> some View {
        content
            .opacity(appeared ? 1 : 0)
            .scaleEffect(appeared ? 1 : 0.96)
            .offset(y: appeared ? 0 : 8)
            .onAppear {
                withAnimation(.spring(response: 0.5, dampingFraction: 0.8).delay(delay)) {
                    appeared = true
                }
            }
    }
}

extension View {
    func cardAppearAnimation(delay: Double = 0) -> some View {
        modifier(CardAppearAnimation(delay: delay))
    }
}
