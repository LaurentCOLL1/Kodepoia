"""KodeCode: safe, structured source-code tooling for Kodepoia."""

from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool, WorktreeInfo
from kodepoia.kodecode.parser_tool import ParserTool
from kodepoia.kodecode.parsing import (
    ChangedRangeSnapshot,
    IncrementalParseResult,
    IncrementalParseSession,
    LanguageCapability,
    LanguageProviderSpec,
    ParseDocument,
    ParseSummary,
    SyntaxNodeSnapshot,
    TreeSitterLanguageRegistry,
    TreeSitterParserService,
    TreeSitterUnavailable,
)
from kodepoia.kodecode.patch import PatchResult, PatchTool
from kodepoia.kodecode.search import SearchMatch, SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation

__all__ = [
    "ChangedRangeSnapshot",
    "FileTool",
    "GitWorktreeTool",
    "IncrementalParseResult",
    "IncrementalParseSession",
    "KodeCodeToolAPI",
    "LanguageCapability",
    "LanguageProviderSpec",
    "ParseDocument",
    "ParseSummary",
    "ParserTool",
    "PatchResult",
    "PatchTool",
    "SearchMatch",
    "SearchTool",
    "SyntaxNodeSnapshot",
    "TreeSitterLanguageRegistry",
    "TreeSitterParserService",
    "TreeSitterUnavailable",
    "WorkspaceBoundary",
    "WorkspaceViolation",
    "WorktreeInfo",
]
