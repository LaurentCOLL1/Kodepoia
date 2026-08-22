from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.secrets import KodeSecrets
from kodepoia.exceptions import PermissionDenied
from kodepoia.intelligence.research.cache import (
    CacheAssessment,
    ResearchCachePolicy,
    ResearchCacheStore,
    ResearchQueryManifest,
    assess_cached_result,
)
from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFinding,
    ResearchFindingKind,
    ResearchFreshness,
    ResearchReport,
    ResearchSourceKind,
    ResearchStatus,
)
from kodepoia.intelligence.research.documents import LocalDocumentAdapter
from kodepoia.intelligence.research.media import MediaDoctor, build_governed_media_runner
from kodepoia.intelligence.research.orchestration import redact_research_text
from kodepoia.intelligence.research.store import ResearchStore
from kodepoia.intelligence.research.web import (
    GuardedHttpTransport,
    SingleRequestTransport,
    WebPolicy,
    WebPolicyViolation,
    WebRateLimitExceeded,
    WebRequest,
    WebResearchClient,
    WebTransportError,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary

RESEARCH_UX_SCHEMA_VERSION = 1
_SHA256_CHARS = frozenset("0123456789abcdef")


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in _SHA256_CHARS for character in value)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _redact_payload(value: Any, secrets: KodeSecrets | None) -> Any:
    if isinstance(value, str):
        return redact_research_text(value, secrets=secrets)
    if isinstance(value, list):
        return [_redact_payload(item, secrets) for item in value]
    if isinstance(value, tuple):
        return [_redact_payload(item, secrets) for item in value]
    if isinstance(value, dict):
        return {str(key): _redact_payload(item, secrets) for key, item in value.items()}
    return value


class ResearchOperationStatus(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"
    STALE = "stale"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ResearchCancellation:
    _event: threading.Event = field(default_factory=threading.Event, init=False, repr=False)

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def require_active(self) -> None:
        if self.cancelled:
            raise ResearchCancelled("research operation cancelled")


class ResearchCancelled(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ResearchViewItem:
    source_kind: str
    source_id: str
    locator: str
    status: ResearchOperationStatus
    freshness: str
    trust: str
    title: str = ""
    version: str = ""
    retrieved_at: str = ""
    published_at: str = ""
    updated_at: str = ""
    artifact_id: str = ""
    finding_id: str = ""
    finding_kind: str = ""
    text: str = ""
    citation_ids: tuple[str, ...] = ()
    citation_locators: tuple[str, ...] = ()
    suspicious: bool = False
    guard_indicators: tuple[str, ...] = ()
    reason: str = ""
    schema_version: int = RESEARCH_UX_SCHEMA_VERSION
    item_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_UX_SCHEMA_VERSION:
            raise ValueError("Unsupported Research UX schema version")
        if self.source_id and not _is_sha256(self.source_id):
            raise ValueError("Research view source_id must be a lowercase SHA-256")
        if self.artifact_id and not _is_sha256(self.artifact_id):
            raise ValueError("Research view artifact_id must be a lowercase SHA-256")
        if self.finding_id and not _is_sha256(self.finding_id):
            raise ValueError("Research view finding_id must be a lowercase SHA-256")
        if any(not _is_sha256(value) for value in self.citation_ids):
            raise ValueError("Research view citation IDs must be lowercase SHA-256")
        object.__setattr__(self, "item_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
            "source_id": self.source_id,
            "locator": self.locator,
            "status": self.status.value,
            "freshness": self.freshness,
            "trust": self.trust,
            "title": self.title,
            "version": self.version,
            "retrieved_at": self.retrieved_at,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "artifact_id": self.artifact_id,
            "finding_id": self.finding_id,
            "finding_kind": self.finding_kind,
            "text": self.text,
            "citation_ids": list(self.citation_ids),
            "citation_locators": list(self.citation_locators),
            "suspicious": self.suspicious,
            "guard_indicators": list(self.guard_indicators),
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["item_id"] = self.item_id
        return payload


@dataclass(frozen=True, slots=True)
class ResearchServiceResult:
    operation: str
    status: ResearchOperationStatus
    items: tuple[ResearchViewItem, ...] = ()
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    schema_version: int = RESEARCH_UX_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "status": self.status.value,
            "reason": self.reason,
            "items": [item.to_dict() for item in self.items],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ResearchFetchRequest:
    kind: ResearchSourceKind
    locator: str
    retrieved_at: str = ""
    canonical_locator: str = ""
    title: str = ""
    publisher: str = ""
    product: str = ""
    version: str = ""
    target_version: str = ""

    def __post_init__(self) -> None:
        if not self.locator.strip():
            raise ValueError("Research fetch locator must not be empty")
        if self.kind not in {
            ResearchSourceKind.LOCAL,
            ResearchSourceKind.OFFICIAL_DOCS,
            ResearchSourceKind.WEB,
        }:
            raise ValueError("Interactive R7.10 fetch supports local, official_docs or web")

    @property
    def effective_retrieved_at(self) -> str:
        return self.retrieved_at or _utc_now()


@dataclass(slots=True)
class ResearchService:
    project_root: Path
    allow_network: bool = False
    secrets: KodeSecrets | None = None
    web_transport: SingleRequestTransport | None = None
    web_policy: WebPolicy = field(default_factory=WebPolicy)
    _boundary: WorkspaceBoundary = field(init=False, repr=False)
    _research_store: ResearchStore = field(init=False, repr=False)
    _cache_store: ResearchCacheStore = field(init=False, repr=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        self.project_root = root
        self._boundary = WorkspaceBoundary(root)
        self._research_store = ResearchStore(root)
        self._cache_store = ResearchCacheStore(root)

    def _require_project(self) -> None:
        if not self._boundary.resolve(".kodepoia").is_dir():
            raise FileNotFoundError("Kodepoia project metadata not found")

    @staticmethod
    def _status_from_research(status: ResearchStatus) -> ResearchOperationStatus:
        return {
            ResearchStatus.READY: ResearchOperationStatus.READY,
            ResearchStatus.STALE: ResearchOperationStatus.STALE,
            ResearchStatus.BLOCKED: ResearchOperationStatus.BLOCKED,
            ResearchStatus.UNAVAILABLE: ResearchOperationStatus.UNAVAILABLE,
            ResearchStatus.UNKNOWN: ResearchOperationStatus.UNKNOWN,
            ResearchStatus.NOT_APPLICABLE: ResearchOperationStatus.UNKNOWN,
        }[status]

    def _artifact_view(
        self,
        artifact: ResearchArtifact,
        *,
        text: str | None = None,
        finding: ResearchFinding | None = None,
        reason: str = "",
    ) -> ResearchViewItem:
        citation_ids: tuple[str, ...] = ()
        citation_locators: tuple[str, ...] = ()
        if finding is not None:
            relevant = tuple(
                citation
                for citation in finding.citations
                if citation.artifact_id == artifact.artifact_id
            )
            citation_ids = tuple(sorted(citation.citation_id for citation in relevant))
            citation_locators = tuple(
                sorted(
                    redact_research_text(citation.locator, secrets=self.secrets)
                    for citation in relevant
                )
            )
        rendered = artifact.content if text is None else text
        rendered = redact_research_text(rendered, secrets=self.secrets).strip()
        if len(rendered) > 4000:
            rendered = rendered[:3999].rstrip() + "…"
        return ResearchViewItem(
            source_kind=artifact.source.kind.value,
            source_id=artifact.source.source_id,
            locator=redact_research_text(artifact.source.locator, secrets=self.secrets),
            status=self._status_from_research(artifact.source.status),
            freshness=artifact.freshness.value,
            trust=artifact.trust.value,
            title=redact_research_text(artifact.source.title, secrets=self.secrets),
            version=redact_research_text(artifact.source.version, secrets=self.secrets),
            retrieved_at=artifact.retrieved_at,
            published_at=artifact.source.published_at or "",
            updated_at=artifact.source.updated_at or "",
            artifact_id=artifact.artifact_id,
            finding_id="" if finding is None else finding.finding_id,
            finding_kind="" if finding is None else finding.kind.value,
            text=rendered,
            citation_ids=citation_ids,
            citation_locators=citation_locators,
            suspicious=artifact.guarded.suspicious,
            guard_indicators=tuple(sorted(artifact.guarded.indicators)),
            reason=reason,
        )

    def _unknown_finding_view(self, finding: ResearchFinding) -> ResearchViewItem:
        text = redact_research_text(finding.claim, secrets=self.secrets)
        return ResearchViewItem(
            source_kind="unknown",
            source_id="",
            locator="",
            status=ResearchOperationStatus.UNKNOWN,
            freshness=ResearchFreshness.UNKNOWN.value,
            trust="external_guarded_untrusted",
            finding_id=finding.finding_id,
            finding_kind=finding.kind.value,
            text=text[:4000],
            citation_ids=tuple(sorted(citation.citation_id for citation in finding.citations)),
            citation_locators=tuple(
                sorted(redact_research_text(citation.locator, secrets=self.secrets) for citation in finding.citations)
            ),
            reason="finding_has_no_available_artifact",
        )

    def _reports(self, cancellation: ResearchCancellation | None = None) -> Iterable[ResearchReport]:
        self._require_project()
        directory = self._boundary.resolve(".kodepoia/research/reports")
        if not directory.is_dir():
            return ()
        reports: list[ResearchReport] = []
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if cancellation is not None:
                cancellation.require_active()
            if path.suffix != ".json" or not _is_sha256(path.stem):
                continue
            reports.append(self._research_store.load_report(path.stem))
        return tuple(reports)

    def query(
        self,
        query: str,
        *,
        source_kinds: Iterable[ResearchSourceKind] = (),
        limit: int = 20,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        wanted = " ".join(query.split()).strip()
        if not wanted:
            raise ValueError("Research query must not be empty")
        if not 1 <= limit <= 100:
            raise ValueError("Research query limit must be between 1 and 100")
        token = cancellation or ResearchCancellation()
        selected_sources = frozenset(source_kinds)
        words = tuple(part.casefold() for part in wanted.split())
        phrase = wanted.casefold()
        scored: list[tuple[int, ResearchViewItem]] = []
        try:
            token.require_active()
            for report in self._reports(token):
                token.require_active()
                artifacts = {artifact.artifact_id: artifact for artifact in report.artifacts}
                for finding in report.findings:
                    token.require_active()
                    cited_artifacts = tuple(
                        artifacts[citation.artifact_id]
                        for citation in finding.citations
                        if citation.artifact_id in artifacts
                    )
                    if selected_sources and cited_artifacts and not any(
                        artifact.source.kind in selected_sources for artifact in cited_artifacts
                    ):
                        continue
                    haystack = " ".join(
                        [
                            report.request.query,
                            finding.claim,
                            *(
                                f"{artifact.source.title} {artifact.source.locator} {artifact.source.product} {artifact.source.version}"
                                for artifact in cited_artifacts
                            ),
                        ]
                    ).casefold()
                    if not all(word in haystack for word in words):
                        continue
                    score = 10 if phrase in haystack else 0
                    if finding.kind is ResearchFindingKind.SOURCE_FACT:
                        score += 5
                    if not cited_artifacts:
                        scored.append((score, self._unknown_finding_view(finding)))
                        continue
                    for artifact in cited_artifacts:
                        if selected_sources and artifact.source.kind not in selected_sources:
                            continue
                        scored.append((score, self._artifact_view(artifact, text=finding.claim, finding=finding)))
                if not report.findings:
                    for artifact in report.artifacts:
                        if selected_sources and artifact.source.kind not in selected_sources:
                            continue
                        haystack = f"{report.request.query} {artifact.source.title} {artifact.source.locator} {artifact.content}".casefold()
                        if all(word in haystack for word in words):
                            score = 10 if phrase in haystack else 0
                            scored.append((score, self._artifact_view(artifact)))
            scored.sort(key=lambda item: (-item[0], item[1].item_id))
            items: list[ResearchViewItem] = []
            seen: set[str] = set()
            for _, item in scored:
                if item.item_id in seen:
                    continue
                seen.add(item.item_id)
                items.append(item)
                if len(items) >= limit:
                    break
            return ResearchServiceResult(
                operation="query",
                status=ResearchOperationStatus.READY,
                items=tuple(items),
                metadata={
                    "query_sha256": hashlib.sha256(wanted.encode("utf-8")).hexdigest(),
                    "result_count": len(items),
                    "source_filters": sorted(kind.value for kind in selected_sources),
                },
            )
        except ResearchCancelled:
            return ResearchServiceResult(
                operation="query",
                status=ResearchOperationStatus.CANCELLED,
                reason="cancelled",
                metadata={"result_count": 0},
            )

    def fetch(
        self,
        request: ResearchFetchRequest,
        *,
        cancellation: ResearchCancellation | None = None,
    ) -> ResearchServiceResult:
        self._require_project()
        token = cancellation or ResearchCancellation()
        if token.cancelled:
            return ResearchServiceResult("fetch", ResearchOperationStatus.CANCELLED, reason="cancelled")
        if request.kind in {ResearchSourceKind.LOCAL, ResearchSourceKind.OFFICIAL_DOCS}:
            return self._fetch_document(request, token)
        return self._fetch_web(request, token)

    def _fetch_document(
        self,
        request: ResearchFetchRequest,
        cancellation: ResearchCancellation,
    ) -> ResearchServiceResult:
        try:
            cancellation.require_active()
            result = LocalDocumentAdapter(self.project_root).research(
                request.locator,
                retrieved_at=request.effective_retrieved_at,
                source_kind=request.kind,
                canonical_locator=request.canonical_locator or None,
                title=request.title,
                publisher=request.publisher,
                product=request.product,
                version=request.version,
                target_version=request.target_version or None,
                persist_cache=False,
            )
            cancellation.require_active()
        except ResearchCancelled:
            return ResearchServiceResult("fetch", ResearchOperationStatus.CANCELLED, reason="cancelled")
        if result.artifact is None:
            return ResearchServiceResult(
                "fetch",
                self._status_from_research(result.status),
                reason=result.reason,
            )
        self._research_store.save_artifact(result.artifact)
        return ResearchServiceResult(
            "fetch",
            self._status_from_research(result.status),
            items=(self._artifact_view(result.artifact),),
            metadata={"cache_hit": False, "chunk_count": len(result.chunks)},
        )

    def _web_client(self) -> WebResearchClient:
        if not self.allow_network:
            raise PermissionDenied("NETWORK capability is not granted for this Research service")
        permissions = PermissionSet()
        permissions.grant(PermissionGrant(Capability.NETWORK))
        guardian = KodeGuardian(permissions)
        transport = self.web_transport or GuardedHttpTransport(guardian)
        return WebResearchClient(
            self.project_root,
            transport,
            policy=self.web_policy,
        )

    def _fetch_web(
        self,
        request: ResearchFetchRequest,
        cancellation: ResearchCancellation,
    ) -> ResearchServiceResult:
        if not self.allow_network:
            return ResearchServiceResult(
                "fetch",
                ResearchOperationStatus.BLOCKED,
                reason="network_permission_not_granted",
            )
        try:
            cancellation.require_active()
            result = self._web_client().research(
                WebRequest(
                    url=request.locator,
                    retrieved_at=request.effective_retrieved_at,
                    persist_cache=False,
                )
            )
            cancellation.require_active()
        except ResearchCancelled:
            return ResearchServiceResult("fetch", ResearchOperationStatus.CANCELLED, reason="cancelled")
        except (PermissionDenied, WebPolicyViolation) as exc:
            return ResearchServiceResult(
                "fetch",
                ResearchOperationStatus.BLOCKED,
                reason=redact_research_text(str(exc), secrets=self.secrets),
            )
        except (WebRateLimitExceeded, WebTransportError) as exc:
            return ResearchServiceResult(
                "fetch",
                ResearchOperationStatus.UNAVAILABLE,
                reason=redact_research_text(str(exc), secrets=self.secrets),
            )
        if result.artifact is None:
            return ResearchServiceResult(
                "fetch",
                self._status_from_research(result.status),
                reason=result.reason,
                metadata={"final_url": result.final_url, "redirects": list(result.redirects)},
            )
        self._research_store.save_artifact(result.artifact)
        return ResearchServiceResult(
            "fetch",
            self._status_from_research(result.status),
            items=(self._artifact_view(result.artifact),),
            metadata={"final_url": result.final_url, "redirects": list(result.redirects)},
        )

    def show(self, identifier: str) -> ResearchServiceResult:
        self._require_project()
        key = identifier.strip().lower()
        if not _is_sha256(key):
            raise ValueError("Research show identifier must be a lowercase SHA-256")
        artifact_path = self._boundary.resolve(f".kodepoia/research/artifacts/{key}.json")
        if artifact_path.is_file():
            artifact = self._research_store.load_artifact(key)
            return ResearchServiceResult(
                "show",
                ResearchOperationStatus.READY,
                items=(self._artifact_view(artifact),),
                metadata={"record_type": "artifact"},
            )
        report_path = self._boundary.resolve(f".kodepoia/research/reports/{key}.json")
        if report_path.is_file():
            report = self._research_store.load_report(key)
            views: list[ResearchViewItem] = []
            artifacts = {artifact.artifact_id: artifact for artifact in report.artifacts}
            for finding in report.findings:
                emitted = False
                for citation in finding.citations:
                    artifact = artifacts.get(citation.artifact_id)
                    if artifact is None:
                        continue
                    views.append(self._artifact_view(artifact, text=finding.claim, finding=finding))
                    emitted = True
                if not emitted:
                    views.append(self._unknown_finding_view(finding))
            if not views:
                views.extend(self._artifact_view(artifact) for artifact in report.artifacts)
            return ResearchServiceResult(
                "show",
                self._status_from_research(report.status),
                items=tuple(views),
                metadata={
                    "record_type": "report",
                    "report_digest": report.digest_sha256,
                    "request_id": report.request.request_id,
                    "generated_at": report.generated_at,
                },
            )
        return ResearchServiceResult("show", ResearchOperationStatus.UNAVAILABLE, reason="not_found")

    def cache(
        self,
        cache_key: str,
        *,
        as_of: str = "",
        policy: ResearchCachePolicy | None = None,
    ) -> ResearchServiceResult:
        self._require_project()
        key = cache_key.strip().lower()
        if not _is_sha256(key):
            raise ValueError("Research cache key must be a lowercase SHA-256")
        active_policy = policy or ResearchCachePolicy()
        try:
            query = self._cache_store.load_query(key)
            manifest = self._cache_store.load_latest_result(key)
        except FileNotFoundError:
            return ResearchServiceResult("cache", ResearchOperationStatus.UNAVAILABLE, reason="not_found")
        assessment: CacheAssessment = assess_cached_result(
            manifest,
            query_manifest=query,
            policy=active_policy,
            as_of=as_of or _utc_now(),
        )
        status = {
            "fresh": ResearchOperationStatus.READY,
            "stale": ResearchOperationStatus.STALE,
            "invalidated": ResearchOperationStatus.UNAVAILABLE,
        }[assessment.decision.value]
        return ResearchServiceResult(
            "cache",
            status,
            reason=assessment.reason,
            metadata={
                "cache_key": query.cache_key,
                "request_id": query.request_id,
                "query_sha256": query.query_sha256,
                "project_scope_sha256": query.project_scope_sha256,
                "source_kinds": list(query.source_kinds),
                "target_constraint_id": query.target_constraint_id,
                "version_fingerprints": list(query.version_fingerprints),
                "policy_digest": query.policy_digest,
                "manifest_id": manifest.manifest_id,
                "report_digest": manifest.report_digest,
                "stored_at": manifest.stored_at,
                "revalidated_at": manifest.revalidated_at,
                "age_seconds": assessment.age_seconds,
                "ttl_seconds": assessment.ttl_seconds,
                "artifact_refs": [reference.to_dict() for reference in manifest.artifact_refs],
            },
        )

    def status(self) -> ResearchServiceResult:
        self._require_project()
        root = self._boundary.resolve(".kodepoia/research")

        def count_json(relative: str) -> int:
            directory = self._boundary.resolve(f".kodepoia/research/{relative}")
            if not directory.is_dir():
                return 0
            return sum(1 for item in directory.iterdir() if item.is_file() and item.suffix == ".json")

        capabilities = {
            "local": {"status": "ready", "interactive_fetch": True},
            "official_docs": {"status": "ready", "interactive_fetch": True, "mode": "offline_snapshot"},
            "web": {
                "status": "ready" if self.allow_network else "blocked",
                "interactive_fetch": True,
                "reason": "" if self.allow_network else "network_permission_not_granted",
            },
            "github": {
                "status": "unknown",
                "interactive_fetch": False,
                "reason": "use_typed_r7_4_provider_configuration",
            },
            "community": {
                "status": "unknown",
                "interactive_fetch": False,
                "reason": "use_typed_r7_5_normalizer/provider_configuration",
            },
            "youtube": {
                "status": "unknown",
                "interactive_fetch": False,
                "reason": "use_typed_r7_6_provider_configuration",
            },
        }
        return ResearchServiceResult(
            "status",
            ResearchOperationStatus.READY,
            metadata={
                "research_root_exists": root.is_dir(),
                "artifacts": count_json("artifacts"),
                "reports": count_json("reports"),
                "cache_queries": count_json("cache/queries"),
                "cache_results": count_json("cache/results"),
                "context_summaries": count_json("context"),
                "capabilities": capabilities,
            },
        )

    def media_capability(self) -> ResearchServiceResult:
        self._require_project()
        try:
            runner = build_governed_media_runner(self.project_root)
            report = MediaDoctor(self.project_root, runner).run()
        except Exception as exc:  # doctor failures must remain explicit rather than crash UX
            return ResearchServiceResult(
                "media_capability",
                ResearchOperationStatus.UNAVAILABLE,
                reason=redact_research_text(str(exc), secrets=self.secrets),
            )
        payload = _redact_payload(report.to_dict(), self.secrets)
        return ResearchServiceResult(
            "media_capability",
            ResearchOperationStatus.READY if report.ready else ResearchOperationStatus.UNAVAILABLE,
            reason="" if report.ready else "required_local_media_capability_unavailable",
            metadata=payload,
        )

    def export(self, result: ResearchServiceResult) -> Path:
        self._require_project()
        payload = _redact_payload(result.to_dict(), self.secrets)
        digest = _sha256(payload)
        target = self._boundary.resolve(f".kodepoia/research/exports/{digest}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return target

    def serialized(self, result: ResearchServiceResult) -> str:
        payload = _redact_payload(result.to_dict(), self.secrets)
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
