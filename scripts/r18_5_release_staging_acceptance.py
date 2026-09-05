from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from kodepoia.release.promotion import (
    ATTESTATION_PROVIDER,
    ATTESTATION_SEMANTICS,
    ReleasePromotionError,
    build_publish_request,
    stage_verified_release,
    verify_published_release,
)

REPOSITORY = "LaurentCOLL1/Kodepoia"


def _digest(label: str, source_sha: str) -> str:
    return hashlib.sha256(f"{label}:{source_sha}".encode()).hexdigest()


def _identity(source_sha: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "product": "Kodepoia",
        "package": "kodepoia",
        "channel": "beta",
        "build_type": "prerelease",
        "source_binding": "exact-head",
        "version": {
            "major": 1,
            "minor": 1,
            "patch": 0,
            "stage": "rc",
            "serial": 1,
        },
        "pep440_version": "1.1.0rc1",
        "public_version": "1.1.0-rc1",
        "installer_version": "1.1.0-rc1",
        "source_sha": source_sha,
    }


def _inputs(
    source_sha: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    archive_sha = _digest("archive", source_sha)
    bundle = {
        "archive_path": "artifacts/Kodepoia-1.1.0-rc1-windows.zip",
        "archive_sha256": archive_sha,
        "archive_size": 120_000_000,
        "manifest_sha256": _digest("manifest", source_sha),
        "source_sha": source_sha,
        "manifest": {
            "format": "kodepoia-release-bundle",
            "schema_version": 1,
            "source_sha": source_sha,
            "platform": "windows",
            "release_identity": _identity(source_sha),
            "provenance": {
                "repository": REPOSITORY,
                "workflow_ref": "synthetic-r18.5",
                "run_id": "synthetic",
                "run_attempt": "1",
            },
            "release_evidence": {
                "sbom_path": "release-sbom.spdx.json",
                "sbom_sha256": _digest("sbom", source_sha),
                "provenance_path": "release-provenance.json",
                "provenance_sha256": _digest("provenance", source_sha),
                "sbom_predicate_type": "https://spdx.dev/Document/v2.3",
                "attestation_semantics": ATTESTATION_SEMANTICS,
            },
            "payload_sha256": _digest("payload", source_sha),
            "semantic_sha256": _digest("semantic", source_sha),
        },
    }
    signing = {
        "schema_version": 1,
        "source_sha": source_sha,
        "mode": "test",
        "hash_algorithm": "sha256",
        "timestamp_protocol": "RFC3161",
        "timestamp_url": "https://timestamp.invalid",
        "certificate_thumbprint": "A" * 40,
        "production_signed": False,
        "public_trust_claim": False,
        "signtool_version": "synthetic",
        "subjects": [
            {
                "filename": "dist/windows/KodepoiaSetup.exe",
                "sha256": _digest("installer", source_sha),
                "authenticode_status": "Valid",
                "signer_subject": "CN=Kodepoia R18.5 synthetic test signer",
                "signer_thumbprint": "A" * 40,
                "timestamp_subject": "CN=Kodepoia R18.5 synthetic TSA",
                "timestamp_verified": True,
                "signtool_verified": True,
                "pre_sign_sha256": _digest("unsigned-installer", source_sha),
            }
        ],
    }
    attestation = {
        "schema_version": 1,
        "provider": ATTESTATION_PROVIDER,
        "semantics": ATTESTATION_SEMANTICS,
        "repository": REPOSITORY,
        "source_sha": source_sha,
        "verified": True,
        "verification_mode": "synthetic-offline",
        "subjects": [
            {
                "name": "Kodepoia-1.1.0-rc1-windows.zip",
                "sha256": archive_sha,
                "size": 120_000_000,
            }
        ],
    }
    tag_state = {
        "tag": "v1.1.0-rc1",
        "tag_exists": False,
        "release_exists": False,
        "immutable_release_capability": "unknown",
    }
    return bundle, signing, attestation, tag_state


def _expect_rejection(
    label: str, fn: Callable[[], object], contains: str
) -> dict[str, Any]:
    try:
        fn()
    except ReleasePromotionError as exc:
        if contains not in str(exc):
            raise AssertionError(f"{label}: unexpected rejection: {exc}") from exc
        return {"case": label, "status": "PASS", "rejected": True, "reason": str(exc)}
    raise AssertionError(f"{label}: expected fail-closed rejection")


def run_acceptance(source_sha: str) -> dict[str, Any]:
    bundle, signing, attestation, tag_state = _inputs(source_sha)
    staged = stage_verified_release(
        verified_bundle=bundle,
        source_sha=source_sha,
        repository=REPOSITORY,
        signing_evidence=signing,
        attestation_receipt=attestation,
        tag_state=tag_state,
    )
    cases: list[dict[str, Any]] = [
        {
            "case": "exact-source-stage",
            "status": "PASS",
            "state": staged["state"],
            "stage_digest": staged["stage_digest"],
            "publication_triggered": staged["github_release"]["publication_triggered"],
        }
    ]

    wrong_bundle = dict(bundle)
    wrong_bundle["source_sha"] = "f" * 40
    cases.append(
        _expect_rejection(
            "source-mismatch",
            lambda: stage_verified_release(
                verified_bundle=wrong_bundle,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=signing,
                attestation_receipt=attestation,
                tag_state=tag_state,
            ),
            "source SHA mismatch",
        )
    )

    no_evidence = json.loads(json.dumps(bundle))
    del no_evidence["manifest"]["release_evidence"]
    cases.append(
        _expect_rejection(
            "missing-r18.3-evidence",
            lambda: stage_verified_release(
                verified_bundle=no_evidence,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=signing,
                attestation_receipt=attestation,
                tag_state=tag_state,
            ),
            "R18.3",
        )
    )

    contradictory = json.loads(json.dumps(signing))
    contradictory["production_signed"] = True
    cases.append(
        _expect_rejection(
            "contradictory-signing",
            lambda: stage_verified_release(
                verified_bundle=bundle,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=contradictory,
                attestation_receipt=attestation,
                tag_state=tag_state,
            ),
            "contradicts production_signed",
        )
    )

    unverified = json.loads(json.dumps(attestation))
    unverified["verified"] = False
    cases.append(
        _expect_rejection(
            "missing-attestation-verification",
            lambda: stage_verified_release(
                verified_bundle=bundle,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=signing,
                attestation_receipt=unverified,
                tag_state=tag_state,
            ),
            "not verified",
        )
    )

    unexpected = json.loads(json.dumps(attestation))
    unexpected["subjects"].append(
        {"name": "unexpected.bin", "sha256": _digest("unexpected", source_sha), "size": 1}
    )
    cases.append(
        _expect_rejection(
            "unexpected-asset",
            lambda: stage_verified_release(
                verified_bundle=bundle,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=signing,
                attestation_receipt=unexpected,
                tag_state=tag_state,
            ),
            "exactly the manifest-approved",
        )
    )

    reused = dict(tag_state)
    reused["tag_exists"] = True
    cases.append(
        _expect_rejection(
            "mutable-tag-reuse",
            lambda: stage_verified_release(
                verified_bundle=bundle,
                source_sha=source_sha,
                repository=REPOSITORY,
                signing_evidence=signing,
                attestation_receipt=attestation,
                tag_state=reused,
            ),
            "reuse is forbidden",
        )
    )

    request = build_publish_request(staged, approved_stage_digest=staged["stage_digest"])
    if request["effect"] != "create-draft-only" or request["public_publish"] is not False:
        raise AssertionError("draft request crossed public publication boundary")
    cases.append(
        {
            "case": "exact-digest-draft-request",
            "status": "PASS",
            "effect": request["effect"],
            "public_publish": request["public_publish"],
        }
    )

    cases.append(
        _expect_rejection(
            "wrong-stage-approval",
            lambda: build_publish_request(staged, approved_stage_digest="e" * 64),
            "does not match exact staged candidate",
        )
    )

    tampered = json.loads(json.dumps(staged))
    tampered["release_name"] = "tampered"
    cases.append(
        _expect_rejection(
            "staged-document-tamper",
            lambda: build_publish_request(
                tampered, approved_stage_digest=staged["stage_digest"]
            ),
            "digest binding is invalid",
        )
    )

    snapshot = {
        "id": 18_005,
        "tag_name": staged["tag"],
        "target_commitish": source_sha,
        "name": staged["release_name"],
        "draft": False,
        "prerelease": True,
        "immutable": True,
        "assets": [
            {
                "name": staged["assets"][0]["name"],
                "digest": f"sha256:{staged['assets'][0]['sha256']}",
                "size": staged["assets"][0]["size"],
            }
        ],
    }
    published = verify_published_release(
        staged, release_snapshot=snapshot, require_immutable=True
    )
    cases.append(
        {
            "case": "immutable-published-snapshot",
            "status": "PASS",
            "immutable": published["immutable"],
            "assets_verified": published["assets_verified"],
        }
    )

    mutable = dict(snapshot)
    mutable["immutable"] = False
    cases.append(
        _expect_rejection(
            "immutable-required-negative",
            lambda: verify_published_release(
                staged, release_snapshot=mutable, require_immutable=True
            ),
            "requires immutable",
        )
    )

    if any(case["status"] != "PASS" for case in cases):
        raise AssertionError("R18.5 acceptance contains non-PASS cases")

    return {
        "schema_version": 1,
        "phase": "R18.5",
        "source_sha": source_sha,
        "repository": REPOSITORY,
        "acceptance_scope": "synthetic-offline-github-release-staging-contract",
        "cases_total": len(cases),
        "cases_passed": len(cases),
        "cases": cases,
        "stage_digest": staged["stage_digest"],
        "tag": staged["tag"],
        "production_signed": staged["signing"]["production_signed"],
        "public_trust_claim": staged["signing"]["public_trust_claim"],
        "github_api_write_calls": 0,
        "public_release_created": False,
        "immutable_release_setting_changed": False,
        "manual_state": "CONDITIONAL_NOT_TRIGGERED",
        "security_claim": False,
        "attestation_semantics": ATTESTATION_SEMANTICS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit R18.5 synthetic acceptance evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if len(args.source_sha) != 40:
        raise SystemExit("--source-sha must be an exact 40-character Git SHA")
    report = run_acceptance(args.source_sha.lower())
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
