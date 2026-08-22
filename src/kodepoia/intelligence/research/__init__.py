"""Secure, typed KodeResearch contracts and governed research adapters."""

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchCitation,
    ResearchFinding,
    ResearchFindingKind,
    ResearchFreshness,
    ResearchReport,
    ResearchRequest,
    ResearchSource,
    ResearchSourceKind,
    ResearchStatus,
    ResearchTrust,
)
from kodepoia.intelligence.research.documents import (
    DocumentChunk,
    DocumentFormat,
    DocumentResearchResult,
    LocalDocumentAdapter,
    OfficialDocEntry,
    OfficialDocsAdapter,
    OfficialDocsManifest,
)
from kodepoia.intelligence.research.store import ResearchStore

__all__ = [
    "DocumentChunk",
    "DocumentFormat",
    "DocumentResearchResult",
    "LocalDocumentAdapter",
    "OfficialDocEntry",
    "OfficialDocsAdapter",
    "OfficialDocsManifest",
    "ResearchArtifact",
    "ResearchCitation",
    "ResearchFinding",
    "ResearchFindingKind",
    "ResearchFreshness",
    "ResearchReport",
    "ResearchRequest",
    "ResearchSource",
    "ResearchSourceKind",
    "ResearchStatus",
    "ResearchStore",
    "ResearchTrust",
]
