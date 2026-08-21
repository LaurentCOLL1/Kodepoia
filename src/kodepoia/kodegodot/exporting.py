from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class GodotExportPreset:
    index: int
    name: str
    platform: str | None
    runnable: bool


class GodotExportPresetInspector:
    """Read non-secret export preset metadata only from export_presets.cfg."""

    def __init__(self, root: Path) -> None:
        self.boundary = WorkspaceBoundary(root)

    def presets(self) -> tuple[GodotExportPreset, ...]:
        target = self.boundary.resolve("export_presets.cfg", must_exist=True)
        if not target.is_file():
            raise FileNotFoundError("export_presets.cfg is not a file")
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        parser.read_string(target.read_text(encoding="utf-8-sig"))
        result: list[GodotExportPreset] = []
        for section in parser.sections():
            if not section.startswith("preset.") or ".options" in section:
                continue
            suffix = section.removeprefix("preset.")
            if not suffix.isdigit():
                continue
            name = parser.get(section, "name", fallback="").strip().strip('"')
            if not name:
                continue
            platform = parser.get(section, "platform", fallback="").strip().strip('"') or None
            runnable_raw = parser.get(section, "runnable", fallback="false").strip().lower()
            result.append(GodotExportPreset(int(suffix), name, platform, runnable_raw == "true"))
        result.sort(key=lambda item: item.index)
        return tuple(result)

    def require(self, name: str) -> GodotExportPreset:
        matches = [item for item in self.presets() if item.name == name]
        if len(matches) != 1:
            raise ValueError(f"Export preset must exist exactly once: {name!r}")
        return matches[0]
