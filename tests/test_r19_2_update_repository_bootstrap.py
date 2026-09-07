from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.identity import CURRENT_RELEASE
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

EXPECTED_PRODUCTION_ROOT_SHA256 = (
    "a036c2aac78092f8d46893cc18954bb64f2b998375ff230f996dc4b85157e9ed"
)
SOURCE_SHA = "a" * 40
INSTALLER = b"synthetic-r19-2-kodepoia-installer\n"
METADATA_DIR = Path("update-repository/metadata")


def _target() -> UpdateTargetSpec:
    return UpdateTargetSpec.from_release(
        CURRENT_RELEASE,
        source_sha=SOURCE_SHA,
        platform="windows-x86_64",
    )


def _metadata(name: str, expected_type: type[object]) -> Metadata[object]:
    metadata = Metadata.from_bytes((METADATA_DIR / name).read_bytes())
    assert isinstance(metadata.signed, expected_type)
    return metadata


def test_default_contract_is_active_https_and_complete() -> None:
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
    rendered = json.loads(contract.to_bytes())
    config = json.loads(Path("configs/update_repository_r19_2.json").read_text(encoding="utf-8"))
    assert rendered == config
    assert config["production_root_state"] == "active"
    assert config["synthetic_root_permitted_for_production"] is False
    assert config["private_keys_permitted_in_repository"] is False


def test_role_policy_separates_storage_and_expiration_profiles() -> None:
    policies = {
        policy.role: policy for policy in default_production_repository_contract().role_policies
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


def test_contract_rejects_non_https_repository_endpoint() -> None:
    contract = default_production_repository_contract()
    with pytest.raises(UpdateRepositoryBootstrapError, match="HTTPS"):
        UpdateRepositoryContract(
            metadata_base_url="http://updates.example.invalid/metadata/",
            release_asset_base_url=contract.release_asset_base_url,
            role_policies=contract.role_policies,
        )


def test_production_root_is_active_distinct_and_digest_pinned() -> None:
    production = load_production_packaged_root()
    synthetic = load_synthetic_packaged_root(allow_synthetic=True)
    assert production.purpose == "production-beta-release-trust-anchor"
    assert production.production_trust_claim is True
    assert production.private_keys_persisted is False
    assert production.pin.version == 1
    assert production.pin.sha256 == EXPECTED_PRODUCTION_ROOT_SHA256
    assert hashlib.sha256(production.root_bytes).hexdigest() == EXPECTED_PRODUCTION_ROOT_SHA256
    assert production.root_bytes != synthetic.root_bytes
    assert production.pin.sha256 != synthetic.pin.sha256


def test_public_metadata_set_is_signed_and_cross_bound() -> None:
    production = load_production_packaged_root()
    root_md = _metadata("root.json", Root)
    targets_md = _metadata("targets.json", Targets)
    snapshot_md = _metadata("snapshot.json", Snapshot)
    timestamp_md = _metadata("timestamp.json", Timestamp)

    assert (METADATA_DIR / "root.json").read_bytes() == production.root_bytes
    root = root_md.signed
    root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
    root.verify_delegate("targets", targets_md.signed_bytes, targets_md.signatures)
    root.verify_delegate("snapshot", snapshot_md.signed_bytes, snapshot_md.signatures)
    root.verify_delegate("timestamp", timestamp_md.signed_bytes, timestamp_md.signatures)

    targets_ref = snapshot_md.signed.meta["targets.json"]
    targets_bytes = (METADATA_DIR / "targets.json").read_bytes()
    assert targets_ref.version == targets_md.signed.version
    targets_ref.verify_length_and_hashes(targets_bytes)

    snapshot_ref = timestamp_md.signed.snapshot_meta
    snapshot_bytes = (METADATA_DIR / "snapshot.json").read_bytes()
    assert snapshot_ref.version == snapshot_md.signed.version
    snapshot_ref.verify_length_and_hashes(snapshot_bytes)
    assert targets_md.signed.targets == {}


def test_real_root_uses_separate_key_scopes_and_two_of_three_root_threshold() -> None:
    root_md = _metadata("root.json", Root)
    roles = root_md.signed.roles
    assert roles["root"].threshold == 2
    assert len(roles["root"].keyids) == 3
    scopes = [set(roles[role].keyids) for role in TOP_LEVEL_TUF_ROLES]
    assert sum(len(scope) for scope in scopes) == len(set().union(*scopes))
    for key in root_md.signed.keys.values():
        assert set(key.to_dict()["keyval"]) == {"public"}


def test_target_binding_covers_hash_size_source_channel_version_and_status() -> None:
    target = _target()
    binding = build_target_binding(
        target,
        INSTALLER,
        release_notes_summary="R19.2 deterministic acceptance release.",
        signing_status="synthetic-test-only",
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
