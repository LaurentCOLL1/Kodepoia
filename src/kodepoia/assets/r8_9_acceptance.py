from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from kodepoia.assets.contracts import (
    AssetId,
    AssetKind,
    AssetRevision,
    AssetRole,
    PreservationPolicy,
    ProjectAssetReference,
)
from kodepoia.assets.godot_bridge import (
    GodotAssetBridge,
    GodotAssetClassification,
    GodotRebuildState,
)
from kodepoia.assets.vcs import AssetVcsService
from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.kodegodot.api import GodotToolAPI
from kodepoia.kodegodot.executor import KodeGodotExecutor
from kodepoia.kodegodot.runtime import GodotRuntime

_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class R89AcceptanceStep:
    name: str
    passed: bool
    elapsed_seconds: float
    details: Any = None
    error: str | None = None


class R89LocalAcceptanceRunner:
    """Exact-head hardware-local acceptance for R8.9 Godot import rebuild."""

    def __init__(
        self,
        repo_root: Path,
        *,
        executable: str,
        expected_head: str,
    ) -> None:
        if not _HEAD_RE.fullmatch(expected_head):
            raise ValueError("expected_head must be a lowercase 40-character Git SHA")
        self.repo_root = repo_root.resolve(strict=False)
        self.expected_head = expected_head
        self.executable = str(executable)
        self.workspace = self.repo_root / ".kodepoia" / "acceptance" / "r8-9" / "project"
        self.output = self.repo_root / ".kodepoia" / "acceptance" / "r8-9-local-acceptance.json"
        self.steps: list[R89AcceptanceStep] = []
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
        audit = AuditLog(self.workspace / ".kodepoia" / "audit" / "r8-9-acceptance.jsonl")
        safe_change = SafeChangeManager(
            self.workspace,
            self.workspace / ".kodepoia" / "snapshots",
        )
        self.executor = KodeGodotExecutor(
            self.workspace,
            guardian=guardian,
            audit=audit,
            safe_change=safe_change,
            api=api,
        )
        self.bridge = GodotAssetBridge(self.workspace, self.executor)
        self.reference = self._fixture_reference()

    def run(self) -> dict[str, Any]:
        self._step("exact_head", self._verify_head)
        self._step("classification", self._verify_classification)
        self._step("rebuild", self._rebuild)
        self._step("audit_chain", self._audit_chain)
        completed = all(item.passed for item in self.steps)
        return self._save(completed)

    def _verify_head(self) -> dict[str, str]:
        status = AssetVcsService(WorkspaceBoundary(self.repo_root)).repository_status()
        if status.head_sha != self.expected_head:
            raise RuntimeError(f"Expected exact head {self.expected_head}, got {status.head_sha}")
        return {"head": self.expected_head}

    def _verify_classification(self) -> dict[str, str]:
        checks = {
            "source.svg": self.bridge.classify("source.svg").value,
            "source.svg.import": self.bridge.classify("source.svg.import").value,
            ".godot/imported/cache.ctex": self.bridge.classify(".godot/imported/cache.ctex").value,
            ".import/legacy.cache": self.bridge.classify(".import/legacy.cache").value,
        }
        if checks["source.svg"] != GodotAssetClassification.SOURCE.value:
            raise RuntimeError("Fixture source is not classified as source")
        if checks["source.svg.import"] != GodotAssetClassification.IMPORT_METADATA.value:
            raise RuntimeError("Godot sidecar is not classified as import metadata")
        if checks[".godot/imported/cache.ctex"] != GodotAssetClassification.GENERATED_CACHE.value:
            raise RuntimeError(".godot cache is not classified as generated state")
        if checks[".import/legacy.cache"] != GodotAssetClassification.GENERATED_CACHE.value:
            raise RuntimeError("legacy .import cache is not generated state")
        return checks

    def _rebuild(self) -> dict[str, Any]:
        source = self.workspace / "source.svg"
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        report = self.bridge.rebuild(
            ["source.svg"],
            references=(self.reference,),
            timeout=300.0,
        )
        if report.state is not GodotRebuildState.READY:
            raise RuntimeError(
                f"Godot rebuild state is {report.state.value}: {[item.code for item in report.issues]}"
            )
        after = hashlib.sha256(source.read_bytes()).hexdigest()
        if before != after:
            raise RuntimeError("Preserved source digest changed during rebuild")
        if report.engine_version is None or not report.engine_version.startswith("4.7"):
            raise RuntimeError(f"Unexpected Godot version: {report.engine_version!r}")
        if report.generated_cache_files <= 0:
            raise RuntimeError("No generated Godot cache was observed")
        if not report.sources or report.sources[0].import_settings is None:
            raise RuntimeError("Godot import sidecar evidence is missing")
        if report.manifest_digest is None:
            raise RuntimeError("Rebuild manifest digest is missing")
        if self.bridge.portability_diagnostics((self.reference,)):
            raise RuntimeError("Fixture Vault reference is not portable after rebuild")
        return {
            "report": report.to_dict(),
            "source_sha256": after,
            "source_length": source.stat().st_size,
        }

    def _audit_chain(self) -> dict[str, bool]:
        if not self.executor.audit.verify():
            raise RuntimeError("R8.9 Godot audit chain is invalid")
        return {"valid": True}

    def _fixture_reference(self) -> ProjectAssetReference:
        source = self.workspace / "source.svg"
        data = source.read_bytes()
        asset_id = AssetId.from_seed("r8.9-fixture", "source.svg")
        revision = AssetRevision.create(
            asset_id=asset_id,
            role=AssetRole.SOURCE,
            kind=AssetKind.IMAGE,
            content_sha256=hashlib.sha256(data).hexdigest(),
            content_length=len(data),
            preservation=PreservationPolicy.PINNED_SOURCE,
        )
        return ProjectAssetReference(
            "r8.9-fixture",
            asset_id,
            revision.revision_id,
            "source.svg",
        )

    def _step(self, name: str, action: Callable[[], Any]) -> None:
        started = time.monotonic()
        try:
            details = action()
        except Exception as exc:
            self.steps.append(
                R89AcceptanceStep(
                    name,
                    False,
                    time.monotonic() - started,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            self.steps.append(R89AcceptanceStep(name, True, time.monotonic() - started, details=details))

    def _save(self, completed: bool) -> dict[str, Any]:
        payload = {
            "metadata": {
                "phase": "R8.9-local-acceptance",
                "generated_at": datetime.now(UTC).isoformat(),
                "expected_head": self.expected_head,
                "acceptance_completed": completed,
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "godot_executable": Path(self.executable).name,
                "fixture": ".kodepoia/acceptance/r8-9/project",
            },
            "steps": [asdict(item) for item in self.steps],
            "summary": {
                "passed": sum(item.passed for item in self.steps),
                "failed": sum(not item.passed for item in self.steps),
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
            'config/name="Kodepoia R8.9 Acceptance"\n\n'
            '[rendering]\n'
            'renderer/rendering_method="gl_compatibility"\n'
            'renderer/rendering_method.mobile="gl_compatibility"\n',
            encoding="utf-8",
        )
        (self.workspace / "source.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">\n'
            '  <rect x="0" y="0" width="16" height="16" fill="#ffffff"/>\n'
            '</svg>\n',
            encoding="utf-8",
        )
        legacy = self.workspace / ".import"
        legacy.mkdir()
        (legacy / "legacy.cache").write_text("disposable\n", encoding="utf-8")
