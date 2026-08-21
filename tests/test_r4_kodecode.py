from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from kodepoia.core.sandbox import SandboxResult
from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool
from kodepoia.kodecode.patch import PatchTool
from kodepoia.kodecode.search import SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation


class FakeSandbox:
    def __init__(self, stdout: str = "") -> None:
        self.stdout = stdout
        self.calls: list[tuple[list[str], Path | None, float]] = []

    def run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        timeout: float = 60.0,
        env: object = None,
    ) -> SandboxResult:
        del env
        self.calls.append((list(argv), cwd, timeout))
        return SandboxResult(returncode=0, stdout=self.stdout, stderr="")


def test_workspace_rejects_absolute_and_parent_escape(tmp_path: Path) -> None:
    boundary = WorkspaceBoundary(tmp_path)

    with pytest.raises(WorkspaceViolation):
        boundary.resolve(str(tmp_path.resolve()))
    with pytest.raises(WorkspaceViolation):
        boundary.resolve("../outside.txt")


def test_files_and_search_are_workspace_scoped(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "sample.py").write_text("alpha\nKodepoia beta\n", encoding="utf-8")

    boundary = WorkspaceBoundary(tmp_path)
    files = FileTool(boundary)
    search = SearchTool(boundary)

    assert files.read_text("src/sample.py") == "alpha\nKodepoia beta\n"
    entries = files.list_entries("src")
    assert [entry.path for entry in entries] == ["src/sample.py"]

    matches = search.search("kodepoia", case_sensitive=False)
    assert len(matches) == 1
    assert matches[0].path == "src/sample.py"
    assert matches[0].line == 2
    assert matches[0].column == 1


def test_patch_is_atomic_guarded_and_unambiguous(tmp_path: Path) -> None:
    target = tmp_path / "app.py"
    target.write_bytes(b"value = 1\r\nnext = 2\r\n")
    patch = PatchTool(WorkspaceBoundary(tmp_path))
    expected = hashlib.sha256(target.read_bytes()).hexdigest()

    result = patch.replace_once(
        "app.py",
        old_text="value = 1",
        new_text="value = 2",
        expected_sha256=expected,
    )
    assert target.read_bytes() == b"value = 2\r\nnext = 2\r\n"
    assert result.before_sha256 == expected
    assert result.replacements == 1

    with pytest.raises(ValueError, match="precondition"):
        patch.replace_once(
            "app.py",
            old_text="value = 2",
            new_text="value = 3",
            expected_sha256=expected,
        )

    target.write_text("x\nx\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        patch.replace_once("app.py", old_text="x", new_text="y")


def test_structured_tool_api_catalog_and_read(tmp_path: Path) -> None:
    (tmp_path / "hello.txt").write_text("hello", encoding="utf-8")
    api = KodeCodeToolAPI(tmp_path)

    names = {item["function"]["name"] for item in api.catalog()}
    assert "kodecode_files_read" in names
    assert "kodecode_patch_replace_once" in names
    assert api.invoke("kodecode_files_read", {"path": "hello.txt"}) == {
        "path": "hello.txt",
        "content": "hello",
    }
    with pytest.raises(KeyError):
        api.invoke("shell")


def test_worktree_porcelain_parser_and_sandbox_dispatch(tmp_path: Path) -> None:
    payload = (
        f"worktree {tmp_path}\0"
        "HEAD abcdef1234\0"
        "branch refs/heads/main\0"
        "worktree M:/Kodepoia/.kodepoia/worktrees/feature\0"
        "HEAD 1234567890\0"
        "branch refs/heads/feature/test\0"
        "locked maintenance\0"
    )
    fake = FakeSandbox(payload)
    tool = GitWorktreeTool(WorkspaceBoundary(tmp_path), sandbox=fake)  # type: ignore[arg-type]

    worktrees = tool.list()
    assert len(worktrees) == 2
    assert worktrees[0].branch == "main"
    assert worktrees[1].branch == "feature/test"
    assert worktrees[1].locked is True
    assert fake.calls[0][0] == ["git", "worktree", "list", "--porcelain", "-z"]


def test_worktree_add_is_confined_and_rejects_option_injection(tmp_path: Path) -> None:
    fake = FakeSandbox()
    tool = GitWorktreeTool(WorkspaceBoundary(tmp_path), sandbox=fake)  # type: ignore[arg-type]

    created = tool.add("task-1", branch="agent/task-1")
    argv = fake.calls[-1][0]
    assert argv[:4] == ["git", "worktree", "add", "-b"]
    assert argv[4] == "agent/task-1"
    assert Path(argv[5]).parent == tmp_path / ".kodepoia" / "worktrees"
    assert created.path == ".kodepoia/worktrees/task-1"

    with pytest.raises(ValueError):
        tool.add("task-2", branch="--force")
