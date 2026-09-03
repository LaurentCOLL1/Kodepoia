from __future__ import annotations

import json
from pathlib import Path

import pytest

from kodepoia.quality.build import BuildArtifact, BuildArtifactKind, BuildManifest
from kodepoia.quality.license_bom import KodeBOM
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


def _policy(*, authority: tuple[str, ...] = (".github/workflows/ci.yml",)) -> SupplyChainPolicy:
    return SupplyChainPolicy(
        policy_id="test-policy",
        pins={
            "actions/checkout": ActionPin(
                "actions/checkout",
                "v4",
                "11d5960a326750d5838078e36cf38b85af677262",
            ),
            "actions/upload-artifact": ActionPin(
                "actions/upload-artifact",
                "v4",
                "ea165f8d65b6e75b540449e92b4886f43607fa02",
            ),
        },
        require_explicit_permissions=True,
        required_contents_permission="read",
        allow_write_workflows=(),
        immutable_authority_workflows=authority,
        legacy_workflows_are_non_authoritative_for_v1_promotion=True,
        forbid_pull_request_target=True,
        forbid_untrusted_pr_shell_interpolation=True,
        forbid_parent_artifact_paths=True,
        require_exact_source_sha=True,
        require_build_manifest_binding=True,
        require_bom_evidence_binding=True,
        external_attestation_required_for_core=False,
        external_attestation_semantics="provenance_only_not_security_verdict",
    )


def _workflow_root(tmp_path: Path, text: str, *, name: str = "ci.yml") -> Path:
    workflow = tmp_path / ".github" / "workflows" / name
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(text, encoding="utf-8")
    return tmp_path


def _synthetic_build_manifest(source_sha: str) -> BuildManifest:
    artifacts = (
        BuildArtifact(
            name="kodepoia-0.1-py3-none-any.whl",
            kind=BuildArtifactKind.WHEEL,
            size_bytes=10,
            sha256=ZERO_DIGEST,
            validated=True,
            validation="synthetic validated wheel evidence",
        ),
        BuildArtifact(
            name="kodepoia-0.1.tar.gz",
            kind=BuildArtifactKind.SDIST,
            size_bytes=10,
            sha256=ONE_DIGEST,
            validated=True,
            validation="synthetic validated sdist evidence",
        ),
    )
    return BuildManifest.build(
        project_root=ROOT,
        source_sha=source_sha,
        platform="synthetic-test",
        python_version="3.12",
        artifacts=artifacts,
        generated_at="2026-09-02T00:00:00Z",
    )


def test_r16_9_policy_is_integrity_bound_and_provenance_only() -> None:
    policy = SupplyChainPolicy.load(ROOT / "configs/r16_supply_chain_policy.json")
    assert len(policy.pins) == 7
    assert len(policy.digest_sha256) == 64
    assert policy.required_contents_permission == "read"
    assert len(policy.immutable_authority_workflows) == 18
    assert (
        ".github/workflows/r16-15-project-durability-acceptance.yml"
        in policy.immutable_authority_workflows
    )
    assert policy.legacy_workflows_are_non_authoritative_for_v1_promotion
    assert policy.forbid_pull_request_target
    assert policy.forbid_untrusted_pr_shell_interpolation
    assert policy.forbid_parent_artifact_paths
    assert not policy.external_attestation_required_for_core
    assert policy.external_attestation_semantics == "provenance_only_not_security_verdict"


def test_r16_9_current_repository_authority_is_pinned_and_least_privilege() -> None:
    policy = SupplyChainPolicy.load(ROOT / "configs/r16_supply_chain_policy.json")
    audit = audit_workflows(ROOT, policy)
    assert audit.status is SupplyChainStatus.PASS
    assert not audit.blockers
    assert audit.workflow_count >= 50
    assert audit.authority_workflow_count == len(policy.immutable_authority_workflows)
    assert audit.legacy_workflow_count == audit.workflow_count - audit.authority_workflow_count
    assert audit.legacy_workflow_count >= 40
    assert audit.observations
    assert len(audit.actions) >= 20
    assert all(item.authoritative for item in audit.actions)
    assert all(len(item.commit_sha) == 40 for item in audit.actions)


def test_r16_9_mutable_authority_action_reference_fails_closed(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n",
    )
    audit = audit_workflows(root, _policy())
    assert audit.status is SupplyChainStatus.FAIL
    assert any("workflow_action_mutable_ref" in blocker for blocker in audit.blockers)


def test_r16_9_mutable_legacy_reference_is_non_authoritative_observation(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n",
        name="legacy.yml",
    )
    audit = audit_workflows(root, _policy(authority=(".github/workflows/authority.yml",)))
    assert audit.status is SupplyChainStatus.FAIL
    assert any("authority_workflow_missing" in blocker for blocker in audit.blockers)
    assert any("legacy_workflow_mutable_ref" in item for item in audit.observations)


def test_r16_9_legacy_mutable_reference_passes_when_authority_exists(tmp_path: Path) -> None:
    _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n",
        name="authority.yml",
    )
    _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n",
        name="legacy.yml",
    )
    audit = audit_workflows(tmp_path, _policy(authority=(".github/workflows/authority.yml",)))
    assert audit.status is SupplyChainStatus.PASS
    assert not audit.blockers
    assert any("legacy_workflow_mutable_ref" in item for item in audit.observations)


def test_r16_9_unapproved_action_fails_closed_even_in_legacy(tmp_path: Path) -> None:
    _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n",
        name="authority.yml",
    )
    _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: example/action@1111111111111111111111111111111111111111\n",
        name="legacy.yml",
    )
    audit = audit_workflows(tmp_path, _policy(authority=(".github/workflows/authority.yml",)))
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


def test_r16_9_pull_request_target_is_forbidden(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "on:\n  pull_request_target:\npermissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_pull_request_target_forbidden" in blocker for blocker in audit.blockers)


def test_r16_9_untrusted_pr_shell_interpolation_is_forbidden(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n"
        "      - run: echo \"${{ github.event.pull_request.title }}\"\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_untrusted_pr_shell_interpolation" in blocker for blocker in audit.blockers)


def test_r16_9_safe_exact_pr_sha_context_is_not_treated_as_shell_injection(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\nenv:\n"
        "  SOURCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}\n"
        "jobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n"
        "      - run: echo \"${{ env.SOURCE_SHA }}\"\n",
    )
    audit = audit_workflows(root, _policy())
    assert audit.status is SupplyChainStatus.PASS


def test_r16_9_parent_artifact_path_is_forbidden(tmp_path: Path) -> None:
    root = _workflow_root(
        tmp_path,
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262\n"
        "      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02\n"
        "        with:\n          path: ../outside.txt\n",
    )
    audit = audit_workflows(root, _policy())
    assert any("workflow_artifact_path_escape" in blocker for blocker in audit.blockers)


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
    assert all(item.source == "pyproject.toml" for item in first)
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


def test_r16_9_digest_only_manifest_is_not_promotable_when_binding_is_required() -> None:
    manifest = SupplyChainManifest.build(
        ROOT,
        source_sha="1" * 40,
        build_manifest_evidence_sha256=ZERO_DIGEST,
        bom_evidence_sha256=ONE_DIGEST,
    )
    assert manifest.status is SupplyChainStatus.FAIL
    assert "build_manifest_binding_unverified" in manifest.blockers
    assert "bom_evidence_binding_unverified" in manifest.blockers


def test_r16_9_manifest_binds_actual_build_and_bom_evidence() -> None:
    source_sha = "1" * 40
    build_manifest = _synthetic_build_manifest(source_sha)
    bom = KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z")
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=build_manifest,
        bom_report=bom,
    )
    assert manifest.status is SupplyChainStatus.PASS
    assert manifest.build_manifest_evidence_sha256 == build_manifest.evidence_sha256
    assert manifest.bom_evidence_sha256 == bom.evidence_sha256
    manifest.assert_promotable(
        expected_source_sha=source_sha,
        expected_evidence_sha256=manifest.evidence_sha256,
    )


def test_r16_9_build_manifest_cross_source_replay_is_blocked() -> None:
    build_manifest = _synthetic_build_manifest("1" * 40)
    bom = KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z")
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha="2" * 40,
        build_manifest=build_manifest,
        bom_report=bom,
    )
    assert manifest.status is SupplyChainStatus.FAIL
    assert "build_manifest_source_sha_mismatch" in manifest.blockers
    with pytest.raises(ValueError, match="not promotable"):
        manifest.assert_promotable(expected_source_sha="2" * 40)


def test_r16_9_cross_source_manifest_replay_is_rejected() -> None:
    source_sha = "1" * 40
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=_synthetic_build_manifest(source_sha),
        bom_report=KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z"),
    )
    with pytest.raises(ValueError, match="source SHA mismatch"):
        manifest.assert_promotable(expected_source_sha="2" * 40)


def test_r16_9_serialized_evidence_tamper_is_rejected() -> None:
    source_sha = "1" * 40
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=_synthetic_build_manifest(source_sha),
        bom_report=KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z"),
    )
    payload = manifest.to_dict()
    payload["bom_evidence_sha256"] = "2" * 64
    with pytest.raises(ValueError, match="evidence hash mismatch"):
        SupplyChainManifest.from_dict(payload)


def test_r16_9_external_attestation_is_provenance_only_not_security_verdict() -> None:
    source_sha = "1" * 40
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=_synthetic_build_manifest(source_sha),
        bom_report=KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z"),
        external_attestation=AttestationState.VERIFIED,
    )
    assert manifest.status is SupplyChainStatus.PASS
    assert manifest.external_attestation is AttestationState.VERIFIED


def test_r16_9_safe_evidence_contains_no_secret_like_field_names() -> None:
    source_sha = "1" * 40
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=_synthetic_build_manifest(source_sha),
        bom_report=KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z"),
    )
    assert not report_contains_secret_like_value(manifest.to_dict())
    assert report_contains_secret_like_value({"api_key": "synthetic-value"})


def test_r16_9_manifest_json_round_trip() -> None:
    source_sha = "1" * 40
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=_synthetic_build_manifest(source_sha),
        bom_report=KodeBOM.from_pyproject(ROOT, generated_at="2026-09-02T00:00:00Z"),
    )
    encoded = json.dumps(manifest.to_dict(), sort_keys=True)
    restored = SupplyChainManifest.from_dict(json.loads(encoded))
    assert restored == manifest
