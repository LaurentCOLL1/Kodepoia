from __future__ import annotations

import pytest

from kodepoia.release.promotion import (
    ATTESTATION_PROVIDER,
    ATTESTATION_SEMANTICS,
    ReleasePromotionError,
    build_publish_request,
    stage_verified_release,
    verify_published_release,
)

SOURCE = "1" * 40
REPOSITORY = "LaurentCOLL1/Kodepoia"
ARCHIVE_SHA = "2" * 64
MANIFEST_SHA = "3" * 64
PAYLOAD_SHA = "4" * 64
SEMANTIC_SHA = "5" * 64
INSTALLER_SHA = "6" * 64


def identity() -> dict:
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
        "source_sha": SOURCE,
    }


def verified_bundle() -> dict:
    return {
        "archive_path": "dist/release/Kodepoia-1.1.0-rc1-windows.zip",
        "archive_sha256": ARCHIVE_SHA,
        "archive_size": 4242,
        "manifest_sha256": MANIFEST_SHA,
        "source_sha": SOURCE,
        "manifest": {
            "format": "kodepoia-release-bundle",
            "schema_version": 1,
            "source_sha": SOURCE,
            "platform": "windows",
            "release_identity": identity(),
            "provenance": {
                "repository": REPOSITORY,
                "workflow_ref": "local",
                "run_id": "local",
                "run_attempt": "local",
            },
            "release_evidence": {
                "sbom_path": "release-sbom.spdx.json",
                "sbom_sha256": "7" * 64,
                "provenance_path": "release-provenance.json",
                "provenance_sha256": "8" * 64,
                "sbom_predicate_type": "https://spdx.dev/Document/v2.3",
                "attestation_semantics": ATTESTATION_SEMANTICS,
            },
            "payload_sha256": PAYLOAD_SHA,
            "semantic_sha256": SEMANTIC_SHA,
        },
    }


def signing_evidence() -> dict:
    return {
        "schema_version": 1,
        "source_sha": SOURCE,
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
                "sha256": INSTALLER_SHA,
                "authenticode_status": "Valid",
                "signer_subject": "CN=R18.5 synthetic test signer",
                "signer_thumbprint": "A" * 40,
                "timestamp_subject": "CN=R18.5 synthetic TSA",
                "timestamp_verified": True,
                "signtool_verified": True,
                "pre_sign_sha256": "9" * 64,
            }
        ],
    }


def attestation_receipt() -> dict:
    return {
        "schema_version": 1,
        "provider": ATTESTATION_PROVIDER,
        "semantics": ATTESTATION_SEMANTICS,
        "repository": REPOSITORY,
        "source_sha": SOURCE,
        "verified": True,
        "verification_mode": "synthetic-offline",
        "subjects": [
            {
                "name": "Kodepoia-1.1.0-rc1-windows.zip",
                "sha256": ARCHIVE_SHA,
                "size": 4242,
            }
        ],
    }


def tag_state() -> dict:
    return {
        "tag": "v1.1.0-rc1",
        "tag_exists": False,
        "release_exists": False,
        "immutable_release_capability": "unknown",
    }


def stage() -> dict:
    return stage_verified_release(
        verified_bundle=verified_bundle(),
        source_sha=SOURCE,
        repository=REPOSITORY,
        signing_evidence=signing_evidence(),
        attestation_receipt=attestation_receipt(),
        tag_state=tag_state(),
    )


def test_stage_is_non_public_and_exact_source_bound() -> None:
    staged = stage()
    assert staged["state"] == "staged"
    assert staged["source_sha"] == SOURCE
    assert staged["tag"] == "v1.1.0-rc1"
    assert staged["github_release"]["draft"] is True
    assert staged["github_release"]["prerelease"] is True
    assert staged["github_release"]["make_latest"] is False
    assert staged["github_release"]["publication_triggered"] is False
    assert staged["signing"]["production_signed"] is False
    assert staged["signing"]["public_trust_claim"] is False
    assert staged["attestation"]["live_verified"] is False
    assert len(staged["stage_digest"]) == 64


def test_source_mismatch_fails_closed() -> None:
    bundle = verified_bundle()
    bundle["source_sha"] = "a" * 40
    with pytest.raises(ReleasePromotionError, match="source SHA mismatch"):
        stage_verified_release(
            verified_bundle=bundle,
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing_evidence(),
            attestation_receipt=attestation_receipt(),
            tag_state=tag_state(),
        )


def test_r18_3_evidence_is_required() -> None:
    bundle = verified_bundle()
    del bundle["manifest"]["release_evidence"]
    with pytest.raises(ReleasePromotionError, match="R18.3"):
        stage_verified_release(
            verified_bundle=bundle,
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing_evidence(),
            attestation_receipt=attestation_receipt(),
            tag_state=tag_state(),
        )


def test_signing_truth_contradiction_fails_closed() -> None:
    signing = signing_evidence()
    signing["production_signed"] = True
    with pytest.raises(ReleasePromotionError, match="contradicts production_signed"):
        stage_verified_release(
            verified_bundle=verified_bundle(),
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing,
            attestation_receipt=attestation_receipt(),
            tag_state=tag_state(),
        )


def test_missing_attestation_fails_closed() -> None:
    receipt = attestation_receipt()
    receipt["verified"] = False
    with pytest.raises(ReleasePromotionError, match="not verified"):
        stage_verified_release(
            verified_bundle=verified_bundle(),
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing_evidence(),
            attestation_receipt=receipt,
            tag_state=tag_state(),
        )


def test_unexpected_asset_fails_closed() -> None:
    receipt = attestation_receipt()
    receipt["subjects"].append(
        {"name": "unexpected.exe", "sha256": "a" * 64, "size": 9}
    )
    with pytest.raises(ReleasePromotionError, match="exactly the manifest-approved"):
        stage_verified_release(
            verified_bundle=verified_bundle(),
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing_evidence(),
            attestation_receipt=receipt,
            tag_state=tag_state(),
        )


def test_tag_reuse_fails_closed() -> None:
    state = tag_state()
    state["tag_exists"] = True
    with pytest.raises(ReleasePromotionError, match="reuse is forbidden"):
        stage_verified_release(
            verified_bundle=verified_bundle(),
            source_sha=SOURCE,
            repository=REPOSITORY,
            signing_evidence=signing_evidence(),
            attestation_receipt=attestation_receipt(),
            tag_state=state,
        )


def test_publish_request_requires_exact_stage_digest_and_stays_draft() -> None:
    staged = stage()
    request = build_publish_request(
        staged, approved_stage_digest=staged["stage_digest"]
    )
    assert request["effect"] == "create-draft-only"
    assert request["public_publish"] is False
    assert request["body"]["draft"] is True
    assert request["body"]["tag_name"] == "v1.1.0-rc1"
    assert request["body"]["target_commitish"] == SOURCE
    assert request["approved_assets"] == staged["assets"]


def test_publish_request_rejects_wrong_approval() -> None:
    staged = stage()
    with pytest.raises(
        ReleasePromotionError, match="does not match exact staged candidate"
    ):
        build_publish_request(staged, approved_stage_digest="f" * 64)


def test_stage_tamper_invalidates_publish_request() -> None:
    staged = stage()
    approved = staged["stage_digest"]
    staged["release_name"] = "tampered"
    with pytest.raises(ReleasePromotionError, match="digest binding is invalid"):
        build_publish_request(staged, approved_stage_digest=approved)


def test_published_snapshot_verification_binds_assets_and_immutability() -> None:
    staged = stage()
    snapshot = {
        "id": 123,
        "tag_name": staged["tag"],
        "target_commitish": SOURCE,
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
    result = verify_published_release(
        staged, release_snapshot=snapshot, require_immutable=True
    )
    assert result["state"] == "published"
    assert result["immutable"] is True
    assert result["assets_verified"] is True


def test_published_snapshot_fails_when_immutable_required_but_absent() -> None:
    staged = stage()
    snapshot = {
        "id": 123,
        "tag_name": staged["tag"],
        "target_commitish": SOURCE,
        "name": staged["release_name"],
        "draft": False,
        "prerelease": True,
        "immutable": False,
        "assets": [
            {
                "name": staged["assets"][0]["name"],
                "digest": f"sha256:{staged['assets'][0]['sha256']}",
                "size": staged["assets"][0]["size"],
            }
        ],
    }
    with pytest.raises(ReleasePromotionError, match="requires immutable"):
        verify_published_release(
            staged, release_snapshot=snapshot, require_immutable=True
        )
