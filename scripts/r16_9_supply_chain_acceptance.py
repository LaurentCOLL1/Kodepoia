from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from kodepoia.quality.build import KodeBuild
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
    repository_supply_chain_digest,
)

ROOT = Path(__file__).resolve().parents[1]


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_payload(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _case(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "detail": detail}


def _synthetic_policy() -> SupplyChainPolicy:
    return SupplyChainPolicy(
        policy_id="r16.9-synthetic",
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
        immutable_authority_workflows=(".github/workflows/ci.yml",),
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


def _synthetic_audit(workflow_text: str):
    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-9-audit-") as tmp:
        root = Path(tmp)
        workflow = root / ".github" / "workflows" / "ci.yml"
        workflow.parent.mkdir(parents=True)
        workflow.write_text(workflow_text, encoding="utf-8")
        return audit_workflows(root, _synthetic_policy())


def _tamper_cases() -> list[dict[str, Any]]:
    pinned = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
    cases: list[dict[str, Any]] = []

    mutable = _synthetic_audit(
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n"
    )
    cases.append(
        _case(
            "mutable-authority-ref",
            any("workflow_action_mutable_ref" in value for value in mutable.blockers),
            "security authority workflow rejects a mutable external-action ref",
        )
    )

    unapproved = _synthetic_audit(
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        "      - uses: example/action@1111111111111111111111111111111111111111\n"
    )
    cases.append(
        _case(
            "unapproved-action",
            any("workflow_action_unapproved" in value for value in unapproved.blockers),
            "unapproved external action identity fails closed",
        )
    )

    pr_target = _synthetic_audit(
        "on:\n  pull_request_target:\npermissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        f"      - uses: {pinned}\n"
    )
    cases.append(
        _case(
            "pull-request-target",
            any("workflow_pull_request_target_forbidden" in value for value in pr_target.blockers),
            "pull_request_target is rejected by the v1 promotion workflow policy",
        )
    )

    interpolation = _synthetic_audit(
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        f"      - uses: {pinned}\n"
        '      - run: echo "${{ github.event.pull_request.title }}"\n'
    )
    cases.append(
        _case(
            "untrusted-shell-interpolation",
            any(
                "workflow_untrusted_pr_shell_interpolation" in value
                for value in interpolation.blockers
            ),
            "untrusted PR text cannot be interpolated directly into a shell run step",
        )
    )

    artifact_escape = _synthetic_audit(
        "permissions:\n  contents: read\njobs:\n  t:\n    steps:\n"
        f"      - uses: {pinned}\n"
        "      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02\n"
        "        with:\n          path: ../outside.txt\n"
    )
    cases.append(
        _case(
            "artifact-path-escape",
            any("workflow_artifact_path_escape" in value for value in artifact_escape.blockers),
            "artifact upload path cannot traverse above the repository workspace",
        )
    )
    return cases


def build_report(*, source_sha: str, platform: str) -> dict[str, Any]:
    policy = SupplyChainPolicy.load(ROOT / "configs/r16_supply_chain_policy.json")
    audit = audit_workflows(ROOT, policy)
    dependencies = declared_dependencies(ROOT)
    build_manifest = KodeBuild.collect(
        ROOT,
        source_sha=source_sha,
        platform=platform,
        python_version="3.12",
        metadata={"phase": "R16.9", "purpose": "supply-chain acceptance"},
    )
    bom = KodeBOM.from_pyproject(ROOT)
    manifest = SupplyChainManifest.from_release_evidence(
        ROOT,
        source_sha=source_sha,
        build_manifest=build_manifest,
        bom_report=bom,
        external_attestation=AttestationState.NOT_EXERCISED,
    )

    cases = [
        _case(
            "policy-integrity",
            len(policy.digest_sha256) == 64
            and {name: pin.commit_sha for name, pin in policy.pins.items()}
            == {
                "actions/attest": "1e69f48acb82d1966a394da916b4c1698aa569d6",
                "actions/checkout": "11d5960a326750d5838078e36cf38b85af677262",
                "actions/download-artifact": "634f93cb2916e3fdff6788551b99b062d0335ce0",
                "actions/setup-dotnet": "67a3573c9a986a3f9c594539f4ab511d57bb3ce9",
                "actions/setup-java": "cf277c60eb25467037889841efdb72551f06f6c3",
                "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
                "android-actions/setup-android": "9fc6c4e9069bf8d3d10b2204b1fb8f6ef7065407",
                "gradle/actions": "ed408507eac070d1f99cc633dbcf757c94c7933a",
            },
            "policy and verified external action pin identities are digest-bound",
        ),
        _case(
            "authority-workflows",
            audit.authority_workflow_count == len(policy.immutable_authority_workflows),
            "all v1 promotion authority workflows are present",
        ),
        _case(
            "workflow-audit",
            audit.status is SupplyChainStatus.PASS and not audit.blockers,
            "workflow permission, action, PR-input and artifact-boundary audit passes",
        ),
        _case(
            "legacy-workflow-boundary",
            audit.legacy_workflow_count > 0 and bool(audit.observations),
            "legacy workflows remain inventoried but non-authoritative for v1 promotion",
        ),
        _case(
            "dependency-inventory",
            len(dependencies) >= 10
            and all(len(item.declaration_sha256) == 64 for item in dependencies),
            "declared dependency/tool inputs have deterministic identity and declaration digests",
        ),
        _case(
            "build-source-binding",
            build_manifest.source_sha.lower() == source_sha.lower(),
            "build manifest is bound to the exact acceptance source SHA",
        ),
        _case(
            "build-artifact-integrity",
            build_manifest.status.value == "pass"
            and all(item.validated and len(item.sha256) == 64 for item in build_manifest.artifacts),
            "wheel and sdist carry validated SHA-256 artifact evidence",
        ),
        _case(
            "bom-coverage",
            bom.inventory_complete and bom.status.value in {"pass", "warn"} and not bom.blockers,
            "RC BOM covers declared build/runtime/optional dependencies and preserves unresolved state",
        ),
        _case(
            "promotion-contract",
            manifest.status is SupplyChainStatus.PASS and not manifest.blockers,
            "bound build+BOM+workflow+dependency provenance is promotable",
        ),
        _case(
            "external-attestation-semantics",
            not policy.external_attestation_required_for_core
            and policy.external_attestation_semantics
            == "provenance_only_not_security_verdict",
            "external attestations remain optional provenance evidence, never a security verdict",
        ),
        _case(
            "sanitized-evidence",
            not report_contains_secret_like_value(manifest.to_dict()),
            "supply-chain promotion evidence contains no secret-like field names",
        ),
    ]
    cases.extend(_tamper_cases())

    replay_rejected = False
    try:
        manifest.assert_promotable(expected_source_sha="0" * 40)
    except ValueError:
        replay_rejected = True
    cases.append(
        _case(
            "cross-source-replay",
            replay_rejected,
            "supply-chain evidence cannot be replayed as promotion authority for another source SHA",
        )
    )

    tampered = manifest.to_dict()
    tampered["bom_evidence_sha256"] = "2" * 64
    tamper_rejected = False
    try:
        SupplyChainManifest.from_dict(tampered)
    except ValueError:
        tamper_rejected = True
    cases.append(
        _case(
            "serialized-manifest-tamper",
            tamper_rejected,
            "serialized provenance evidence mutation invalidates its evidence digest",
        )
    )

    promotable = False
    try:
        manifest.assert_promotable(
            expected_source_sha=source_sha,
            expected_evidence_sha256=manifest.evidence_sha256,
        )
        promotable = True
    except ValueError:
        promotable = False
    cases.append(
        _case(
            "exact-promotion-verification",
            promotable,
            "exact source and evidence digests are required at the final promotion boundary",
        )
    )

    security_claim = all(item["pass"] for item in cases) and manifest.status is SupplyChainStatus.PASS
    semantic_payload = {
        "phase": "R16.9",
        "case_results": [{"name": item["name"], "pass": item["pass"]} for item in cases],
        "policy_sha256": policy.digest_sha256,
        "workflow_audit_sha256": audit.evidence_sha256,
        "dependency_count": len(dependencies),
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "manual_state": "NONE",
    }
    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": "R16.9",
        "source_sha": source_sha.lower(),
        "platform": platform,
        "security_claim": security_claim,
        "critical_veto": not security_claim,
        "manual_state": "NONE",
        "network_calls": 0,
        "live_credentials_used": False,
        "destructive_host_actions": False,
        "external_signing_key_required": False,
        "external_attestation": AttestationState.NOT_EXERCISED.value,
        "external_attestation_semantics": policy.external_attestation_semantics,
        "policy_sha256": policy.digest_sha256,
        "repository_input_sha256": repository_supply_chain_digest(ROOT),
        "workflow_audit": audit.to_dict(),
        "dependency_count": len(dependencies),
        "dependency_inventory": [item.to_dict() for item in dependencies],
        "build_manifest": build_manifest.to_dict(),
        "bom": bom.to_dict(),
        "supply_chain_manifest": manifest.to_dict(),
        "cases": cases,
        "summary": {
            "total": len(cases),
            "passed": sum(bool(item["pass"]) for item in cases),
            "failed": sum(not bool(item["pass"]) for item in cases),
        },
        "semantic_sha256": _sha256_payload(semantic_payload),
    }
    report["evidence_sha256"] = _sha256_payload(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="R16.9 exact-source supply-chain acceptance")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = build_report(source_sha=args.source_sha, platform=args.platform)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["security_claim"] and not report["critical_veto"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
