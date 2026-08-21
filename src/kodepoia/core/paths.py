from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    data: Path
    config: Path
    cache: Path

    @classmethod
    def default(cls) -> "AppPaths":
        home = Path.home()
        if os.name == "nt":
            local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            roaming = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
            return cls(local / "Kodepoia" / "Data", roaming / "Kodepoia", local / "Kodepoia" / "Cache")
        xdg_data = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
        xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        xdg_cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
        return cls(xdg_data / "kodepoia", xdg_config / "kodepoia", xdg_cache / "kodepoia")

    def ensure(self) -> "AppPaths":
        for path in (self.data, self.config, self.cache):
            path.mkdir(parents=True, exist_ok=True)
        return self
