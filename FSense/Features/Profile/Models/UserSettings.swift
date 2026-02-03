import Foundation

/// User settings model with UserDefaults persistence
/// Manages city/region selection for flower search
struct UserSettings {

    // MARK: - UserDefaults Keys

    private enum Keys {
        static let selectedCity = "selectedCity"
        static let selectedRegion = "selectedRegion"
    }

    // MARK: - Defaults

    static let defaultCity = "Москва"
    static let defaultRegion = "RU"

    // MARK: - Accessors

    static var selectedCity: String {
        get { UserDefaults.standard.string(forKey: Keys.selectedCity) ?? defaultCity }
        set { UserDefaults.standard.set(newValue, forKey: Keys.selectedCity) }
    }

    static var selectedRegion: String {
        get { UserDefaults.standard.string(forKey: Keys.selectedRegion) ?? defaultRegion }
        set { UserDefaults.standard.set(newValue, forKey: Keys.selectedRegion) }
    }

    // MARK: - Supported Regions

    static let supportedRegions: [Region] = [
        Region(code: "RU", name: "Russia"),
        Region(code: "US", name: "United States"),
        Region(code: "CA", name: "Canada")
    ]

    // MARK: - Cities by Region

    static func cities(for regionCode: String) -> [String] {
        switch regionCode {
        case "RU":
            return russianCities
        case "US":
            return usCities
        case "CA":
            return canadianCities
        default:
            return []
        }
    }

    // MARK: - Russian Cities (from Yandex provider)

    private static let russianCities = [
        "Москва",
        "Санкт-Петербург",
        "Новосибирск",
        "Екатеринбург",
        "Нижний Новгород",
        "Казань",
        "Челябинск",
        "Омск",
        "Самара",
        "Ростов-на-Дону",
        "Уфа",
        "Красноярск",
        "Пермь",
        "Воронеж",
        "Волгоград",
        "Краснодар",
        "Саратов",
        "Тюмень",
        "Тольятти",
        "Ижевск",
        "Барнаул",
        "Ульяновск",
        "Иркутск",
        "Хабаровск",
        "Ярославль",
        "Владивосток",
        "Махачкала",
        "Томск",
        "Оренбург",
        "Кемерово",
        "Новокузнецк",
        "Рязань",
        "Астрахань",
        "Набережные Челны",
        "Пенза",
        "Липецк",
        "Тула",
        "Киров",
        "Чебоксары",
        "Калининград",
        "Брянск",
        "Курск",
        "Иваново",
        "Магнитогорск",
        "Тверь",
        "Ставрополь",
        "Белгород",
        "Сочи"
    ]

    // MARK: - US Cities

    private static let usCities = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
        "Austin",
        "Jacksonville",
        "Fort Worth",
        "Columbus",
        "Charlotte",
        "Indianapolis",
        "San Francisco",
        "Seattle",
        "Denver",
        "Washington",
        "Boston",
        "Nashville",
        "Las Vegas",
        "Portland",
        "Miami"
    ]

    // MARK: - Canadian Cities (from Florist One provider)

    private static let canadianCities = [
        "Toronto",
        "Vancouver",
        "Montreal",
        "Calgary",
        "Ottawa",
        "Edmonton",
        "Winnipeg",
        "Quebec City",
        "Hamilton",
        "Kitchener",
        "London",
        "Victoria",
        "Halifax",
        "Saskatoon",
        "Regina"
    ]
}

// MARK: - Region Model

struct Region: Identifiable, Hashable {
    let code: String
    let name: String

    var id: String { code }
}
