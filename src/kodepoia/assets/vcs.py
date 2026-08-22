from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Iterable

from kodepoia.assets.contracts import AssetRevisionId
from kodepoia.assets.store import VaultStore
from kodepoia.core.audit import AuditLog
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary


class VcsFileState(StrEnum):
    MODIFIED = "modified"
    ADDED = "added"
    DELETED = "deleted"
    RENAMED = "renamed"
    UNTRACKED = "untracked"
    IGNORED = "ignored"
    CONFLICTED = "conflicted"


@dataclass(frozen=True, slots=True)
class VcsFileStatus:
    path: str
    state: VcsFileState
    index_status: str
    worktree_status: str
    original_path: str | None = None


@dataclass(frozen=True, slots=True)
class VcsRepositoryStatus:
    head_sha: str | None
    branch: str | None
    detached: bool
    files: tuple[VcsFileStatus, ...]


@dataclass(frozen=True, slots=True)
class BinaryDiffStat:
    path: str
    staged: bool
    binary: bool
    added_lines: int | None
    deleted_lines: int | None


@dataclass(frozen=True, slots=True)
class AssetVcsEvidence:
    revision_id: AssetRevisionId
    path: str
    tracked: bool
    working_sha256: str
    working_length: int
    matches_revision: bool
    last_commit_sha: str | None


class AssetVcsService:
    """Structured, local-only asset VCS adapter over a fixed Git command surface."""

    _CONFLICT_CODES = {"DD", "AU", "UD", "UA", "DU", "AA", "UU"}

    def __init__(
        self,
        boundary: WorkspaceBoundary,
        *,
        store: VaultStore | None = None,
        sandbox: ProcessSandbox | None = None,
        audit: AuditLog | None = None,
        safe_change: SafeChangeManager | None = None,
    ) -> None:
        self.boundary = boundary
        self.store = store
        self.sandbox = sandbox or ProcessSandbox(boundary.root, {"git", "git.exe"})
        self.audit = audit or AuditLog(boundary.resolve(".kodepoia/audit/asset-vcs.jsonl"))
        self.safe_change = safe_change or SafeChangeManager(
            boundary.root,
            boundary.resolve(".kodepoia/snapshots/asset-vcs"),
        )

    def _run(self, args: list[str], *, allow_failure: bool = False) -> SandboxResult:
        result = self.sandbox.run(["git", *args], cwd=self.boundary.root, timeout=120.0)
        if result.timed_out:
            raise TimeoutError(f"Git operation timed out: {args[0] if args else 'unknown'}")
        if result.cancelled:
            raise RuntimeError("Git operation cancelled by Kodepoia kill switch")
        if result.returncode != 0 and not allow_failure:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise RuntimeError(f"Structured Git operation failed: {detail}")
        return result

    def _path(self, value: str) -> str:
        if not value or "\x00" in value:
            raise ValueError("Git path must be a non-empty relative path")
        path = Path(value)
        if path.is_absolute():
            raise ValueError("Git path must be relative")
        resolved = self.boundary.resolve(path)
        relative = self.boundary.relative(resolved).replace("\\", "/")
        if relative == "." or relative == ".git" or relative.startswith(".git/"):
            raise ValueError("Git metadata paths are not valid asset paths")
        return relative

    def is_repository(self) -> bool:
        result = self._run(["rev-parse", "--is-inside-work-tree"], allow_failure=True)
        return result.returncode == 0 and result.stdout.strip() == "true"

    def repository_status(self) -> VcsRepositoryStatus:
        head_result = self._run(["rev-parse", "--verify", "HEAD"], allow_failure=True)
        head = head_result.stdout.strip() if head_result.returncode == 0 else None
        branch_result = self._run(["symbolic-ref", "--quiet", "--short", "HEAD"], allow_failure=True)
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
        payload = self._run(
            ["status", "--porcelain=v1", "-z", "--ignored=matching", "--untracked-files=all"]
        ).stdout
        return VcsRepositoryStatus(head, branch, branch is None and head is not None, tuple(self._parse_status(payload)))

    @classmethod
    def _state(cls, code: str) -> VcsFileState:
        if code == "??":
            return VcsFileState.UNTRACKED
        if code == "!!":
            return VcsFileState.IGNORED
        if code in cls._CONFLICT_CODES or "U" in code:
            return VcsFileState.CONFLICTED
        if "D" in code:
            return VcsFileState.DELETED
        if "R" in code or "C" in code:
            return VcsFileState.RENAMED
        if "A" in code:
            return VcsFileState.ADDED
        return VcsFileState.MODIFIED

    @classmethod
    def _parse_status(cls, payload: str) -> list[VcsFileStatus]:
        tokens = payload.split("\x00")
        result: list[VcsFileStatus] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            index += 1
            if not token:
                continue
            if len(token) < 4 or token[2] != " ":
                raise ValueError(f"Unexpected Git porcelain record: {token!r}")
            code = token[:2]
            path = token[3:].replace("\\", "/")
            original: str | None = None
            if ("R" in code or "C" in code) and index < len(tokens):
                original = tokens[index].replace("\\", "/")
                index += 1
            result.append(VcsFileStatus(path, cls._state(code), code[0], code[1], original))
        return sorted(result, key=lambda item: (item.path, item.state.value))

    def diff_stat(self, path: str, *, staged: bool = False) -> BinaryDiffStat:
        relative = self._path(path)
        args = ["diff"]
        if staged:
            args.append("--cached")
        args.extend(["--no-ext-diff", "--numstat", "--", relative])
        output = self._run(args).stdout.strip("\r\n")
        if not output:
            return BinaryDiffStat(relative, staged, False, 0, 0)
        first = output.splitlines()[0]
        added, deleted, _ = first.split("\t", 2)
        binary = added == "-" and deleted == "-"
        return BinaryDiffStat(
            relative,
            staged,
            binary,
            None if binary else int(added),
            None if binary else int(deleted),
        )

    def _snapshot_index(self) -> str | None:
        result = self._run(["rev-parse", "--git-path", "index"])
        raw = result.stdout.strip()
        path = Path(raw)
        if not path.is_absolute():
            path = self.boundary.root / path
        try:
            resolved = self.safe_change.ensure_inside_project(path)
        except ValueError as exc:
            raise PermissionError("Git index escapes authorized project root") from exc
        snapshot = self.safe_change.snapshot([resolved])
        return self.boundary.relative(snapshot).replace("\\", "/")

    def _validated_paths(self, paths: Iterable[str]) -> list[str]:
        values = [self._path(item) for item in paths]
        if not values:
            raise ValueError("At least one explicit path is required")
        if len(values) > 100:
            raise ValueError("At most 100 paths may be mutated per operation")
        return list(dict.fromkeys(values))

    def stage(self, paths: Iterable[str], *, actor: str = "user") -> str | None:
        values = self._validated_paths(paths)
        snapshot = self._snapshot_index()
        try:
            self._run(["add", "--", *values])
        except Exception:
            self.audit.append("asset_vcs", "stage", actor, "failure", {"paths": values, "snapshot": snapshot})
            raise
        self.audit.append("asset_vcs", "stage", actor, "success", {"paths": values, "snapshot": snapshot})
        return snapshot

    def unstage(self, paths: Iterable[str], *, actor: str = "user") -> str | None:
        values = self._validated_paths(paths)
        snapshot = self._snapshot_index()
        try:
            self._run(["restore", "--staged", "--", *values])
        except Exception:
            self.audit.append("asset_vcs", "unstage", actor, "failure", {"paths": values, "snapshot": snapshot})
            raise
        self.audit.append("asset_vcs", "unstage", actor, "success", {"paths": values, "snapshot": snapshot})
        return snapshot

    @staticmethod
    def _hash(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
                total += len(chunk)
        return digest.hexdigest(), total

    def asset_evidence(self, revision_id: AssetRevisionId, path: str) -> AssetVcsEvidence:
        if self.store is None:
            raise RuntimeError("Asset VCS evidence requires a VaultStore")
        relative = self._path(path)
        working_path = self.boundary.resolve(relative, must_exist=True)
        if not working_path.is_file():
            raise ValueError("Asset VCS evidence requires a file")
        revision = self.store._load_revision_manifest(revision_id)
        digest, length = self._hash(working_path)
        tracked_result = self._run(["ls-files", "--error-unmatch", "--", relative], allow_failure=True)
        tracked = tracked_result.returncode == 0
        commit_result = self._run(["log", "-1", "--format=%H", "--", relative], allow_failure=True)
        commit_sha = commit_result.stdout.strip() if commit_result.returncode == 0 and commit_result.stdout.strip() else None
        return AssetVcsEvidence(
            revision_id,
            relative,
            tracked,
            digest,
            length,
            digest == revision.content_sha256 and length == revision.content_length,
            commit_sha,
        )
