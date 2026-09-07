from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from kodepoia.release.identity import CURRENT_RELEASE
from kodepoia.release.tuf_security import TufVerificationError
from kodepoia.update.bootstrap import (
    load_production_packaged_root,
    load_synthetic_packaged_root,
)
from kodepoia.update.repository_bootstrap import (
    CANONICAL_METADATA_BASE_URL,
    GITHUB_RELEASE_BASE_URL,
    TOP_LEVEL_TUF_ROLES,
    UpdateRepositoryBootstrapError,
    UpdateRepositoryContract,
    UpdateTargetBinding,
    assert_repository_safe_payload,
    build_target_binding,
    default_production_repository_contract,
)
from kodepoia.update.trust import UpdateTargetSpec

SOURCE_SHA = "a" * 40
INSTALLER = b"synthetic-r19-2-kodepoia-installer\n"


def _target() -> UpdateTargetSpec:
    return UpdateTargetSpec.from_release(
        CURRENT_RELEASE,
        source_sha=SOURCE_SHA,
        platform="windows-x86_64",
    )


def test_default_contract_is_https_and_declares_all_top_level_roles() -> None:
    contract = default_production_repository_contract()

    assert contract.metadata_base_url == CANONICAL_METADATA_BASE_URL
    assert contract.release_asset_base_url == GITHUB_RELEASE_BASE_URL
    assert tuple(policy.role for policy in contract.role_policies) == TOP_LEVEL_TUF_ROLES
    assert contract.metadata_files == {
        "root": "root.json",
        "targets": "targets.json",
        "snapshot": "snapshot.json",
        "timestamp": "timestamp.json",
    }
    assert contract.consistent_snapshot is False


def test_role_policy_separates_keys_and_expiration_profiles() -> None:
    policies = {
        policy.role: policy
        for policy in default_production_repository_contract().role_policies
    }

    assert policies["root"].threshold == 2
    assert policies["root"].key_storage == "offline"
    assert policies["targets"].key_storage == "offline"
    assert policies["snapshot"].key_storage == "online"
    assert policies["timestamp"].key_storage == "online"
    assert policies["root"].expires_after_days == 365
    assert policies["targets"].expires_after_days == 365
    assert policies["snapshot"].expires_after_days == 1
    assert policies["timestamp"].expires_after_days == 1
    assert policies["timestamp"].rotate_after_days < policies["snapshot"].rotate_after_days


def test_contract_rendering_is_deterministic_and_matches_versioned_config() -> None:
    contract = default_production_repository_contract()
    first = contract.to_bytes()
    second = default_production_repository_contract().to_bytes()

    assert first == second
    config = json.loads(Path("configs/update_repository_r19_2.json").read_text(encoding="utf-8"))
    assert json.loads(first) == config
    assert config["production_root_state"] == "pending-real-key-bootstrap"
    assert config["synthetic_root_permitted_for_production"] is False
    assert config["private_keys_permitted_in_repository"] is False


def test_contract_rejects_non_https_repository_endpoint() -> None:
    contract = default_production_repository_contract()

    with pytest.raises(UpdateRepositoryBootstrapError, match="HTTPS"):
        UpdateRepositoryContract(
            metadata_base_url="http://updates.example.invalid/metadata/",
            release_asset_base_url=contract.release_asset_base_url,
            role_policies=contract.role_policies,
        )


def test_target_binding_covers_hash_size_source_channel_version_and_status() -> None:
    target = _target()
    binding = build_target_binding(
        target,
        INSTALLER,
        release_notes_summary="R19.2 synthetic acceptance release.",
        signing_status="synthetic-not-production",
        provenance_status="synthetic-verified",
    )

    assert binding.target_path == target.path
    assert binding.length == len(INSTALLER)
    assert binding.sha256 == hashlib.sha256(INSTALLER).hexdigest()
    assert binding.custom["source_sha"] == SOURCE_SHA
    assert binding.custom["channel"] == CURRENT_RELEASE.channel
    assert binding.custom["public_version"] == CURRENT_RELEASE.public_version
    assert binding.custom["withdrawn"] is False
    assert binding.payload_url == (
        f"{GITHUB_RELEASE_BASE_URL}v{CURRENT_RELEASE.public_version}/KodepoiaSetup.exe"
    )
    tuf_target = binding.to_tuf_target_dict()
    assert tuf_target["length"] == len(INSTALLER)
    assert tuf_target["hashes"] == {"sha256": binding.sha256}


def test_target_binding_rejects_identity_mismatch() -> None:
    target = _target()
    binding = build_target_binding(
        target,
        INSTALLER,
        release_notes_summary="Synthetic acceptance.",
        signing_status="synthetic",
        provenance_status="synthetic",
    )
    custom = dict(binding.custom)
    custom["source_sha"] = "b" * 40

    with pytest.raises(UpdateRepositoryBootstrapError, match="does not match its path"):
        UpdateTargetBinding(
            target_path=binding.target_path,
            length=binding.length,
            sha256=binding.sha256,
            custom=custom,
        )


def test_repository_safe_payload_rejects_private_key_material() -> None:
    assert_repository_safe_payload('{"public_key_only":true}\n')

    with pytest.raises(UpdateRepositoryBootstrapError, match="private key material"):
        assert_repository_safe_payload(
            "-----BEGIN " + "PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n"
        )


def test_production_root_fails_closed_until_real_key_bootstrap() -> None:
    with pytest.raises(TufVerificationError, match="pending real-key bootstrap"):
        load_production_packaged_root()


def test_synthetic_root_remains_acceptance_only() -> None:
    material = load_synthetic_packaged_root(allow_synthetic=True)

    assert material.purpose == "synthetic-acceptance-only"
    assert material.production_trust_claim is False
    assert material.private_keys_persisted is False
