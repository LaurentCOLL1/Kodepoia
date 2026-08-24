from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from kodepoia.media.serialization import canonical_sha256


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_NAMESPACE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


class ContinuityScope(StrEnum):
    SHOT = "shot"
    SEQUENCE = "sequence"
    SCENE = "scene"
    PROJECT = "project"
    FRANCHISE = "franchise"


class ContinuityRefState(StrEnum):
    ACTIVE = "ACTIVE"
    STALE = "STALE"
    MISSING = "MISSING"
    DELETED = "DELETED"
    CONFLICTED = "CONFLICTED"


class ContinuitySeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


def _id(value: str, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"Invalid {label}")
    return value


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("Continuity values must be finite")
        return value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 128:
                raise ValueError("Continuity object keys must be bounded strings")
            result[key] = _json_value(item)
        return result
    raise ValueError("Continuity fact value must be JSON-compatible")


@dataclass(frozen=True, slots=True)
class ContinuityFact:
    fact_id: str
    namespace: str
    key: str
    value: Any
    source_authority: str
    source_ref: str
    content_version: str
    state: ContinuityRefState = ContinuityRefState.ACTIVE

    def __post_init__(self) -> None:
        _id(self.fact_id, "fact_id")
        if not _NAMESPACE.fullmatch(self.namespace):
            raise ValueError("Invalid continuity namespace")
        _id(self.key, "fact key")
        _id(self.source_authority, "source authority")
        _id(self.source_ref, "source ref")
        _id(self.content_version, "content version")
        object.__setattr__(self, "value", _json_value(self.value))

    def canonical(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "namespace": self.namespace,
            "key": self.key,
            "value": self.value,
            "source_authority": self.source_authority,
            "source_ref": self.source_ref,
            "content_version": self.content_version,
            "state": self.state.value,
        }


@dataclass(frozen=True, slots=True)
class ContinuitySnapshot:
    snapshot_id: str
    scope: ContinuityScope
    project_id: str
    content_version: str
    facts: tuple[ContinuityFact, ...]
    extensions: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _id(self.snapshot_id, "snapshot_id")
        _id(self.project_id, "project_id")
        _id(self.content_version, "content version")
        ids = [fact.fact_id for fact in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate continuity fact_id")
        if len(ids) > 10000:
            raise ValueError("Continuity snapshot fact budget exceeded")
        normalized: dict[str, dict[str, Any]] = {}
        for namespace, payload in self.extensions.items():
            if not _NAMESPACE.fullmatch(namespace) or "." not in namespace:
                raise ValueError("Extension namespaces must be namespaced, e.g. vendor.feature")
            if not isinstance(payload, Mapping):
                raise ValueError("Extension payload must be an object")
            normalized[namespace] = _json_value(dict(payload))
        object.__setattr__(self, "extensions", normalized)

    def canonical(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "scope": self.scope.value,
            "project_id": self.project_id,
            "content_version": self.content_version,
            "facts": [fact.canonical() for fact in sorted(self.facts, key=lambda item: item.fact_id)],
            "extensions": {key: self.extensions[key] for key in sorted(self.extensions)},
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


@dataclass(frozen=True, slots=True)
class ContinuityFinding:
    finding_id: str
    fact_id: str
    kind: str
    severity: ContinuitySeverity
    before_state: str | None
    after_state: str | None
    before_digest: str | None
    after_digest: str | None

    def canonical(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "fact_id": self.fact_id,
            "kind": self.kind,
            "severity": self.severity.value,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
        }


@dataclass(frozen=True, slots=True)
class ContinuityDiffReport:
    before_snapshot_digest: str
    after_snapshot_digest: str
    findings: tuple[ContinuityFinding, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "before_snapshot_digest": self.before_snapshot_digest,
            "after_snapshot_digest": self.after_snapshot_digest,
            "findings": [item.canonical() for item in sorted(self.findings, key=lambda item: item.finding_id)],
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())
