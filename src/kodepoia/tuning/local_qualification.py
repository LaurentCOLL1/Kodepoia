from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .contracts import CapabilityReport, RuntimeDisposition, RuntimeRequest
from .runtime import TrainingRuntime, redact_runtime_text

_SCHEMA = "kodepoia.r15.16.local-qualification.v1"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class QualificationError(ValueError):
    """Invalid or unsafe R15.16 qualification input."""


class RuntimeProbe(Protocol):
    def probe(self, request: RuntimeRequest) -> CapabilityReport: ...


class SourceProbe(Protocol):
    def head(self, root: Path) -> str: ...


class ToolProbe(Protocol):
    def ollama(self) -> dict[str, object]: ...


class GitSourceProbe:
    """Read only the repository HEAD through a fixed Git invocation."""

    def head(self, root: Path) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise QualificationError("unable to resolve repository HEAD")
        value = result.stdout.strip().lower()
        if _SHA40.fullmatch(value) is None:
            raise QualificationError("repository HEAD is not a full Git SHA")
        return value


class LocalToolProbe:
    """Bounded, non-mutating tool version probes; never accepts caller-provided argv."""

    def ollama(self) -> dict[str, object]:
        executable = shutil.which("ollama")
        if executable is None:
            return {"available": False, "version": None}
        try:
            result = subprocess.run(
                [executable, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {"available": False, "version": None}
        if result.returncode != 0:
            return {"available": False, "version": None}
        combined = result.stdout.strip() or result.stderr.strip()
        return {
            "available": True,
            "version": redact_runtime_text(combined)[:256] or "unknown",
        }


@dataclass(frozen=True, slots=True)
class QualificationPolicy:
    training_required: bool = False
    ollama_required: bool = False

    def to_dict(self) -> dict[str, bool]:
        return {
            "ollama_required": self.ollama_required,
            "training_required": self.training_required,
        }


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _host_descriptor() -> dict[str, str]:
    return {
        "machine": redact_runtime_text(platform.machine())[:128],
        "os": redact_runtime_text(platform.system())[:128],
        "os_release": redact_runtime_text(platform.release())[:128],
        "python_version": platform.python_version(),
    }


def safe_output_path(root: Path, output: Path) -> Path:
    resolved_root = root.resolve(strict=False)
    candidate = output if output.is_absolute() else resolved_root / output
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise QualificationError("output must remain inside the project root") from exc
    return resolved


class LocalQualificationService:
    """R15.16 non-mutating doctor and qualification authority."""

    def __init__(
        self,
        root: Path,
        *,
        runtime: RuntimeProbe | None = None,
        source_probe: SourceProbe | None = None,
        tool_probe: ToolProbe | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.runtime = runtime or TrainingRuntime(self.root)
        self.source_probe = source_probe or GitSourceProbe()
        self.tool_probe = tool_probe or LocalToolProbe()

    def doctor(
        self,
        *,
        expected_source_sha: str,
        runtime_request: RuntimeRequest,
        policy: QualificationPolicy = QualificationPolicy(),
    ) -> dict[str, object]:
        expected = expected_source_sha.strip().lower()
        if _SHA40.fullmatch(expected) is None:
            raise QualificationError("expected_source_sha must be a 40-character lowercase Git SHA")

        actual = self.source_probe.head(self.root)
        if actual != expected:
            return self._finish(
                expected=expected,
                actual=actual,
                policy=policy,
                runtime_report=None,
                tools={"ollama": {"available": False, "version": None}},
                status="blocked",
                result="source_sha_mismatch",
                blockers=("source_sha_mismatch",),
                warnings=(),
            )

        runtime_report = self.runtime.probe(runtime_request)
        tools = {"ollama": self.tool_probe.ollama()}
        blockers: list[str] = []
        warnings: list[str] = []

        if policy.training_required:
            if runtime_report.disposition is RuntimeDisposition.READY:
                result = "training_backend_ready"
            elif runtime_report.disposition is RuntimeDisposition.BUDGET_BLOCKED:
                result = "resource_budget_blocked"
                blockers.append("resource_budget_blocked")
            else:
                result = "training_backend_unavailable"
                blockers.append("training_backend_unavailable")
        else:
            result = "no_train_required"
            if runtime_report.disposition is not RuntimeDisposition.READY:
                warnings.append(f"training_probe:{runtime_report.disposition.value}")

        ollama = tools["ollama"]
        if policy.ollama_required and ollama.get("available") is not True:
            blockers.append("ollama_unavailable")
            if result == "no_train_required":
                result = "ollama_required_unavailable"
        elif not policy.ollama_required and ollama.get("available") is not True:
            warnings.append("ollama_unavailable")

        status = "blocked" if blockers else "pass"
        return self._finish(
            expected=expected,
            actual=actual,
            policy=policy,
            runtime_report=runtime_report,
            tools=tools,
            status=status,
            result=result,
            blockers=tuple(sorted(set(blockers))),
            warnings=tuple(sorted(set(warnings))),
        )

    def _finish(
        self,
        *,
        expected: str,
        actual: str,
        policy: QualificationPolicy,
        runtime_report: CapabilityReport | None,
        tools: dict[str, object],
        status: str,
        result: str,
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "blockers": list(blockers),
            "host": _host_descriptor(),
            "policy": policy.to_dict(),
            "result": result,
            "runtime": None if runtime_report is None else runtime_report.to_dict(),
            "schema": _SCHEMA,
            "source": {
                "actual_sha": actual,
                "expected_sha": expected,
                "match": actual == expected,
            },
            "status": status,
            "tools": tools,
            "warnings": list(warnings),
        }
        payload["report_sha256"] = _digest(payload)
        return payload


def save_report(root: Path, output: Path, report: dict[str, object]) -> Path:
    target = safe_output_path(root, output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
