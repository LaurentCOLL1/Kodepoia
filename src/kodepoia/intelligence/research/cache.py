from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable, Mapping

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFreshness,
    ResearchReport,
    ResearchRequest,
    ResearchTrust,
)
from kodepoia.intelligence.research.versioning import (
    SourceIdentity,
    SourceMutability,
    TargetVersionConstraint,
    VersionObservation,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary

CACHE_SCHEMA_VERSION = 1
CACHE_POLICY_VERSION = 1
_SHA256 = frozenset("0123456789abcdef")


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_sha256(value: str, name: str) -> None:
    if len(value) != 64 or any(character not in _SHA256 for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _require_timestamp(value: str, name: str) -> datetime:
    if not value:
        raise ValueError(f"{name} must not be empty")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{name} must include a timezone")
    return parsed


def normalize_cache_query(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    return " ".join(normalized.split()).strip()


def _version_evidence_payload(observation: VersionObservation) -> dict[str, Any]:
    return {
        "product": observation.product,
        "kind": observation.kind.value,
        "scheme": observation.scheme.value,
        "value": observation.value,
        "interval": None if observation.interval is None else observation.interval.to_dict(),
        "channel": observation.channel,
        "inference_reason": observation.inference_reason,
    }


def version_fingerprint(observation: VersionObservation | None) -> str:
    if observation is None:
        return _sha256_payload({"kind": "unknown"})
    return _sha256_payload(_version_evidence_payload(observation))


class CacheDecision(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    INVALIDATED = "invalidated"


@dataclass(frozen=True, slots=True)
class ResearchCachePolicy:
    ttl_seconds: int = 86_400
    mutable_ttl_seconds: int = 3_600
    max_context_chars: int = 12_000
    max_context_items: int = 16
    policy_version: int = CACHE_POLICY_VERSION
    schema_version: int = CACHE_SCHEMA_VERSION
    policy_digest: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CACHE_SCHEMA_VERSION:
            raise ValueError("Unsupported research cache schema version")
        if self.policy_version != CACHE_POLICY_VERSION:
            raise ValueError("Unsupported research cache policy version")
        if not 0 <= self.ttl_seconds <= 31_536_000:
            raise ValueError("ttl_seconds must be between 0 and one year")
        if not 0 <= self.mutable_ttl_seconds <= 31_536_000:
            raise ValueError("mutable_ttl_seconds must be between 0 and one year")
        if not 256 <= self.max_context_chars <= 1_000_000:
            raise ValueError("max_context_chars must be between 256 and 1,000,000")
        if not 1 <= self.max_context_items <= 1000:
            raise ValueError("max_context_items must be between 1 and 1000")
        object.__setattr__(self, "policy_digest", _sha256_payload(self.identity_payload()))

    def identity_payload(self) -> dict[str, int]:
        return {
            "schema_version": self.schema_version,
            "policy_version": self.policy_version,
            "ttl_seconds": self.ttl_seconds,
            "mutable_ttl_seconds": self.mutable_ttl_seconds,
            "max_context_chars": self.max_context_chars,
            "max_context_items": self.max_context_items,
        }

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = self.identity_payload()
        payload["policy_digest"] = self.policy_digest
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResearchCachePolicy:
        policy = cls(
            ttl_seconds=int(payload["ttl_seconds"]),
            mutable_ttl_seconds=int(payload["mutable_ttl_seconds"]),
            max_context_chars=int(payload["max_context_chars"]),
            max_context_items=int(payload["max_context_items"]),
            policy_version=int(payload.get("policy_version", 0)),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("policy_digest", "")) != policy.policy_digest:
            raise ValueError("Research cache policy digest does not match policy evidence")
        return policy


@dataclass(frozen=True, slots=True)
class ResearchQueryManifest:
    request_id: str
    query_sha256: str
    project_scope_sha256: str
    source_kinds: tuple[str, ...]
    max_results: int
    target_constraint_id: str
    version_fingerprints: tuple[str, ...]
    policy_digest: str
    schema_version: int = CACHE_SCHEMA_VERSION
    cache_key: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CACHE_SCHEMA_VERSION:
            raise ValueError("Unsupported research query cache schema version")
        for name, value in (
            ("request_id", self.request_id),
            ("query_sha256", self.query_sha256),
            ("project_scope_sha256", self.project_scope_sha256),
            ("policy_digest", self.policy_digest),
        ):
            _require_sha256(value, name)
        if self.target_constraint_id:
            _require_sha256(self.target_constraint_id, "target_constraint_id")
        for value in self.version_fingerprints:
            _require_sha256(value, "version_fingerprint")
        if len(set(self.source_kinds)) != len(self.source_kinds):
            raise ValueError("Research query source kinds must be unique")
        if tuple(sorted(self.source_kinds)) != self.source_kinds:
            raise ValueError("Research query source kinds must be sorted")
        if tuple(sorted(self.version_fingerprints)) != self.version_fingerprints:
            raise ValueError("Version fingerprints must be sorted")
        if len(set(self.version_fingerprints)) != len(self.version_fingerprints):
            raise ValueError("Version fingerprints must be unique")
        if not 1 <= self.max_results <= 100:
            raise ValueError("Research query max_results must be between 1 and 100")
        object.__setattr__(self, "cache_key", _sha256_payload(self.identity_payload()))

    @classmethod
    def from_request(
        cls,
        request: ResearchRequest,
        *,
        policy: ResearchCachePolicy,
        target: TargetVersionConstraint | None = None,
        version_observations: Iterable[VersionObservation] = (),
    ) -> ResearchQueryManifest:
        normalized_query = normalize_cache_query(request.query)
        if not normalized_query:
            raise ValueError("Normalized research query must not be empty")
        project_scope = unicodedata.normalize("NFC", request.project_scope.strip())
        fingerprints = tuple(sorted({version_fingerprint(item) for item in version_observations}))
        return cls(
            request_id=request.request_id,
            query_sha256=_sha256_text(normalized_query),
            project_scope_sha256=_sha256_text(project_scope),
            source_kinds=tuple(sorted(kind.value for kind in request.source_kinds)),
            max_results=request.max_results,
            target_constraint_id="" if target is None else target.constraint_id,
            version_fingerprints=fingerprints,
            policy_digest=policy.policy_digest,
        )

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "query_sha256": self.query_sha256,
            "project_scope_sha256": self.project_scope_sha256,
            "source_kinds": list(self.source_kinds),
            "max_results": self.max_results,
            "target_constraint_id": self.target_constraint_id,
            "version_fingerprints": list(self.version_fingerprints),
            "policy_digest": self.policy_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["cache_key"] = self.cache_key
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResearchQueryManifest:
        manifest = cls(
            request_id=str(payload["request_id"]),
            query_sha256=str(payload["query_sha256"]),
            project_scope_sha256=str(payload["project_scope_sha256"]),
            source_kinds=tuple(str(value) for value in payload["source_kinds"]),
            max_results=int(payload["max_results"]),
            target_constraint_id=str(payload.get("target_constraint_id", "")),
            version_fingerprints=tuple(str(value) for value in payload.get("version_fingerprints", [])),
            policy_digest=str(payload["policy_digest"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("cache_key", "")) != manifest.cache_key:
            raise ValueError("Research query cache key does not match canonical evidence")
        return manifest


@dataclass(frozen=True, slots=True)
class CachedArtifactReference:
    artifact_id: str
    source_id: str
    content_sha256: str
    source_identity_id: str
    version_fingerprint: str
    mutability: SourceMutability
    original_retrieved_at: str
    original_freshness: ResearchFreshness
    trust: ResearchTrust
    suspicious: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("artifact_id", self.artifact_id),
            ("source_id", self.source_id),
            ("content_sha256", self.content_sha256),
            ("version_fingerprint", self.version_fingerprint),
        ):
            _require_sha256(value, name)
        if self.source_identity_id:
            _require_sha256(self.source_identity_id, "source_identity_id")
        _require_timestamp(self.original_retrieved_at, "original_retrieved_at")
        if self.trust is not ResearchTrust.GUARDED:
            raise ValueError("Cached research artifacts must retain guarded trust evidence")

    @classmethod
    def from_artifact(
        cls,
        artifact: ResearchArtifact,
        *,
        identity: SourceIdentity | None = None,
        observation: VersionObservation | None = None,
    ) -> CachedArtifactReference:
        return cls(
            artifact_id=artifact.artifact_id,
            source_id=artifact.source.source_id,
            content_sha256=artifact.content_sha256,
            source_identity_id="" if identity is None else identity.identity_id,
            version_fingerprint=version_fingerprint(observation),
            mutability=SourceMutability.UNKNOWN if identity is None else identity.mutability,
            original_retrieved_at=artifact.retrieved_at,
            original_freshness=artifact.freshness,
            trust=artifact.trust,
            suspicious=artifact.guarded.suspicious,
        )

    def signature(self) -> tuple[str, str, str, str, str]:
        source_key = self.source_identity_id or self.source_id
        return (
            source_key,
            self.source_id,
            self.content_sha256,
            self.version_fingerprint,
            self.mutability.value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "source_id": self.source_id,
            "content_sha256": self.content_sha256,
            "source_identity_id": self.source_identity_id,
            "version_fingerprint": self.version_fingerprint,
            "mutability": self.mutability.value,
            "original_retrieved_at": self.original_retrieved_at,
            "original_freshness": self.original_freshness.value,
            "trust": self.trust.value,
            "suspicious": self.suspicious,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> CachedArtifactReference:
        return cls(
            artifact_id=str(payload["artifact_id"]),
            source_id=str(payload["source_id"]),
            content_sha256=str(payload["content_sha256"]),
            source_identity_id=str(payload.get("source_identity_id", "")),
            version_fingerprint=str(payload["version_fingerprint"]),
            mutability=SourceMutability(payload["mutability"]),
            original_retrieved_at=str(payload["original_retrieved_at"]),
            original_freshness=ResearchFreshness(payload["original_freshness"]),
            trust=ResearchTrust(payload["trust"]),
            suspicious=bool(payload["suspicious"]),
        )


@dataclass(frozen=True, slots=True)
class ResearchResultManifest:
    cache_key: str
    request_id: str
    report_digest: str
    artifact_refs: tuple[CachedArtifactReference, ...]
    stored_at: str
    revalidated_at: str | None
    policy_digest: str
    schema_version: int = CACHE_SCHEMA_VERSION
    manifest_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != CACHE_SCHEMA_VERSION:
            raise ValueError("Unsupported research result cache schema version")
        for name, value in (
            ("cache_key", self.cache_key),
            ("request_id", self.request_id),
            ("report_digest", self.report_digest),
            ("policy_digest", self.policy_digest),
        ):
            _require_sha256(value, name)
        stored = _require_timestamp(self.stored_at, "stored_at")
        if self.revalidated_at is not None:
            revalidated = _require_timestamp(self.revalidated_at, "revalidated_at")
            if revalidated.astimezone(timezone.utc) < stored.astimezone(timezone.utc):
                raise ValueError("revalidated_at cannot be before stored_at")
        artifact_ids = [item.artifact_id for item in self.artifact_refs]
        if len(artifact_ids) != len(set(artifact_ids)):
            raise ValueError("Cached artifact references must be unique")
        object.__setattr__(self, "manifest_id", _sha256_payload(self.identity_payload()))

    @classmethod
    def from_report(
        cls,
        report: ResearchReport,
        *,
        query_manifest: ResearchQueryManifest,
        policy: ResearchCachePolicy,
        stored_at: str,
        identities: Mapping[str, SourceIdentity] | None = None,
        observations: Mapping[str, VersionObservation] | None = None,
        revalidated_at: str | None = None,
    ) -> ResearchResultManifest:
        if report.request.request_id != query_manifest.request_id:
            raise ValueError("Research report request does not match query manifest")
        refs = tuple(
            CachedArtifactReference.from_artifact(
                artifact,
                identity=None if identities is None else identities.get(artifact.artifact_id),
                observation=None if observations is None else observations.get(artifact.artifact_id),
            )
            for artifact in report.artifacts
        )
        return cls(
            cache_key=query_manifest.cache_key,
            request_id=report.request.request_id,
            report_digest=report.digest_sha256,
            artifact_refs=refs,
            stored_at=stored_at,
            revalidated_at=revalidated_at,
            policy_digest=policy.policy_digest,
        )

    def identity_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cache_key": self.cache_key,
            "request_id": self.request_id,
            "report_digest": self.report_digest,
            "artifact_refs": [item.to_dict() for item in self.artifact_refs],
            "stored_at": self.stored_at,
            "revalidated_at": self.revalidated_at,
            "policy_digest": self.policy_digest,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["manifest_id"] = self.manifest_id
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> ResearchResultManifest:
        manifest = cls(
            cache_key=str(payload["cache_key"]),
            request_id=str(payload["request_id"]),
            report_digest=str(payload["report_digest"]),
            artifact_refs=tuple(
                CachedArtifactReference.from_dict(item) for item in payload.get("artifact_refs", [])
            ),
            stored_at=str(payload["stored_at"]),
            revalidated_at=None if payload.get("revalidated_at") is None else str(payload["revalidated_at"]),
            policy_digest=str(payload["policy_digest"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        if str(payload.get("manifest_id", "")) != manifest.manifest_id:
            raise ValueError("Research result manifest ID does not match canonical evidence")
        return manifest

    def with_revalidation(
        self,
        *,
        revalidated_at: str,
        artifact_refs: Iterable[CachedArtifactReference],
    ) -> ResearchResultManifest:
        current = tuple(sorted((item.signature() for item in self.artifact_refs)))
        proposed_refs = tuple(artifact_refs)
        proposed = tuple(sorted((item.signature() for item in proposed_refs)))
        if current != proposed:
            raise ValueError("Revalidation evidence changed source/version/content identity")
        return ResearchResultManifest(
            cache_key=self.cache_key,
            request_id=self.request_id,
            report_digest=self.report_digest,
            artifact_refs=proposed_refs,
            stored_at=self.stored_at,
            revalidated_at=revalidated_at,
            policy_digest=self.policy_digest,
        )


@dataclass(frozen=True, slots=True)
class CacheAssessment:
    decision: CacheDecision
    reason: str
    age_seconds: int | None
    ttl_seconds: int | None

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError("Cache assessment reason must not be empty")
        if self.age_seconds is not None and self.age_seconds < 0:
            raise ValueError("Cache age cannot be negative")
        if self.ttl_seconds is not None and self.ttl_seconds < 0:
            raise ValueError("Cache TTL cannot be negative")


def assess_cached_result(
    manifest: ResearchResultManifest,
    *,
    query_manifest: ResearchQueryManifest,
    policy: ResearchCachePolicy,
    as_of: str,
    current_artifact_refs: Iterable[CachedArtifactReference] | None = None,
) -> CacheAssessment:
    now = _require_timestamp(as_of, "as_of")
    if manifest.cache_key != query_manifest.cache_key or manifest.request_id != query_manifest.request_id:
        return CacheAssessment(CacheDecision.INVALIDATED, "query_cache_key_changed", None, None)
    if manifest.policy_digest != policy.policy_digest or query_manifest.policy_digest != policy.policy_digest:
        return CacheAssessment(CacheDecision.INVALIDATED, "cache_policy_changed", None, None)
    if current_artifact_refs is not None:
        stored_signatures = tuple(sorted(item.signature() for item in manifest.artifact_refs))
        current_signatures = tuple(sorted(item.signature() for item in current_artifact_refs))
        if stored_signatures != current_signatures:
            return CacheAssessment(
                CacheDecision.INVALIDATED,
                "source_version_or_content_identity_changed",
                None,
                None,
            )
    basis_text = manifest.revalidated_at or manifest.stored_at
    basis = _require_timestamp(basis_text, "cache_age_basis")
    delta = (now.astimezone(timezone.utc) - basis.astimezone(timezone.utc)).total_seconds()
    if delta < 0:
        return CacheAssessment(CacheDecision.INVALIDATED, "cache_age_basis_is_in_the_future", None, None)
    age = int(delta)
    has_mutable = any(item.mutability is SourceMutability.MUTABLE for item in manifest.artifact_refs)
    ttl = policy.mutable_ttl_seconds if has_mutable else policy.ttl_seconds
    if age <= ttl:
        return CacheAssessment(CacheDecision.FRESH, "inside_cache_ttl", age, ttl)
    return CacheAssessment(CacheDecision.STALE, "cache_ttl_expired_revalidation_required", age, ttl)


@dataclass(frozen=True, slots=True)
class ArtifactDedupeGroup:
    representative_artifact_id: str
    artifact_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_identity_ids: tuple[str, ...]
    content_sha256: str
    version_fingerprint: str

    def __post_init__(self) -> None:
        _require_sha256(self.representative_artifact_id, "representative_artifact_id")
        _require_sha256(self.content_sha256, "content_sha256")
        _require_sha256(self.version_fingerprint, "version_fingerprint")
        for name, values in (
            ("artifact_id", self.artifact_ids),
            ("source_id", self.source_ids),
            ("source_identity_id", self.source_identity_ids),
        ):
            for value in values:
                _require_sha256(value, name)
        if self.representative_artifact_id not in self.artifact_ids:
            raise ValueError("Dedupe representative must be present in artifact IDs")


@dataclass(frozen=True, slots=True)
class ArtifactDedupeResult:
    artifacts: tuple[ResearchArtifact, ...]
    groups: tuple[ArtifactDedupeGroup, ...]


def deduplicate_artifacts(
    artifacts: Iterable[ResearchArtifact],
    *,
    identities: Mapping[str, SourceIdentity] | None = None,
    observations: Mapping[str, VersionObservation] | None = None,
) -> ArtifactDedupeResult:
    buckets: dict[tuple[str, str, str], list[ResearchArtifact]] = {}
    identity_values: dict[tuple[str, str, str], set[str]] = {}
    source_values: dict[tuple[str, str, str], set[str]] = {}
    for artifact in artifacts:
        identity = None if identities is None else identities.get(artifact.artifact_id)
        observation = None if observations is None else observations.get(artifact.artifact_id)
        source_key = artifact.source.source_id if identity is None else identity.identity_id
        version_key = version_fingerprint(observation)
        key = (source_key, version_key, artifact.content_sha256)
        buckets.setdefault(key, []).append(artifact)
        source_values.setdefault(key, set()).add(artifact.source.source_id)
        if identity is not None:
            identity_values.setdefault(key, set()).add(identity.identity_id)

    representatives: list[ResearchArtifact] = []
    groups: list[ArtifactDedupeGroup] = []
    for key in sorted(buckets):
        members = sorted(buckets[key], key=lambda item: item.artifact_id)
        representative = members[0]
        representatives.append(representative)
        groups.append(
            ArtifactDedupeGroup(
                representative_artifact_id=representative.artifact_id,
                artifact_ids=tuple(sorted({item.artifact_id for item in members})),
                source_ids=tuple(sorted(source_values[key])),
                source_identity_ids=tuple(sorted(identity_values.get(key, set()))),
                content_sha256=key[2],
                version_fingerprint=key[1],
            )
        )
    return ArtifactDedupeResult(tuple(representatives), tuple(groups))


@dataclass(frozen=True, slots=True)
class ResearchCacheStore:
    project_root: Path
    _boundary: WorkspaceBoundary = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        root = Path(self.project_root).resolve(strict=False)
        object.__setattr__(self, "project_root", root)
        object.__setattr__(self, "_boundary", WorkspaceBoundary(root))

    @property
    def metadata_root(self) -> Path:
        return self._boundary.resolve(".kodepoia")

    @property
    def cache_root(self) -> Path:
        return self._boundary.resolve(".kodepoia/research/cache")

    def _require_initialized_project(self) -> None:
        if not self.metadata_root.is_dir():
            raise FileNotFoundError(f"Kodepoia project metadata not found: {self.metadata_root}")

    @staticmethod
    def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Research cache document must be a JSON object")
        return payload

    def _hashed_path(self, category: str, identifier: str) -> Path:
        _require_sha256(identifier, "cache identifier")
        return self._boundary.resolve(f".kodepoia/research/cache/{category}/{identifier}.json")

    def save_query(self, manifest: ResearchQueryManifest) -> Path:
        self._require_initialized_project()
        path = self._hashed_path("queries", manifest.cache_key)
        self._write_json(path, manifest.to_dict())
        return path

    def load_query(self, cache_key: str) -> ResearchQueryManifest:
        self._require_initialized_project()
        path = self._hashed_path("queries", cache_key)
        return ResearchQueryManifest.from_dict(self._read_json(path))

    def save_result(self, manifest: ResearchResultManifest) -> Path:
        self._require_initialized_project()
        result_path = self._hashed_path("results", manifest.manifest_id)
        self._write_json(result_path, manifest.to_dict())
        index_path = self._hashed_path("result-index", manifest.cache_key)
        self._write_json(
            index_path,
            {
                "schema_version": CACHE_SCHEMA_VERSION,
                "cache_key": manifest.cache_key,
                "manifest_id": manifest.manifest_id,
            },
        )
        return result_path

    def load_result(self, manifest_id: str) -> ResearchResultManifest:
        self._require_initialized_project()
        return ResearchResultManifest.from_dict(
            self._read_json(self._hashed_path("results", manifest_id))
        )

    def load_latest_result(self, cache_key: str) -> ResearchResultManifest:
        self._require_initialized_project()
        index = self._read_json(self._hashed_path("result-index", cache_key))
        if int(index.get("schema_version", 0)) != CACHE_SCHEMA_VERSION:
            raise ValueError("Unsupported research cache result index schema version")
        if str(index.get("cache_key", "")) != cache_key:
            raise ValueError("Research cache result index key mismatch")
        manifest_id = str(index.get("manifest_id", ""))
        _require_sha256(manifest_id, "manifest_id")
        manifest = self.load_result(manifest_id)
        if manifest.cache_key != cache_key:
            raise ValueError("Indexed research cache result does not match query key")
        return manifest
