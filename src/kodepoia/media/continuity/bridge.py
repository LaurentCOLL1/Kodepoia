from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kodepoia.media.continuity.contracts import (
    ContinuityDiffReport,
    ContinuityFact,
    ContinuityFinding,
    ContinuityRefState,
    ContinuitySeverity,
    ContinuitySnapshot,
)
from kodepoia.media.serialization import canonical_sha256


def _fact_digest(fact: ContinuityFact | None) -> str | None:
    return None if fact is None else canonical_sha256(fact.canonical())


def _finding_id(*, fact_id: str, kind: str, before: ContinuityFact | None, after: ContinuityFact | None) -> str:
    return canonical_sha256(
        {
            "fact_id": fact_id,
            "kind": kind,
            "before": _fact_digest(before),
            "after": _fact_digest(after),
        }
    )[:24]


def compare_snapshots(before: ContinuitySnapshot, after: ContinuitySnapshot) -> ContinuityDiffReport:
    if before.project_id != after.project_id:
        raise ValueError("Continuity compare requires the same project_id")
    before_map = {fact.fact_id: fact for fact in before.facts}
    after_map = {fact.fact_id: fact for fact in after.facts}
    findings: list[ContinuityFinding] = []

    for fact_id in sorted(set(before_map) | set(after_map)):
        left = before_map.get(fact_id)
        right = after_map.get(fact_id)
        if left is None:
            kind = "FACT_ADDED"
            severity = ContinuitySeverity.INFO
        elif right is None:
            kind = "FACT_MISSING"
            severity = ContinuitySeverity.ERROR
        elif left.state != right.state:
            kind = "STATE_CHANGED"
            severity = ContinuitySeverity.ERROR if right.state in {
                ContinuityRefState.MISSING,
                ContinuityRefState.DELETED,
                ContinuityRefState.CONFLICTED,
            } else ContinuitySeverity.WARNING
        elif left.value != right.value:
            kind = "VALUE_CHANGED"
            severity = ContinuitySeverity.WARNING
        elif (
            left.source_authority != right.source_authority
            or left.source_ref != right.source_ref
            or left.content_version != right.content_version
        ):
            kind = "SOURCE_CHANGED"
            severity = ContinuitySeverity.WARNING
        else:
            continue

        findings.append(
            ContinuityFinding(
                finding_id=_finding_id(fact_id=fact_id, kind=kind, before=left, after=right),
                fact_id=fact_id,
                kind=kind,
                severity=severity,
                before_state=left.state.value if left else None,
                after_state=right.state.value if right else None,
                before_digest=_fact_digest(left),
                after_digest=_fact_digest(right),
            )
        )

    return ContinuityDiffReport(before.digest(), after.digest(), tuple(findings))


@dataclass(frozen=True, slots=True)
class ContinuityBridgePackage:
    package_id: str
    source_project_id: str
    target_project_id: str
    source_artifact_revision_id: str
    snapshot: ContinuitySnapshot
    snapshot_digest: str

    def __post_init__(self) -> None:
        for value, label in (
            (self.package_id, "package_id"),
            (self.source_project_id, "source_project_id"),
            (self.target_project_id, "target_project_id"),
            (self.source_artifact_revision_id, "source_artifact_revision_id"),
        ):
            if not isinstance(value, str) or not value or len(value) > 128:
                raise ValueError(f"Invalid {label}")
        if self.source_project_id != self.snapshot.project_id:
            raise ValueError("Bridge source project must match snapshot project")
        if self.source_project_id == self.target_project_id:
            raise ValueError("Bridge package must target a different project")
        if self.snapshot_digest != self.snapshot.digest():
            raise ValueError("Bridge snapshot digest mismatch")

    def canonical(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "source_project_id": self.source_project_id,
            "target_project_id": self.target_project_id,
            "source_artifact_revision_id": self.source_artifact_revision_id,
            "snapshot_digest": self.snapshot_digest,
            "snapshot": self.snapshot.canonical(),
            "promotion_policy": "compare_only_no_canon_mutation",
        }

    def digest(self) -> str:
        return canonical_sha256(self.canonical())


def import_bridge_package(
    document: Mapping[str, Any],
    *,
    expected_target_project_id: str,
    max_facts: int = 10000,
) -> dict[str, Any]:
    required = {
        "package_id",
        "source_project_id",
        "target_project_id",
        "source_artifact_revision_id",
        "snapshot_digest",
        "snapshot",
        "promotion_policy",
    }
    if set(document) != required:
        raise ValueError("Unexpected continuity bridge package fields")
    if document["target_project_id"] != expected_target_project_id:
        raise ValueError("Continuity bridge target project mismatch")
    if document["promotion_policy"] != "compare_only_no_canon_mutation":
        raise ValueError("Continuity bridge cannot auto-promote canon")
    snapshot = document["snapshot"]
    if not isinstance(snapshot, Mapping):
        raise ValueError("Continuity bridge snapshot must be an object")
    facts = snapshot.get("facts")
    if not isinstance(facts, list) or len(facts) > max_facts:
        raise ValueError("Continuity bridge fact budget exceeded")
    computed = canonical_sha256(dict(snapshot))
    if document["snapshot_digest"] != computed:
        raise ValueError("Continuity bridge snapshot digest mismatch")
    return {
        "status": "VALIDATED",
        "target_project_id": expected_target_project_id,
        "snapshot_digest": computed,
        "fact_count": len(facts),
        "promotion_policy": document["promotion_policy"],
    }
