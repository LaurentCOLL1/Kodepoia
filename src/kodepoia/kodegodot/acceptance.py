from __future__ import annotations

import hashlib
import json
import platform
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.kodegodot.api import GodotToolAPI
from kodepoia.kodegodot.executor import KodeGodotExecutor
from kodepoia.kodegodot.runtime import GodotRuntime
from kodepoia.kodegodot.services import GodotEditorServices, GodotServicePorts


@dataclass(frozen=True, slots=True)
class AcceptanceStep:
    name: str
    passed: bool
    elapsed_seconds: float
    details: Any = None
    error: str | None = None


class R5AcceptanceRunner:
    """Hardware-local R5 acceptance against a generated, disposable Godot project."""

    def __init__(
        self,
        repo_root: Path,
        *,
        executable: str = "godot",
        output: Path | None = None,
        ports: GodotServicePorts | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve(strict=False)
        self.workspace = self.repo_root / ".kodepoia" / "r5-acceptance" / "project"
        self.output = (output or self.repo_root / ".kodepoia" / "benchmarks" / "r5-local-acceptance.json").resolve(strict=False)
        self.executable = str(executable)
        self.ports = ports or GodotServicePorts()
        self.steps: list[AcceptanceStep] = []
        self._prepare_fixture()
        runtime = GodotRuntime(self.workspace, executable=self.executable)
        services = GodotEditorServices(self.workspace, executable=self.executable)
        api = GodotToolAPI(self.workspace, runtime=runtime, services=services)
        permissions = PermissionSet()
        permissions.grant(PermissionGrant(Capability.FILE_READ, roots=(self.workspace,)))
        permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(self.workspace,)))
        permissions.grant(PermissionGrant(Capability.PROCESS_EXECUTE, executables=(Path(self.executable).name,)))
        guardian = KodeGuardian(permissions)
        audit = AuditLog(self.workspace / ".kodepoia" / "audit" / "r5-acceptance.jsonl")
        safe_change = SafeChangeManager(self.workspace, self.workspace / ".kodepoia" / "snapshots")
        self.executor = KodeGodotExecutor(
            self.workspace,
            guardian=guardian,
            audit=audit,
            safe_change=safe_change,
            api=api,
        )

    def probe(self) -> dict[str, Any]:
        self._step("engine_version", lambda: self.executor.invoke("kodegodot_engine_version").result)
        self._step("project_inspect", lambda: self.executor.invoke("kodegodot_project_inspect").result)
        self._step("scene_parse", lambda: self.executor.invoke("kodegodot_document_parse", {"path": "main.tscn"}).result)
        self._step("gdscript_inspect", lambda: self.executor.invoke("kodegodot_gdscript_inspect", {"path": "main.gd"}).result)
        self._step("export_presets", lambda: self.executor.invoke("kodegodot_export_presets").result)
        return self._save(acceptance_completed=False, probe_only=True)

    def run(self) -> dict[str, Any]:
        self._step("engine_version", self._require_version)
        self._step("project_inspect", lambda: self.executor.invoke("kodegodot_project_inspect").result)
        self._step("scene_parse", lambda: self.executor.invoke("kodegodot_document_parse", {"path": "main.tscn"}).result)
        self._step("scene_domain", lambda: self.executor.invoke("kodegodot_scene_analyze", {"path": "main.tscn"}).result)
        self._step("gdscript_inspect", lambda: self.executor.invoke("kodegodot_gdscript_inspect", {"path": "main.gd"}).result)
        self._step("check_script", lambda: self._require_ok(self.executor.invoke("kodegodot_check_script", {"path": "main.gd"}).result))
        self._step("import_project", lambda: self._require_ok(self.executor.invoke("kodegodot_import_project", {"timeout": 300}).result))
        self._step("smoke_scene", lambda: self._require_ok(self.executor.invoke("kodegodot_smoke_project", {"scene": "main.tscn", "quit_after": 5, "timeout": 120}).result))
        self._step("benchmark_scene", self._benchmark)
        self._step("capture_movie", self._capture)
        self._step("governed_scene_edit", self._governed_edit)
        self._step("services_start", self._services_start)
        self._step("lsp_symbols", lambda: self.executor.invoke("kodegodot_lsp_symbols", {"path": "main.gd"}).result)
        self._step("lsp_diagnostics", lambda: self.executor.invoke("kodegodot_lsp_diagnostics", {"path": "main.gd"}).result)
        self._step("dap_initialize", lambda: self.executor.invoke("kodegodot_dap_initialize").result)
        self._step("dap_launch_project", lambda: self.executor.invoke("kodegodot_dap_launch_project").result)
        self._step("dap_threads", lambda: self.executor.invoke("kodegodot_dap_threads").result)
        self._step("export_release", self._export)
        self._step("audit_chain", self._audit_verify)
        try:
            self.executor.api.services.close()
        except Exception:
            pass
        completed = all(step.passed for step in self.steps)
        return self._save(acceptance_completed=completed, probe_only=False)

    def _require_version(self) -> dict[str, Any]:
        result = self.executor.invoke("kodegodot_engine_version").result
        if not bool(result.get("compatible_47")):
            raise RuntimeError(f"R5 requires Godot 4.7.x, got {result.get('raw')!r}")
        return result

    def _benchmark(self) -> dict[str, Any]:
        result = self.executor.invoke(
            "kodegodot_benchmark_scene",
            {"scene": "main.tscn", "frames": 120, "timeout": 180},
        ).result
        invocation = result.get("invocation", {})
        self._require_ok(invocation)
        if float(result.get("effective_fps", 0.0)) <= 0.0:
            raise RuntimeError("Godot benchmark returned a non-positive effective_fps")
        return result

    def _capture(self) -> dict[str, Any]:
        result = self.executor.invoke(
            "kodegodot_capture_movie",
            {"scene": "main.tscn", "output_name": "r5-acceptance.avi", "frames": 8, "fps": 30, "timeout": 180},
        ).result
        self._require_ok(result)
        movie = self.workspace / ".kodepoia" / "captures" / "r5-acceptance.avi"
        if not movie.is_file() or movie.stat().st_size <= 0:
            raise RuntimeError("Godot movie capture did not produce a non-empty AVI")
        return {**result, "artifact": movie.relative_to(self.workspace).as_posix(), "bytes": movie.stat().st_size}

    def _governed_edit(self) -> dict[str, Any]:
        scene = self.workspace / "main.tscn"
        before = hashlib.sha256(scene.read_bytes()).hexdigest()
        result = self.executor.invoke(
            "kodegodot_scene_set_existing_property",
            {
                "path": "main.tscn",
                "node": "AcceptanceRoot",
                "property": "process_mode",
                "raw_value": "3",
                "expected_sha256": before,
            },
        )
        if not result.snapshot:
            raise RuntimeError("Governed scene edit did not create a SafeChange snapshot")
        if "process_mode = 3" not in scene.read_text(encoding="utf-8"):
            raise RuntimeError("Governed scene edit was not applied")
        return {"result": result.result, "snapshot_created": True}

    def _services_start(self) -> dict[str, Any]:
        return self.executor.invoke(
            "kodegodot_services_start",
            {
                "lsp_port": self.ports.lsp,
                "dap_port": self.ports.dap,
                "debug_port": self.ports.debug,
                "timeout": 45,
            },
        ).result

    def _export(self) -> dict[str, Any]:
        result = self.executor.invoke(
            "kodegodot_export_project",
            {
                "preset": "Windows Desktop",
                "output_name": "r5-acceptance.exe",
                "mode": "release",
                "timeout": 900,
            },
        ).result
        self._require_ok(result)
        artifact = self.workspace / ".kodepoia" / "exports" / "r5-acceptance.exe"
        if not artifact.is_file() or artifact.stat().st_size <= 0:
            raise RuntimeError("Godot export did not produce a non-empty Windows executable")
        return {**result, "artifact": artifact.relative_to(self.workspace).as_posix(), "bytes": artifact.stat().st_size}

    def _audit_verify(self) -> dict[str, Any]:
        valid = self.executor.audit.verify()
        if not valid:
            raise RuntimeError("KodeGodot audit hash chain verification failed")
        return {"valid": True}

    @staticmethod
    def _require_ok(result: dict[str, Any]) -> dict[str, Any]:
        if int(result.get("returncode", -1)) != 0 or bool(result.get("timed_out")) or bool(result.get("cancelled")):
            stderr = str(result.get("stderr", "")).strip()
            raise RuntimeError(f"Godot invocation failed: rc={result.get('returncode')} stderr={stderr}")
        return result

    def _step(self, name: str, action: Callable[[], Any]) -> None:
        started = time.monotonic()
        try:
            details = action()
        except Exception as exc:
            self.steps.append(
                AcceptanceStep(name, False, time.monotonic() - started, error=f"{type(exc).__name__}: {exc}")
            )
        else:
            self.steps.append(AcceptanceStep(name, True, time.monotonic() - started, details=details))

    def _save(self, *, acceptance_completed: bool, probe_only: bool) -> dict[str, Any]:
        payload = {
            "metadata": {
                "phase": "R5-local-acceptance",
                "acceptance_completed": acceptance_completed,
                "probe_only": probe_only,
                "generated_at": datetime.now(UTC).isoformat(),
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "godot_executable": Path(self.executable).name,
                "ports": asdict(self.ports),
                "fixture": ".kodepoia/r5-acceptance/project",
            },
            "steps": [asdict(step) for step in self.steps],
            "summary": {
                "passed": sum(step.passed for step in self.steps),
                "failed": sum(not step.passed for step in self.steps),
                "total": len(self.steps),
            },
        }
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def _prepare_fixture(self) -> None:
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=False)
        (self.workspace / "project.godot").write_text(
            'config_version=5\n\n'
            '[application]\n'
            'config/name="Kodepoia R5 Acceptance"\n'
            'run/main_scene="res://main.tscn"\n\n'
            '[display]\n'
            'window/size/viewport_width=320\n'
            'window/size/viewport_height=180\n\n'
            '[rendering]\n'
            'renderer/rendering_method="gl_compatibility"\n'
            'renderer/rendering_method.mobile="gl_compatibility"\n',
            encoding="utf-8",
        )
        (self.workspace / "main.gd").write_text(
            'extends Node2D\n\n'
            'var ticks: int = 0\n\n'
            'func _process(_delta: float) -> void:\n'
            '    ticks += 1\n',
            encoding="utf-8",
        )
        (self.workspace / "main.tscn").write_text(
            '[gd_scene load_steps=2 format=3]\n\n'
            '[ext_resource type="Script" path="res://main.gd" id="1_script"]\n\n'
            '[node name="AcceptanceRoot" type="Node2D"]\n'
            'process_mode = 0\n'
            'script = ExtResource("1_script")\n',
            encoding="utf-8",
        )
        (self.workspace / "export_presets.cfg").write_text(
            '[preset.0]\n\n'
            'name="Windows Desktop"\n'
            'platform="Windows Desktop"\n'
            'runnable=true\n'
            'advanced_options=false\n'
            'dedicated_server=false\n'
            'custom_features=""\n'
            'export_filter="all_resources"\n'
            'include_filter=""\n'
            'exclude_filter=""\n'
            'export_path=""\n'
            'encryption_include_filters=""\n'
            'encryption_exclude_filters=""\n'
            'encrypt_pck=false\n'
            'encrypt_directory=false\n'
            'script_export_mode=2\n\n'
            '[preset.0.options]\n\n'
            'custom_template/debug=""\n'
            'custom_template/release=""\n'
            'debug/export_console_wrapper=0\n'
            'binary_format/embed_pck=false\n'
            'texture_format/bptc=true\n'
            'texture_format/s3tc=true\n'
            'texture_format/etc=false\n'
            'texture_format/etc2=false\n'
            'binary_format/architecture="x86_64"\n'
            'codesign/enable=false\n',
            encoding="utf-8",
        )
