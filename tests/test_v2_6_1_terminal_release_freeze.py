from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from kodepoia.release import CURRENT_RELEASE
from kodepoia.release.terminal_freeze import (
    TERMINAL_RELEASE_FREEZE,
    TerminalReleaseFreeze,
    TerminalReleaseFreezeError,
)

ROOT = Path(__file__).resolve().parents[1]


def test_terminal_successor_is_stable_1_1_0_and_monotonic_from_rc8() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    target = freeze.successor_identity

    assert CURRENT_RELEASE.public_version == "1.1.0-rc8"
    assert CURRENT_RELEASE.channel == "beta"
    assert target.public_version == "1.1.0"
    assert target.pep440_version == "1.1.0"
    assert target.channel == "stable"
    assert target.build_type == "release"
    assert freeze.successor["tag"] == "v1.1.0"
    freeze.assert_transition_from(CURRENT_RELEASE)
    assert target.is_newer_than(CURRENT_RELEASE)


def test_v261_does_not_promote_runtime_identity_before_candidate_phase() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    assert freeze.successor["candidate_source_freeze_phase"] == "V2.6.3"
    assert freeze.successor["candidate_source_sha"] is None
    assert freeze.terminal_scope_base_sha == "6402041e6c86b21260c9b0fd7176141fff53a0ee"

    runtime_payload = json.loads(
        (ROOT / "src/kodepoia/release/release_identity.json").read_text(encoding="utf-8")
    )
    assert runtime_payload["channel"] == "beta"
    assert runtime_payload["version"]["stage"] == "rc"
    assert runtime_payload["version"]["serial"] == 8


def test_windows_installer_and_update_identity_are_frozen_to_existing_contract() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    installer = freeze.windows_installer
    iss = (ROOT / "packaging/windows/Kodepoia.iss").read_text(encoding="utf-8")

    assert installer["filename"] == "KodepoiaSetup.exe"
    assert installer["app_id"] in iss
    assert '#define AppName "Kodepoia"' in iss
    assert '#define AppExeName "KodepoiaStudio.exe"' in iss
    assert "UsePreviousAppDir=yes" in iss
    assert "DisableDirPage=no" in iss
    assert "DefaultDirName={localappdata}\\Programs\\Kodepoia" in iss
    assert installer["target_path_template"] == (
        "channels/stable/windows-x86_64/1.1.0/{source_sha}/KodepoiaSetup.exe"
    )


def test_rc8_installed_baseline_and_channel_behavior_are_explicit() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    transition = freeze.transition

    assert transition["supported_installed_upgrade_baselines"] == ["1.1.0-rc8"]
    assert transition["clean_install_supported"] is True
    assert transition["stable_channel_behavior"] == "stable-final-releases-only"
    assert transition["beta_channel_behavior"] == (
        "prerelease-feed-no-implicit-cross-channel-promotion"
    )
    assert transition["rc8_to_stable_rehearsal_channel"] == "stable"


def test_authenticode_truth_and_winget_decision_fail_closed() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    signing = freeze.authenticode
    winget = freeze.winget

    assert signing["production_signing_verified"] is False
    assert signing["production_signing_capability"] == "not-verified"
    assert signing["production_signing_secret_provisioning_authorized"] is False
    assert signing["candidate_truth_rule"] == "report-exact-observed-signing-state"
    assert signing["unsigned_tuf_policy"] == "allow-unsigned"
    assert signing["unsigned_policy_scope"] == "exact-target-only"
    assert signing["broken_invalid_untrusted_signature_action"] == "reject"

    assert winget["decision"] == "out"
    assert winget["preview_generation_allowed"] is True
    assert winget["public_submission_authorized"] is False


def test_no_new_feature_and_no_live_effect_freeze_is_terminal() -> None:
    freeze = TERMINAL_RELEASE_FREEZE
    scope = freeze.no_new_feature_freeze

    assert scope["effective_after_v2_6_1_normalization"] is True
    assert scope["new_product_capability_allowed"] is False
    assert scope["v2_7_authorized"] is False
    assert scope["r20_7_authorized"] is False
    assert all(value is False for value in freeze.effects.values())


def test_invalid_freeze_cannot_claim_production_signing_or_winget() -> None:
    payload = copy.deepcopy(dict(TERMINAL_RELEASE_FREEZE.payload))
    payload["authenticode"] = dict(payload["authenticode"])
    payload["authenticode"]["production_signing_verified"] = True
    with pytest.raises(TerminalReleaseFreezeError, match="production signing"):
        TerminalReleaseFreeze.from_mapping(payload)

    payload = copy.deepcopy(dict(TERMINAL_RELEASE_FREEZE.payload))
    payload["winget"] = dict(payload["winget"])
    payload["winget"]["decision"] = "in"
    with pytest.raises(TerminalReleaseFreezeError, match="WinGet"):
        TerminalReleaseFreeze.from_mapping(payload)


def test_repository_tuf_freshness_truth_is_observed_without_authorizing_mutation() -> None:
    observation = TERMINAL_RELEASE_FREEZE.production_tuf_repository_observation

    assert observation["observed_from_source_sha"] == (
        "6402041e6c86b21260c9b0fd7176141fff53a0ee"
    )
    assert observation["root_expires"] == "2027-09-08T14:59:19Z"
    assert observation["targets_expires"] == "2027-09-12T20:49:31Z"
    assert observation["snapshot_expires"] == "2026-09-17T19:48:41Z"
    assert observation["timestamp_expires"] == "2026-09-16T19:48:41Z"
    assert observation["expired_roles_at_v2_6_1"] == ["snapshot", "timestamp"]
    assert observation["repository_metadata_fresh"] is False
    assert observation["expired_metadata_accepted_by_updater"] is False
    assert observation["production_metadata_mutation_authorized"] is False
    assert observation["resolution_phase"] == "V2.6.4"
