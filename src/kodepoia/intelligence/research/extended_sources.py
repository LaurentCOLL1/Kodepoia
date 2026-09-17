from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlsplit

from kodepoia.intelligence.research.community import CommunityResearchClient
from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.evidence import (
    EvidenceSelectionStore,
    EvidenceWorkspace,
)
from kodepoia.intelligence.research.service import (
    ResearchOperationStatus,
    ResearchServiceResult,
    ResearchViewItem,
)
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.intelligence.research.web import RawWebResponse, WebPolicyViolation
from kodepoia.intelligence.research.youtube import YouTubeLocator, YouTubeResearchClient

V2_1_5_SCHEMA_VERSION = 1
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}
_COMMUNITY_HOSTS = {
    "reddit.com",
    "www.reddit.com",
    "old.reddit.com",
    "stackoverflow.com",
    "www.stackoverflow.com",
    "stackexchange.com",
    "www.stackexchange.com",
    "news.ycombinator.com",
    "lobste.rs",
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _candidate_id(provider_id: str, locator: str) -> str:
    return _sha256_text(f"v2.1.5\0{provider_id}\0{locator.strip()}")


def _status(value: ResearchStatus) -> ResearchOperationStatus:
    return {
        ResearchStatus.READY: ResearchOperationStatus.READY,
        ResearchStatus.STALE: ResearchOperationStatus.STALE,
        ResearchStatus.BLOCKED: ResearchOperationStatus.BLOCKED,
        ResearchStatus.UNAVAILABLE: ResearchOperationStatus.UNAVAILABLE,
        ResearchStatus.UNKNOWN: ResearchOperationStatus.UNKNOWN,
        ResearchStatus.NOT_APPLICABLE: ResearchOperationStatus.UNKNOWN,
    }[value]


def _artifact_item(artifact: ResearchArtifact, *, reason: str) -> ResearchViewItem:
    source = artifact.source
    return ResearchViewItem(
        source_kind=source.kind.value,
        source_id=source.source_id,
        locator=source.locator,
        status=_status(source.status),
        freshness=artifact.freshness.value,
        trust=artifact.trust.value,
        title=source.title,
        version=source.version,
        retrieved_at=artifact.retrieved_at,
        published_at=source.published_at or "",
        updated_at=source.updated_at or "",
        artifact_id=artifact.artifact_id,
        text=artifact.content,
        suspicious=artifact.guarded.suspicious,
        guard_indicators=tuple(artifact.guarded.indicators),
        reason=reason,
    )


def _looks_community(locator: str) -> bool:
    parsed = urlsplit(locator.strip())
    host = (parsed.hostname or "").lower().rstrip(".")
    if host in _COMMUNITY_HOSTS:
        return True
    labels = host.split(".")
    return bool(labels and labels[0] in {"community", "discuss", "discussion", "forum", "forums"})


def _looks_youtube(locator: str) -> bool:
    parsed = urlsplit(locator.strip())
    return (parsed.hostname or "").lower().rstrip(".") in _YOUTUBE_HOSTS


@dataclass(frozen=True, slots=True)
class ExtendedSourceCandidate:
    provider_id: str
    source_kind: ResearchSourceKind
    locator: str
    title: str = ""
    snippet: str = ""
    rank: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = V2_1_5_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != V2_1_5_SCHEMA_VERSION:
            raise ValueError("Unsupported V2.1.5 extended-source schema version")
        if self.source_kind not in {ResearchSourceKind.YOUTUBE, ResearchSourceKind.COMMUNITY}:
            raise ValueError("Extended source candidates must be YouTube or community sources")
        if not self.provider_id.strip() or not self.locator.strip():
            raise ValueError("Extended source candidates require provider_id and locator")
        if self.rank < 0:
            raise ValueError("Extended source candidate rank cannot be negative")
        json.dumps(dict(self.metadata), sort_keys=True, allow_nan=False)

    @property
    def candidate_id(self) -> str:
        return _candidate_id(self.provider_id, self.locator)

    def to_view_item(self) -> ResearchViewItem:
        return ResearchViewItem(
            source_kind=self.source_kind.value,
            source_id=self.candidate_id,
            locator=self.locator.strip(),
            status=ResearchOperationStatus.READY,
            freshness="unfetched",
            trust="candidate-only",
            title=self.title.strip(),
            text=self.snippet.strip()[:4000],
            reason=f"descriptor_only_not_fetched:{self.provider_id}:rank={self.rank}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "provider_id": self.provider_id,
            "source_kind": self.source_kind.value,
            "locator": self.locator,
            "title": self.title,
            "snippet": self.snippet,
            "rank": self.rank,
            "metadata": dict(self.metadata),
            "candidate_only": True,
            "fetched": False,
            "persisted": False,
        }


@dataclass(frozen=True, slots=True)
class ExtendedFetchResult:
    operation: str
    status: ResearchOperationStatus
    items: tuple[ResearchViewItem, ...] = ()
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = V2_1_5_SCHEMA_VERSION

    def to_service_result(self) -> ResearchServiceResult:
        return ResearchServiceResult(
            operation=self.operation,
            status=self.status,
            items=self.items,
            reason=self.reason,
            metadata={"v2_1_5": True, **dict(self.metadata)},
        )


@dataclass(slots=True)
class ExtendedSourceCoordinator:
    """V2.1.5 bridge from candidate discovery to the canonical ResearchStore/Evidence lifecycle.

    Discovery stays descriptor-only. Only guarded YouTube/community clients can create
    persisted artifacts, and their artifacts are projected through the same revision and
    evidence-selection stores used by the rest of the Research Workspace.
    """

    project_root: Path
    youtube_client: YouTubeResearchClient | None = None
    community_client: CommunityResearchClient | None = None
    _store: ResearchStore = field(init=False, repr=False)
    _selection_store: EvidenceSelectionStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._store = ResearchStore(root)
        self._selection_store = EvidenceSelectionStore(root)

    @staticmethod
    def classify_discovery(items: Iterable[ResearchViewItem]) -> tuple[ResearchViewItem, ...]:
        """Reclassify existing guarded web-discovery descriptors without fetching them."""

        classified: list[ResearchViewItem] = []
        for item in items:
            kind: ResearchSourceKind | None = None
            provider = ""
            if _looks_youtube(item.locator):
                kind = ResearchSourceKind.YOUTUBE
                provider = "youtube-via-guarded-discovery"
            elif _looks_community(item.locator):
                kind = ResearchSourceKind.COMMUNITY
                provider = "community-via-guarded-discovery"
            if kind is None:
                continue
            classified.append(
                ExtendedSourceCandidate(
                    provider_id=provider,
                    source_kind=kind,
                    locator=item.locator,
                    title=item.title,
                    snippet=item.text,
                    rank=len(classified) + 1,
                    metadata={"origin_item_id": item.item_id},
                ).to_view_item()
            )
        return tuple(classified)

    @staticmethod
    def youtube_search_candidates(payload: Mapping[str, Any]) -> tuple[ResearchViewItem, ...]:
        """Normalize official YouTube search.list JSON into candidate-only video descriptors."""

        raw_items = payload.get("items", [])
        if not isinstance(raw_items, list):
            raise ValueError("YouTube search items must be a list")
        candidates: list[ResearchViewItem] = []
        for raw in raw_items:
            if not isinstance(raw, Mapping):
                continue
            identity = raw.get("id")
            if not isinstance(identity, Mapping) or str(identity.get("kind", "")) != "youtube#video":
                continue
            video_id = str(identity.get("videoId", ""))
            try:
                locator = YouTubeLocator(video_id)
            except ValueError:
                continue
            snippet = raw.get("snippet") if isinstance(raw.get("snippet"), Mapping) else {}
            candidate = ExtendedSourceCandidate(
                provider_id="youtube-search",
                source_kind=ResearchSourceKind.YOUTUBE,
                locator=locator.canonical_url,
                title=str(snippet.get("title", "")),
                snippet=str(snippet.get("description", "")),
                rank=len(candidates) + 1,
                metadata={
                    "video_id": video_id,
                    "channel_id": str(snippet.get("channelId", "")),
                    "channel_title": str(snippet.get("channelTitle", "")),
                    "published_at": str(snippet.get("publishedAt", "")),
                },
            )
            candidates.append(candidate.to_view_item())
        return tuple(candidates)

    @staticmethod
    def community_candidate(
        locator: str,
        *,
        title: str = "",
        snippet: str = "",
        provider_id: str = "community-discovery",
        rank: int = 1,
    ) -> ResearchViewItem:
        if not _looks_community(locator):
            raise ValueError("Community candidate locator is not a recognized community host")
        return ExtendedSourceCandidate(
            provider_id=provider_id,
            source_kind=ResearchSourceKind.COMMUNITY,
            locator=locator,
            title=title,
            snippet=snippet,
            rank=rank,
        ).to_view_item()

    def fetch_youtube(
        self,
        locator: str,
        *,
        retrieved_at: str,
        preferred_languages: tuple[str, ...] = (),
        include_transcript: bool = True,
    ) -> ExtendedFetchResult:
        if self.youtube_client is None:
            return ExtendedFetchResult(
                "fetch-youtube",
                ResearchOperationStatus.UNAVAILABLE,
                reason="youtube_provider_unconfigured",
                metadata={"fetched": False, "persisted": False},
            )
        result = self.youtube_client.research(
            locator,
            retrieved_at=retrieved_at,
            preferred_languages=preferred_languages,
            include_transcript=include_transcript,
            persist_cache=True,
        )
        items: list[ResearchViewItem] = []
        if result.metadata_artifact is not None:
            items.append(_artifact_item(result.metadata_artifact, reason="fetched:youtube-metadata"))
        if result.transcript_artifact is not None:
            items.append(_artifact_item(result.transcript_artifact, reason="fetched:youtube-transcript"))
        statuses = {result.metadata_status, result.transcript_status}
        if items:
            status = ResearchOperationStatus.READY
            reason = "youtube_fetched" if statuses <= {ResearchStatus.READY, ResearchStatus.NOT_APPLICABLE} else "youtube_fetched_partial"
        elif ResearchStatus.BLOCKED in statuses:
            status = ResearchOperationStatus.BLOCKED
            reason = result.transcript_reason or result.metadata_reason or "youtube_fetch_blocked"
        else:
            status = ResearchOperationStatus.UNAVAILABLE
            reason = result.transcript_reason or result.metadata_reason or "youtube_fetch_unavailable"
        return ExtendedFetchResult(
            "fetch-youtube",
            status,
            tuple(items),
            reason=reason,
            metadata={
                "fetched": bool(items),
                "persisted": bool(items),
                "metadata_status": result.metadata_status.value,
                "transcript_status": result.transcript_status.value,
                "metadata_reason": result.metadata_reason,
                "transcript_reason": result.transcript_reason,
                "transcript_authority": "provider-caption-only",
                "stt_fallback_trusted": False,
                "frame_extraction_trusted": False,
            },
        )

    def fetch_community(
        self,
        response: RawWebResponse,
        *,
        retrieved_at: str,
        platform: str = "",
    ) -> ExtendedFetchResult:
        if self.community_client is None:
            return ExtendedFetchResult(
                "fetch-community",
                ResearchOperationStatus.UNAVAILABLE,
                reason="community_provider_unconfigured",
                metadata={"fetched": False, "persisted": False},
            )
        try:
            result = self.community_client.normalize(
                response,
                retrieved_at=retrieved_at,
                platform=platform,
                persist_cache=True,
            )
        except WebPolicyViolation as exc:
            return ExtendedFetchResult(
                "fetch-community",
                ResearchOperationStatus.UNAVAILABLE,
                reason=str(exc),
                metadata={"fetched": False, "persisted": False},
            )
        if result.artifact is None:
            return ExtendedFetchResult(
                "fetch-community",
                _status(result.status),
                reason=result.reason or "community_fetch_unavailable",
                metadata={"fetched": False, "persisted": False},
            )
        return ExtendedFetchResult(
            "fetch-community",
            ResearchOperationStatus.READY,
            (_artifact_item(result.artifact, reason="fetched:community-thread"),),
            reason="community_fetched",
            metadata={
                "fetched": True,
                "persisted": True,
                "typed_relationships": True,
                "post_count": 0 if result.thread is None else len(result.thread.posts),
                "popularity_is_authority": False,
            },
        )

    def workspace(self, items: Iterable[ResearchViewItem]) -> EvidenceWorkspace:
        return EvidenceWorkspace.project(
            items,
            revisions=self._store.list_evidence_revisions(),
            selections=self._selection_store.load(),
        )
