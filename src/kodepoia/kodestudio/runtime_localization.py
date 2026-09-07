from __future__ import annotations

from typing import Any

from kodepoia.kodestudio.fr_catalogs import KODESTUDIO_FR, translated
from kodepoia.kodestudio.localization import KodeStudioTranslator as SourceKodeStudioTranslator


class KodeStudioTranslator:
    """Runtime translator adding the complete shipped French catalog."""

    def __init__(self, locale: str = "en") -> None:
        normalized = locale.strip().lower()
        self.locale = "fr" if normalized.startswith("fr") else normalized or "en"
        self._source = SourceKodeStudioTranslator("en" if self.locale == "fr" else self.locale)

    def text(self, message_id: str, **values: Any) -> str:
        if self.locale == "fr":
            try:
                return translated(KODESTUDIO_FR, message_id, **values)
            except KeyError as exc:
                raise KeyError(f"missing French KodeStudio translation: {message_id}") from exc
        return self._source.text(message_id, **values)


__all__ = ["KodeStudioTranslator"]
