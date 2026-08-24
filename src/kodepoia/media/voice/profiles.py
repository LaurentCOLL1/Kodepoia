from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from ..contracts import bounded_text, stable_id
from ..serialization import canonical_sha256

_LOCALE_PART_RE = re.compile(r"^[A-Za-z0-9]{1,8}$")
_DISALLOWED_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_BIDI_CONTROL_CODEPOINTS = {
    0x061C,
    0x200E,
    0x200F,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}


def normalize_voice_text(value: str, *, field: str = "text", maximum: int = 8192) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = unicodedata.normalize("NFC", value)
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{field} has invalid length")
    if _DISALLOWED_TEXT_RE.search(normalized):
        raise ValueError(f"{field} contains disallowed control characters")
    if any(ord(ch) in _BIDI_CONTROL_CODEPOINTS for ch in normalized):
        raise ValueError(f"{field} contains bidi control characters")
    return normalized


def normalize_locale(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 63:
        raise ValueError("locale is invalid")
    raw = value.replace("_", "-")
    parts = raw.split("-")
    if not 2 <= len(parts) <= 8 or any(not part or _LOCALE_PART_RE.fullmatch(part) is None for part in parts):
        raise ValueError("locale is invalid")
    language = parts[0]
    if not language.isalpha() or not 2 <= len(language) <= 3:
        raise ValueError("locale language subtag is invalid")
    normalized: list[str] = [language.lower()]
    for index, part in enumerate(parts[1:], start=1):
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            normalized.append(part.upper())
        else:
            if index == 1 and len(part) == 1:
                raise ValueError("locale extension requires a preceding language/script/region structure")
            normalized.append(part.lower())
    return "-".join(normalized)


@dataclass(frozen=True, slots=True)
class ProsodyIntent:
    pace: float = 1.0
    pitch_semitones: float = 0.0
    energy: float = 1.0
    styles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value, low, high in (
            ("pace", self.pace, 0.5, 2.0),
            ("pitch_semitones", self.pitch_semitones, -12.0, 12.0),
            ("energy", self.energy, 0.0, 2.0),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or not low <= float(value) <= high:
                raise ValueError(f"{name} must be finite and between {low} and {high}")
        normalized_styles = tuple(sorted(set(self.styles)))
        if len(normalized_styles) > 8:
            raise ValueError("styles must contain at most 8 entries")
        for style in normalized_styles:
            stable_id(style, field="style")
        object.__setattr__(self, "styles", normalized_styles)

    def canonical(self) -> dict[str, Any]:
        return {
            "pace": float(self.pace),
            "pitch_semitones": float(self.pitch_semitones),
            "energy": float(self.energy),
            "styles": list(self.styles),
        }


@dataclass(frozen=True, slots=True)
class VoiceProfile:
    profile_id: str
    scope_id: str
    locale: str
    fallback_locales: tuple[str, ...] = ()
    prosody: ProsodyIntent = ProsodyIntent()
    display_name: str = "Voice"

    def __post_init__(self) -> None:
        stable_id(self.profile_id, field="profile_id")
        stable_id(self.scope_id, field="scope_id")
        object.__setattr__(self, "locale", normalize_locale(self.locale))
        normalized_fallbacks: list[str] = []
        for locale in self.fallback_locales:
            normalized = normalize_locale(locale)
            if normalized != self.locale and normalized not in normalized_fallbacks:
                normalized_fallbacks.append(normalized)
        if len(normalized_fallbacks) > 8:
            raise ValueError("fallback_locales must contain at most 8 entries")
        object.__setattr__(self, "fallback_locales", tuple(normalized_fallbacks))
        bounded_text(self.display_name, field="display_name", maximum=128)

    def locale_candidates(self) -> tuple[str, ...]:
        return (self.locale,) + self.fallback_locales

    def canonical(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "scope_id": self.scope_id,
            "locale": self.locale,
            "fallback_locales": list(self.fallback_locales),
            "prosody": self.prosody.canonical(),
            "display_name": unicodedata.normalize("NFC", self.display_name),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
