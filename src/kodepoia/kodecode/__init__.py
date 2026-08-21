"""KodeCode: safe, structured source-code tooling for Kodepoia."""

from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool, WorktreeInfo
from kodepoia.kodecode.patch import PatchResult, PatchTool
from kodepoia.kodecode.search import SearchMatch, SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation

__all__ = [
    "FileTool",
    "GitWorktreeTool",
    "KodeCodeToolAPI",
    "PatchResult",
    "PatchTool",
    "SearchMatch",
    "SearchTool",
    "WorkspaceBoundary",
    "WorkspaceViolation",
    "WorktreeInfo",
]
