from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

DEFAULT_SETTINGS_PATH = Path.home() / ".kodepoia" / "settings.json"


class ApplicationPreferences:
    """Small merge-safe JSON preference store for KodeStudio application settings."""

    def __init__(self, path: Path | str = DEFAULT_SETTINGS_PATH) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}
        return dict(payload) if isinstance(payload, dict) else {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.load().get(key, default)

    def locale(self) -> str | None:
        value = self.get("locale")
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def update(self, values: Mapping[str, Any]) -> dict[str, Any]:
        payload = self.load()
        payload.update(dict(values))
        self._write_atomic(payload)
        return payload

    def set_locale(self, locale: str) -> dict[str, Any]:
        return self.update({"locale": str(locale)})

    def _write_atomic(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                dir=self.path.parent,
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(dict(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except OSError:
                    pass


__all__ = ["ApplicationPreferences", "DEFAULT_SETTINGS_PATH"]
