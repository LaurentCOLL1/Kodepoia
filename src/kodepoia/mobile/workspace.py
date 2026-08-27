from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping, Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.project.dna import Platform, ProjectDNA


class MobileWorkspaceOperation(StrEnum):
    STATUS = "status"
    SCAFFOLD = "scaffold"
    BUILD = "build"
    TEST = "test"
    PACKAGE = "package"
    DEVICE = "device"
    COMPLIANCE = "compliance"
    RELEASE = "release"


class MobileWorkspaceState(StrEnum):
    READY = "ready"
    PASS = "pass"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class MobileExecutionContext:
    project_root: Path
    project_name: str
    platforms: tuple[str, ...]
    source_kind: str
    package_kinds: tuple[str, ...]
    release_channel: str
    signing_intent: str
    network_intent: str


@dataclass(frozen=True, slots=True)
class MobileExecutionReceipt:
    state: MobileWorkspaceState
    summary: str
    blockers: tuple[str, ...] = ()
    evidence: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        if self.state not in {
            MobileWorkspaceState.PASS,
            MobileWorkspaceState.BLOCKED,
            MobileWorkspaceState.FAILED,
            MobileWorkspaceState.CANCELLED,
        }:
            raise ValueError("Execution receipt must use a terminal execution state")
        if self.state is MobileWorkspaceState.PASS and self.blockers:
            raise ValueError("PASS execution receipt cannot contain blockers")


class MobileWorkspaceExecutor(Protocol):
    def __call__(
        self,
        operation: MobileWorkspaceOperation,
        context: MobileExecutionContext,
        kill_switch: KillSwitch,
    ) -> MobileExecutionReceipt: ...


@dataclass(frozen=True, slots=True)
class MobileWorkspaceResult:
    schema_version: int
    operation: MobileWorkspaceOperation
    state: MobileWorkspaceState
    project_root: str
    project_name: str | None
    platforms: tuple[str, ...]
    source_kind: str | None
    package_kinds: tuple[str, ...]
    release_channel: str | None
    signing_intent: str | None
    network_intent: str | None
    capability_matrix: tuple[tuple[str, object], ...]
    blockers: tuple[str, ...]
    evidence: tuple[tuple[str, object], ...]
    summary: str

    @property
    def ok(self) -> bool:
        return self.state in {MobileWorkspaceState.READY, MobileWorkspaceState.PASS}

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation.value,
            "state": self.state.value,
            "project_root": self.project_root,
            "project_name": self.project_name,
            "platforms": list(self.platforms),
            "source_kind": self.source_kind,
            "package_kinds": list(self.package_kinds),
            "release_channel": self.release_channel,
            "signing_intent": self.signing_intent,
            "network_intent": self.network_intent,
            "capability_matrix": {key: value for key, value in self.capability_matrix},
            "blockers": list(self.blockers),
            "evidence": {key: value for key, value in self.evidence},
            "summary": self.summary,
        }


class MobileWorkspaceService:
    """Passive R13 status plus explicit structured mobile execution intents.

    Passive status reads only owned Project DNA and bounded JSON evidence. It never
    probes an SDK, launches a process, performs a network request or changes release
    state. Process-backed work requires a trusted injected executor, so callers
    cannot provide executable paths, argv, Gradle/Xcode settings, signing material,
    device shell commands, store tokens or fabricated PASS evidence.
    """

    EVIDENCE_FILES: Mapping[str, str] = {
        "scaffold": ".kodepoia/mobile/evidence/scaffold.json",
        "build": ".kodepoia/mobile/evidence/build.json",
        "test": ".kodepoia/mobile/evidence/test.json",
        "package": ".kodepoia/mobile/evidence/package.json",
        "device": ".kodepoia/mobile/evidence/device.json",
        "compliance": ".kodepoia/mobile/evidence/compliance.json",
        "release": ".kodepoia/mobile/evidence/release.json",
        "diagnostics": ".kodepoia/mobile/evidence/diagnostics.json",
    }
    MAX_EVIDENCE_BYTES = 1_048_576

    def __init__(
        self,
        project_root: Path,
        *,
        executor: MobileWorkspaceExecutor | None = None,
        kill_switch: KillSwitch | None = None,
    ) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.executor = executor
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH

    def status(self) -> MobileWorkspaceResult:
        dna, blockers = self._load_mobile_dna()
        evidence = self._read_passive_evidence()
        if dna is None:
            return self._result(
                MobileWorkspaceOperation.STATUS,
                MobileWorkspaceState.BLOCKED,
                None,
                blockers=blockers,
                evidence=evidence,
                summary="Mobile workspace is blocked until valid mobile Project DNA is available.",
            )
        return self._result(
            MobileWorkspaceOperation.STATUS,
            MobileWorkspaceState.READY,
            dna,
            evidence=evidence,
            summary=(
                "Mobile workspace metadata is ready; passive refresh did not launch, "
                "probe or mutate any external capability."
            ),
        )

    def execute(self, operation: MobileWorkspaceOperation) -> MobileWorkspaceResult:
        if operation is MobileWorkspaceOperation.STATUS:
            return self.status()
        if operation not in {
            MobileWorkspaceOperation.SCAFFOLD,
            MobileWorkspaceOperation.BUILD,
            MobileWorkspaceOperation.TEST,
            MobileWorkspaceOperation.PACKAGE,
            MobileWorkspaceOperation.DEVICE,
            MobileWorkspaceOperation.COMPLIANCE,
            MobileWorkspaceOperation.RELEASE,
        }:
            raise ValueError(f"Unsupported mobile workspace operation: {operation}")

        dna, blockers = self._load_mobile_dna()
        if dna is None:
            return self._result(
                operation,
                MobileWorkspaceState.BLOCKED,
                None,
                blockers=blockers,
                summary=f"Mobile {operation.value} is blocked by Project DNA.",
            )
        if self.kill_switch.triggered:
            return self._result(
                operation,
                MobileWorkspaceState.CANCELLED,
                dna,
                blockers=("KILL_SWITCH_ACTIVE",),
                summary="Global KillSwitch is active; protected mobile execution is cancelled.",
            )
        if self.executor is None:
            return self._result(
                operation,
                MobileWorkspaceState.BLOCKED,
                dna,
                blockers=("EXECUTION_BACKEND_UNAVAILABLE",),
                summary=(
                    f"Mobile {operation.value} requires a governed execution backend; "
                    "the R13 workspace does not expose raw tool or store controls."
                ),
            )

        mobile = dna.mobile
        assert mobile is not None
        context = MobileExecutionContext(
            project_root=self.project_root,
            project_name=dna.name,
            platforms=tuple(
                item.value for item in dna.platforms if item in {Platform.ANDROID, Platform.IOS}
            ),
            source_kind=mobile.source_kind.value,
            package_kinds=tuple(item.value for item in mobile.package_kinds),
            release_channel=mobile.release_channel.value,
            signing_intent=mobile.signing_intent.value,
            network_intent=mobile.network_intent.value,
        )
        try:
            receipt = self.executor(operation, context, self.kill_switch)
        except (OSError, RuntimeError, ValueError) as exc:
            return self._result(
                operation,
                MobileWorkspaceState.FAILED,
                dna,
                blockers=("EXECUTION_FAILED",),
                summary=f"Governed mobile execution failed: {exc}",
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

    def _load_mobile_dna(self) -> tuple[ProjectDNA | None, tuple[str, ...]]:
        path = self.project_root / ".kodepoia" / "project.yaml"
        try:
            self._require_owned_file(path)
            dna = ProjectDNA.load(path)
            dna.validate()
        except FileNotFoundError:
            return None, ("PROJECT_DNA_MISSING",)
        except (OSError, ValueError) as exc:
            return None, (f"PROJECT_DNA_INVALID:{exc}",)
        if dna.mobile is None:
            return None, ("MOBILE_PROFILE_MISSING",)
        if not ({Platform.ANDROID, Platform.IOS} & set(dna.platforms)):
            return None, ("MOBILE_TARGET_MISSING",)
        return dna, ()

    def _capability_matrix(self, dna: ProjectDNA | None) -> tuple[tuple[str, object], ...]:
        dna_ready = dna is not None
        gateway_available = self.executor is not None and not self.kill_switch.triggered
        items: list[tuple[str, object]] = [
            (
                "passive_refresh",
                {
                    "state": "AVAILABLE" if dna_ready else "BLOCKED",
                    "external_process_launch": False,
                    "network_access": False,
                    "read_only": True,
                },
            )
        ]
        for operation in MobileWorkspaceOperation:
            if operation is MobileWorkspaceOperation.STATUS:
                continue
            blockers: list[str] = []
            if not dna_ready:
                blockers.append("PROJECT_DNA_BLOCKED")
            if self.kill_switch.triggered:
                blockers.append("KILL_SWITCH_ACTIVE")
            elif self.executor is None:
                blockers.append("EXECUTION_BACKEND_UNAVAILABLE")
            items.append(
                (
                    operation.value,
                    {
                        "state": "AVAILABLE" if gateway_available and dna_ready else "BLOCKED",
                        "structured_intent_only": True,
                        "blockers": blockers,
                    },
                )
            )
        return tuple(items)

    def _read_passive_evidence(self) -> tuple[tuple[str, object], ...]:
        items: list[tuple[str, object]] = []
        for key, relative in self.EVIDENCE_FILES.items():
            path = self.project_root / relative
            if not path.exists():
                items.append((key, {"available": False, "read_only": True}))
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
                            "evidence_id": (
                                payload.get("evidence_id")
                                or payload.get("run_id")
                                or payload.get("bundle_id")
                            ),
                            "source_digest": payload.get("source_digest"),
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
        operation: MobileWorkspaceOperation,
        state: MobileWorkspaceState,
        dna: ProjectDNA | None,
        *,
        blockers: tuple[str, ...] = (),
        evidence: tuple[tuple[str, object], ...] = (),
        summary: str,
    ) -> MobileWorkspaceResult:
        mobile = dna.mobile if dna is not None else None
        platforms = (
            tuple(item.value for item in dna.platforms if item in {Platform.ANDROID, Platform.IOS})
            if dna is not None
            else ()
        )
        return MobileWorkspaceResult(
            schema_version=1,
            operation=operation,
            state=state,
            project_root=str(self.project_root),
            project_name=dna.name if dna is not None else None,
            platforms=platforms,
            source_kind=mobile.source_kind.value if mobile is not None else None,
            package_kinds=(
                tuple(item.value for item in mobile.package_kinds) if mobile is not None else ()
            ),
            release_channel=mobile.release_channel.value if mobile is not None else None,
            signing_intent=mobile.signing_intent.value if mobile is not None else None,
            network_intent=mobile.network_intent.value if mobile is not None else None,
            capability_matrix=self._capability_matrix(dna),
            blockers=tuple(blockers),
            evidence=tuple(evidence),
            summary=summary,
        )


__all__ = [
    "MobileExecutionContext",
    "MobileExecutionReceipt",
    "MobileWorkspaceExecutor",
    "MobileWorkspaceOperation",
    "MobileWorkspaceResult",
    "MobileWorkspaceService",
    "MobileWorkspaceState",
]
