from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Callable, Mapping, Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.project.dna import ProjectDNA, ProjectType


class DesktopWorkspaceOperation(StrEnum):
    STATUS = "status"
    SCAFFOLD = "scaffold"
    VALIDATE = "validate"
    BUILD = "build"
    TEST = "test"
    PACKAGE = "package"


class DesktopWorkspaceState(StrEnum):
    READY = "ready"
    PASS = "pass"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class DesktopExecutionContext:
    project_root: Path
    project_name: str
    framework: str
    architecture: str
    package_kind: str


@dataclass(frozen=True, slots=True)
class DesktopExecutionReceipt:
    state: DesktopWorkspaceState
    summary: str
    blockers: tuple[str, ...] = ()
    evidence: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        if self.state not in {
            DesktopWorkspaceState.PASS,
            DesktopWorkspaceState.BLOCKED,
            DesktopWorkspaceState.FAILED,
            DesktopWorkspaceState.CANCELLED,
        }:
            raise ValueError("Execution receipt must use a terminal execution state")
        if self.state is DesktopWorkspaceState.PASS and self.blockers:
            raise ValueError("PASS execution receipt cannot contain blockers")


class DesktopWorkspaceExecutor(Protocol):
    def __call__(
        self,
        operation: DesktopWorkspaceOperation,
        context: DesktopExecutionContext,
        kill_switch: KillSwitch,
    ) -> DesktopExecutionReceipt: ...


@dataclass(frozen=True, slots=True)
class DesktopWorkspaceResult:
    schema_version: int
    operation: DesktopWorkspaceOperation
    state: DesktopWorkspaceState
    project_root: str
    project_name: str | None
    framework: str | None
    architecture: str | None
    package_kind: str | None
    blockers: tuple[str, ...]
    evidence: tuple[tuple[str, object], ...]
    summary: str

    @property
    def ok(self) -> bool:
        return self.state in {DesktopWorkspaceState.READY, DesktopWorkspaceState.PASS}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation.value,
            "state": self.state.value,
            "project_root": self.project_root,
            "project_name": self.project_name,
            "framework": self.framework,
            "architecture": self.architecture,
            "package_kind": self.package_kind,
            "blockers": list(self.blockers),
            "evidence": {key: value for key, value in self.evidence},
            "summary": self.summary,
        }


class DesktopWorkspaceService:
    """Read-only status plus explicit governed R12 desktop execution intents.

    `status()` and `validate()` never launch an external process. Mutating or
    process-backed operations require a trusted, injected executor; no raw
    executable, argv, shell, SQL, signing key or model-supplied command reaches
    this service.
    """

    EVIDENCE_FILES: Mapping[str, str] = {
        "build": ".kodepoia/desktop/evidence/build.json",
        "test": ".kodepoia/desktop/evidence/test.json",
        "package": ".kodepoia/desktop/evidence/package.json",
    }
    MAX_EVIDENCE_BYTES = 1_048_576

    def __init__(
        self,
        project_root: Path,
        *,
        executor: DesktopWorkspaceExecutor | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.executor = executor
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH

    def status(self) -> DesktopWorkspaceResult:
        dna, blockers = self._load_desktop_dna()
        evidence = self._read_passive_evidence()
        if dna is None:
            return self._result(
                DesktopWorkspaceOperation.STATUS,
                DesktopWorkspaceState.BLOCKED,
                None,
                blockers=blockers,
                evidence=evidence,
                summary="Desktop workspace is blocked until valid desktop Project DNA is available.",
            )
        return self._result(
            DesktopWorkspaceOperation.STATUS,
            DesktopWorkspaceState.READY,
            dna,
            evidence=evidence,
            summary="Desktop workspace metadata is ready; execution capabilities have not been probed by refresh.",
        )

    def validate(self) -> DesktopWorkspaceResult:
        dna, blockers = self._load_desktop_dna()
        if dna is None:
            return self._result(
                DesktopWorkspaceOperation.VALIDATE,
                DesktopWorkspaceState.BLOCKED,
                None,
                blockers=blockers,
                summary="Desktop Project DNA validation is blocked.",
            )
        return self._result(
            DesktopWorkspaceOperation.VALIDATE,
            DesktopWorkspaceState.PASS,
            dna,
            summary="Desktop Project DNA is valid.",
        )

    def execute(self, operation: DesktopWorkspaceOperation) -> DesktopWorkspaceResult:
        if operation is DesktopWorkspaceOperation.STATUS:
            return self.status()
        if operation is DesktopWorkspaceOperation.VALIDATE:
            return self.validate()
        if operation not in {
            DesktopWorkspaceOperation.SCAFFOLD,
            DesktopWorkspaceOperation.BUILD,
            DesktopWorkspaceOperation.TEST,
            DesktopWorkspaceOperation.PACKAGE,
        }:
            raise ValueError(f"Unsupported desktop workspace operation: {operation}")

        dna, blockers = self._load_desktop_dna()
        if dna is None:
            return self._result(
                operation,
                DesktopWorkspaceState.BLOCKED,
                None,
                blockers=blockers,
                summary=f"Desktop {operation.value} is blocked by Project DNA.",
            )
        if self.kill_switch.triggered:
            return self._result(
                operation,
                DesktopWorkspaceState.CANCELLED,
                dna,
                blockers=("KILL_SWITCH_ACTIVE",),
                summary="Global KillSwitch is active; protected execution is cancelled.",
            )
        if self.executor is None:
            return self._result(
                operation,
                DesktopWorkspaceState.BLOCKED,
                dna,
                blockers=("EXECUTION_BACKEND_UNAVAILABLE",),
                summary=(
                    f"Desktop {operation.value} requires a governed execution backend; "
                    "passive status never installs, restores, builds or runs tools."
                ),
            )

        desktop = dna.desktop
        assert desktop is not None
        context = DesktopExecutionContext(
            project_root=self.project_root,
            project_name=dna.name,
            framework=desktop.framework.value,
            architecture=desktop.architecture.value,
            package_kind=desktop.package_kind.value,
        )
        try:
            receipt = self.executor(operation, context, self.kill_switch)
        except (OSError, RuntimeError, ValueError) as exc:
            return self._result(
                operation,
                DesktopWorkspaceState.FAILED,
                dna,
                blockers=("EXECUTION_FAILED",),
                summary=f"Governed desktop execution failed: {exc}",
            )
        return self._result(
            operation,
            receipt.state,
            dna,
            blockers=receipt.blockers,
            evidence=receipt.evidence,
            summary=receipt.summary,
        )

    def cancel(self) -> int:
        return self.kill_switch.trigger()

    def _load_desktop_dna(self) -> tuple[ProjectDNA | None, tuple[str, ...]]:
        path = self.project_root / ".kodepoia" / "project.yaml"
        try:
            self._require_owned_file(path)
            dna = ProjectDNA.load(path)
            dna.validate()
        except FileNotFoundError:
            return None, ("PROJECT_DNA_MISSING",)
        except (OSError, ValueError) as exc:
            return None, (f"PROJECT_DNA_INVALID:{exc}",)
        if dna.project_type is not ProjectType.DESKTOP_APP:
            return None, ("PROJECT_NOT_DESKTOP_APP",)
        if dna.desktop is None:
            return None, ("DESKTOP_PROFILE_MISSING",)
        return dna, ()

    def _read_passive_evidence(self) -> tuple[tuple[str, object], ...]:
        items: list[tuple[str, object]] = []
        for key, relative in self.EVIDENCE_FILES.items():
            path = self.project_root / relative
            if not path.exists():
                items.append((key, {"available": False}))
                continue
            try:
                self._require_owned_file(path)
                size = path.stat().st_size
                if size > self.MAX_EVIDENCE_BYTES:
                    raise ValueError("evidence file exceeds passive-read limit")
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("evidence payload must be a JSON object")
                items.append(
                    (
                        key,
                        {
                            "available": True,
                            "read_only": True,
                            "reported_status": payload.get("status"),
                            "evidence_id": payload.get("evidence_id") or payload.get("run_id"),
                        },
                    )
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                items.append(
                    (
                        key,
                        {
                            "available": False,
                            "read_only": True,
                            "error": str(exc),
                        },
                    )
                )
        return tuple(items)

    def _require_owned_file(self, path: Path) -> None:
        if path.is_symlink():
            raise ValueError("workspace metadata/evidence symlink is not allowed")
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError("workspace metadata/evidence escapes project root") from exc
        if not resolved.is_file():
            raise ValueError("workspace metadata/evidence must be a regular file")

    def _result(
        self,
        operation: DesktopWorkspaceOperation,
        state: DesktopWorkspaceState,
        dna: ProjectDNA | None,
        *,
        blockers: tuple[str, ...] = (),
        evidence: tuple[tuple[str, object], ...] = (),
        summary: str,
    ) -> DesktopWorkspaceResult:
        desktop = dna.desktop if dna is not None else None
        return DesktopWorkspaceResult(
            schema_version=1,
            operation=operation,
            state=state,
            project_root=str(self.project_root),
            project_name=dna.name if dna is not None else None,
            framework=desktop.framework.value if desktop is not None else None,
            architecture=desktop.architecture.value if desktop is not None else None,
            package_kind=desktop.package_kind.value if desktop is not None else None,
            blockers=tuple(blockers),
            evidence=tuple(evidence),
            summary=summary,
        )
