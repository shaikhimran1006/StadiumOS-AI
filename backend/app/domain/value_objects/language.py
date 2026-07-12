from __future__ import annotations

from enum import Enum


class Language(str, Enum):
    """Supported FIFA languages for multilingual AI interactions."""

    ARABIC = "ar"
    BENGALI = "bn"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    DUTCH = "nl"
    ENGLISH = "en"
    FRENCH = "fr"
    GERMAN = "de"
    HINDI = "hi"
    INDONESIAN = "id"
    ITALIAN = "it"
    JAPANESE = "ja"
    KOREAN = "ko"
    MALAY = "ms"
    PORTUGUESE = "pt"
    PORTUGUESE_BRAZIL = "pt-BR"
    RUSSIAN = "ru"
    SPANISH = "es"
    SPANISH_LATAM = "es-419"
    SWAHILI = "sw"
    THAI = "th"
    TURKISH = "tr"
    UKRAINIAN = "uk"
    URDU = "ur"
    VIETNAMESE = "vi"

    @classmethod
    def default(cls) -> Language:
        return cls.ENGLISH

    @classmethod
    def from_bcp47(cls, tag: str) -> Language:
        tag_normalized = tag.strip()
        for member in cls:
            if member.value == tag_normalized:
                return member
        raise ValueError(f"Unsupported language tag: {tag_normalized}")

    def display_name(self) -> str:
        names = {
            "ar": "Arabic",
            "bn": "Bengali",
            "zh-CN": "Chinese (Simplified)",
            "zh-TW": "Chinese (Traditional)",
            "nl": "Dutch",
            "en": "English",
            "fr": "French",
            "de": "German",
            "hi": "Hindi",
            "id": "Indonesian",
            "it": "Italian",
            "ja": "Japanese",
            "ko": "Korean",
            "ms": "Malay",
            "pt": "Portuguese",
            "pt-BR": "Portuguese (Brazil)",
            "ru": "Russian",
            "es": "Spanish",
            "es-419": "Spanish (Latin America)",
            "sw": "Swahili",
            "th": "Thai",
            "tr": "Turkish",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "vi": "Vietnamese",
        }
        return names.get(self.value, self.value)

    def is_rtl(self) -> bool:
        return self in {Language.ARABIC, Language.URDU}
