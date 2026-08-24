from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import ActionRequest, ActionType, DecisionKind, KodeGuardian
from kodepoia.core.safe_change import SafeChangeManager
from kodepoia.media.serialization import canonical_json_bytes, canonical_sha256


_MAX_RECORDS = 4096
_MAX_REFS = 64


def _required_text(value: str, field: str, *, max_len: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ValueError(f"{field} must be non-empty and <= {max_len} characters")
    return value


def _finite_json(value: Any) -> Any:
    canonical_json_bytes({"value": value})
    return value


class CanonStatus(StrEnum):
    PROPOSED = "PROPOSED"
    REVIEWED = "REVIEWED"
    CANONICAL = "CANONICAL"
    DEPRECATED = "DEPRECATED"


class AuthorityTier(IntEnum):
    RESEARCH = 10
    PROJECT = 20
    FRANCHISE = 30


@dataclass(frozen=True, slots=True)
class FranchiseDNA:
    franchise_dna_id: str
    version: str
    compatible_project_dna_refs: tuple[str, ...]
    policies: dict[str, str]

    def __post_init__(self) -> None:
        _required_text(self.franchise_dna_id, "franchise_dna_id", max_len=128)
        _required_text(self.version, "version", max_len=64)
        if len(self.compatible_project_dna_refs) > 256 or len(set(self.compatible_project_dna_refs)) != len(self.compatible_project_dna_refs):
            raise ValueError("compatible_project_dna_refs must be unique and bounded")
        for ref in self.compatible_project_dna_refs:
            _required_text(ref, "project DNA ref", max_len=128)
        if not isinstance(self.policies, dict) or len(self.policies) > 128:
            raise ValueError("policies must be a bounded object")
        for key, value in self.policies.items():
            _required_text(key, "policy key", max_len=128)
            _required_text(value, "policy value", max_len=512)

    def canonical(self) -> dict[str, Any]:
        return {
            "franchise_dna_id": self.franchise_dna_id,
            "version": self.version,
            "compatible_project_dna_refs": sorted(self.compatible_project_dna_refs),
            "policies": {key: self.policies[key] for key in sorted(self.policies)},
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class CanonRecord:
    record_id: str
    subject: str
    predicate: str
    value: Any
    authority: AuthorityTier
    status: CanonStatus
    source_refs: tuple[str, ...]
    content_version: str
    valid_from: int | None = None
    valid_to: int | None = None
    supersedes: tuple[str, ...] = ()
    deprecates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required_text(self.record_id, "record_id", max_len=128)
        _required_text(self.subject, "subject", max_len=256)
        _required_text(self.predicate, "predicate", max_len=256)
        _required_text(self.content_version, "content_version", max_len=64)
        _finite_json(self.value)
        if not isinstance(self.authority, AuthorityTier) or not isinstance(self.status, CanonStatus):
            raise ValueError("authority/status must use typed enum values")
        if not self.source_refs or len(self.source_refs) > _MAX_REFS or len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("source_refs must be non-empty, unique and bounded")
        for ref in self.source_refs:
            _required_text(ref, "source_ref", max_len=256)
        if self.valid_from is not None and (not isinstance(self.valid_from, int) or self.valid_from < 0):
            raise ValueError("valid_from must be a non-negative integer or null")
        if self.valid_to is not None and (not isinstance(self.valid_to, int) or self.valid_to < 0):
            raise ValueError("valid_to must be a non-negative integer or null")
        if self.valid_from is not None and self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to cannot precede valid_from")
        for links, name in ((self.supersedes, "supersedes"), (self.deprecates, "deprecates")):
            if len(links) > _MAX_REFS or len(set(links)) != len(links) or self.record_id in links:
                raise ValueError(f"{name} links must be unique, bounded and non-self-referential")
            for ref in links:
                _required_text(ref, name, max_len=128)
        if self.authority is AuthorityTier.RESEARCH and self.status is CanonStatus.CANONICAL:
            raise ValueError("R7/external research authority cannot be canonical")

    def canonical(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "value": self.value,
            "authority": self.authority.name,
            "status": self.status.value,
            "source_refs": sorted(self.source_refs),
            "content_version": self.content_version,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "supersedes": sorted(self.supersedes),
            "deprecates": sorted(self.deprecates),
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class CanonSnapshot:
    snapshot_id: str
    franchise_dna_id: str
    records: tuple[CanonRecord, ...]
    previous_snapshot_digest: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.snapshot_id, "snapshot_id", max_len=128)
        _required_text(self.franchise_dna_id, "franchise_dna_id", max_len=128)
        if len(self.records) > _MAX_RECORDS:
            raise ValueError("Canon record budget exceeded")
        ids = [item.record_id for item in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Canon record IDs must be unique")
        known = set(ids)
        graph: dict[str, set[str]] = {}
        for item in self.records:
            links = set(item.supersedes) | set(item.deprecates)
            missing = links - known
            if missing:
                raise ValueError(f"Canon relation references missing records: {sorted(missing)}")
            graph[item.record_id] = links
        _reject_cycles(graph)
        if self.previous_snapshot_digest is not None and (
            len(self.previous_snapshot_digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.previous_snapshot_digest)
        ):
            raise ValueError("previous_snapshot_digest must be lowercase SHA-256 or null")

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "franchise_dna_id": self.franchise_dna_id,
            "records": [item.canonical() for item in sorted(self.records, key=lambda item: item.record_id)],
            "previous_snapshot_digest": self.previous_snapshot_digest,
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ConflictFinding:
    subject: str
    predicate: str
    record_ids: tuple[str, ...]
    kind: str

    @property
    def finding_id(self) -> str:
        return canonical_sha256(
            {
                "subject": self.subject,
                "predicate": self.predicate,
                "record_ids": sorted(self.record_ids),
                "kind": self.kind,
            }
        )[:24]


class CanonConflictError(ValueError):
    pass


def _reject_cycles(graph: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError("Circular canon supersession/deprecation is forbidden")
        if node in visited:
            return
        visiting.add(node)
        for target in sorted(graph[node]):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node)


def _overlap(a: CanonRecord, b: CanonRecord) -> bool:
    a_start = 0 if a.valid_from is None else a.valid_from
    b_start = 0 if b.valid_from is None else b.valid_from
    a_end = 2**63 - 1 if a.valid_to is None else a.valid_to
    b_end = 2**63 - 1 if b.valid_to is None else b.valid_to
    return max(a_start, b_start) <= min(a_end, b_end)


def _same_value(a: CanonRecord, b: CanonRecord) -> bool:
    return canonical_json_bytes({"value": a.value}) == canonical_json_bytes({"value": b.value})


def detect_conflicts(snapshot: CanonSnapshot) -> tuple[ConflictFinding, ...]:
    active = [item for item in snapshot.records if item.status is CanonStatus.CANONICAL]
    findings: dict[tuple[str, str, tuple[str, ...], str], ConflictFinding] = {}
    for index, left in enumerate(active):
        for right in active[index + 1 :]:
            if left.subject != right.subject or left.predicate != right.predicate or not _overlap(left, right) or _same_value(left, right):
                continue
            kind = "CONFLICTED" if left.authority == right.authority else "SHADOWED_BY_HIGHER_AUTHORITY"
            record_ids = tuple(sorted((left.record_id, right.record_id)))
            finding = ConflictFinding(left.subject, left.predicate, record_ids, kind)
            findings[(finding.subject, finding.predicate, finding.record_ids, finding.kind)] = finding
    return tuple(sorted(findings.values(), key=lambda item: item.finding_id))


def query_canon(snapshot: CanonSnapshot, *, subject: str, predicate: str, point: int | None = None) -> CanonRecord | None:
    _required_text(subject, "subject")
    _required_text(predicate, "predicate")
    candidates = []
    for item in snapshot.records:
        if item.status is not CanonStatus.CANONICAL or item.subject != subject or item.predicate != predicate:
            continue
        if point is not None:
            if item.valid_from is not None and point < item.valid_from:
                continue
            if item.valid_to is not None and point > item.valid_to:
                continue
        candidates.append(item)
    if not candidates:
        return None
    highest = max(item.authority for item in candidates)
    top = sorted((item for item in candidates if item.authority == highest), key=lambda item: item.record_id)
    values = {canonical_sha256({"value": item.value}) for item in top}
    if len(values) > 1:
        raise CanonConflictError("Ambiguous highest-authority canonical facts remain CONFLICTED")
    return top[0]


def transition_record(record: CanonRecord, to_status: CanonStatus) -> CanonRecord:
    allowed = {
        CanonStatus.PROPOSED: {CanonStatus.REVIEWED},
        CanonStatus.REVIEWED: {CanonStatus.CANONICAL},
        CanonStatus.CANONICAL: {CanonStatus.DEPRECATED},
        CanonStatus.DEPRECATED: set(),
    }
    if to_status not in allowed[record.status]:
        raise ValueError(f"Invalid canon transition: {record.status.value} -> {to_status.value}")
    if to_status is CanonStatus.CANONICAL and record.authority is AuthorityTier.RESEARCH:
        raise ValueError("R7/external research suggestions cannot auto-promote to canon")
    return replace(record, status=to_status)


class CanonRepository:
    """Durable snapshot writer constrained by existing Guardian/SafeChange/Audit foundations."""

    def __init__(
        self,
        *,
        project_root: Path,
        snapshot_root: Path,
        guardian: KodeGuardian,
        audit: AuditLog,
    ) -> None:
        self.project_root = project_root.resolve(strict=False)
        self.guardian = guardian
        self.audit = audit
        self.safe_change = SafeChangeManager(self.project_root, snapshot_root)

    def persist_snapshot(self, relative_path: Path, snapshot: CanonSnapshot, *, actor: str) -> dict[str, Any]:
        target = self.safe_change.ensure_inside_project(self.project_root / relative_path)
        decision = self.guardian.authorize(
            ActionRequest(ActionType.WRITE, actor=actor, target=str(target), project_root=self.project_root)
        )
        if decision.kind is not DecisionKind.ALLOW:
            raise PermissionError(f"Guardian did not allow canon persistence: {decision.reason}")
        backup = self.safe_change.snapshot([target]) if decision.snapshot_required else None
        target.parent.mkdir(parents=True, exist_ok=True)
        document = snapshot.canonical()
        payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(payload, encoding="utf-8")
        temporary.replace(target)
        event = self.audit.append(
            "canon",
            "persist_snapshot",
            actor,
            "success",
            {
                "target": target.relative_to(self.project_root).as_posix(),
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_digest": snapshot.digest(),
                "backup": None if backup is None else backup.name,
            },
        )
        return {
            "status": "PERSISTED",
            "snapshot_digest": snapshot.digest(),
            "backup_created": backup is not None,
            "audit_event_hash": event.event_hash,
        }
