from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable

from kodepoia.intelligence.research.contracts import (
    ResearchArtifact,
    ResearchFindingKind,
    ResearchFreshness,
)
from kodepoia.project.dna import ProjectDNA

VERSION_PROVENANCE_SCHEMA_VERSION = 1
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
_PEP440_SIMPLE_RELEASE_RE = re.compile(r"^v?(\d+(?:\.\d+)*)$", re.IGNORECASE)


def _canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def _sha256(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _clean(value: str) -> str:
    return value.strip()


def _validate_timestamp(value: str, *, field_name: str) -> datetime:
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed


def _validate_sha256(value: str, *, field_name: str) -> None:
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


def _validate_evidence_refs(values: tuple[str, ...], *, required: bool) -> tuple[str, ...]:
    cleaned = tuple(_clean(value) for value in values)
    if any(not value for value in cleaned):
        raise ValueError("Version evidence references must not be empty")
    if len(set(cleaned)) != len(cleaned):
        raise ValueError("Version evidence references must be unique")
    if required and not cleaned:
        raise ValueError("Version evidence is required")
    return cleaned


class VersionEvidenceKind(StrEnum):
    EXACT = "exact"
    RANGE = "range"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class VersionScheme(StrEnum):
    OPAQUE = "opaque"
    SEMVER = "semver"
    PEP440 = "pep440"


class SourceMutability(StrEnum):
    UNKNOWN = "unknown"
    MUTABLE = "mutable"
    IMMUTABLE = "immutable"


class VersionRelation(StrEnum):
    EXACT_MATCH = "exact_match"
    RANGE_MATCH = "range_match"
    INFERRED_MATCH = "inferred_match"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


class ConflictState(StrEnum):
    AGREEMENT = "agreement"
    CONFLICT = "conflict"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class VersionInterval:
    lower: str | None = None
    upper: str | None = None
    include_lower: bool = True
    include_upper: bool = False

    def __post_init__(self) -> None:
        lower = None if self.lower is None else _clean(self.lower)
        upper = None if self.upper is None else _clean(self.upper)
        if lower == "" or upper == "":
            raise ValueError("Version interval bounds must be non-empty when present")
        if lower is None and upper is None:
            raise ValueError("Version interval requires at least one bound")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lower": self.lower,
            "upper": self.upper,
            "include_lower": self.include_lower,
            "include_upper": self.include_upper,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VersionInterval:
        return cls(
            lower=None if payload.get("lower") is None else str(payload["lower"]),
            upper=None if payload.get("upper") is None else str(payload["upper"]),
            include_lower=bool(payload.get("include_lower", True)),
            include_upper=bool(payload.get("include_upper", False)),
        )


@dataclass(frozen=True, slots=True)
class VersionObservation:
    product: str
    kind: VersionEvidenceKind
    scheme: VersionScheme = VersionScheme.OPAQUE
    value: str = ""
    interval: VersionInterval | None = None
    channel: str = ""
    observed_at: str | None = None
    evidence_refs: tuple[str, ...] = ()
    inference_reason: str = ""
    observation_id: str = field(init=False)

    def __post_init__(self) -> None:
        product = _clean(self.product)
        value = _clean(self.value)
        channel = _clean(self.channel)
        inference_reason = _clean(self.inference_reason)
        if not product:
            raise ValueError("Version observation product must not be empty")
        if self.observed_at is not None:
            _validate_timestamp(self.observed_at, field_name="observed_at")
        refs = _validate_evidence_refs(
            self.evidence_refs,
            required=self.kind is not VersionEvidenceKind.UNKNOWN,
        )
        if self.kind in {VersionEvidenceKind.EXACT, VersionEvidenceKind.INFERRED}:
            if not value or self.interval is not None:
                raise ValueError("Exact/inferred version observations require value and no interval")
        elif self.kind is VersionEvidenceKind.RANGE:
            if value or self.interval is None:
                raise ValueError("Range version observations require interval and no scalar value")
        else:
            if value or self.interval is not None or inference_reason:
                raise ValueError("Unknown version observations cannot contain version claims")
        if self.kind is VersionEvidenceKind.INFERRED:
            if not inference_reason:
                raise ValueError("Inferred version observations require an inference reason")
        elif inference_reason:
            raise ValueError("Only inferred version observations may contain inference_reason")
        object.__setattr__(self, "product", product)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "inference_reason", inference_reason)
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "observation_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "kind": self.kind.value,
            "scheme": self.scheme.value,
            "value": self.value,
            "interval": None if self.interval is None else self.interval.to_dict(),
            "channel": self.channel,
            "observed_at": self.observed_at,
            "evidence_refs": list(self.evidence_refs),
            "inference_reason": self.inference_reason,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["observation_id"] = self.observation_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VersionObservation:
        raw_interval = payload.get("interval")
        observation = cls(
            product=str(payload["product"]),
            kind=VersionEvidenceKind(payload["kind"]),
            scheme=VersionScheme(payload.get("scheme", VersionScheme.OPAQUE.value)),
            value=str(payload.get("value", "")),
            interval=(
                None
                if raw_interval is None
                else VersionInterval.from_dict(_require_dict(raw_interval, "interval"))
            ),
            channel=str(payload.get("channel", "")),
            observed_at=None if payload.get("observed_at") is None else str(payload["observed_at"]),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
            inference_reason=str(payload.get("inference_reason", "")),
        )
        if str(payload.get("observation_id", "")) != observation.observation_id:
            raise ValueError("Version observation ID does not match canonical evidence")
        return observation


@dataclass(frozen=True, slots=True)
class TargetVersionConstraint:
    product: str
    kind: VersionEvidenceKind
    scheme: VersionScheme = VersionScheme.OPAQUE
    value: str = ""
    interval: VersionInterval | None = None
    evidence_refs: tuple[str, ...] = ()
    constraint_id: str = field(init=False)

    def __post_init__(self) -> None:
        product = _clean(self.product)
        value = _clean(self.value)
        if not product:
            raise ValueError("Target version product must not be empty")
        if self.kind is VersionEvidenceKind.INFERRED:
            raise ValueError("Target constraints cannot silently be inferred")
        refs = _validate_evidence_refs(
            self.evidence_refs,
            required=self.kind is not VersionEvidenceKind.UNKNOWN,
        )
        if self.kind is VersionEvidenceKind.EXACT:
            if not value or self.interval is not None:
                raise ValueError("Exact target constraints require value and no interval")
        elif self.kind is VersionEvidenceKind.RANGE:
            if value or self.interval is None:
                raise ValueError("Range target constraints require interval and no scalar value")
        elif value or self.interval is not None:
            raise ValueError("Unknown target constraints cannot contain a version claim")
        object.__setattr__(self, "product", product)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "constraint_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "kind": self.kind.value,
            "scheme": self.scheme.value,
            "value": self.value,
            "interval": None if self.interval is None else self.interval.to_dict(),
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["constraint_id"] = self.constraint_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TargetVersionConstraint:
        raw_interval = payload.get("interval")
        constraint = cls(
            product=str(payload["product"]),
            kind=VersionEvidenceKind(payload["kind"]),
            scheme=VersionScheme(payload.get("scheme", VersionScheme.OPAQUE.value)),
            value=str(payload.get("value", "")),
            interval=(
                None
                if raw_interval is None
                else VersionInterval.from_dict(_require_dict(raw_interval, "interval"))
            ),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
        )
        if str(payload.get("constraint_id", "")) != constraint.constraint_id:
            raise ValueError("Target version constraint ID does not match canonical evidence")
        return constraint


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    locator: str
    mutability: SourceMutability
    source_id: str = ""
    revision: str = ""
    snapshot_sha256: str = ""
    evidence_refs: tuple[str, ...] = ()
    identity_id: str = field(init=False)

    def __post_init__(self) -> None:
        locator = _clean(self.locator)
        source_id = _clean(self.source_id)
        revision = _clean(self.revision)
        snapshot_sha256 = _clean(self.snapshot_sha256)
        if not locator:
            raise ValueError("Source identity locator must not be empty")
        if source_id:
            _validate_sha256(source_id, field_name="source_id")
        if snapshot_sha256:
            _validate_sha256(snapshot_sha256, field_name="snapshot_sha256")
        refs = _validate_evidence_refs(self.evidence_refs, required=False)
        if self.mutability is SourceMutability.IMMUTABLE and not (revision or snapshot_sha256):
            raise ValueError("Immutable source identity requires revision or snapshot hash evidence")
        object.__setattr__(self, "locator", locator)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "revision", revision)
        object.__setattr__(self, "snapshot_sha256", snapshot_sha256)
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "identity_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "locator": self.locator,
            "mutability": self.mutability.value,
            "source_id": self.source_id,
            "revision": self.revision,
            "snapshot_sha256": self.snapshot_sha256,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["identity_id"] = self.identity_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SourceIdentity:
        identity = cls(
            locator=str(payload["locator"]),
            mutability=SourceMutability(payload["mutability"]),
            source_id=str(payload.get("source_id", "")),
            revision=str(payload.get("revision", "")),
            snapshot_sha256=str(payload.get("snapshot_sha256", "")),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
        )
        if str(payload.get("identity_id", "")) != identity.identity_id:
            raise ValueError("Source identity ID does not match canonical evidence")
        return identity


@dataclass(frozen=True, slots=True)
class FreshnessEvidence:
    mutability: SourceMutability
    observed_or_updated_at: str | None = None
    validated_at: str | None = None

    def __post_init__(self) -> None:
        if self.observed_or_updated_at is not None:
            _validate_timestamp(self.observed_or_updated_at, field_name="observed_or_updated_at")
        if self.validated_at is not None:
            _validate_timestamp(self.validated_at, field_name="validated_at")

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutability": self.mutability.value,
            "observed_or_updated_at": self.observed_or_updated_at,
            "validated_at": self.validated_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FreshnessEvidence:
        return cls(
            mutability=SourceMutability(payload["mutability"]),
            observed_or_updated_at=(
                None
                if payload.get("observed_or_updated_at") is None
                else str(payload["observed_or_updated_at"])
            ),
            validated_at=None if payload.get("validated_at") is None else str(payload["validated_at"]),
        )


@dataclass(frozen=True, slots=True)
class FreshnessPolicy:
    immutable_max_age_days: int = 3650
    mutable_revalidate_days: int = 30

    def __post_init__(self) -> None:
        if not 0 <= self.immutable_max_age_days <= 36500:
            raise ValueError("immutable_max_age_days must be between 0 and 36500")
        if not 0 <= self.mutable_revalidate_days <= 36500:
            raise ValueError("mutable_revalidate_days must be between 0 and 36500")


@dataclass(frozen=True, slots=True)
class FreshnessAssessment:
    freshness: ResearchFreshness
    as_of: str
    basis_timestamp: str | None
    age_days: int | None
    reason: str

    def __post_init__(self) -> None:
        _validate_timestamp(self.as_of, field_name="as_of")
        if self.basis_timestamp is not None:
            _validate_timestamp(self.basis_timestamp, field_name="basis_timestamp")
        if self.age_days is not None and self.age_days < 0:
            raise ValueError("Freshness age_days cannot be negative")
        if self.freshness is ResearchFreshness.CURRENT and self.basis_timestamp is None:
            raise ValueError("Current freshness requires timestamp evidence")

    def to_dict(self) -> dict[str, Any]:
        return {
            "freshness": self.freshness.value,
            "as_of": self.as_of,
            "basis_timestamp": self.basis_timestamp,
            "age_days": self.age_days,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VersionAssessment:
    observation_id: str
    constraint_id: str
    relation: VersionRelation
    reason: str

    def __post_init__(self) -> None:
        _validate_sha256(self.observation_id, field_name="observation_id")
        _validate_sha256(self.constraint_id, field_name="constraint_id")
        if not _clean(self.reason):
            raise ValueError("Version assessment reason must not be empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "observation_id": self.observation_id,
            "constraint_id": self.constraint_id,
            "relation": self.relation.value,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class VersionedClaim:
    finding_id: str
    finding_kind: ResearchFindingKind
    claim_key: str
    claim_value: str
    observation_id: str
    identity_id: str
    citation_ids: tuple[str, ...]
    freshness: ResearchFreshness
    version_relation: VersionRelation
    authority_rank: int | None = None
    claim_id: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_sha256(self.finding_id, field_name="finding_id")
        _validate_sha256(self.observation_id, field_name="observation_id")
        _validate_sha256(self.identity_id, field_name="identity_id")
        key = _clean(self.claim_key)
        value = _clean(self.claim_value)
        if not key or not value:
            raise ValueError("Versioned claims require non-empty key and value")
        citation_ids = tuple(_clean(item) for item in self.citation_ids)
        for item in citation_ids:
            _validate_sha256(item, field_name="citation_id")
        if len(set(citation_ids)) != len(citation_ids):
            raise ValueError("Versioned claim citation IDs must be unique")
        if self.finding_kind is ResearchFindingKind.SOURCE_FACT and not citation_ids:
            raise ValueError("Source-fact versioned claims require citation evidence")
        if self.authority_rank is not None and not 0 <= self.authority_rank <= 100:
            raise ValueError("authority_rank must be between 0 and 100 when provided")
        object.__setattr__(self, "claim_key", key)
        object.__setattr__(self, "claim_value", value)
        object.__setattr__(self, "citation_ids", citation_ids)
        object.__setattr__(self, "claim_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_kind": self.finding_kind.value,
            "claim_key": self.claim_key,
            "claim_value": self.claim_value,
            "observation_id": self.observation_id,
            "identity_id": self.identity_id,
            "citation_ids": list(self.citation_ids),
            "freshness": self.freshness.value,
            "version_relation": self.version_relation.value,
            "authority_rank": self.authority_rank,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["claim_id"] = self.claim_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VersionedClaim:
        claim = cls(
            finding_id=str(payload["finding_id"]),
            finding_kind=ResearchFindingKind(payload["finding_kind"]),
            claim_key=str(payload["claim_key"]),
            claim_value=str(payload["claim_value"]),
            observation_id=str(payload["observation_id"]),
            identity_id=str(payload["identity_id"]),
            citation_ids=tuple(str(item) for item in payload.get("citation_ids", [])),
            freshness=ResearchFreshness(payload["freshness"]),
            version_relation=VersionRelation(payload["version_relation"]),
            authority_rank=(
                None if payload.get("authority_rank") is None else int(payload["authority_rank"])
            ),
        )
        if str(payload.get("claim_id", "")) != claim.claim_id:
            raise ValueError("Versioned claim ID does not match canonical evidence")
        return claim


@dataclass(frozen=True, slots=True)
class SupersessionLink:
    older_claim_id: str
    newer_claim_id: str
    reason: str
    evidence_refs: tuple[str, ...]
    link_id: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_sha256(self.older_claim_id, field_name="older_claim_id")
        _validate_sha256(self.newer_claim_id, field_name="newer_claim_id")
        if self.older_claim_id == self.newer_claim_id:
            raise ValueError("Supersession link cannot self-reference")
        reason = _clean(self.reason)
        if not reason:
            raise ValueError("Supersession link reason must not be empty")
        refs = _validate_evidence_refs(self.evidence_refs, required=True)
        object.__setattr__(self, "reason", reason)
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "link_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "older_claim_id": self.older_claim_id,
            "newer_claim_id": self.newer_claim_id,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["link_id"] = self.link_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SupersessionLink:
        link = cls(
            older_claim_id=str(payload["older_claim_id"]),
            newer_claim_id=str(payload["newer_claim_id"]),
            reason=str(payload["reason"]),
            evidence_refs=tuple(str(item) for item in payload.get("evidence_refs", [])),
        )
        if str(payload.get("link_id", "")) != link.link_id:
            raise ValueError("Supersession link ID does not match canonical evidence")
        return link


@dataclass(frozen=True, slots=True)
class ConflictGroup:
    claim_key: str
    claim_ids: tuple[str, ...]
    state: ConflictState
    distinct_values: tuple[str, ...]
    supersession_link_ids: tuple[str, ...] = ()
    group_id: str = field(init=False)

    def __post_init__(self) -> None:
        key = _clean(self.claim_key)
        if not key:
            raise ValueError("Conflict group key must not be empty")
        if not self.claim_ids:
            raise ValueError("Conflict group requires at least one claim")
        for value in (*self.claim_ids, *self.supersession_link_ids):
            _validate_sha256(value, field_name="conflict group reference")
        if len(set(self.claim_ids)) != len(self.claim_ids):
            raise ValueError("Conflict group claim IDs must be unique")
        if len(set(self.supersession_link_ids)) != len(self.supersession_link_ids):
            raise ValueError("Conflict group supersession link IDs must be unique")
        values = tuple(sorted({_clean(value) for value in self.distinct_values if _clean(value)}))
        if not values:
            raise ValueError("Conflict group requires at least one distinct value")
        expected = (
            ConflictState.UNRESOLVED
            if len(self.claim_ids) == 1
            else ConflictState.AGREEMENT
            if len(values) == 1
            else ConflictState.CONFLICT
        )
        if self.state is not expected:
            raise ValueError("Conflict group state does not match visible claim values")
        object.__setattr__(self, "claim_key", key)
        object.__setattr__(self, "distinct_values", values)
        object.__setattr__(self, "group_id", _sha256(self.identity_payload()))

    def identity_payload(self) -> dict[str, Any]:
        return {
            "claim_key": self.claim_key,
            "claim_ids": list(self.claim_ids),
            "state": self.state.value,
            "distinct_values": list(self.distinct_values),
            "supersession_link_ids": list(self.supersession_link_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self.identity_payload()
        payload["group_id"] = self.group_id
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ConflictGroup:
        group = cls(
            claim_key=str(payload["claim_key"]),
            claim_ids=tuple(str(item) for item in payload["claim_ids"]),
            state=ConflictState(payload["state"]),
            distinct_values=tuple(str(item) for item in payload["distinct_values"]),
            supersession_link_ids=tuple(str(item) for item in payload.get("supersession_link_ids", [])),
        )
        if str(payload.get("group_id", "")) != group.group_id:
            raise ValueError("Conflict group ID does not match canonical evidence")
        return group


@dataclass(frozen=True, slots=True)
class VersionProvenanceReport:
    target: TargetVersionConstraint
    observations: tuple[VersionObservation, ...]
    identities: tuple[SourceIdentity, ...]
    claims: tuple[VersionedClaim, ...]
    supersession_links: tuple[SupersessionLink, ...]
    groups: tuple[ConflictGroup, ...]
    generated_at: str
    schema_version: int = VERSION_PROVENANCE_SCHEMA_VERSION
    digest_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != VERSION_PROVENANCE_SCHEMA_VERSION:
            raise ValueError("Unsupported version provenance schema version")
        _validate_timestamp(self.generated_at, field_name="generated_at")
        _require_unique_ids(self.observations, "observation_id", "observations")
        _require_unique_ids(self.identities, "identity_id", "identities")
        _require_unique_ids(self.claims, "claim_id", "claims")
        _require_unique_ids(self.supersession_links, "link_id", "supersession links")
        _require_unique_ids(self.groups, "group_id", "conflict groups")
        observation_ids = {item.observation_id for item in self.observations}
        identity_ids = {item.identity_id for item in self.identities}
        claim_ids = {item.claim_id for item in self.claims}
        link_ids = {item.link_id for item in self.supersession_links}
        for claim in self.claims:
            if claim.observation_id not in observation_ids:
                raise ValueError("Versioned claim references absent observation")
            if claim.identity_id not in identity_ids:
                raise ValueError("Versioned claim references absent source identity")
        for link in self.supersession_links:
            if link.older_claim_id not in claim_ids or link.newer_claim_id not in claim_ids:
                raise ValueError("Supersession link references absent claim")
        recomputed = build_conflict_groups(self.claims, self.supersession_links)
        if tuple(group.to_dict() for group in self.groups) != tuple(group.to_dict() for group in recomputed):
            raise ValueError("Conflict groups do not match recomputed visible evidence")
        for group in self.groups:
            if any(item not in claim_ids for item in group.claim_ids):
                raise ValueError("Conflict group references absent claim")
            if any(item not in link_ids for item in group.supersession_link_ids):
                raise ValueError("Conflict group references absent supersession link")
        object.__setattr__(self, "digest_sha256", _sha256(self._payload_without_digest()))

    def _payload_without_digest(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "target": self.target.to_dict(),
            "observations": [item.to_dict() for item in self.observations],
            "identities": [item.to_dict() for item in self.identities],
            "claims": [item.to_dict() for item in self.claims],
            "supersession_links": [item.to_dict() for item in self.supersession_links],
            "groups": [item.to_dict() for item in self.groups],
            "generated_at": self.generated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._payload_without_digest()
        payload["digest_sha256"] = self.digest_sha256
        return payload

    @classmethod
    def create(
        cls,
        *,
        target: TargetVersionConstraint,
        observations: Iterable[VersionObservation],
        identities: Iterable[SourceIdentity],
        claims: Iterable[VersionedClaim],
        supersession_links: Iterable[SupersessionLink] = (),
        generated_at: str,
    ) -> VersionProvenanceReport:
        claim_items = tuple(claims)
        link_items = tuple(supersession_links)
        return cls(
            target=target,
            observations=tuple(observations),
            identities=tuple(identities),
            claims=claim_items,
            supersession_links=link_items,
            groups=build_conflict_groups(claim_items, link_items),
            generated_at=generated_at,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> VersionProvenanceReport:
        report = cls(
            target=TargetVersionConstraint.from_dict(_require_dict(payload.get("target"), "target")),
            observations=tuple(
                VersionObservation.from_dict(_require_dict(item, "observation"))
                for item in _require_list(payload.get("observations"), "observations")
            ),
            identities=tuple(
                SourceIdentity.from_dict(_require_dict(item, "identity"))
                for item in _require_list(payload.get("identities"), "identities")
            ),
            claims=tuple(
                VersionedClaim.from_dict(_require_dict(item, "claim"))
                for item in _require_list(payload.get("claims"), "claims")
            ),
            supersession_links=tuple(
                SupersessionLink.from_dict(_require_dict(item, "supersession link"))
                for item in _require_list(payload.get("supersession_links"), "supersession_links")
            ),
            groups=tuple(
                ConflictGroup.from_dict(_require_dict(item, "conflict group"))
                for item in _require_list(payload.get("groups"), "groups")
            ),
            generated_at=str(payload["generated_at"]),
            schema_version=int(payload.get("schema_version", 0)),
        )
        stored = str(payload.get("digest_sha256", ""))
        _validate_sha256(stored, field_name="digest_sha256")
        if stored != report.digest_sha256:
            raise ValueError("Version provenance report digest does not match canonical evidence")
        return report


def target_constraint_from_project_dna(
    dna: ProjectDNA,
    *,
    scheme: VersionScheme = VersionScheme.OPAQUE,
) -> TargetVersionConstraint | None:
    dna.validate()
    if not dna.engine:
        return None
    product = dna.engine.strip()
    if dna.engine_version and dna.engine_version.strip():
        return TargetVersionConstraint(
            product=product,
            kind=VersionEvidenceKind.EXACT,
            scheme=scheme,
            value=dna.engine_version,
            evidence_refs=("project_dna:engine", "project_dna:engine_version"),
        )
    return TargetVersionConstraint(
        product=product,
        kind=VersionEvidenceKind.UNKNOWN,
        scheme=scheme,
        evidence_refs=(),
    )


def observation_from_artifact(
    artifact: ResearchArtifact,
    *,
    scheme: VersionScheme = VersionScheme.OPAQUE,
) -> VersionObservation:
    product = artifact.source.product.strip() or "unknown-product"
    if artifact.source.version.strip():
        return VersionObservation(
            product=product,
            kind=VersionEvidenceKind.EXACT,
            scheme=scheme,
            value=artifact.source.version,
            observed_at=artifact.retrieved_at,
            evidence_refs=(f"artifact:{artifact.artifact_id}:source.version",),
        )
    return VersionObservation(
        product=product,
        kind=VersionEvidenceKind.UNKNOWN,
        scheme=scheme,
        observed_at=artifact.retrieved_at,
    )


def source_identity_from_artifact(
    artifact: ResearchArtifact,
    *,
    mutability: SourceMutability,
    revision: str = "",
    evidence_refs: tuple[str, ...] = (),
) -> SourceIdentity:
    return SourceIdentity(
        locator=artifact.source.locator,
        mutability=mutability,
        source_id=artifact.source.source_id,
        revision=revision,
        snapshot_sha256=artifact.content_sha256,
        evidence_refs=evidence_refs,
    )


def assess_freshness(
    evidence: FreshnessEvidence,
    *,
    as_of: str,
    policy: FreshnessPolicy = FreshnessPolicy(),
) -> FreshnessAssessment:
    now = _validate_timestamp(as_of, field_name="as_of")
    if evidence.mutability is SourceMutability.MUTABLE:
        basis = evidence.validated_at
        max_age = policy.mutable_revalidate_days
        missing_reason = "mutable_source_has_no_revalidation_evidence"
    else:
        basis = evidence.observed_or_updated_at
        max_age = policy.immutable_max_age_days
        missing_reason = "source_has_no_observed_or_updated_timestamp"
    if basis is None:
        return FreshnessAssessment(ResearchFreshness.UNKNOWN, as_of, None, None, missing_reason)
    parsed = _validate_timestamp(basis, field_name="freshness_basis")
    delta_seconds = (now.astimezone(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    if delta_seconds < 0:
        return FreshnessAssessment(
            ResearchFreshness.UNKNOWN,
            as_of,
            basis,
            None,
            "freshness_basis_is_in_the_future",
        )
    age_days = int(delta_seconds // 86400)
    freshness = ResearchFreshness.CURRENT if age_days <= max_age else ResearchFreshness.STALE
    return FreshnessAssessment(
        freshness,
        as_of,
        basis,
        age_days,
        "within_freshness_policy" if freshness is ResearchFreshness.CURRENT else "outside_freshness_policy",
    )


def assess_version(
    observation: VersionObservation,
    target: TargetVersionConstraint,
) -> VersionAssessment:
    if observation.product.casefold() != target.product.casefold():
        return VersionAssessment(
            observation.observation_id,
            target.constraint_id,
            VersionRelation.UNKNOWN,
            "product_identity_differs",
        )
    if observation.scheme is not target.scheme:
        return VersionAssessment(
            observation.observation_id,
            target.constraint_id,
            VersionRelation.UNKNOWN,
            "version_scheme_differs",
        )
    if observation.kind is VersionEvidenceKind.UNKNOWN or target.kind is VersionEvidenceKind.UNKNOWN:
        return VersionAssessment(
            observation.observation_id,
            target.constraint_id,
            VersionRelation.UNKNOWN,
            "version_evidence_is_unknown",
        )

    if target.kind is VersionEvidenceKind.EXACT:
        target_value = target.value
        if observation.kind is VersionEvidenceKind.EXACT:
            equal = _exact_equal(observation.value, target_value, observation.scheme)
            if equal is None:
                return VersionAssessment(
                    observation.observation_id,
                    target.constraint_id,
                    VersionRelation.UNKNOWN,
                    "exact_comparison_not_supported_for_version_shape",
                )
            return VersionAssessment(
                observation.observation_id,
                target.constraint_id,
                VersionRelation.EXACT_MATCH if equal else VersionRelation.MISMATCH,
                "exact_version_evidence_matches_target" if equal else "exact_version_evidence_differs",
            )
        if observation.kind is VersionEvidenceKind.INFERRED:
            equal = _exact_equal(observation.value, target_value, observation.scheme)
            if equal is None:
                relation = VersionRelation.UNKNOWN
                reason = "inferred_comparison_not_supported_for_version_shape"
            elif equal:
                relation = VersionRelation.INFERRED_MATCH
                reason = "inferred_version_matches_but_remains_inferred"
            else:
                relation = VersionRelation.MISMATCH
                reason = "inferred_version_differs_from_target"
            return VersionAssessment(observation.observation_id, target.constraint_id, relation, reason)
        if observation.interval is None:
            raise AssertionError("range observation lost interval")
        contained = _interval_contains(observation.interval, target_value, observation.scheme)
        if contained is None:
            relation = VersionRelation.UNKNOWN
            reason = "range_comparison_not_supported_for_version_shape"
        elif contained:
            relation = VersionRelation.RANGE_MATCH
            reason = "target_exact_version_is_inside_observed_range"
        else:
            relation = VersionRelation.MISMATCH
            reason = "target_exact_version_is_outside_observed_range"
        return VersionAssessment(observation.observation_id, target.constraint_id, relation, reason)

    if target.interval is None:
        raise AssertionError("range target lost interval")
    if observation.kind in {VersionEvidenceKind.EXACT, VersionEvidenceKind.INFERRED}:
        contained = _interval_contains(target.interval, observation.value, observation.scheme)
        if contained is None:
            relation = VersionRelation.UNKNOWN
            reason = "target_range_comparison_not_supported_for_version_shape"
        elif contained and observation.kind is VersionEvidenceKind.EXACT:
            relation = VersionRelation.RANGE_MATCH
            reason = "observed_exact_version_is_inside_target_range"
        elif contained:
            relation = VersionRelation.INFERRED_MATCH
            reason = "observed_inferred_version_is_inside_target_range_but_remains_inferred"
        else:
            relation = VersionRelation.MISMATCH
            reason = "observed_version_is_outside_target_range"
        return VersionAssessment(observation.observation_id, target.constraint_id, relation, reason)

    if observation.interval is None:
        raise AssertionError("range observation lost interval")
    overlap = _intervals_overlap(observation.interval, target.interval, observation.scheme)
    if overlap is None:
        relation = VersionRelation.UNKNOWN
        reason = "range_overlap_not_supported_for_version_shape"
    elif overlap:
        relation = VersionRelation.RANGE_MATCH
        reason = "observed_and_target_version_ranges_overlap"
    else:
        relation = VersionRelation.MISMATCH
        reason = "observed_and_target_version_ranges_do_not_overlap"
    return VersionAssessment(observation.observation_id, target.constraint_id, relation, reason)


def build_conflict_groups(
    claims: Iterable[VersionedClaim],
    supersession_links: Iterable[SupersessionLink] = (),
) -> tuple[ConflictGroup, ...]:
    claim_items = tuple(claims)
    links = tuple(supersession_links)
    claims_by_key: dict[str, list[VersionedClaim]] = {}
    for claim in claim_items:
        claims_by_key.setdefault(claim.claim_key, []).append(claim)
    link_by_claim: dict[str, set[str]] = {}
    for link in links:
        link_by_claim.setdefault(link.older_claim_id, set()).add(link.link_id)
        link_by_claim.setdefault(link.newer_claim_id, set()).add(link.link_id)
    groups: list[ConflictGroup] = []
    for key in sorted(claims_by_key):
        members = sorted(claims_by_key[key], key=lambda item: item.claim_id)
        values = tuple(sorted({item.claim_value for item in members}))
        state = (
            ConflictState.UNRESOLVED
            if len(members) == 1
            else ConflictState.AGREEMENT
            if len(values) == 1
            else ConflictState.CONFLICT
        )
        related_links = tuple(
            sorted({link_id for item in members for link_id in link_by_claim.get(item.claim_id, set())})
        )
        groups.append(
            ConflictGroup(
                claim_key=key,
                claim_ids=tuple(item.claim_id for item in members),
                state=state,
                distinct_values=values,
                supersession_link_ids=related_links,
            )
        )
    return tuple(groups)


def rank_claims(
    claims: Iterable[VersionedClaim],
    identities: Iterable[SourceIdentity],
) -> tuple[VersionedClaim, ...]:
    identity_map = {identity.identity_id: identity for identity in identities}
    version_score = {
        VersionRelation.EXACT_MATCH: 4,
        VersionRelation.RANGE_MATCH: 3,
        VersionRelation.INFERRED_MATCH: 2,
        VersionRelation.UNKNOWN: 1,
        VersionRelation.MISMATCH: 0,
    }
    freshness_score = {
        ResearchFreshness.CURRENT: 2,
        ResearchFreshness.UNKNOWN: 1,
        ResearchFreshness.NOT_APPLICABLE: 1,
        ResearchFreshness.STALE: 0,
    }
    mutability_score = {
        SourceMutability.IMMUTABLE: 2,
        SourceMutability.UNKNOWN: 1,
        SourceMutability.MUTABLE: 0,
    }

    def key(claim: VersionedClaim) -> tuple[int, int, int, int, str]:
        identity = identity_map.get(claim.identity_id)
        if identity is None:
            raise ValueError("Cannot rank claim with absent source identity")
        authority = -1 if claim.authority_rank is None else claim.authority_rank
        return (
            version_score[claim.version_relation],
            authority,
            freshness_score[claim.freshness],
            mutability_score[identity.mutability],
            claim.claim_id,
        )

    return tuple(sorted(tuple(claims), key=key, reverse=True))


def _parse_semver(value: str) -> tuple[int, int, int, tuple[str, ...], tuple[str, ...]] | None:
    match = _SEMVER_RE.fullmatch(_clean(value))
    if not match:
        return None
    pre = () if match.group(4) is None else tuple(match.group(4).split("."))
    build = () if match.group(5) is None else tuple(match.group(5).split("."))
    for identifier in pre:
        if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
            return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), pre, build


def _compare_semver_precedence(left: str, right: str) -> int | None:
    left_parsed = _parse_semver(left)
    right_parsed = _parse_semver(right)
    if left_parsed is None or right_parsed is None:
        return None
    left_core = left_parsed[:3]
    right_core = right_parsed[:3]
    if left_core != right_core:
        return -1 if left_core < right_core else 1
    left_pre = left_parsed[3]
    right_pre = right_parsed[3]
    if not left_pre and not right_pre:
        return 0
    if not left_pre:
        return 1
    if not right_pre:
        return -1
    for l_item, r_item in zip(left_pre, right_pre, strict=False):
        if l_item == r_item:
            continue
        l_numeric = l_item.isdigit()
        r_numeric = r_item.isdigit()
        if l_numeric and r_numeric:
            return -1 if int(l_item) < int(r_item) else 1
        if l_numeric != r_numeric:
            return -1 if l_numeric else 1
        return -1 if l_item < r_item else 1
    if len(left_pre) == len(right_pre):
        return 0
    return -1 if len(left_pre) < len(right_pre) else 1


def _parse_pep440_simple_release(value: str) -> tuple[int, ...] | None:
    match = _PEP440_SIMPLE_RELEASE_RE.fullmatch(_clean(value))
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def _compare_pep440_simple_release(left: str, right: str) -> int | None:
    left_parts = _parse_pep440_simple_release(left)
    right_parts = _parse_pep440_simple_release(right)
    if left_parts is None or right_parts is None:
        return None
    width = max(len(left_parts), len(right_parts))
    left_padded = left_parts + (0,) * (width - len(left_parts))
    right_padded = right_parts + (0,) * (width - len(right_parts))
    if left_padded == right_padded:
        return 0
    return -1 if left_padded < right_padded else 1


def _compare_order(left: str, right: str, scheme: VersionScheme) -> int | None:
    if scheme is VersionScheme.SEMVER:
        return _compare_semver_precedence(left, right)
    if scheme is VersionScheme.PEP440:
        return _compare_pep440_simple_release(left, right)
    if _clean(left) == _clean(right):
        return 0
    return None


def _exact_equal(left: str, right: str, scheme: VersionScheme) -> bool | None:
    if scheme is VersionScheme.SEMVER:
        left_parsed = _parse_semver(left)
        right_parsed = _parse_semver(right)
        if left_parsed is None or right_parsed is None:
            return None
        return left_parsed == right_parsed
    if scheme is VersionScheme.PEP440:
        compared = _compare_pep440_simple_release(left, right)
        if compared is not None:
            return compared == 0
        if _clean(left).casefold() == _clean(right).casefold():
            return True
        return None
    return _clean(left) == _clean(right)


def _interval_contains(interval: VersionInterval, value: str, scheme: VersionScheme) -> bool | None:
    if interval.lower is not None:
        comparison = _compare_order(value, interval.lower, scheme)
        if comparison is None:
            return None
        if comparison < 0 or (comparison == 0 and not interval.include_lower):
            return False
    if interval.upper is not None:
        comparison = _compare_order(value, interval.upper, scheme)
        if comparison is None:
            return None
        if comparison > 0 or (comparison == 0 and not interval.include_upper):
            return False
    return True


def _intervals_overlap(
    left: VersionInterval,
    right: VersionInterval,
    scheme: VersionScheme,
) -> bool | None:
    if left.upper is not None and right.lower is not None:
        comparison = _compare_order(left.upper, right.lower, scheme)
        if comparison is None:
            return None
        if comparison < 0:
            return False
        if comparison == 0 and not (left.include_upper and right.include_lower):
            return False
    if right.upper is not None and left.lower is not None:
        comparison = _compare_order(right.upper, left.lower, scheme)
        if comparison is None:
            return None
        if comparison < 0:
            return False
        if comparison == 0 and not (right.include_upper and left.include_lower):
            return False
    return True


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return value


def _require_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_unique_ids(values: Iterable[Any], attribute: str, label: str) -> None:
    ids = [getattr(item, attribute) for item in values]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Version provenance {label} must be unique")
