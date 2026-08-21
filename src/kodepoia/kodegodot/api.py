from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodegodot.document import GodotTextDocumentParser
from kodepoia.kodegodot.domain import GodotSceneDomainAnalyzer
from kodepoia.kodegodot.edit import GodotSceneEditor
from kodepoia.kodegodot.exporting import GodotExportPresetInspector
from kodepoia.kodegodot.gdscript import GDScriptInspector
from kodepoia.kodegodot.project import GodotProjectInspector
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.kodegodot.services import GodotEditorServices, GodotServicePorts


class GodotToolAPI:
    """Structured KodeGodot tool surface with no arbitrary Godot argv or remote hosts."""

    def __init__(self, root: Path, *, runtime: GodotRuntime | None = None, services: GodotEditorServices | None = None) -> None:
        self.root = root.resolve(strict=False)
        self.project = GodotProjectInspector(self.root)
        self.documents = GodotTextDocumentParser(self.root)
        self.domain = GodotSceneDomainAnalyzer(self.root)
        self.scene_editor = GodotSceneEditor(self.root)
        self.gdscript = GDScriptInspector(self.root)
        self.exports = GodotExportPresetInspector(self.root)
        self.runtime = runtime or GodotRuntime(self.root)
        self.services = services or GodotEditorServices(self.root, executable=self.runtime.executable)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "kodegodot_project_inspect": self._project_inspect,
            "kodegodot_document_parse": self._document_parse,
            "kodegodot_document_dependencies": self._document_dependencies,
            "kodegodot_scene_analyze": self._scene_analyze,
            "kodegodot_scene_set_existing_property": self._scene_set_existing_property,
            "kodegodot_gdscript_inspect": self._gdscript_inspect,
            "kodegodot_engine_version": self._engine_version,
            "kodegodot_check_script": self._check_script,
            "kodegodot_import_project": self._import_project,
            "kodegodot_smoke_project": self._smoke_project,
            "kodegodot_export_presets": self._export_presets,
            "kodegodot_export_project": self._export_project,
            "kodegodot_capture_movie": self._capture_movie,
            "kodegodot_benchmark_scene": self._benchmark_scene,
            "kodegodot_services_start": self._services_start,
            "kodegodot_services_stop": self._services_stop,
            "kodegodot_lsp_symbols": self._lsp_symbols,
            "kodegodot_lsp_diagnostics": self._lsp_diagnostics,
            "kodegodot_dap_initialize": self._dap_initialize,
            "kodegodot_dap_launch_project": self._dap_launch_project,
            "kodegodot_dap_threads": self._dap_threads,
        }

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        handler = self._dispatch.get(tool_name)
        if handler is None:
            raise KeyError(f"Unknown KodeGodot tool: {tool_name}")
        return handler(dict(arguments or {}))

    def catalog(self) -> list[dict[str, Any]]:
        path = {"path": {"type": "string"}}
        port = {"type": "integer", "minimum": 1024, "maximum": 49151}
        return [
            self._schema("kodegodot_project_inspect", "Inspect project.godot and Godot asset counts", {}),
            self._schema("kodegodot_document_parse", "Parse one Godot 4 text scene/resource", path, ["path"]),
            self._schema("kodegodot_document_dependencies", "List declared external resource paths", path, ["path"]),
            self._schema("kodegodot_scene_analyze", "Analyze Godot scene 2D/3D domain composition and conservative risks", path, ["path"]),
            self._schema("kodegodot_scene_set_existing_property", "Change one existing non-protected TSCN node property with SHA precondition", {
                "path": {"type": "string"}, "node": {"type": "string"}, "parent": {"type": ["string", "null"]},
                "property": {"type": "string"}, "raw_value": {"type": "string", "minLength": 1, "maxLength": 4096},
                "expected_sha256": {"type": "string", "pattern": "^[0-9a-fA-F]{64}$"},
            }, ["path", "node", "property", "raw_value", "expected_sha256"]),
            self._schema("kodegodot_gdscript_inspect", "Inspect GDScript structure and typing coverage", path, ["path"]),
            self._schema("kodegodot_engine_version", "Report configured Godot engine version", {}),
            self._schema("kodegodot_check_script", "Parse one workspace GDScript with Godot --check-only", path, ["path"]),
            self._schema("kodegodot_import_project", "Run a bounded headless Godot project import", {"timeout": {"type": "number", "minimum": 1, "maximum": 900}}),
            self._schema("kodegodot_smoke_project", "Run a bounded headless Godot project/scene smoke", {
                "scene": {"type": ["string", "null"]}, "quit_after": {"type": "integer", "minimum": 1, "maximum": 600},
                "timeout": {"type": "number", "minimum": 1, "maximum": 900},
            }),
            self._schema("kodegodot_export_presets", "List non-secret export preset names/platforms from export_presets.cfg", {}),
            self._schema("kodegodot_export_project", "Export using an existing preset into .kodepoia/exports", {
                "preset": {"type": "string"}, "output_name": {"type": "string"},
                "mode": {"type": "string", "enum": ["release", "debug", "pack"]},
                "timeout": {"type": "number", "minimum": 1, "maximum": 900},
            }, ["preset", "output_name"]),
            self._schema("kodegodot_capture_movie", "Record a bounded AVI from one scene into .kodepoia/captures", {
                "scene": {"type": "string"}, "output_name": {"type": "string"},
                "frames": {"type": "integer", "minimum": 1, "maximum": 36000},
                "fps": {"type": "integer", "minimum": 1, "maximum": 240},
                "timeout": {"type": "number", "minimum": 1, "maximum": 900},
            }, ["scene", "output_name"]),
            self._schema("kodegodot_benchmark_scene", "Measure bounded headless scene execution throughput", {
                "scene": {"type": ["string", "null"]}, "frames": {"type": "integer", "minimum": 1, "maximum": 3600},
                "timeout": {"type": "number", "minimum": 1, "maximum": 900},
            }),
            self._schema("kodegodot_services_start", "Start and initialize Godot LSP/DAP services on fixed loopback host", {
                "lsp_port": port, "dap_port": port, "debug_port": port,
                "timeout": {"type": "number", "minimum": 1, "maximum": 120},
            }),
            self._schema("kodegodot_services_stop", "Stop the managed Godot LSP/DAP service process", {}),
            self._schema("kodegodot_lsp_symbols", "Read GDScript document symbols through Godot LSP", path, ["path"]),
            self._schema("kodegodot_lsp_diagnostics", "Read current GDScript diagnostics through Godot LSP", path, ["path"]),
            self._schema("kodegodot_dap_initialize", "Read initialized Godot DAP capability state on loopback", {}),
            self._schema("kodegodot_dap_launch_project", "Launch the pre-registered Godot project debug configuration", {}),
            self._schema("kodegodot_dap_threads", "Read debug threads from the connected Godot DAP session", {}),
        ]

    @staticmethod
    def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
        return {"type": "function", "function": {"name": name, "description": description, "parameters": {
            "type": "object", "properties": properties, "required": required or [], "additionalProperties": False,
        }}}

    @staticmethod
    def _bounded_timeout(args: dict[str, Any], default: float) -> float:
        value = float(args.get("timeout", default))
        if not 1.0 <= value <= 900.0:
            raise ValueError("timeout must be between 1 and 900 seconds")
        return value

    def _project_inspect(self, _args: dict[str, Any]) -> dict[str, Any]: return asdict(self.project.inspect())
    def _document_parse(self, args: dict[str, Any]) -> dict[str, Any]: return self.documents.parse(str(args["path"])).to_dict()
    def _document_dependencies(self, args: dict[str, Any]) -> dict[str, Any]:
        document = self.documents.parse(str(args["path"])); return {"path": document.path, "dependencies": list(document.dependencies)}
    def _scene_analyze(self, args: dict[str, Any]) -> dict[str, Any]: return self.domain.analyze(str(args["path"])).to_dict()
    def _scene_set_existing_property(self, args: dict[str, Any]) -> dict[str, Any]:
        return asdict(self.scene_editor.set_existing_property(str(args["path"]), node=str(args["node"]), parent=str(args["parent"]) if args.get("parent") is not None else None, property_name=str(args["property"]), raw_value=str(args["raw_value"]), expected_sha256=str(args["expected_sha256"])))
    def _gdscript_inspect(self, args: dict[str, Any]) -> dict[str, Any]: return self.gdscript.inspect(str(args["path"])).to_dict()
    def _engine_version(self, _args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.version())
    def _check_script(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.check_script(str(args["path"])))
    def _import_project(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.import_project(timeout=self._bounded_timeout(args, 300.0)))
    def _smoke_project(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.smoke_project(scene=str(args["scene"]) if args.get("scene") is not None else None, quit_after=int(args.get("quit_after", 2)), timeout=self._bounded_timeout(args, 60.0)))
    def _export_presets(self, _args: dict[str, Any]) -> list[dict[str, Any]]: return [asdict(item) for item in self.exports.presets()]
    def _export_project(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.export_project(preset=str(args["preset"]), output_name=str(args["output_name"]), mode=str(args.get("mode", "release")), timeout=self._bounded_timeout(args, 900.0)))
    def _capture_movie(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.capture_movie(scene=str(args["scene"]), output_name=str(args["output_name"]), frames=int(args.get("frames", 60)), fps=int(args.get("fps", 30)), timeout=self._bounded_timeout(args, 900.0)))
    def _benchmark_scene(self, args: dict[str, Any]) -> dict[str, Any]: return asdict(self.runtime.benchmark_scene(scene=str(args["scene"]) if args.get("scene") is not None else None, frames=int(args.get("frames", 120)), timeout=self._bounded_timeout(args, 300.0)))
    def _services_start(self, args: dict[str, Any]) -> dict[str, Any]:
        ports = GodotServicePorts(int(args.get("lsp_port", 6005)), int(args.get("dap_port", 6006)), int(args.get("debug_port", 6007)))
        return self.services.start(ports, timeout=float(args.get("timeout", 30.0)))
    def _services_stop(self, _args: dict[str, Any]) -> dict[str, Any]: self.services.close(); return {"stopped": True}
    def _lsp_symbols(self, args: dict[str, Any]) -> Any:
        session = self.services.connect_lsp() if self.services.lsp is None else self.services.lsp
        return session.document_symbols(self.documents.boundary.resolve(str(args["path"]), must_exist=True))
    def _lsp_diagnostics(self, args: dict[str, Any]) -> Any:
        session = self.services.connect_lsp() if self.services.lsp is None else self.services.lsp
        return session.diagnostics(self.documents.boundary.resolve(str(args["path"]), must_exist=True))
    def _dap_initialize(self, _args: dict[str, Any]) -> dict[str, Any]:
        session = self.services.connect_dap() if self.services.dap is None else self.services.dap
        return {"initialized": session.initialized, "capabilities": dict(session.capabilities)}
    def _dap_launch_project(self, _args: dict[str, Any]) -> dict[str, Any]:
        session = self.services.connect_dap() if self.services.dap is None else self.services.dap
        config = session.spec.configurations[0]; body = session.start_configuration(config); session.configuration_done(); return {"launched": True, "body": body}
    def _dap_threads(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        session = self.services.connect_dap() if self.services.dap is None else self.services.dap
        return session.threads()
