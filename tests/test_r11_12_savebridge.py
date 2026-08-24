from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.core.audit import AuditLog
from kodepoia.core.guardian import KodeGuardian
from kodepoia.core.permissions import Capability, PermissionGrant, PermissionSet
from kodepoia.core.recovery import RecoveryJournal
from kodepoia.media.savebridge import (
    CompatibilityState,
    MigrationRegistry,
    MigrationStep,
    SaveBridgeStore,
    build_save_document,
    check_compatibility,
    migrate_document,
    parse_save_document,
)
from kodepoia.media.serialization import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
CANON_DIGEST = "a" * 64


def _v1_to_v2(state: dict[str, object]) -> dict[str, object]:
    result = dict(state)
    result["coins"] = int(result.pop("money", 0))
    return result


def _v2_to_v3(state: dict[str, object]) -> dict[str, object]:
    result = dict(state)
    result.setdefault("difficulty", "normal")
    return result


def _v2_to_v1(state: dict[str, object]) -> dict[str, object]:
    return dict(state)


def _registry() -> MigrationRegistry:
    registry = MigrationRegistry()
    registry.register(MigrationStep("save.v1-v2", 1, 2, _v1_to_v2))
    registry.register(MigrationStep("save.v2-v3", 2, 3, _v2_to_v3))
    return registry


def _document(version: int = 1):
    state = {"player": {"name": "Alex"}, "money": 42} if version == 1 else {"player": {"name": "Alex"}, "coins": 42}
    return build_save_document(
        schema_id="save.main",
        schema_version=version,
        project_id="project.alpha",
        franchise_dna_id="franchise.alpha",
        content_version="content.v1",
        canon_snapshot_digest=CANON_DIGEST,
        state=state,
        extensions={"kodepoia.scene": {"scene_id": "scene.main"}},
    )


def test_save_document_roundtrip_checksum_and_namespaced_extensions() -> None:
    document = _document()
    encoded = json.dumps(document.canonical(), ensure_ascii=False)
    parsed = parse_save_document(encoded)
    assert parsed == document
    assert parsed.verify()
    with pytest.raises(ValueError, match="namespaced"):
        build_save_document(
            schema_id="save.main",
            schema_version=1,
            project_id="project.alpha",
            franchise_dna_id="franchise.alpha",
            content_version="v1",
            canon_snapshot_digest=CANON_DIGEST,
            state={},
            extensions={"bad": {}},
        )


def test_tampered_truncated_and_unknown_fields_fail_closed() -> None:
    data = _document().canonical()
    data["state"]["money"] = 999
    with pytest.raises(ValueError, match="checksum mismatch"):
        parse_save_document(data)
    with pytest.raises(ValueError, match="corrupt or truncated"):
        parse_save_document('{"schema_id":')
    extra = _document().canonical()
    extra["unexpected"] = True
    with pytest.raises(ValueError, match="fields are invalid"):
        parse_save_document(extra)


def test_compatibility_reports_newer_and_migration_required_without_downgrade() -> None:
    registry = _registry()
    required = check_compatibility(_document(1), target_schema_version=3, registry=registry)
    assert required.state is CompatibilityState.MIGRATION_REQUIRED
    assert required.migration_step_ids == ("save.v1-v2", "save.v2-v3")
    newer = check_compatibility(_document(3), target_schema_version=2, registry=registry)
    assert newer.state is CompatibilityState.UNSUPPORTED_NEWER
    with pytest.raises(ValueError, match="UNSUPPORTED_NEWER"):
        migrate_document(_document(3), target_schema_version=2, registry=registry)


def test_migration_is_deterministic_idempotent_and_cannot_rewrite_canon_reference() -> None:
    registry = _registry()
    source = _document(1)
    migrated, report = migrate_document(source, target_schema_version=3, registry=registry)
    assert migrated.schema_version == 3
    assert migrated.state == {"player": {"name": "Alex"}, "coins": 42, "difficulty": "normal"}
    assert migrated.project_id == source.project_id
    assert migrated.franchise_dna_id == source.franchise_dna_id
    assert migrated.canon_snapshot_digest == source.canon_snapshot_digest
    assert report.migration_step_ids == ("save.v1-v2", "save.v2-v3")
    again, second = migrate_document(migrated, target_schema_version=3, registry=registry)
    assert again == migrated
    assert second.migration_step_ids == ()


def test_migration_graph_cycle_and_missing_path_fail_closed() -> None:
    registry = MigrationRegistry()
    registry.register(MigrationStep("a", 1, 2, _v1_to_v2))
    with pytest.raises(ValueError, match="cycle"):
        registry.register(MigrationStep("b", 2, 1, _v2_to_v1))
    with pytest.raises(ValueError, match="No bounded migration path"):
        registry.path(1, 5)


def _store(tmp_path: Path, *, verifier=None) -> tuple[SaveBridgeStore, Path, AuditLog, RecoveryJournal]:
    project = tmp_path / "project"
    saves = project / "saves"
    saves.mkdir(parents=True)
    target = saves / "slot1.json"
    target.write_text(json.dumps(_document().canonical(), sort_keys=True) + "\n", encoding="utf-8")
    permissions = PermissionSet()
    permissions.grant(PermissionGrant(Capability.FILE_WRITE, roots=(project,)))
    audit = AuditLog(project / ".kodepoia" / "audit.jsonl")
    recovery = RecoveryJournal(project / ".kodepoia" / "savebridge-recovery.json")
    store = SaveBridgeStore(
        project_root=project,
        snapshot_root=project / ".kodepoia" / "safe-change",
        backup_root=tmp_path / "backups",
        guardian=KodeGuardian(permissions),
        audit=audit,
        recovery=recovery,
        post_write_verifier=verifier,
    )
    return store, target, audit, recovery


def test_dry_run_never_mutates_bytes(tmp_path: Path) -> None:
    store, target, _audit, recovery = _store(tmp_path)
    before = target.read_bytes()
    report = store.migrate_file(Path("saves/slot1.json"), target_schema_version=3, registry=_registry(), actor="fixture", dry_run=True)
    assert report["status"] == "DRY_RUN"
    assert target.read_bytes() == before
    assert recovery.load() is None


def test_durable_migration_creates_verified_backup_safechange_and_audit(tmp_path: Path) -> None:
    store, target, audit, recovery = _store(tmp_path)
    before = target.read_bytes()
    report = store.migrate_file(Path("saves/slot1.json"), target_schema_version=3, registry=_registry(), actor="fixture", dry_run=False)
    assert report["status"] == "MIGRATED"
    assert report["backup_verified"] is True
    assert report["safe_snapshot_created"] is True
    after = parse_save_document(target.read_bytes())
    assert after.schema_version == 3
    assert canonical_sha256(after.canonical()) == report["after_digest"]
    assert target.read_bytes() != before
    assert recovery.load() is None
    assert audit.verify()
    snapshots = list((target.parents[1] / ".kodepoia" / "safe-change").glob("*/saves/slot1.json"))
    assert len(snapshots) == 1
    assert snapshots[0].read_bytes() == before


def test_injected_post_write_failure_rolls_back_exact_prior_bytes(tmp_path: Path) -> None:
    def fail(_document) -> None:
        raise RuntimeError("fixture verification failure")

    store, target, audit, recovery = _store(tmp_path, verifier=fail)
    before = target.read_bytes()
    with pytest.raises(RuntimeError, match="fixture verification failure"):
        store.migrate_file(Path("saves/slot1.json"), target_schema_version=3, registry=_registry(), actor="fixture", dry_run=False)
    assert target.read_bytes() == before
    checkpoint = recovery.load()
    assert checkpoint is not None and checkpoint.phase == "rolled_back"
    assert audit.verify()


def test_corrupt_input_compatibility_is_explicit() -> None:
    report = check_compatibility(b"{bad", target_schema_version=3, registry=_registry())
    assert report.state is CompatibilityState.CORRUPT


def test_r11_12_schema_accepts_canonical_document() -> None:
    schema = json.loads((ROOT / "schemas/r11/savebridge-document.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(_document().canonical())
