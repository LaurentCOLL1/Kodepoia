from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from kodepoia.core.sandbox import ProcessSandbox, SandboxResult
from kodepoia.kodecode.workspace import WorkspaceBoundary


@dataclass(frozen=True, slots=True)
class WorktreeInfo:
    path: str
    head: str | None = None
    branch: str | None = None
    detached: bool = False
    locked: bool = False
    prunable: bool = False


class GitWorktreeTool:
    """Manage linked Git worktrees through ProcessSandbox only."""

    _NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
    _REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")

    def __init__(
        self,
        boundary: WorkspaceBoundary,
        sandbox: ProcessSandbox | None = None,
    ) -> None:
        self.boundary = boundary
        self.sandbox = sandbox or ProcessSandbox(boundary.root, {"git", "git.exe"})
        self.worktree_root = boundary.resolve(".kodepoia/worktrees")

    def list(self) -> list[WorktreeInfo]:
        result = self._run(["git", "worktree", "list", "--porcelain", "-z"])
        return self._parse_porcelain(result.stdout)

    def add(
        self,
        name: str,
        *,
        branch: str | None = None,
        start_point: str = "HEAD",
        detach: bool = False,
    ) -> WorktreeInfo:
        self._validate_name(name)
        self._validate_ref(start_point, field="start_point")
        if branch is not None:
            self._validate_ref(branch, field="branch")
        if branch is not None and detach:
            raise ValueError("branch and detach are mutually exclusive")

        self.worktree_root.mkdir(parents=True, exist_ok=True)
        destination = self.worktree_root / name
        if destination.exists():
            raise FileExistsError(destination)

        argv = ["git", "worktree", "add"]
        if detach:
            argv.append("--detach")
        elif branch is not None:
            argv.extend(["-b", branch])
        argv.extend([str(destination), start_point])
        self._run(argv)

        resolved = destination.resolve(strict=False)
        return WorktreeInfo(path=self.boundary.relative(resolved), branch=branch, detached=detach)

    def remove(self, name: str) -> None:
        self._validate_name(name)
        destination = (self.worktree_root / name).resolve(strict=False)
        if destination != self.worktree_root and self.worktree_root not in destination.parents:
            raise PermissionError("Worktree path escapes managed root")
        self._run(["git", "worktree", "remove", str(destination)])

    def _run(self, argv: list[str]) -> SandboxResult:
        result = self.sandbox.run(argv, cwd=self.boundary.root, timeout=120.0)
        if result.timed_out:
            raise TimeoutError(f"Git command timed out: {argv[1:]}")
        if result.cancelled:
            raise RuntimeError("Git command cancelled by Kodepoia kill switch")
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise RuntimeError(f"Git worktree command failed: {detail}")
        return result

    @classmethod
    def _validate_name(cls, value: str) -> None:
        if not cls._NAME_RE.fullmatch(value) or value in {".", ".."}:
            raise ValueError(f"Invalid managed worktree name: {value!r}")

    @classmethod
    def _validate_ref(cls, value: str, *, field: str) -> None:
        if (
            not cls._REF_RE.fullmatch(value)
            or value.startswith("-")
            or ".." in value
            or "//" in value
            or "@{" in value
            or value.endswith("/")
        ):
            raise ValueError(f"Invalid Git {field}: {value!r}")

    @staticmethod
    def _parse_porcelain(payload: str) -> list[WorktreeInfo]:
        records: list[dict[str, str | bool]] = []
        current: dict[str, str | bool] | None = None
        for token in payload.split("\0"):
            if not token:
                continue
            if token.startswith("worktree "):
                if current is not None:
                    records.append(current)
                current = {"path": token.removeprefix("worktree ")}
                continue
            if current is None:
                continue
            key, separator, value = token.partition(" ")
            current[key] = value if separator else True
        if current is not None:
            records.append(current)

        result: list[WorktreeInfo] = []
        for item in records:
            branch_value = item.get("branch")
            branch = str(branch_value).removeprefix("refs/heads/") if branch_value else None
            result.append(
                WorktreeInfo(
                    path=str(item["path"]),
                    head=str(item["HEAD"]) if item.get("HEAD") else None,
                    branch=branch,
                    detached=bool(item.get("detached", False)),
                    locked=bool(item.get("locked", False)),
                    prunable=bool(item.get("prunable", False)),
                )
            )
        return result
