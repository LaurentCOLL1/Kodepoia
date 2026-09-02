from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.quality.supply_chain import (
    ActionPin,
    AttestationState,
    SupplyChainManifest,
    SupplyChainPolicy,
    SupplyChainStatus,
    audit_workflows,
    declared_dependencies,
    report_contains_secret_like_value,
)

ROOT = Path(__file__).resolve().parents[1]
ZERO_DIGEST = "0" * 64
ONE_DIGEST = "1" * 64


def _policy() -> SupplyChainPolicy:
    return SupplyChainPolicy(
        policy_id="test-policy",
        pins={
            "actions/checkout": ActionPin(
                "actions/checkout",
                "v4",
                "11d5960a326750d5838078e36cf38b85af677262",
            )
        },
        require_explicit_permissions=True,
        required_contents_permission="read",
        allow_write_workflows=(),
        require_exact_source_sha=True,
        require_build_manifest_binding=True,
        require_bom_evidence_binding=True,
        external_attestation_required_for_core=False,
        external_attestation_semantics="provenance_only_not_security_verdict",
    )


def _workflow_root(tmp_path: Path, text: str) -> Path:
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(text, encoding="utf-8")
    return tmp_path


def test_r16_9_policy_is_integrity_bound_and_provenance_only() -> None:
    policy = SupplyChainPolicy.load(ROOT / "configs/r16_supply_chain_policy.json")
    assert len(policy.pins) == 7
    assert len(policy.digest_sha256) == 64
    assert policy.required_contents_permission == "read"
    assert not policy.external_attestation_required_for_core
    assert policy.external_attestation_semantics == "provenance_only_not_security_verdict"


def test_r16_9_current_repository_workflows_are_pinned_and_least_privilege() -> None:
    policy = SupplyChainPolicy.load(ROOT / "configs/r16_supply_chain_policy.json")
    audit = audit_workflows(ROOT, policy)
    assert audit.status is SupplyChainStatus.PASS
    assert not audit.blockers
    assert audit.workflow_count >= 50
    assert len(audit.actions) >= 100
    assert all(len(item.commit_sha) == 40 for item in audit.actions)


def test_r16_9_mutable_action_reference_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n",
    )
    audit = audit_workflows(root, _policy())
    assert audit.status is SupplyChainStatus.FAIL
    assert any("workflow_action_mutable_ref" in blocker for blocker in audit.blockers)


def test_r16_9_unapproved_action_pin_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: example/action@1111111111111111111111111111111111111111\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_action_unapproved" in blocker for blocker in audit.blockers)


def test_r16_9_wrong_commit_for_approved_action_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@1111111111111111111111111111111111111111\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_action_pin_drift" in blocker for blocker in audit.blockers)


def test_r16_9_write_permission_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: write\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_write_permission" in blocker for blocker in audit.blockers)


def test_r16_9_missing_explicit_permissions_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "jobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_permissions_missing" in blocker for blocker in audit.blockers)


def test_r16_9_local_action_does_not_require_external_pin(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: ./local-action\n",
    )
    audit = audit_workflows(root, _policy())
    assert audit.status is SupplyChainStatus.PASS
    assert not audit.actions


def test_r16_9_declared_dependency_inventory_is_deterministic() -> None:
    first = declared_dependencies(ROOT)
    second = declared_dependencies(ROOT)
    assert first == second
    assert len(first) >= 10
    assert {item.group for item in first} >= {"build-system", "runtime", "optional:dev"}
    assert all(len(item.declaration_sha256) == 64 for item in first)


def test_r16_9_dependency_declaration_change_changes_digest(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[build-system]\nrequires=["hatchling>=1"]\n'
        '[project]\nname="x"\nversion="0"\ndependencies=["demo>=1"]\n',
        encoding="utf-8",
    )
    first = declared_dependencies(tmp_path)
    pyproject.write_text(
        '[build-system]\nrequires=["hatchling>=1"]\n'
        '[project]\nname="x"\nversion="0"\ndependencies=["demo>=2"]\n',
        encoding="utf-8",
    )
    second = declared_dependencies(tmp_path)
    assert first != second
    assert first[-1].declaration_sha256 != second[-1].declaration_sha256


def test_r16_9_manifest_binds_source_build_bom_policy_and_workflows() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    assert manifest.status is SupplyChainStatus.PASS
    assert manifest.external_attestation is AttestationState.NOT_EXERCISED
    manifest.assert_promotable(
        expected_source_sha="1" * 40,
        expected_evidence_sha256=manifest.evidence_sha256,
    )


def test_r16_9_cross_source_replay_is_rejected() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    with pytest.raises(ValueError, match="source SHA mismatch"):
        manifest.assert_promotable(expected_source_sha="2" * 40)


def test_r16_9_serialized_evidence_tamper_is_rejected() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    payload = manifest.to_dict()
    payload["bom_evidence_sha256"] = "2" * 64
    with pytest.raises(ValueError, match="evidence hash mismatch"):
        SupplyChainManifest.from_dict(payload)


def test_r16_9_build_and_bom_evidence_require_sha256() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        SupplyChainManifest.build(
            ROOT,
            source_sha="1" * 40,
            build_manifest_evidence_sha256="not-a-digest",
            bom_evidence_sha256=ONE_DIGEST,
        )


def test_r16_9_external_attestation_is_not_security_verdict() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
        external_attestation=AttestationState.VERIFIED,
    )
    assert manifest.status is SupplyChainStatus.PASS
    assert manifest.external_attestation is AttestationState.VERIFIED


def test_r16_9_safe_evidence_contains_no_secret_like_field_names() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    assert not report_contains_secret_like_value(manifest.to_dict())
    assert report_contains_secret_like_value({"api_key": "synthetic-value"})


def test_r16_9_manifest_json_round_trip() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    encoded = json.dumps(manifest.to_dict(), sort_keys=True)
    restored = SupplyChainManifest.from_dict(json.loads(encoded))
    assert restored == manifest
