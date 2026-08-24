from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

from ..contracts import bounded_text, stable_id
from ..serialization import canonical_sha256
from .profiles import normalize_locale, normalize_voice_text

_ALLOWED_ALPHABETS = {"ipa", "xsampa", "engine"}


@dataclass(frozen=True, slots=True)
class PronunciationEntry:
    entry_id: str
    locale: str
    grapheme: str
    pronunciation: str
    alphabet: str = "ipa"

    def __post_init__(self) -> None:
        stable_id(self.entry_id, field="entry_id")
        object.__setattr__(self, "locale", normalize_locale(self.locale))
        object.__setattr__(self, "grapheme", normalize_voice_text(self.grapheme, field="grapheme", maximum=256))
        pronunciation = unicodedata.normalize("NFC", self.pronunciation)
        bounded_text(pronunciation, field="pronunciation", maximum=512)
        object.__setattr__(self, "pronunciation", pronunciation)
        if self.alphabet not in _ALLOWED_ALPHABETS:
            raise ValueError("alphabet must be ipa, xsampa or engine")

    @property
    def lookup_key(self) -> tuple[str, str]:
        return (self.locale, self.grapheme.casefold())

    def canonical(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "locale": self.locale,
            "grapheme": self.grapheme,
            "pronunciation": self.pronunciation,
            "alphabet": self.alphabet,
        }


@dataclass(frozen=True, slots=True)
class PronunciationLexicon:
    lexicon_id: str
    entries: tuple[PronunciationEntry, ...]

    def __post_init__(self) -> None:
        stable_id(self.lexicon_id, field="lexicon_id")
        if len(self.entries) > 4096:
            raise ValueError("lexicon contains too many entries")
        keys: set[tuple[str, str]] = set()
        ids: set[str] = set()
        for entry in self.entries:
            if entry.entry_id in ids:
                raise ValueError("duplicate pronunciation entry_id")
            if entry.lookup_key in keys:
                raise ValueError("duplicate pronunciation key for locale")
            ids.add(entry.entry_id)
            keys.add(entry.lookup_key)
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda item: (item.locale, item.grapheme.casefold(), item.entry_id))))

    def resolve(self, text: str, locale_candidates: tuple[str, ...]) -> PronunciationEntry | None:
        normalized_text = normalize_voice_text(text, field="text", maximum=256).casefold()
        candidates = tuple(normalize_locale(locale) for locale in locale_candidates)
        by_key = {entry.lookup_key: entry for entry in self.entries}
        for locale in candidates:
            hit = by_key.get((locale, normalized_text))
            if hit is not None:
                return hit
        return None

    def canonical(self) -> dict[str, Any]:
        return {"lexicon_id": self.lexicon_id, "entries": [entry.canonical() for entry in self.entries]}

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
