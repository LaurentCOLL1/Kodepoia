from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.media.franchise import (
    AuthorityTier,
    CanonConflictError,
    CanonRecord,
    CanonRepository,
    CanonSnapshot,
    CanonStatus,
    FranchiseDNA,
    detect_conflicts,
    query_canon,
    transition_record,
)


ROOT = Path(__file__).resolve().parents[1]


def _record(
    record_id: str,
    value: object,
    *,
    subject: str = "character.alex",
    predicate: str = "home",
    authority: AuthorityTier = AuthorityTier.FRANCHISE,
    status: CanonStatus = CanonStatus.CANONICAL,
    valid_from: int | None = None,
    valid_to: int | None = None,
    supersedes: tuple[str, ...] = (),
    deprecates: tuple[str, ...] = (),
) -> CanonRecord:
    return CanonRecord(
        record_id,
        subject,
        predicate,
        value,
        authority,
        status,
        (f"fixture:{record_id}",),
        "content.v1",
        valid_from,
        valid_to,
        supersedes,
        deprecates,
    )


def test_franchise_dna_identity_is_order_independent_and_separate_from_project_dna() -> None:
    first = FranchiseDNA("franchise.alpha", "1", ("project.dna.b", "project.dna.a"), {"locale": "fr-FR", "rating": "adult"})
    second = FranchiseDNA("franchise.alpha", "1", ("project.dna.a", "project.dna.b"), {"rating": "adult", "locale": "fr-FR"})
    assert first.canonical() == second.canonical()
    assert first.digest() == second.digest()
    assert first.canonical()["franchise_dna_id"] != first.canonical()["compatible_project_dna_refs"][0]


def test_canon_snapshot_is_order_independent_and_history_bound() -> None:
    a = _record("canon.a", "home")
    b = _record("canon.b", "school", predicate="school")
    first = CanonSnapshot("snapshot.1", "franchise.alpha", (a, b))
    second = CanonSnapshot("snapshot.1", "franchise.alpha", (b, a))
    assert first.canonical() == second.canonical()
    assert first.digest() == second.digest()
    historical = CanonSnapshot("snapshot.2", "franchise.alpha", (a, b), first.digest())
    assert historical.previous_snapshot_digest == first.digest()


def test_graph_integrity_rejects_missing_self_and_circular_relations() -> None:
    missing = _record("canon.new", "x", supersedes=("canon.missing",))
    with pytest.raises(ValueError, match="missing records"):
        CanonSnapshot("snap.missing", "franchise.alpha", (missing,))

    with pytest.raises(ValueError, match="non-self"):
        _record("canon.self", "x", supersedes=("canon.self",))

    a = _record("canon.a", "x", supersedes=("canon.b",))
    b = _record("canon.b", "y", supersedes=("canon.a",))
    with pytest.raises(ValueError, match="Circular"):
        CanonSnapshot("snap.cycle", "franchise.alpha", (a, b))


def test_conflicts_are_deterministic_and_query_refuses_ambiguous_top_authority() -> None:
    a = _record("canon.a", "Paris", valid_from=1, valid_to=10)
    b = _record("canon.b", "Lyon", valid_from=5, valid_to=12)
    snapshot = CanonSnapshot("snap.conflict", "franchise.alpha", (b, a))
    findings = detect_conflicts(snapshot)
    assert len(findings) == 1
    assert findings[0].kind == "CONFLICTED"
    assert findings[0].record_ids == ("canon.a", "canon.b")
    assert findings[0].finding_id == detect_conflicts(snapshot)[0].finding_id
    with pytest.raises(CanonConflictError, match="CONFLICTED"):
        query_canon(snapshot, subject="character.alex", predicate="home", point=7)


def test_higher_authority_wins_deterministically_but_conflict_remains_visible() -> None:
    project = _record("canon.project", "Paris", authority=AuthorityTier.PROJECT)
    franchise = _record("canon.franchise", "Lyon", authority=AuthorityTier.FRANCHISE)
    snapshot = CanonSnapshot("snap.authority", "franchise.alpha", (project, franchise))
    findings = detect_conflicts(snapshot)
    assert [item.kind for item in findings] == ["SHADOWED_BY_HIGHER_AUTHORITY"]
    selected = query_canon(snapshot, subject="character.alex", predicate="home")
    assert selected is not None and selected.record_id == "canon.franchise"


def test_workflow_is_one_way_and_r7_research_cannot_be_promoted_to_canon() -> None:
    proposed = _record("canon.proposal", "Paris", authority=AuthorityTier.RESEARCH, status=CanonStatus.PROPOSED)
    reviewed = transition_record(proposed, CanonStatus.REVIEWED)
    assert reviewed.status is CanonStatus.REVIEWED
    with pytest.raises(ValueError, match="research suggestions"):
        transition_record(reviewed, CanonStatus.CANONICAL)
    with pytest.raises(ValueError, match="Invalid canon transition"):
        transition_record(reviewed, CanonStatus.PROPOSED)


def test_project_fact_can_progress_reviewed_canonical_deprecated_without_mutating_prior_versions() -> None:
    proposed = _record("canon.workflow", "Paris", authority=AuthorityTier.PROJECT, status=CanonStatus.PROPOSED)
    reviewed = transition_record(proposed, CanonStatus.REVIEWED)
    canonical = transition_record(reviewed, CanonStatus.CANONICAL)
    deprecated = transition_record(canonical, CanonStatus.DEPRECATED)
    assert proposed.status is CanonStatus.PROPOSED
    assert reviewed.status is CanonStatus.REVIEWED
    assert canonical.status is CanonStatus.CANONICAL
    assert deprecated.status is CanonStatus.DEPRECATED


def test_nonfinite_canon_values_fail_closed() -> None:
    with pytest.raises(ValueError):
        _record("canon.nan", float("nan"))


def test_guardian_safechange_and_audit_wrap_durable_snapshot_promotion(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    target = project / "canon" / "current.json"
    target.parent.mkdir()
    target.write_text('{"old":true}\n', encoding="utf-8")

    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(project,)))
    audit = AuditLog(project / ".kodepoia" / "audit.jsonl")
    repository = CanonRepository(
        project_root=project,
        snapshot_root=project / ".kodepoia" / "snapshots",
        guardian=KodeGuardian(permissions),
        audit=audit,
    )
    snapshot = CanonSnapshot("snap.persist", "franchise.alpha", (_record("canon.persist", "Paris"),))
    result = repository.persist_snapshot(Path("canon/current.json"), snapshot, actor="fixture")
    assert result["status"] == "PERSISTED"
    assert result["backup_created"] is True
    assert result["snapshot_digest"] == snapshot.digest()
    assert json.loads(target.read_text(encoding="utf-8"))["snapshot_id"] == "snap.persist"
    assert audit.verify()
    backups = list((project / ".kodepoia" / "snapshots").glob("*/canon/current.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == '{"old":true}\n'


def test_guardian_permission_scope_blocks_canon_write_outside_granted_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    allowed = project / "allowed"
    allowed.mkdir(parents=True)
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(allowed,)))
    repository = CanonRepository(
        project_root=project,
        snapshot_root=project / ".snapshots",
        guardian=KodeGuardian(permissions),
        audit=AuditLog(project / ".audit.jsonl"),
    )
    snapshot = CanonSnapshot("snap.block", "franchise.alpha", ())
    with pytest.raises(Exception, match="Path outside permitted roots"):
        repository.persist_snapshot(Path("canon/current.json"), snapshot, actor="fixture")


def test_r11_11_schemas_accept_canonical_examples() -> None:
    dna = FranchiseDNA("franchise.alpha", "1", ("project.dna.a",), {"locale": "fr-FR"})
    snapshot = CanonSnapshot("snapshot.schema", dna.franchise_dna_id, (_record("canon.schema", "Paris"),))
    dna_schema = json.loads((ROOT / "schemas/r11/franchise-dna.schema.json").read_text(encoding="utf-8"))
    snapshot_schema = json.loads((ROOT / "schemas/r11/canon-snapshot.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(dna_schema).validate(dna.canonical())
    Draft202012Validator(snapshot_schema).validate(snapshot.canonical())
