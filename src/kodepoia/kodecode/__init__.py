"""KodeCode: safe, structured source-code tooling for Kodepoia."""

from kodepoia.kodecode.api import KodeCodeToolAPI
from kodepoia.kodecode.files import FileTool
from kodepoia.kodecode.git_worktree import GitWorktreeTool, WorktreeInfo
from kodepoia.kodecode.lsp import (
    LanguageServerCapability,
    LanguageServerRegistry,
    LanguageServerSpec,
    LspError,
    LspRpcError,
    LspSession,
    LspTool,
)
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
from kodepoia.kodecode.protocol import (
    ContentLengthJsonStream,
    FramedMessageChannel,
    FramingLimits,
    ProtocolError,
)
from kodepoia.kodecode.search import SearchMatch, SearchTool
from kodepoia.kodecode.workspace import WorkspaceBoundary, WorkspaceViolation

__all__ = [
    "ChangedRangeSnapshot",
    "ContentLengthJsonStream",
    "FileTool",
    "FramedMessageChannel",
    "FramingLimits",
    "GitWorktreeTool",
    "IncrementalParseResult",
    "IncrementalParseSession",
    "KodeCodeToolAPI",
    "LanguageCapability",
    "LanguageProviderSpec",
    "LanguageServerCapability",
    "LanguageServerRegistry",
    "LanguageServerSpec",
    "LspError",
    "LspRpcError",
    "LspSession",
    "LspTool",
    "ParseDocument",
    "ParseSummary",
    "ParserTool",
    "PatchResult",
    "PatchTool",
    "ProtocolError",
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
