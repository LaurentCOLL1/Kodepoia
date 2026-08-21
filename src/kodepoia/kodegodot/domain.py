from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from kodepoia.kodegodot.document import GodotTextDocumentParser


@dataclass(frozen=True, slots=True)
class GodotDomainIssue:
    severity: str
    code: str
    message: str
    node: str | None = None
    line: int | None = None


@dataclass(frozen=True, slots=True)
class GodotSceneDomainReport:
    path: str
    dimension: str
    node_count: int
    character_bodies: tuple[str, ...]
    collision_nodes: tuple[str, ...]
    navigation_nodes: tuple[str, ...]
    tilemap_layers: tuple[str, ...]
    ui_nodes: tuple[str, ...]
    cameras: tuple[str, ...]
    mesh_nodes: tuple[str, ...]
    lights: tuple[str, ...]
    issues: tuple[GodotDomainIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GodotSceneDomainAnalyzer:
    """Conservative 2D/3D scene intelligence derived from parsed node types."""

    _UI_TYPES = {"Control", "Container", "CanvasLayer", "Panel", "Label", "Button", "LineEdit", "TextureRect"}

    def __init__(self, root: Path) -> None:
        self.parser = GodotTextDocumentParser(root)

    def analyze(self, path: str) -> GodotSceneDomainReport:
        doc = self.parser.parse(path)
        if doc.document_type != "scene":
            raise ValueError("Scene domain analysis requires a .tscn scene")
        typed = [(node.name or "<unnamed>", node.node_type or "", node.line) for node in doc.nodes]
        types = [item[1] for item in typed]
        has_2d = any(t.endswith("2D") or t in {"Control", "CanvasLayer", "TileMap", "TileMapLayer"} for t in types)
        has_3d = any(t.endswith("3D") for t in types)
        dimension = "hybrid" if has_2d and has_3d else "3d" if has_3d else "2d" if has_2d else "unknown"

        def names(predicate) -> tuple[str, ...]:
            return tuple(name for name, node_type, _line in typed if predicate(node_type))

        characters = names(lambda t: t in {"CharacterBody2D", "CharacterBody3D"})
        collisions = names(lambda t: t in {"CollisionShape2D", "CollisionPolygon2D", "CollisionShape3D", "CollisionPolygon3D"})
        navigation = names(lambda t: t.startswith("Navigation") or t in {"Path2D", "Path3D"})
        tilemaps = names(lambda t: t == "TileMapLayer")
        ui = names(lambda t: t in self._UI_TYPES or t.endswith("Container"))
        cameras = names(lambda t: t in {"Camera2D", "Camera3D"})
        meshes = names(lambda t: t in {"MeshInstance2D", "MeshInstance3D", "MultiMeshInstance2D", "MultiMeshInstance3D"})
        lights = names(lambda t: "Light" in t)

        issues: list[GodotDomainIssue] = []
        for name, node_type, line in typed:
            if node_type == "TileMap":
                issues.append(GodotDomainIssue("warning", "legacy-tilemap", "TileMap detected; prefer TileMapLayer for Godot 4.7 scene composition.", name, line))
            if node_type in {"CharacterBody2D", "CharacterBody3D"} and not collisions:
                issues.append(GodotDomainIssue("warning", "character-no-collision", "CharacterBody scene has no collision shape/polygon node.", name, line))
            if node_type in {"NavigationAgent2D", "NavigationAgent3D"} and not any(t in {"NavigationRegion2D", "NavigationRegion3D"} for t in types):
                issues.append(GodotDomainIssue("info", "agent-no-region", "NavigationAgent present without NavigationRegion in this scene; region may be inherited or external.", name, line))
        if dimension == "hybrid":
            issues.append(GodotDomainIssue("info", "hybrid-scene", "Scene mixes 2D/UI and 3D nodes; verify this is intentional."))

        return GodotSceneDomainReport(
            path=doc.path,
            dimension=dimension,
            node_count=len(doc.nodes),
            character_bodies=characters,
            collision_nodes=collisions,
            navigation_nodes=navigation,
            tilemap_layers=tilemaps,
            ui_nodes=ui,
            cameras=cameras,
            mesh_nodes=meshes,
            lights=lights,
            issues=tuple(issues),
        )
