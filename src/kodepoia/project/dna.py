from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import yaml


class ProjectType(StrEnum):
    GAME = "game"
    DESKTOP_APP = "desktop_app"
    TOOL = "tool"
    PLUGIN = "plugin"
    LIBRARY = "library"
    AI_PROJECT = "ai_project"
    OTHER = "other"


class Platform(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    STEAM_DECK = "steam_deck"
    XR = "xr"


class Dimension(StrEnum):
    D2 = "2d"
    D25 = "2.5d"
    D3 = "3d"
    HYBRID = "hybrid"


class DecisionState(StrEnum):
    YES = "yes"
    NO = "no"
    UNDECIDED = "undecided"


@dataclass(slots=True)
class PerformanceBudget:
    target_fps: int = 60
    min_fps: int = 30
    max_vram_mb: int | None = None
    max_ram_mb: int | None = None
    max_build_mb: int | None = None


@dataclass(slots=True)
class ProjectDNA:
    schema_version: int
    name: str
    project_type: ProjectType
    platforms: list[Platform]
    engine: str | None = None
    engine_version: str | None = None
    dimension: Dimension | None = None
    genres: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    graphics_style: str | None = None
    online: DecisionState = DecisionState.NO
    multiplayer: DecisionState = DecisionState.NO
    performance: dict[str, PerformanceBudget] = field(default_factory=dict)
    tools: dict[str, bool] = field(default_factory=dict)
    lineage: dict[str, str] = field(default_factory=dict)
    capabilities: dict[str, DecisionState] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Project name is required")
        if not self.platforms:
            raise ValueError("At least one target platform is required")
        if self.project_type is ProjectType.GAME and not self.dimension:
            raise ValueError("Game projects require a dimension")
        mobile = {Platform.ANDROID, Platform.IOS} & set(self.platforms)
        if not mobile:
            forbidden = {"touch", "gyro", "accelerometer"} & {item.lower() for item in self.inputs}
            if forbidden:
                raise ValueError(f"Mobile-only inputs selected without mobile platform: {sorted(forbidden)}")
        for platform in self.performance:
            if Platform(platform) not in self.platforms:
                raise ValueError(f"Performance budget defined for non-target platform: {platform}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()

        def primitive(value: Any) -> Any:
            if isinstance(value, Enum):
                return value.value
            if isinstance(value, dict):
                return {str(primitive(key)): primitive(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [primitive(item) for item in value]
            return value

        return primitive(asdict(self))

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(self.to_dict(), sort_keys=False, allow_unicode=True), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ProjectDNA":
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        performance = {key: PerformanceBudget(**value) for key, value in raw.get("performance", {}).items()}
        dna = cls(
            schema_version=int(raw["schema_version"]), name=raw["name"], project_type=ProjectType(raw["project_type"]),
            platforms=[Platform(item) for item in raw["platforms"]], engine=raw.get("engine"), engine_version=raw.get("engine_version"),
            dimension=Dimension(raw["dimension"]) if raw.get("dimension") else None, genres=list(raw.get("genres", [])),
            inputs=list(raw.get("inputs", [])), graphics_style=raw.get("graphics_style"), online=DecisionState(raw.get("online", "no")),
            multiplayer=DecisionState(raw.get("multiplayer", "no")), performance=performance, tools=dict(raw.get("tools", {})),
            lineage=dict(raw.get("lineage", {})), capabilities={key: DecisionState(value) for key, value in raw.get("capabilities", {}).items()},
        )
        dna.validate()
        return dna
