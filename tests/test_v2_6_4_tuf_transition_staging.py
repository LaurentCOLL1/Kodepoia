from __future__ import annotations

import copy
from pathlib import Path

import pytest

from kodepoia.release.tuf_transition_staging import (
    CANDIDATE_INSTALLER_BYTES,
    CANDIDATE_INSTALLER_SHA256,
    CANDIDATE_SOURCE_SHA,
    REFERENCE_TIME,
    build_transition_request,
    build_v2_6_4_report,
    isolated_updater_rehearsal,
    production_observation,
    validate_transition_request,
)

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "update-repository" / "metadata"
DEVELOPMENT_SHA = "a" * 40


def _request() -> dict[str, object]:
    observation = production_observation(METADATA, reference_time=REFERENCE_TIME)
    return build_transition_request(DEVELOPMENT_SHA, observation)


def test_production_observation_is_read_only_and_fail_closed() -> None:
    before = {path.name: path.read_bytes() for path in METADATA.glob("*.json")}
    observation = production_observation(METADATA, reference_time=REFERENCE_TIME)
    after = {path.name: path.read_bytes() for path in METADATA.glob("*.json")}

    assert before == after
    assert observation["root_threshold"] == 2
    assert observation["root_key_count"] == 3
    assert set(observation["expired_roles"]) == {"snapshot", "timestamp"}
    assert observation["fail_closed_required"] is True
    assert observation["rc8_target_present"] is True
    assert observation["stable_candidate_target_present"] is False


def test_transition_request_binds_exact_frozen_candidate() -> None:
    request = _request()
    target = dict(request["requested_target"])
    custom = dict(target["custom"])

    validate_transition_request(request)
    assert request["release_candidate_source_sha"] == CANDIDATE_SOURCE_SHA
    assert target["length"] == CANDIDATE_INSTALLER_BYTES
    assert target["sha256"] == CANDIDATE_INSTALLER_SHA256
    assert custom["authenticode_policy"] == "allow-unsigned"
    assert dict(request["target_history"])["revoke"] == []
    assert not any(dict(request["effect_boundary"]).values())


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("release_candidate_source_sha", "b" * 40),
        ("length", CANDIDATE_INSTALLER_BYTES + 1),
        ("sha256", "0" * 64),
    ],
)
def test_transition_request_rejects_candidate_mismatch(field: str, bad_value: object) -> None:
    request = _request()
    mutated = copy.deepcopy(request)
    if field == "release_candidate_source_sha":
        mutated[field] = bad_value
    else:
        mutated["requested_target"] = {
            **dict(mutated["requested_target"]),
            field: bad_value,
        }
    with pytest.raises(ValueError):
        validate_transition_request(mutated)


def test_isolated_rehearsal_proves_compatibility_not_production_signing() -> None:
    rehearsal = isolated_updater_rehearsal(reference_time=REFERENCE_TIME)
    assert rehearsal["fixture_only"] is True
    assert rehearsal["production_proof"] is False
    assert rehearsal["fixture_matches_release_candidate_binary"] is False
    assert rehearsal["rc8_to_stable_discovery"] == "update-available"
    assert rehearsal["wrong_channel"] == "channel-unavailable"
    assert rehearsal["target_validation_before_eligibility"] == "verified"
    assert rehearsal["tampered_target"] == "verification-failed"
    assert rehearsal["offline_after_verified_cache"] == "offline-cached"
    assert rehearsal["expired_metadata"] == "metadata-expired"
    assert rehearsal["timestamp_rollback"] == "verification-failed"
    assert rehearsal["corrupt_metadata"] == "verification-failed"
    assert rehearsal["wrong_root_pin"] == "verification-failed"


def test_v2_6_4_report_has_no_live_effect() -> None:
    report = build_v2_6_4_report(DEVELOPMENT_SHA, repository_root=ROOT)
    assert report["status"] == "PASS"
    assert report["release_candidate_source_sha"] == CANDIDATE_SOURCE_SHA
    assert report["production_tuf_mutation_triggered"] is False
    assert report["public_release_triggered"] is False
    assert report["public_tag_triggered"] is False
    assert report["public_asset_upload_triggered"] is False
    assert report["live_updater_activation_triggered"] is False
    assert report["signing_secret_provisioned"] is False
    assert report["winget_submission_triggered"] is False
