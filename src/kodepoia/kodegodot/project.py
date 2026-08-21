from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kodepoia.kodecode.workspace import WorkspaceBoundary

_PACKED_STRINGS = re.compile(r'PackedStringArray\((.*)\)\s*$')
_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')


@dataclass(frozen=True, slots=True)
class GodotProjectInfo:
    project_file: str
    config_version: int | None
    name: str | None
    main_scene: str | None
    rendering_method: str | None
    rendering_method_mobile: str | None
    features: tuple[str, ...]
    setting_count: int
    scripts: int
    scenes: int
    resources: int
    shaders: int


class GodotProjectInspector:
    """Read-only parser for the subset of project.godot needed by Kodepoia.

    Values that are not simple JSON-like scalars remain raw strings. This
    avoids evaluating Godot Variant expressions while still preserving useful
    project metadata.
    """

    def __init__(self, root: Path) -> None:
        self.boundary = WorkspaceBoundary(root)

    def inspect(self) -> GodotProjectInfo:
        project = self.boundary.resolve("project.godot", must_exist=True)
        if not project.is_file():
            raise FileNotFoundError("project.godot is not a file")
        settings = self._parse(project.read_text(encoding="utf-8-sig"))
        features = self._features(settings.get("application/config/features"))
        counts = self._counts()
        return GodotProjectInfo(
            project_file="project.godot",
            config_version=self._int(settings.get("__root__/config_version")),
            name=self._string(settings.get("application/config/name")),
            main_scene=self._string(settings.get("application/run/main_scene")),
            rendering_method=self._string(settings.get("rendering/renderer/rendering_method")),
            rendering_method_mobile=self._string(
                settings.get("rendering/renderer/rendering_method.mobile")
            ),
            features=features,
            setting_count=sum(1 for key in settings if not key.startswith("__root__/")),
            scripts=counts["scripts"],
            scenes=counts["scenes"],
            resources=counts["resources"],
            shaders=counts["shaders"],
        )

    @staticmethod
    def _parse(text: str) -> dict[str, Any]:
        section = "__root__"
        values: dict[str, Any] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                continue
            if "=" not in line:
                continue
            key, raw_value = line.split("=", 1)
            values[f"{section}/{key.strip()}"] = GodotProjectInspector._scalar(raw_value.strip())
        return values

    @staticmethod
    def _scalar(raw: str) -> Any:
        if not raw:
            return ""
        if raw in {"true", "false"}:
            return raw == "true"
        if raw == "null":
            return None
        if raw.startswith('"') and raw.endswith('"'):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            return raw

    @staticmethod
    def _string(value: Any) -> str | None:
        return value if isinstance(value, str) else None

    @staticmethod
    def _int(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @staticmethod
    def _features(value: Any) -> tuple[str, ...]:
        if not isinstance(value, str):
            return ()
        match = _PACKED_STRINGS.fullmatch(value)
        if not match:
            return ()
        result: list[str] = []
        for quoted in _QUOTED.finditer(match.group(1)):
            try:
                result.append(json.loads(f'"{quoted.group(1)}"'))
            except json.JSONDecodeError:
                continue
        return tuple(result)

    def _counts(self) -> dict[str, int]:
        counts = {"scripts": 0, "scenes": 0, "resources": 0, "shaders": 0}
        ignored = {".git", ".godot", ".kodepoia", "build", "builds"}
        for path in self.boundary.root.rglob("*"):
            if any(part in ignored for part in path.relative_to(self.boundary.root).parts):
                continue
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix == ".gd":
                counts["scripts"] += 1
            elif suffix in {".tscn", ".scn"}:
                counts["scenes"] += 1
            elif suffix in {".tres", ".res"}:
                counts["resources"] += 1
            elif suffix in {".gdshader", ".shader"}:
                counts["shaders"] += 1
        return counts
