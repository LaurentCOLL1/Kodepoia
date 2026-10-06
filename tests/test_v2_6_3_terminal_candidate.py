from __future__ import annotations

import json
from pathlib import Path

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import TERMINAL_RELEASE_FREEZE

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v263_historical_source_identity_remains_frozen_while_current_release_advances() -> None:
    freeze = TERMINAL_RELEASE_FREEZE

    assert freeze.successor_identity.public_version == "1.1.0"
    assert freeze.successor_identity.pep440_version == "1.1.0"
    assert CURRENT_RELEASE.public_version == "1.1.1"
    assert CURRENT_RELEASE.pep440_version == "1.1.1"
    assert CURRENT_RELEASE.channel == "stable"
    assert CURRENT_RELEASE.build_type == "release"
    assert CURRENT_RELEASE.is_newer_than(freeze.successor_identity)

    assert freeze.public_baseline["public_version"] == "1.1.0-rc8"
    assert freeze.public_baseline["tag"] == "v1.1.0-rc8"
    assert freeze.successor["candidate_source_freeze_phase"] == "V2.6.3"
    assert freeze.successor["candidate_source_sha"] is None


def test_v263_release_identity_and_package_version_are_consistent() -> None:
    identity = json.loads(_read("src/kodepoia/release/release_identity.json"))
    pyproject = _read("pyproject.toml")

    assert identity["channel"] == "stable"
    assert identity["build_type"] == "release"
    assert identity["version"] == {
        "major": 1,
        "minor": 1,
        "patch": 1,
        "stage": "final",
        "serial": 0,
    }
    assert 'version = "1.1.1"' in pyproject
    assert 'version = "1.1.0rc8"' not in pyproject


def test_v263_candidate_workflow_is_exact_source_and_non_publishing() -> None:
    workflow = _read(".github/workflows/v2-6-3-terminal-candidate.yml")

    required = (
        "EVIDENCE_SHA: ${{ github.event.pull_request.head.sha || github.sha }}",
        "Checkout exact candidate source",
        "Assert exact checkout provenance",
        "Detect terminal publication state",
        "Verify terminal published stable authority",
        "Upload V2.6.3 post-publication historical verification",
        "Build exact-source Windows candidate one",
        "Build exact-source Windows candidate two",
        "Generate exact-source SPDX SBOM and provenance",
        "Inspect exact candidate Authenticode truth",
        "Stage immutable release description without publishing",
        "Clean install, packaged smoke and uninstall",
        "Run actual V2.6.3 exact-source candidate acceptance",
        "Upload V2.6.3 exact-source candidate evidence",
    )
    for marker in required:
        assert marker in workflow, marker

    assert "permissions:\n  contents: read" in workflow
    assert "attestations: write" not in workflow
    assert "id-token: write" not in workflow
    assert "gh release create" not in workflow
    assert "git tag" not in workflow
    assert "tuf_release_ceremony" not in workflow
    assert "signing-secret" not in workflow.casefold()


def test_v263_candidate_workflow_reuses_r17_r18_contracts() -> None:
    workflow = _read(".github/workflows/v2-6-3-terminal-candidate.yml")

    for marker in (
        "scripts/build_windows_installer.ps1",
        "scripts/generate_release_evidence.py",
        "scripts/build_release_bundle.py",
        "scripts/r18_2_release_bundle_acceptance.py",
        "scripts/windows_authenticode.py",
        "stage_release_archive",
        "tests/test_r18_release_identity.py",
        "tests/test_r18_release_bundle.py",
        "tests/test_r18_sbom_provenance.py",
        "tests/test_r18_authenticode.py",
        "tests/test_r18_5_release_promotion.py",
    ):
        assert marker in workflow, marker

    assert "--mode unsigned" in workflow
    assert "synthetic-offline" in workflow
    assert "tag_exists = $false" in workflow
    assert "release_exists = $false" in workflow
    assert "post-publication-historical-verification" in workflow
    assert "candidate_rebuilt = $false" in workflow
    assert "candidate_republished = $false" in workflow


def test_v263_python_core_emits_cross_platform_synthetic_evidence() -> None:
    workflow = _read(".github/workflows/python-core.yml")

    assert "Run V2.6.3 exact-source candidate focused tests" in workflow
    assert "pytest tests/test_v2_6_3_terminal_candidate.py" in workflow
    assert "Run V2.6.3 exact-source candidate synthetic acceptance" in workflow
    assert "scripts/v2_6_3_acceptance.py --source-sha" in workflow
    assert (
        "v2-6-3-terminal-candidate-${{ matrix.os }}-${{ env.KODEPOIA_SOURCE_SHA }}"
        in workflow
    )


def test_v263_signing_winget_and_tuf_boundaries_remain_fail_closed() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    targets = _read("docs/release/evidence/V2_6_4_PRETRANSITION_METADATA/targets.json")

    assert freeze.authenticode["production_signing_verified"] is False
    assert freeze.authenticode["production_signing_secret_provisioning_authorized"] is False
    assert freeze.authenticode["candidate_truth_rule"] == "report-exact-observed-signing-state"
    assert freeze.winget["decision"] == "out"
    assert freeze.winget["public_submission_authorized"] is False
    assert freeze.production_tuf_repository_observation["repository_metadata_fresh"] is False
    assert freeze.production_tuf_repository_observation[
        "production_metadata_mutation_authorized"
    ] is False
    assert freeze.production_tuf_repository_observation["resolution_phase"] == "V2.6.4"
    assert "channels/stable/windows-x86_64/1.1.0/" not in targets


def test_v263_release_candidate_contract_authorizes_v264_only_after_normalization() -> None:
    contract = _read("docs/release/V2_6_3_TERMINAL_CANDIDATE.md")

    assert "post-merge normalization" in contract
    assert "authorizes V2.6.4 only" in contract
    assert "No GitHub Release, public tag, public asset" in contract
    assert "production TUF mutation" in contract


def test_v263_candidate_workflow_verifies_frozen_publication_after_release() -> None:
    workflow = _read(".github/workflows/v2-6-3-terminal-candidate.yml")

    for marker in (
        "PUBLISHED_STABLE_SOURCE_SHA: 46ed800888b4f19da9e984232dd1ad6cdb639cc1",
        'PUBLISHED_STABLE_BYTES: "38834833"',
        "PUBLISHED_STABLE_SHA256: 8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef",
        'PUBLISHED_STABLE_RELEASE_ID: "404195689"',
        "steps.publication.outputs.published == 'true'",
        "steps.publication.outputs.published != 'true'",
        "Published v1.1.0 tag source drift",
        "Published v1.1.0 installer digest drift",
        "post-publication-historical-verification",
    ):
        assert marker in workflow, marker

    assert "gh release create" not in workflow
    assert "gh release upload" not in workflow
    assert "contents: write" not in workflow
    assert "candidate_rebuilt = $false" in workflow
    assert "candidate_republished = $false" in workflow
    assert "production_tuf_mutated = $false" in workflow
