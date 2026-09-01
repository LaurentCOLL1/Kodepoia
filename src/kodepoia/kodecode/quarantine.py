from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from kodepoia.exceptions import PolicyDenied
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation


class WorkspaceTrustState(StrEnum):
    QUARANTINED = "quarantined"
    APPROVED = "approved"
    BLOCKED = "blocked"


class WorkspaceOperation(StrEnum):
    READ = "read"
    INDEX = "index"
    PARSE = "parse"
    WRITE = "write"
    EXECUTE = "execute"
    INSTALL = "install"
    NETWORK = "network"


class FindingSeverity(StrEnum):
    INFO = "info"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_READ_ONLY_OPERATIONS = frozenset(
    {WorkspaceOperation.READ, WorkspaceOperation.INDEX, WorkspaceOperation.PARSE}
)
_ARCHIVE_SUFFIXES = frozenset({".zip", ".tar", ".tgz", ".tbz", ".tbz2", ".txz", ".7z", ".rar"})
_SCRIPT_SUFFIXES = frozenset({".sh", ".bash", ".zsh", ".fish", ".bat", ".cmd", ".ps1", ".psm1"})
_EXECUTABLE_SUFFIXES = frozenset({".exe", ".com", ".msi", ".dll", ".dylib", ".so", ".appimage"})
_INSTRUCTION_NAMES = frozenset(
    {"agents.md", "claude.md", "copilot-instructions.md", "instructions.md"}
)
_TASK_NAMES = frozenset(
    {
        "makefile",
        "justfile",
        "taskfile.yml",
        "taskfile.yaml",
        "package.json",
        "pyproject.toml",
        "project.godot",
        "plugin.cfg",
    }
)
_EXTERNAL_RE = re.compile(rb"(?:https?|ssh|git)://|git@", re.I)
_POLICY_WIDEN_RE = re.compile(
    rb"(?:hooksPath|safe\.directory|shell\s*=|permissions?\s*=|network\s*=|post[_ -]?open)",
    re.I,
)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class WorkspaceRiskFinding:
    id: str
    kind: str
    severity: FindingSeverity
    path: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": self.kind,
            "severity": self.severity.value,
            "path": self.path,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class WorkspaceRiskSummary:
    workspace_fingerprint: str
    state: WorkspaceTrustState
    scanned_files: int
    scanned_bytes: int
    findings: tuple[WorkspaceRiskFinding, ...]
    approved_fingerprint: str | None = None
    schema_version: int = 1

    @property
    def critical_veto(self) -> bool:
        return any(item.severity is FindingSeverity.CRITICAL for item in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workspace_fingerprint": self.workspace_fingerprint,
            "state": self.state.value,
            "scanned_files": self.scanned_files,
            "scanned_bytes": self.scanned_bytes,
            "critical_veto": self.critical_veto,
            "approved_fingerprint": self.approved_fingerprint,
            "findings": [item.to_dict() for item in self.findings],
        }

    @property
    def semantic_sha256(self) -> str:
        return _sha256_bytes(_canonical_json(self.to_dict()))


class WorkspacePreflight:
    """Read-only malicious-workspace preflight.

    It never executes repository-controlled commands and never persists approval
    into the repository. Approval is bound to the exact content fingerprint.
    """

    def __init__(
        self,
        root: Path,
        *,
        max_files: int = 100_000,
        max_bytes: int = 256 * 1024 * 1024,
    ) -> None:
        if max_files < 1 or max_bytes < 1:
            raise ValueError("preflight bounds must be positive")
        self.boundary = WorkspaceBoundary(root)
        self.max_files = max_files
        self.max_bytes = max_bytes

    def inspect(self, *, approved_fingerprint: str | None = None) -> WorkspaceRiskSummary:
        entries: list[dict[str, Any]] = []
        findings: list[WorkspaceRiskFinding] = []
        scanned_files = 0
        scanned_bytes = 0

        for path in self._iter_workspace_entries():
            relative = self._lexical_relative(path)
            lowered = relative.lower()
            name = path.name.lower()

            if path.is_symlink():
                target = os.readlink(path)
                try:
                    resolved = path.resolve(strict=False)
                    self.boundary.relative(resolved)
                except (WorkspaceViolation, OSError):
                    findings.append(
                        WorkspaceRiskFinding(
                            "R16.3.WS.SYMLINK_ESCAPE",
                            "workspace-escape",
                            FindingSeverity.CRITICAL,
                            relative,
                            "symlink resolves outside the workspace boundary",
                        )
                    )
                else:
                    findings.append(
                        WorkspaceRiskFinding(
                            "R16.3.WS.SYMLINK",
                            "symlink",
                            FindingSeverity.MEDIUM,
                            relative,
                            "symlink retained as non-authoritative workspace metadata",
                        )
                    )
                entries.append(
                    {
                        "path": relative,
                        "type": "symlink",
                        "target_sha256": _sha256_bytes(target.encode("utf-8", "surrogatepass")),
                    }
                )
                scanned_files += 1
                if scanned_files > self.max_files:
                    return self._bounded_failure(
                        entries, findings, scanned_files, scanned_bytes, "file-count"
                    )
                continue

            if not path.is_file():
                continue

            size = path.stat().st_size
            scanned_files += 1
            if scanned_files > self.max_files or scanned_bytes + size > self.max_bytes:
                return self._bounded_failure(
                    entries,
                    findings,
                    scanned_files,
                    scanned_bytes,
                    "file-count" if scanned_files > self.max_files else "byte-count",
                )

            content_hash = hashlib.sha256()
            sample = bytearray()
            with path.open("rb") as handle:
                while chunk := handle.read(1024 * 1024):
                    content_hash.update(chunk)
                    scanned_bytes += len(chunk)
                    if len(sample) < 65_536:
                        sample.extend(chunk[: 65_536 - len(sample)])

            entries.append(
                {
                    "path": relative,
                    "type": "file",
                    "size": size,
                    "sha256": content_hash.hexdigest(),
                }
            )
            findings.extend(self._classify(relative, lowered, name, bytes(sample)))

        fingerprint = _sha256_bytes(_canonical_json(entries))
        critical = any(item.severity is FindingSeverity.CRITICAL for item in findings)
        if critical:
            state = WorkspaceTrustState.BLOCKED
        elif approved_fingerprint is not None and approved_fingerprint.lower() == fingerprint:
            state = WorkspaceTrustState.APPROVED
        else:
            state = WorkspaceTrustState.QUARANTINED
        return WorkspaceRiskSummary(
            workspace_fingerprint=fingerprint,
            state=state,
            scanned_files=scanned_files,
            scanned_bytes=scanned_bytes,
            findings=tuple(sorted(findings, key=lambda item: (item.path, item.id))),
            approved_fingerprint=approved_fingerprint.lower() if approved_fingerprint else None,
        )

    def require(
        self,
        operation: WorkspaceOperation,
        *,
        approved_fingerprint: str | None = None,
    ) -> WorkspaceRiskSummary:
        summary = self.inspect(approved_fingerprint=approved_fingerprint)
        if operation in _READ_ONLY_OPERATIONS:
            return summary
        if summary.state is WorkspaceTrustState.BLOCKED:
            raise PolicyDenied(
                f"Workspace operation {operation.value} denied: critical preflight finding"
            )
        if summary.state is not WorkspaceTrustState.APPROVED:
            raise PolicyDenied(
                f"Workspace operation {operation.value} denied while workspace is quarantined; "
                f"approve fingerprint {summary.workspace_fingerprint}"
            )
        return summary

    def _iter_workspace_entries(self) -> list[Path]:
        root = self.boundary.root
        result: list[Path] = []
        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            relative_current = current_path.relative_to(root)
            if relative_current == Path(".git"):
                dirs[:] = ["hooks"] if "hooks" in dirs else []
                files[:] = [name for name in files if name == "config"]
            else:
                dirs[:] = sorted(
                    name
                    for name in dirs
                    if name not in {".kodepoia", "__pycache__", ".pytest_cache", ".ruff_cache"}
                )
            for name in sorted(files):
                result.append(current_path / name)
            for name in sorted(dirs):
                candidate = current_path / name
                if candidate.is_symlink():
                    result.append(candidate)
        return sorted(result, key=self._lexical_relative)

    def _lexical_relative(self, path: Path) -> str:
        return path.relative_to(self.boundary.root).as_posix()

    def _classify(
        self,
        relative: str,
        lowered: str,
        name: str,
        sample: bytes,
    ) -> list[WorkspaceRiskFinding]:
        suffix = Path(name).suffix.lower()
        found: list[WorkspaceRiskFinding] = []

        def add(identifier: str, kind: str, severity: FindingSeverity, note: str) -> None:
            found.append(WorkspaceRiskFinding(identifier, kind, severity, relative, note))

        if lowered.startswith(".git/hooks/") and not name.endswith(".sample"):
            add(
                "R16.3.WS.GIT_HOOK",
                "repository-hook",
                FindingSeverity.HIGH,
                "repository hook discovered; never authoritative during bootstrap",
            )
        if suffix in _SCRIPT_SUFFIXES or suffix in _EXECUTABLE_SUFFIXES:
            add(
                "R16.3.WS.EXECUTABLE_BAIT",
                "executable-file",
                FindingSeverity.HIGH,
                "executable or script discovered; execution requires exact-fingerprint approval",
            )
        if name in _TASK_NAMES or lowered.endswith("/.vscode/tasks.json"):
            add(
                "R16.3.WS.TASK_METADATA",
                "task-metadata",
                FindingSeverity.MEDIUM,
                "task/build/project metadata discovered as non-authoritative data",
            )
        if name in _INSTRUCTION_NAMES or name.startswith("readme"):
            add(
                "R16.3.WS.INSTRUCTIONS",
                "project-instructions",
                FindingSeverity.MEDIUM,
                "project instructions are readable data and cannot grant authority",
            )
        if "/addons/" in f"/{lowered}" and suffix == ".gd":
            add(
                "R16.3.WS.GODOT_EDITOR_CODE",
                "godot-editor-code",
                FindingSeverity.HIGH,
                "Godot addon/editor script discovered and quarantined from execution",
            )
        if suffix in _ARCHIVE_SUFFIXES:
            add(
                "R16.3.WS.ARCHIVE",
                "archive",
                FindingSeverity.MEDIUM,
                "archive is not expanded during bootstrap",
            )
        if name == ".gitmodules":
            add(
                "R16.3.WS.SUBMODULE",
                "external-reference",
                FindingSeverity.HIGH,
                "submodule metadata discovered; external content remains quarantined",
            )
        if name == ".gitattributes" and b"filter=lfs" in sample.lower():
            add(
                "R16.3.WS.LFS",
                "external-reference",
                FindingSeverity.MEDIUM,
                "Git LFS reference discovered; external content remains quarantined",
            )
        if _EXTERNAL_RE.search(sample) and name in {
            ".gitmodules",
            "project.godot",
            "package.json",
            "pyproject.toml",
            "plugin.cfg",
        }:
            add(
                "R16.3.WS.EXTERNAL_REFERENCE",
                "external-reference",
                FindingSeverity.HIGH,
                "external reference discovered; destination omitted from risk evidence",
            )
        if _POLICY_WIDEN_RE.search(sample) and name in {
            "config",
            "package.json",
            "pyproject.toml",
            "project.godot",
            "tasks.json",
        }:
            add(
                "R16.3.WS.PERMISSION_WIDENING",
                "permission-metadata",
                FindingSeverity.HIGH,
                "repository-controlled metadata requests privileged behavior; request is non-authoritative",
            )
        return found

    def _bounded_failure(
        self,
        entries: list[dict[str, Any]],
        findings: list[WorkspaceRiskFinding],
        scanned_files: int,
        scanned_bytes: int,
        bound: str,
    ) -> WorkspaceRiskSummary:
        findings.append(
            WorkspaceRiskFinding(
                "R16.3.WS.BOUNDS",
                "resource-bound",
                FindingSeverity.CRITICAL,
                ".",
                f"preflight {bound} bound exceeded",
            )
        )
        fingerprint = _sha256_bytes(_canonical_json(entries))
        return WorkspaceRiskSummary(
            workspace_fingerprint=fingerprint,
            state=WorkspaceTrustState.BLOCKED,
            scanned_files=scanned_files,
            scanned_bytes=scanned_bytes,
            findings=tuple(sorted(findings, key=lambda item: (item.path, item.id))),
        )


class QuarantinedKodeCodeExecutor:
    """Gate an existing KodeCodeExecutor behind exact-fingerprint workspace trust."""

    def __init__(
        self,
        executor: Any,
        *,
        preflight: WorkspacePreflight | None = None,
        approved_fingerprint: str | None = None,
    ) -> None:
        self.executor = executor
        root = Path(executor.root)
        self.preflight = preflight or WorkspacePreflight(root)
        self.approved_fingerprint = approved_fingerprint.lower() if approved_fingerprint else None

    def inspect(self) -> WorkspaceRiskSummary:
        return self.preflight.inspect(approved_fingerprint=self.approved_fingerprint)

    def approve(self, fingerprint: str) -> WorkspaceRiskSummary:
        candidate = fingerprint.strip().lower()
        current = self.preflight.inspect()
        if current.state is WorkspaceTrustState.BLOCKED:
            raise PolicyDenied("Critical workspace finding cannot be approved")
        if candidate != current.workspace_fingerprint:
            raise PolicyDenied("Workspace approval fingerprint does not match current content")
        self.approved_fingerprint = candidate
        return self.inspect()

    def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        policy = self.executor.policy(tool_name)
        effect = str(policy.effect.value)
        operation = {
            "read": WorkspaceOperation.READ,
            "write": WorkspaceOperation.WRITE,
            "execute": WorkspaceOperation.EXECUTE,
        }.get(effect)
        if operation is None:
            raise PolicyDenied(f"Unknown KodeCode tool effect: {effect}")
        self.preflight.require(
            operation,
            approved_fingerprint=self.approved_fingerprint,
        )
        return self.executor.invoke(tool_name, arguments, **kwargs)
