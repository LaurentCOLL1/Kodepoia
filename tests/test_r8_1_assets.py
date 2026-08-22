from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.assets import (
    AssetId,
    AssetKind,
    AssetRecord,
    AssetRevision,
    AssetRole,
    AssetStatus,
    PreservationPolicy,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
    VaultBoundary,
    VaultViolation,
    load_asset_record,
    load_asset_revision,
    load_project_reference,
    verify_content,
)
from kodepoia.assets.serialization import (
    asset_record_document,
    asset_revision_document,
    project_reference_document,
)

ROOT = Path(__file__).resolve().parents[1]


def _revision(content: bytes = b"kodepoia-r8") -> AssetRevision:
    asset_id = AssetId.from_seed("tests", "wood-crate")
    return AssetRevision.create(
        asset_id=asset_id,
        role=AssetRole.SOURCE,
        kind=AssetKind.MODEL_3D,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_length=len(content),
        reuse_scope=ReuseScope.VAULT_LOCAL,
        preservation=PreservationPolicy.PINNED_SOURCE,
        provenance=(ProvenanceRef("local", "fixtures/wood-crate.glb"),),
        status=AssetStatus.READY,
    )


def test_ids_are_deterministic_and_revision_identity_ignores_runtime_status() -> None:
    first = AssetId.from_seed("tests", "wood-crate")
    second = AssetId.from_seed("tests", "wood-crate")
    assert first == second
    ready = _revision()
    staged = AssetRevision.create(
        asset_id=ready.asset_id,
        role=ready.role,
        kind=ready.kind,
        content_sha256=ready.content_sha256,
        content_length=ready.content_length,
        reuse_scope=ready.reuse_scope,
        preservation=ready.preservation,
        provenance=ready.provenance,
        lineage=ready.lineage,
        status=AssetStatus.STAGED,
    )
    assert ready.revision_id == staged.revision_id


def test_manifest_round_trip_and_tamper_rejection() -> None:
    revision = _revision()
    document = asset_revision_document(revision)
    assert load_asset_revision(document) == revision
    tampered = json.loads(json.dumps(document))
    tampered["payload"]["content_length"] += 1
    with pytest.raises(ValueError, match="does not match"):
        load_asset_revision(tampered)


def test_record_and_project_reference_round_trip() -> None:
    revision = _revision()
    record = AssetRecord(revision.asset_id, revision.kind, "Wood Crate", ("crate", "wood", "crate"), revision.revision_id)
    reference = ProjectAssetReference("project-a", revision.asset_id, revision.revision_id, "assets/crate.glb", {"purpose": "prop"})
    assert load_asset_record(asset_record_document(record)) == record
    assert load_project_reference(project_reference_document(reference)) == reference


def test_json_schemas_validate_documents() -> None:
    revision = _revision()
    record = AssetRecord(revision.asset_id, revision.kind, "Wood Crate", current_revision_id=revision.revision_id)
    reference = ProjectAssetReference("project-a", revision.asset_id, revision.revision_id)
    cases = [
        ("asset-record-v1.schema.json", asset_record_document(record)),
        ("asset-revision-v1.schema.json", asset_revision_document(revision)),
        ("project-asset-reference-v1.schema.json", project_reference_document(reference)),
    ]
    for schema_name, document in cases:
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator(schema).validate(document)


def test_verify_content_fails_closed(tmp_path: Path) -> None:
    payload = b"immutable-source"
    source = tmp_path / "source.bin"
    source.write_bytes(payload)
    verify_content(source, hashlib.sha256(payload).hexdigest(), len(payload))
    with pytest.raises(ValueError, match="length mismatch"):
        verify_content(source, hashlib.sha256(payload).hexdigest(), len(payload) + 1)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_content(source, "0" * 64, len(payload))


def test_vault_boundary_rejects_absolute_traversal_and_symlink_escape(tmp_path: Path) -> None:
    root = tmp_path / "vault"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    boundary = VaultBoundary(root)
    assert boundary.resolve("objects/item").is_relative_to(root)
    with pytest.raises(VaultViolation):
        boundary.resolve("../outside")
    with pytest.raises(VaultViolation):
        boundary.resolve(outside)
    link = root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable on this runner")
    with pytest.raises(VaultViolation):
        boundary.resolve("escape/secret.bin")
