from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

from kodepoia.kodegodot.document import GodotTextDocumentParser
from kodepoia.kodegodot.gdscript import GDScriptInspector
from kodepoia.kodegodot.project import GodotProjectInspector
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.kodegodot.services import GodotEditorServices, GodotServicePorts


class GodotToolAPI:
    """Structured KodeGodot tool surface with no arbitrary Godot argv or remote hosts."""

    def __init__(
        self,
        root: Path,
        *,
        runtime: GodotRuntime | None = None,
        services: GodotEditorServices | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.project = GodotProjectInspector(self.root)
        self.documents = GodotTextDocumentParser(self.root)
        self.gdscript = GDScriptInspector(self.root)
        self.runtime = runtime or GodotRuntime(self.root)
        self.services = services or GodotEditorServices(self.root, executable=self.runtime.executable)
        self._dispatch: dict[str, Callable[[dict[str, Any]], Any]] = {
            "kodegodot_project_inspect": self._project_inspect,
            "kodegodot_document_parse": self._document_parse,
            "kodegodot_document_dependencies": self._document_dependencies,
            "kodegodot_gdscript_inspect": self._gdscript_inspect,
            "kodegodot_engine_version": self._engine_version,
            "kodegodot_check_script": self._check_script,
            "kodegodot_import_project": self._import_project,
            "kodegodot_smoke_project": self._smoke_project,
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
        return [
            self._schema("kodegodot_project_inspect", "Inspect project.godot and Godot asset counts", {}),
            self._schema("kodegodot_document_parse", "Parse one Godot 4 text scene/resource", path, ["path"]),
            self._schema("kodegodot_document_dependencies", "List declared external resource paths", path, ["path"]),
            self._schema("kodegodot_gdscript_inspect", "Inspect GDScript structure and typing coverage", path, ["path"]),
            self._schema("kodegodot_engine_version", "Report configured Godot engine version", {}),
            self._schema("kodegodot_check_script", "Parse one workspace GDScript with Godot --check-only", path, ["path"]),
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
            self._schema(
                "kodegodot_services_start",
                "Start Godot editor LSP/DAP services on local loopback ports",
                {
                    "lsp_port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                    "dap_port": {"type": "integer", "minimum": 1024, "maximum": 65535},
                    "timeout": {"type": "number", "minimum": 1, "maximum": 120},
                },
            ),
            self._schema("kodegodot_services_stop", "Stop the managed Godot LSP/DAP service process", {}),
            self._schema("kodegodot_lsp_symbols", "Read GDScript document symbols through Godot LSP", path, ["path"]),
            self._schema("kodegodot_lsp_diagnostics", "Read current GDScript diagnostics through Godot LSP", path, ["path"]),
            self._schema("kodegodot_dap_initialize", "Connect to and initialize Godot DAP on loopback", {}),
            self._schema("kodegodot_dap_launch_project", "Launch the pre-registered Godot project debug configuration", {}),
            self._schema("kodegodot_dap_threads", "Read debug threads from the connected Godot DAP session", {}),
        ]

    @staticmethod
    def _schema(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
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

    def _document_parse(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.documents.parse(str(args["path"])).to_dict()

    def _document_dependencies(self, args: dict[str, Any]) -> dict[str, Any]:
        document = self.documents.parse(str(args["path"]))
        return {"path": document.path, "dependencies": list(document.dependencies)}

    def _gdscript_inspect(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.gdscript.inspect(str(args["path"])).to_dict()

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

    def _services_start(self, args: dict[str, Any]) -> dict[str, Any]:
        ports = GodotServicePorts(int(args.get("lsp_port", 6005)), int(args.get("dap_port", 6006)))
        return self.services.start(ports, timeout=float(args.get("timeout", 30.0)))

    def _services_stop(self, _args: dict[str, Any]) -> dict[str, Any]:
        self.services.close()
        return {"stopped": True}

    def _lsp_symbols(self, args: dict[str, Any]) -> Any:
        if self.services.lsp is None:
            self.services.connect_lsp()
        assert self.services.lsp is not None
        target = self.documents.boundary.resolve(str(args["path"]), must_exist=True)
        return self.services.lsp.document_symbols(target)

    def _lsp_diagnostics(self, args: dict[str, Any]) -> Any:
        if self.services.lsp is None:
            self.services.connect_lsp()
        assert self.services.lsp is not None
        target = self.documents.boundary.resolve(str(args["path"]), must_exist=True)
        return self.services.lsp.diagnostics(target)

    def _dap_initialize(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.services.dap is None:
            session = self.services.connect_dap()
        else:
            session = self.services.dap
        return {"initialized": session.initialized, "capabilities": dict(session.capabilities)}

    def _dap_launch_project(self, _args: dict[str, Any]) -> dict[str, Any]:
        if self.services.dap is None:
            self.services.connect_dap()
        assert self.services.dap is not None
        config = self.services.dap.spec.configurations[0]
        body = self.services.dap.start_configuration(config)
        self.services.dap.configuration_done()
        return {"launched": True, "body": body}

    def _dap_threads(self, _args: dict[str, Any]) -> list[dict[str, Any]]:
        if self.services.dap is None:
            self.services.connect_dap()
        assert self.services.dap is not None
        return self.services.dap.threads()
