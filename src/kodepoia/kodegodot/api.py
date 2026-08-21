from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodegodot.project import GodotProjectInspector
from kodepoia.kodegodot.runtime import GodotRuntime


class GodotToolAPI:
    """Structured KodeGodot R5.1 tool surface with no arbitrary Godot argv."""

    def __init__(self, root: Path, *, runtime: GodotRuntime | None = None) -> None:
        self.root = root.resolve(strict=False)
        self.project = GodotProjectInspector(self.root)
        self.runtime = runtime or GodotRuntime(self.root)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "kodegodot_project_inspect": self._project_inspect,
            "kodegodot_engine_version": self._engine_version,
            "kodegodot_check_script": self._check_script,
            "kodegodot_import_project": self._import_project,
            "kodegodot_smoke_project": self._smoke_project,
        }

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise KeyError(f"Unknown KodeGodot tool: {tool_name}")
        return handler(dict(arguments or {}))

    def catalog(self) -> list[dict[str, Any]]:
        return [
            self._schema("kodegodot_project_inspect", "Inspect project.godot and Godot asset counts", {}),
            self._schema("kodegodot_engine_version", "Report configured Godot engine version", {}),
            self._schema(
                "kodegodot_check_script",
                "Parse one workspace GDScript with Godot --check-only",
                {"path": {"type": "string"}},
                ["path"],
            ),
            self._schema(
                "kodegodot_import_project",
                "Run a bounded headless Godot project import",
                {"timeout": {"type": "number", "minimum": 1, "maximum": 900}},
            ),
            self._schema(
                "kodegodot_smoke_project",
                "Run a bounded headless Godot project/scene smoke",
                {
                    "scene": {"type": ["string", "null"]},
                    "quit_after": {"type": "integer", "minimum": 1, "maximum": 600},
                    "timeout": {"type": "number", "minimum": 1, "maximum": 900},
                },
            ),
        ]

    @staticmethod
    def _schema(
        name: str,
        description: str,
        properties: dict[str, Any],
        required: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required or [],
                    "additionalProperties": False,
                },
            },
        }

    @staticmethod
    def _bounded_timeout(args: dict[str, Any], default: float) -> float:
        value = float(args.get("timeout", default))
        if not 1.0 <= value <= 900.0:
            raise ValueError("timeout must be between 1 and 900 seconds")
        return value

    def _project_inspect(self, _args: dict[str, Any]) -> dict[str, Any]:
        return asdict(self.project.inspect())

    def _engine_version(self, _args: dict[str, Any]) -> dict[str, Any]:
        return asdict(self.runtime.version())

    def _check_script(self, args: dict[str, Any]) -> dict[str, Any]:
        return asdict(self.runtime.check_script(str(args["path"])))

    def _import_project(self, args: dict[str, Any]) -> dict[str, Any]:
        return asdict(self.runtime.import_project(timeout=self._bounded_timeout(args, 300.0)))

    def _smoke_project(self, args: dict[str, Any]) -> dict[str, Any]:
        scene = args.get("scene")
        return asdict(
            self.runtime.smoke_project(
                scene=str(scene) if scene is not None else None,
                quit_after=int(args.get("quit_after", 2)),
                timeout=self._bounded_timeout(args, 60.0),
            )
        )
