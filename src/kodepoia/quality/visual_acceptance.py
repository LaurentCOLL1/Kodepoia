from __future__ import annotations

import argparse
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
from kodepoia.quality.tests import TestCaseStatus
from kodepoia.quality.visual import KodeVisualQA, VisualPolicy, VisualStatus


@dataclass(frozen=True, slots=True)
class AcceptanceStep:
    name: str
    passed: bool
    elapsed_seconds: float
    details: Any = None
    error: str | None = None


class R64AcceptanceRunner:
    """Hardware-local R6.4 acceptance using a real rendered Godot fixture."""

    def __init__(
        self,
        repo_root: Path,
        *,
        executable: str,
        output: Path | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve(strict=False)
        self.workspace = self.repo_root / ".kodepoia" / "r6-4-acceptance" / "project"
        self.output = (
            output
            or self.repo_root
            / ".kodepoia"
            / "visual_tests"
            / "r6-4-local-acceptance.json"
        ).resolve(strict=False)
        self.executable = str(executable)
        self.steps: list[AcceptanceStep] = []
        self.render_info: dict[str, str] = {}
        self.visual_report = None
        self.baseline = None
        self._prepare_fixture()

        runtime = GodotRuntime(self.workspace, executable=self.executable)
        api = GodotToolAPI(self.workspace, runtime=runtime)
        permissions = PermissionSet()
        permissions.grant(PermissionGrant(Capability.FILE_READ, roots=(self.workspace,)))
        permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(self.workspace,)))
        permissions.grant(
            PermissionGrant(
                Capability.PROCESS_EXECUTE,
                executables=(Path(self.executable).name,),
            )
        )
        guardian = KodeGuardian(permissions)
        audit = AuditLog(
            self.workspace / ".kodepoia" / "audit" / "r6-4-acceptance.jsonl"
        )
        safe_change = SafeChangeManager(
            self.workspace, self.workspace / ".kodepoia" / "snapshots"
        )
        self.executor = KodeGodotExecutor(
            self.workspace,
            guardian=guardian,
            audit=audit,
            safe_change=safe_change,
            api=api,
        )
        self.visual = KodeVisualQA(self.workspace)

    def run(self) -> dict[str, Any]:
        self._step("engine_version", self._require_version)
        self._step("baseline_capture", self._capture_baseline)
        self._step("baseline_approval", self._approve_baseline)
        self._step("current_capture", self._capture_current)
        self._step("real_renderer_evidence", self._require_real_renderer)
        self._step("visual_compare", self._compare)
        self._step("r6_3_regression_hook", self._regression_hook)
        self._step("audit_chain", self._audit_verify)
        completed = bool(self.steps) and all(step.passed for step in self.steps)
        return self._save(acceptance_completed=completed)

    def _require_version(self) -> dict[str, Any]:
        result = self.executor.invoke(
            "kodegodot_engine_version", actor="r6-4-acceptance"
        ).result
        if not bool(result.get("compatible_47")):
            raise RuntimeError(f"R6.4 requires Godot 4.7.x, got {result.get('raw')!r}")
        return result

    def _capture_baseline(self) -> dict[str, Any]:
        result = self._capture("r6-baseline.png")
        frame = self._frame("r6-baseline", 1)
        if not frame.is_file() or frame.stat().st_size <= 0:
            raise RuntimeError("Baseline PNG frame was not produced")
        return {
            **result,
            "frame": frame.relative_to(self.workspace).as_posix(),
            "sha256": self._sha256(frame),
            "bytes": frame.stat().st_size,
        }

    def _approve_baseline(self) -> dict[str, Any]:
        frame = self._frame("r6-baseline", 1)
        self.baseline = self.visual.store.approve_baseline(
            case_id="godot-real-render",
            source_path=frame.relative_to(self.workspace).as_posix(),
            approved_by="R6.4 hardware-local acceptance fixture",
            reason="Deterministic fixture baseline generated on the same real-render run",
        )
        return {
            "image_sha256": self.baseline.image.sha256,
            "manifest_sha256": self.baseline.manifest_sha256,
            "artifact": self.baseline.image.path,
        }

    def _capture_current(self) -> dict[str, Any]:
        result = self._capture("r6-current.png")
        frame = self._frame("r6-current", 1)
        if not frame.is_file() or frame.stat().st_size <= 0:
            raise RuntimeError("Current PNG frame was not produced")
        self.render_info = self._parse_render_info(str(result.get("stdout", "")))
        return {
            **result,
            "frame": frame.relative_to(self.workspace).as_posix(),
            "sha256": self._sha256(frame),
            "bytes": frame.stat().st_size,
            "render": dict(self.render_info),
        }

    def _capture(self, output_name: str) -> dict[str, Any]:
        result = self.executor.invoke(
            "kodegodot_capture_png_sequence",
            {
                "scene": "main.tscn",
                "output_name": output_name,
                "frames": 3,
                "fps": 30,
                "timeout": 240,
            },
            actor="r6-4-acceptance",
        ).result
        self._require_ok(result)
        return result

    def _require_real_renderer(self) -> dict[str, str]:
        required = ("rendering_method", "rendering_driver", "video_adapter")
        missing = [key for key in required if not self.render_info.get(key, "").strip()]
        if missing:
            raise RuntimeError(
                "Real-render evidence is incomplete; empty fields are not accepted: "
                + ", ".join(missing)
            )
        lowered = " ".join(self.render_info.values()).lower()
        if "dummy" in lowered or "headless" in lowered:
            raise RuntimeError(f"Headless/dummy renderer is not valid R6.4 evidence: {self.render_info}")
        return dict(self.render_info)

    def _compare(self) -> dict[str, Any]:
        if self.baseline is None:
            raise RuntimeError("Baseline approval step did not complete")
        current = self._frame("r6-current", 1)
        policy = VisualPolicy(
            pixel_delta_threshold=1,
            warn_changed_ratio=0.001,
            fail_changed_ratio=0.01,
            warn_perceptual_ratio=0.05,
            fail_perceptual_ratio=0.15,
        )
        self.visual_report = self.visual.compare(
            case_id="godot-real-render",
            baseline=self.baseline,
            current_path=current.relative_to(self.workspace).as_posix(),
            policy=policy,
        )
        if self.visual_report.status is not VisualStatus.PASS:
            raise RuntimeError(
                f"Real-render VisualQA comparison did not PASS: {self.visual_report.status.value} "
                f"{self.visual_report.reasons}"
            )
        if self.visual_report.diff is None:
            raise RuntimeError("VisualQA PASS did not preserve a diff artifact")
        latest, _snapshot = self.visual.store.save_report(self.visual_report)
        return {
            "status": self.visual_report.status.value,
            "baseline_sha256": self.visual_report.baseline.sha256,
            "current_sha256": self.visual_report.current.sha256,
            "policy_sha256": self.visual_report.policy_sha256,
            "evidence_sha256": self.visual_report.evidence_sha256,
            "changed_ratio": self.visual_report.metrics.changed_ratio,
            "perceptual_distance_ratio": self.visual_report.metrics.perceptual_distance_ratio,
            "diff": self.visual_report.diff.path,
            "report": latest.relative_to(self.workspace).as_posix(),
        }

    def _regression_hook(self) -> dict[str, Any]:
        if self.visual_report is None:
            raise RuntimeError("Visual comparison step did not complete")
        case = KodeVisualQA.to_test_case(self.visual_report)
        if case.status is not TestCaseStatus.PASS:
            raise RuntimeError(f"R6.3 hook did not produce PASS: {case.status.value}")
        if case.id != "visual:godot-real-render":
            raise RuntimeError(f"Unexpected stable visual test ID: {case.id}")
        return {
            "id": case.id,
            "status": case.status.value,
            "evidence_sha256": case.details["evidence_sha256"],
        }

    def _audit_verify(self) -> dict[str, bool]:
        valid = self.executor.audit.verify()
        if not valid:
            raise RuntimeError("R6.4 KodeGodot audit hash chain verification failed")
        return {"valid": True}

    @staticmethod
    def _parse_render_info(stdout: str) -> dict[str, str]:
        mapping = {
            "KODEPOIA_R6_RENDERING_METHOD=": "rendering_method",
            "KODEPOIA_R6_RENDERING_DRIVER=": "rendering_driver",
            "KODEPOIA_R6_VIDEO_ADAPTER=": "video_adapter",
        }
        result: dict[str, str] = {}
        for line in stdout.splitlines():
            stripped = line.strip()
            for prefix, key in mapping.items():
                if stripped.startswith(prefix):
                    result[key] = stripped[len(prefix) :].strip()
        return result

    def _frame(self, stem: str, index: int) -> Path:
        return (
            self.workspace
            / ".kodepoia"
            / "visual_tests"
            / "runs"
            / f"{stem}{index:08d}.png"
        )

    @staticmethod
    def _require_ok(result: dict[str, Any]) -> None:
        if (
            int(result.get("returncode", -1)) != 0
            or bool(result.get("timed_out"))
            or bool(result.get("cancelled"))
        ):
            raise RuntimeError(
                "Godot capture failed: "
                f"rc={result.get('returncode')} timed_out={result.get('timed_out')} "
                f"cancelled={result.get('cancelled')} stderr={str(result.get('stderr', '')).strip()}"
            )

    def _step(self, name: str, action: Callable[[], Any]) -> None:
        started = time.monotonic()
        try:
            details = action()
        except Exception as exc:
            self.steps.append(
                AcceptanceStep(
                    name=name,
                    passed=False,
                    elapsed_seconds=time.monotonic() - started,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            self.steps.append(
                AcceptanceStep(
                    name=name,
                    passed=True,
                    elapsed_seconds=time.monotonic() - started,
                    details=details,
                )
            )

    def _save(self, *, acceptance_completed: bool) -> dict[str, Any]:
        report_path = None
        diff_path = None
        visual_status = None
        baseline_hash = None
        current_hash = None
        evidence_hash = None
        if self.visual_report is not None:
            visual_status = self.visual_report.status.value
            baseline_hash = (
                None if self.visual_report.baseline is None else self.visual_report.baseline.sha256
            )
            current_hash = (
                None if self.visual_report.current is None else self.visual_report.current.sha256
            )
            evidence_hash = self.visual_report.evidence_sha256
            report_path = (
                self.workspace
                / ".kodepoia"
                / "visual_tests"
                / "runs"
                / "godot-real-render"
                / "latest.json"
            )
            if self.visual_report.diff is not None:
                diff_path = self.workspace / self.visual_report.diff.path

        payload = {
            "metadata": {
                "phase": "R6.4-local-acceptance",
                "acceptance_completed": acceptance_completed,
                "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "godot_executable": Path(self.executable).name,
                "fixture": ".kodepoia/r6-4-acceptance/project",
            },
            "render": dict(self.render_info),
            "visual": {
                "status": visual_status,
                "baseline_sha256": baseline_hash,
                "current_sha256": current_hash,
                "evidence_sha256": evidence_hash,
                "report": self._repo_relative(report_path),
                "diff": self._repo_relative(diff_path),
            },
            "steps": [asdict(step) for step in self.steps],
            "summary": {
                "passed": sum(step.passed for step in self.steps),
                "failed": sum(not step.passed for step in self.steps),
                "total": len(self.steps),
            },
        }
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return payload

    def _repo_relative(self, path: Path | None) -> str | None:
        if path is None:
            return None
        return path.resolve(strict=False).relative_to(self.repo_root).as_posix()

    @staticmethod
    def _sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _prepare_fixture(self) -> None:
        if self.workspace.exists():
            shutil.rmtree(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=False)
        (self.workspace / ".kodepoia" / "visual_tests" / "runs").mkdir(
            parents=True, exist_ok=True
        )
        (self.workspace / "project.godot").write_text(
            'config_version=5\n\n'
            '[application]\n'
            'config/name="Kodepoia R6.4 Visual Acceptance"\n'
            'run/main_scene="res://main.tscn"\n\n'
            '[display]\n'
            'window/size/viewport_width=320\n'
            'window/size/viewport_height=180\n'
            'window/size/window_width_override=320\n'
            'window/size/window_height_override=180\n\n'
            '[rendering]\n'
            'renderer/rendering_method="gl_compatibility"\n'
            'renderer/rendering_method.mobile="gl_compatibility"\n',
            encoding="utf-8",
        )
        (self.workspace / "main.gd").write_text(
            'extends Node2D\n\n'
            'func _ready() -> void:\n'
            '    print("KODEPOIA_R6_RENDERING_METHOD=" + RenderingServer.get_current_rendering_method())\n'
            '    print("KODEPOIA_R6_RENDERING_DRIVER=" + RenderingServer.get_current_rendering_driver_name())\n'
            '    print("KODEPOIA_R6_VIDEO_ADAPTER=" + RenderingServer.get_video_adapter_name())\n'
            '    queue_redraw()\n\n'
            'func _draw() -> void:\n'
            '    draw_rect(Rect2(0.0, 0.0, 320.0, 180.0), Color("172033"))\n'
            '    draw_rect(Rect2(24.0, 22.0, 272.0, 44.0), Color("3874cb"))\n'
            '    draw_circle(Vector2(84.0, 124.0), 28.0, Color("f2c14e"))\n'
            '    draw_rect(Rect2(136.0, 96.0, 136.0, 54.0), Color("48a868"))\n'
            '    draw_line(Vector2(146.0, 110.0), Vector2(258.0, 138.0), Color.WHITE, 4.0)\n',
            encoding="utf-8",
        )
        (self.workspace / "main.tscn").write_text(
            '[gd_scene load_steps=2 format=3]\n\n'
            '[ext_resource type="Script" path="res://main.gd" id="1_script"]\n\n'
            '[node name="VisualAcceptance" type="Node2D"]\n'
            'script = ExtResource("1_script")\n',
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kodepoia R6.4 hardware-local acceptance")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--godot", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    runner = R64AcceptanceRunner(
        Path(args.repo_root),
        executable=args.godot,
        output=None if args.output is None else Path(args.output),
    )
    payload = runner.run()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if bool(payload["metadata"]["acceptance_completed"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
