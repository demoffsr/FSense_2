#!/usr/bin/env python3
"""
Add a new language to FSense iOS app.

Usage:
    python scripts/add_language.py <language_code> <native_name> <translations_json>

Example:
    python scripts/add_language.py ko "한국어" scripts/translations/ko.json

The translations JSON file should have this structure:
{
    "strings": {
        "Settings": "설정",
        "Language": "언어",
        ...
    },
    "info_plist": {
        "NSCameraUsageDescription": "FSense에서 꽃을 스캔하고 식별하려면 카메라 접근이 필요합니다",
        "NSPhotoLibraryUsageDescription": "FSense에서 꽃 이미지를 첨부하려면 사진 접근이 필요합니다"
    }
}
"""

import json
import re
import sys
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
LANGUAGE_MANAGER = PROJECT_ROOT / "FSense/Shared/Services/LanguageManager.swift"
PROJECT_PBXPROJ = PROJECT_ROOT / "FSense_2.xcodeproj/project.pbxproj"
LOCALIZABLE = PROJECT_ROOT / "FSense/Localizable.xcstrings"
INFO_PLIST = PROJECT_ROOT / "InfoPlist.xcstrings"
FSENSE_APP = PROJECT_ROOT / "FSense/App/FSenseApp.swift"

# Globe icons by region
GLOBE_ICONS = {
    "ko": "globe.asia.australia",
    "pt": "globe.americas",
    "pt-BR": "globe.americas",
    "it": "globe.europe.africa",
    "nl": "globe.europe.africa",
    "pl": "globe.europe.africa",
    "tr": "globe.europe.africa",
    "ar": "globe.europe.africa",
    "hi": "globe.asia.australia",
    "th": "globe.asia.australia",
    "vi": "globe.asia.australia",
    "id": "globe.asia.australia",
    "default": "globe"
}


def get_globe_icon(lang_code: str) -> str:
    """Get appropriate globe icon for language."""
    return GLOBE_ICONS.get(lang_code, GLOBE_ICONS["default"])


def get_case_name(lang_code: str) -> str:
    """Convert language code to Swift case name."""
    # Handle special cases like zh-Hans, pt-BR
    if "-" in lang_code:
        parts = lang_code.split("-")
        return parts[0] + parts[1].capitalize()
    return lang_code


def update_language_manager(lang_code: str, native_name: str) -> bool:
    """Add new language case to LanguageManager.swift."""
    content = LANGUAGE_MANAGER.read_text()
    case_name = get_case_name(lang_code)
    icon = get_globe_icon(lang_code)

    # Check if already exists
    if f'case .{case_name}' in content:
        print(f"  ⚠️  Language {case_name} already exists in LanguageManager.swift")
        return False

    # 1. Add case to enum (after japanese)
    content = re.sub(
        r'(case japanese = "ja")',
        f'\\1\n    case {case_name} = "{lang_code}"',
        content
    )

    # 2. Add to displayName switch
    content = re.sub(
        r'(case \.japanese: return "日本語")',
        f'\\1\n        case .{case_name}: return "{native_name}"',
        content
    )

    # 3. Add to nativeName switch
    content = re.sub(
        r'(case \.japanese: return "日本語")\n(\s+\}\n\s+\}\n\s+var icon)',
        f'\\1\n        case .{case_name}: return "{native_name}"\\2',
        content
    )

    # 4. Add to icon switch
    content = re.sub(
        r'(case \.japanese: return "globe\.asia\.australia")',
        f'\\1\n        case .{case_name}: return "{icon}"',
        content
    )

    # 5. Add to applyLanguage switch
    content = re.sub(
        r'(case \.english, \.russian, \.spanish, \.german, \.french, \.chinese, \.japanese:)',
        f'case .english, .russian, .spanish, .german, .french, .chinese, .japanese, .{case_name}:',
        content
    )

    LANGUAGE_MANAGER.write_text(content)
    print(f"  ✓ Updated LanguageManager.swift")
    return True


def update_project_pbxproj(lang_code: str) -> bool:
    """Add language to knownRegions in project.pbxproj."""
    content = PROJECT_PBXPROJ.read_text()

    # Check if already exists
    if f'"{lang_code}"' in content or f'{lang_code},' in content:
        print(f"  ⚠️  Language {lang_code} already in project.pbxproj")
        return False

    # Add before closing parenthesis of knownRegions
    # Handle both quoted and unquoted formats
    content = re.sub(
        r'(knownRegions = \([^)]+)(ja,?\s*)\)',
        f'\\1\\2"{lang_code}",\n\t\t\t)',
        content
    )

    PROJECT_PBXPROJ.write_text(content)
    print(f"  ✓ Updated project.pbxproj")
    return True


def update_localizable(lang_code: str, translations: dict) -> bool:
    """Add translations to Localizable.xcstrings."""
    with open(LOCALIZABLE, 'r') as f:
        data = json.load(f)

    added = 0
    for key, value in translations.items():
        if key in data["strings"]:
            if "localizations" not in data["strings"][key]:
                data["strings"][key]["localizations"] = {}
            if lang_code not in data["strings"][key]["localizations"]:
                data["strings"][key]["localizations"][lang_code] = {
                    "stringUnit": {"state": "translated", "value": value}
                }
                added += 1

    with open(LOCALIZABLE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Added {added} translations to Localizable.xcstrings")
    return True


def update_info_plist(lang_code: str, translations: dict) -> bool:
    """Add translations to InfoPlist.xcstrings."""
    with open(INFO_PLIST, 'r') as f:
        data = json.load(f)

    for key, value in translations.items():
        if key in data["strings"]:
            if "localizations" not in data["strings"][key]:
                data["strings"][key]["localizations"] = {}
            data["strings"][key]["localizations"][lang_code] = {
                "stringUnit": {"state": "translated", "value": value}
            }

    with open(INFO_PLIST, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Updated InfoPlist.xcstrings")
    return True


def update_fsense_app(lang_code: str) -> bool:
    """Add locale case to FSenseApp.swift."""
    content = FSENSE_APP.read_text()
    case_name = get_case_name(lang_code)

    # Check if already exists
    if f'case .{case_name}:' in content:
        print(f"  ⚠️  Language {case_name} already in FSenseApp.swift")
        return False

    # Add case before closing brace of currentLocale switch
    content = re.sub(
        r'(case \.japanese:\s+return Locale\(identifier: "ja"\))\n(\s+\})',
        f'\\1\n        case .{case_name}:\n            return Locale(identifier: "{lang_code}")\\2',
        content
    )

    FSENSE_APP.write_text(content)
    print(f"  ✓ Updated FSenseApp.swift")
    return True


def export_current_strings() -> dict:
    """Export all current English strings for translation."""
    with open(LOCALIZABLE, 'r') as f:
        data = json.load(f)

    strings = {}
    for key in data["strings"]:
        strings[key] = key  # Use key as default (English)

    return {
        "strings": strings,
        "info_plist": {
            "NSCameraUsageDescription": "FSense needs camera access to scan and identify flowers",
            "NSPhotoLibraryUsageDescription": "FSense needs access to your photos to attach flower images"
        }
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nTo export current strings for translation:")
        print("  python scripts/add_language.py --export > translations_template.json")
        sys.exit(1)

    if sys.argv[1] == "--export":
        template = export_current_strings()
        print(json.dumps(template, indent=2, ensure_ascii=False))
        sys.exit(0)

    if len(sys.argv) < 4:
        print("Error: Missing arguments")
        print(__doc__)
        sys.exit(1)

    lang_code = sys.argv[1]
    native_name = sys.argv[2]
    translations_file = sys.argv[3]

    print(f"\n🌍 Adding language: {native_name} ({lang_code})\n")

    # Load translations
    with open(translations_file, 'r') as f:
        translations = json.load(f)

    # Update all files
    update_language_manager(lang_code, native_name)
    update_project_pbxproj(lang_code)
    update_localizable(lang_code, translations.get("strings", {}))
    update_info_plist(lang_code, translations.get("info_plist", {}))
    update_fsense_app(lang_code)

    print(f"\n✅ Done! Now build the project to verify.")
    print(f"   If there are Swift compiler errors, check switch statements for exhaustiveness.")


if __name__ == "__main__":
    main()
