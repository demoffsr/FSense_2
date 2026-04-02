import Foundation

/// Centralized date formatting service to avoid creating expensive formatters in view bodies
/// Performance: Formatters are created once and reused; results are cached
@Observable
final class DateFormattingService: @unchecked Sendable {
    static let shared = DateFormattingService()

    // MARK: - Formatters (created once, reused)

    private let relativeFormatter: RelativeDateTimeFormatter = {
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .abbreviated
        return f
    }()

    // MARK: - Cache

    /// Cache for relative time strings (key: date rounded to minute)
    private var relativeTimeCache: [Date: String] = [:]
    private let cacheSizeLimit = 100

    /// Reference date for cache invalidation (update every minute)
    private var lastCacheUpdate = Date()

    private init() {}

    // MARK: - Public API

    /// Returns relative time string (e.g. "5 min. ago", "2 hrs. ago")
    /// Performance: Uses cached results, only recomputes if date changes or cache expired
    func timeAgo(for date: Date) -> String {
        let now = Date()

        // Invalidate cache if it's been > 1 minute since last update
        if now.timeIntervalSince(lastCacheUpdate) > 60 {
            clearCache()
            lastCacheUpdate = now
        }

        // Round date to minute for better cache hits
        let roundedDate = roundToMinute(date)

        // Check cache first
        if let cached = relativeTimeCache[roundedDate] {
            return cached
        }

        // Compute and cache
        let result = relativeFormatter.localizedString(for: date, relativeTo: now)

        // Simple cache size management
        if relativeTimeCache.count >= cacheSizeLimit {
            // Remove oldest entries (simple approach: clear half)
            let sortedKeys = relativeTimeCache.keys.sorted()
            let keysToRemove = sortedKeys.prefix(cacheSizeLimit / 2)
            for key in keysToRemove {
                relativeTimeCache.removeValue(forKey: key)
            }
        }

        relativeTimeCache[roundedDate] = result
        return result
    }

    // MARK: - Cache Management

    /// Clear all cached values (called automatically when cache expires)
    func clearCache() {
        relativeTimeCache.removeAll()
    }

    // MARK: - Helpers

    private func roundToMinute(_ date: Date) -> Date {
        Calendar.current.date(
            bySetting: .second,
            value: 0,
            of: date
        ) ?? date
    }
}
