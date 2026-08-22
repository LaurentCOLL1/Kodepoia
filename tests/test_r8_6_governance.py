from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.assets import (
    AssetGovernanceOutcome,
    AssetGovernanceService,
    AssetId,
    AssetKind,
    AssetLicenseEvidence,
    ProjectAssetReference,
    ProvenanceRef,
    ReuseScope,
    VaultBoundary,
    VaultStore,
)
from kodepoia.kodecode.workspace import WorkspaceBoundary
from kodepoia.quality.license_bom import (
    LicenseAssertion,
    LicenseAssertionState,
    LicensePolicy,
    LicensePolicyAction,
    LicensePolicyRule,
)


def _assertion(token: str, source: str = "fixture-license") -> LicenseAssertion:
    return LicenseAssertion(LicenseAssertionState.SPDX_EXPRESSION, source, expression=token)


def _policy() -> LicensePolicy:
    return LicensePolicy(
        "asset-fixture-policy",
        rules=(
            LicensePolicyRule("MIT", LicensePolicyAction.ALLOW, "fixture-policy"),
            LicensePolicyRule("Apache-2.0", LicensePolicyAction.WARN, "fixture-policy"),
            LicensePolicyRule("GPL-3.0-only", LicensePolicyAction.DENY, "fixture-policy"),
        ),
    )


def _ingest(tmp_path: Path, *, name: str = "asset.txt", content: str = "asset"):
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    (project / name).write_text(content, encoding="utf-8")
    vault = tmp_path / "vault"
    store = VaultStore(VaultBoundary(vault))
    revision = store.ingest(
        project_boundary=WorkspaceBoundary(project),
        source_path=name,
        asset_id=AssetId.from_seed("test", name),
        kind=AssetKind.DOCUMENT,
        display_name=name,
        provenance=(ProvenanceRef("local_source", str(project / name)),),
        reuse_scope=ReuseScope.EXPORTABLE,
    )
    store.add_project_reference(
        ProjectAssetReference(
            project_id="game",
            asset_id=revision.asset_id,
            revision_id=revision.revision_id,
            target_path=f"assets/{name}",
        )
    )
    return store, revision, project


def test_unknown_license_is_blocked_before_any_export_write(tmp_path: Path) -> None:
    store, revision, _ = _ingest(tmp_path)
    service = AssetGovernanceService(store, _policy())
    export_root = tmp_path / "exports"
    boundary = WorkspaceBoundary(export_root)

    decision = service.decision(revision.revision_id, AssetLicenseEvidence(revision.revision_id))
    assert decision.outcome is AssetGovernanceOutcome.BLOCK
    with pytest.raises(PermissionError):
        service.export_project("game", {}, export_boundary=boundary, target_dir="release")
    assert not (export_root / "release").exists()
    if export_root.exists():
        assert not any(export_root.glob(".kodepoia-export-stage-*"))


def test_allowed_export_contains_attribution_bom_and_redacted_local_locator(tmp_path: Path) -> None:
    store, revision, _ = _ingest(tmp_path)
    evidence = AssetLicenseEvidence(
        revision.revision_id,
        assertions=(_assertion("MIT"),),
        creator="Example Artist",
        attribution="Example Artist — MIT fixture",
        notice="Keep this notice.",
        evidence_refs=("research:fixture",),
    )
    service = AssetGovernanceService(store, _policy())
    export_root = tmp_path / "exports"
    report = service.export_project(
        "game",
        {revision.revision_id: evidence},
        export_boundary=WorkspaceBoundary(export_root),
        target_dir="release",
    )

    assert report.exported_revision_ids == (str(revision.revision_id),)
    notices = (export_root / "release" / "ASSET_NOTICES.txt").read_text(encoding="utf-8")
    assert "Example Artist — MIT fixture" in notices
    manifest = json.loads((export_root / "release" / "ASSET_EXPORT_MANIFEST.json").read_text(encoding="utf-8"))
    component = manifest["bom"]["components"][0]
    locator = component["details"]["provenance_chain"][0]["locator"]
    assert locator.startswith("local-locator-sha256:")
    assert str(tmp_path) not in json.dumps(manifest)


def test_conflicting_license_evidence_remains_visible_and_blocks(tmp_path: Path) -> None:
    store, revision, _ = _ingest(tmp_path)
    evidence = AssetLicenseEvidence(
        revision.revision_id,
        assertions=(_assertion("MIT", "source-a"), _assertion("Apache-2.0", "source-b")),
    )
    service = AssetGovernanceService(store, _policy())
    component = service.bom_component(revision.revision_id, evidence)
    decision = service.decision(revision.revision_id, evidence)

    assert component.details["license_conflict"] is True
    assert component.details["license_assertions"] == ["MIT", "Apache-2.0"]
    assert component.concluded_license.state is LicenseAssertionState.NOASSERTION
    assert decision.outcome is AssetGovernanceOutcome.BLOCK


def test_project_bom_includes_referenced_vault_asset(tmp_path: Path) -> None:
    store, revision, _ = _ingest(tmp_path)
    service = AssetGovernanceService(store, _policy())
    evidence = AssetLicenseEvidence(revision.revision_id, assertions=(_assertion("MIT"),))
    bom = service.project_bom("game", {revision.revision_id: evidence})

    assert bom.counts["assets"] == 1
    assert bom.components[0].source_sha256 == revision.content_sha256
    assert bom.components[0].concluded_license.spdx_token == "MIT"


def test_derived_asset_retains_source_revision_requirement(tmp_path: Path) -> None:
    store, source, _ = _ingest(tmp_path, name="source.txt", content="source")
    from kodepoia.assets.transforms import (
        DeterministicTextTransform,
        TransformRecipe,
        TransformRegistry,
        TransformService,
    )

    registry = TransformRegistry()
    registry.register(DeterministicTextTransform())
    transform_service = TransformService(store, registry)
    result = transform_service.run(
        (source.revision_id,),
        TransformRecipe(
            "fixture.text-uppercase.v1",
            1,
            {"suffix": ""},
            AssetKind.DOCUMENT,
        ),
        output_asset_id=AssetId.from_seed("test", "derived.txt"),
        display_name="derived.txt",
    )
    derived_id = result.output_revision_ids[0]
    service = AssetGovernanceService(store, _policy())
    evidence = AssetLicenseEvidence(derived_id, assertions=(_assertion("MIT"),))
    component = service.bom_component(derived_id, evidence)

    assert component.details["role"] == "derived"
    assert any(item.requirement == str(source.revision_id) for item in component.requirements)
