from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "docs" / "release" / "V1_1_1_TUF_TRANSITION_REQUEST.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v111_transition_request_is_self_consistent() -> None:
    request = _load_json(REQUEST)
    expected_digest = request.pop("request_sha256")
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == expected_digest
    assert expected_digest == "03f9225ae1529b1816f3e745f7c6a4f2e84400c7570f4c3ff02172102e857abe"


def test_v111_transition_request_binds_qualified_candidate() -> None:
    request = _load_json(REQUEST)
    candidate = request["candidate"]
    assert candidate["source_sha"] == "aa1c80389b10f5ef44737241bf192c04f847e4ec"
    assert candidate["workflow_run_id"] == 37536813744
    assert candidate["artifact_id"] == 11448467632
    assert candidate["candidate_evidence_sha256"] == (
        "19a1fb1e73693f64cae7d1571c529b3f35625046ac4210375ad23ed2ac2b0d97"
    )
    assert candidate["installer_bytes"] == 38880869
    assert candidate["installer_sha256"] == (
        "c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd"
    )
    assert candidate["authenticode_policy"] == "allow-unsigned"
    assert candidate["production_signed"] is False


def test_v111_transition_request_matches_current_tuf_generation() -> None:
    request = _load_json(REQUEST)
    current = request["current_tuf"]
    root = _load_json(ROOT / "update-repository" / "metadata" / "root.json")
    targets = _load_json(ROOT / "update-repository" / "metadata" / "targets.json")
    snapshot = _load_json(ROOT / "update-repository" / "metadata" / "snapshot.json")
    timestamp = _load_json(ROOT / "update-repository" / "metadata" / "timestamp.json")

    assert root["signed"]["version"] == current["root_version"] == 2
    assert targets["signed"]["version"] == current["targets_version"] == 9
    assert snapshot["signed"]["version"] == current["snapshot_version"] == 11
    assert timestamp["signed"]["version"] == current["timestamp_version"] == 11

    target_ref = snapshot["signed"]["meta"]["targets.json"]
    assert target_ref["hashes"]["sha256"] == current["targets_sha256"]
    assert target_ref["length"] == current["targets_length"]

    snapshot_ref = timestamp["signed"]["meta"]["snapshot.json"]
    assert snapshot_ref["hashes"]["sha256"] == current["snapshot_sha256"]
    assert snapshot_ref["length"] == current["snapshot_length"]


def test_v111_transition_request_is_monotonic_and_fail_closed() -> None:
    request = _load_json(REQUEST)
    current = request["current_tuf"]
    transition = request["requested_transition"]
    safety = request["safety"]

    assert transition["expected_targets_version"] == current["targets_version"] + 1
    assert transition["expected_snapshot_version"] == current["snapshot_version"] + 1
    assert transition["expected_timestamp_version"] == current["timestamp_version"] + 1
    assert transition["target_path"] == (
        "channels/stable/windows-x86_64/1.1.1/"
        "aa1c80389b10f5ef44737241bf192c04f847e4ec/KodepoiaSetup.exe"
    )
    assert transition["preserve_all_prior_targets"] is True
    assert transition["offline_targets_custody_required"] is True
    assert transition["public_release_before_metadata"] is False
    assert transition["winget_submission"] is False

    assert safety["private_keys_in_request"] is False
    assert safety["passphrases_in_request"] is False
    assert safety["secret_values_in_request"] is False
    assert safety["candidate_rebuild_allowed"] is False
    assert safety["tag_repoint_allowed"] is False
    assert safety["asset_substitution_allowed"] is False
