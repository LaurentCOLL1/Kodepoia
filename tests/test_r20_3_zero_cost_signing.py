from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from securesystemslib.signer import SSlibKey, Signature
from tuf.api.metadata import Metadata, Root

from kodepoia.update.online_signing import OnlineSigningError, resolve_online_signers
from kodepoia.update.zero_cost_signing import (
    SNAPSHOT_SECRET_NAME,
    TIMESTAMP_SECRET_NAME,
    GitHubEnvironmentSecretResolver,
    generate_online_key,
    prepare_zero_cost_rotation,
)

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOT = ROOT / "update-repository" / "metadata" / "root.json"
PUBLIC_KEYS = ROOT / "docs" / "roadmap" / "R20_3_PUBLIC_KEYS.json"
UNSIGNED_ROOT = ROOT / "docs" / "roadmap" / "R20_3_ROOT_V2_UNSIGNED.json"
ROTATION_MANIFEST = ROOT / "docs" / "roadmap" / "R20_3_ROOT_ROTATION_MANIFEST.json"
PUBLIC_ACCEPTANCE = ROOT / "docs" / "roadmap" / "R20_3_PUBLIC_PACKAGE_ACCEPTANCE.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_zero_cost_keys_are_distinct_ed25519_seed_secrets() -> None:
    snapshot = generate_online_key("snapshot")
    timestamp = generate_online_key("timestamp")

    assert snapshot.secret_name == SNAPSHOT_SECRET_NAME
    assert timestamp.secret_name == TIMESTAMP_SECRET_NAME
    assert snapshot.config.keyid != timestamp.config.keyid
    assert snapshot.config.provider == "github-environment-secret"
    assert timestamp.config.provider == "github-environment-secret"
    assert len(base64.b64decode(snapshot.secret_value_b64, validate=True)) == 32
    assert len(base64.b64decode(timestamp.secret_value_b64, validate=True)) == 32
    assert snapshot.secret_value_b64 != timestamp.secret_value_b64


def test_github_environment_resolver_uses_memory_only_secret_values() -> None:
    snapshot = generate_online_key("snapshot")
    timestamp = generate_online_key("timestamp")
    resolver = GitHubEnvironmentSecretResolver(
        {
            SNAPSHOT_SECRET_NAME: snapshot.secret_value_b64,
            TIMESTAMP_SECRET_NAME: timestamp.secret_value_b64,
        }
    )

    resolved = resolve_online_signers(
        [snapshot.config, timestamp.config],
        resolver,
    )
    payload = b"r20.3 zero-cost signing challenge"
    snapshot_signature = resolved.snapshot.sign(payload)
    timestamp_signature = resolved.timestamp.sign(payload)

    assert isinstance(snapshot_signature, Signature)
    assert isinstance(timestamp_signature, Signature)
    snapshot.config.public_key.verify_signature(snapshot_signature, payload)
    timestamp.config.public_key.verify_signature(timestamp_signature, payload)


def test_github_environment_resolver_fails_closed_for_missing_invalid_or_wrong_secret() -> None:
    snapshot = generate_online_key("snapshot")
    timestamp = generate_online_key("timestamp")

    with pytest.raises(OnlineSigningError, match="missing GitHub Actions secret"):
        GitHubEnvironmentSecretResolver({})(snapshot.config)

    with pytest.raises(OnlineSigningError, match="strict base64"):
        GitHubEnvironmentSecretResolver({SNAPSHOT_SECRET_NAME: "not base64!"})(
            snapshot.config
        )

    with pytest.raises(OnlineSigningError, match="exactly 32 bytes"):
        GitHubEnvironmentSecretResolver(
            {SNAPSHOT_SECRET_NAME: base64.b64encode(b"short").decode("ascii")}
        )(snapshot.config)

    with pytest.raises(OnlineSigningError, match="does not match configured public key"):
        GitHubEnvironmentSecretResolver(
            {SNAPSHOT_SECRET_NAME: timestamp.secret_value_b64}
        )(snapshot.config)


def test_public_rotation_material_contains_no_private_seed_and_preserves_offline_roles() -> None:
    current_root_bytes = PRODUCTION_ROOT.read_bytes()
    material = prepare_zero_cost_rotation(current_root_bytes=current_root_bytes)
    public_manifest_bytes = json.dumps(
        material.public_manifest(), sort_keys=True
    ).encode("utf-8")
    combined_public = (
        public_manifest_bytes
        + material.rotation.unsigned_root_bytes
        + material.rotation.manifest_bytes
    )

    assert material.snapshot.secret_value_b64.encode("ascii") not in combined_public
    assert material.timestamp.secret_value_b64.encode("ascii") not in combined_public
    assert b"PRIVATE KEY" not in combined_public.upper()
    assert material.public_manifest()["private_material_in_manifest"] is False
    assert material.public_manifest()["paid_provider_required"] is False

    current = Metadata.from_bytes(current_root_bytes)
    proposed = Metadata.from_bytes(material.rotation.unsigned_root_bytes)
    assert isinstance(current.signed, Root)
    assert isinstance(proposed.signed, Root)
    assert proposed.signed.version == current.signed.version + 1
    assert proposed.signatures == {}
    assert proposed.signed.roles["root"] == current.signed.roles["root"]
    assert proposed.signed.roles["targets"] == current.signed.roles["targets"]
    assert proposed.signed.roles["snapshot"].keyids == [material.snapshot.config.keyid]
    assert proposed.signed.roles["timestamp"].keyids == [material.timestamp.config.keyid]


def test_public_manifest_uses_only_expected_github_environment_resources() -> None:
    material = prepare_zero_cost_rotation(current_root_bytes=PRODUCTION_ROOT.read_bytes())
    manifest = material.public_manifest()
    assert manifest["provider"] == "github-environment-secret"
    assert manifest["environment"] == "tuf-production-signing"
    assert manifest["snapshot"]["secret_name"] == SNAPSHOT_SECRET_NAME
    assert manifest["timestamp"]["secret_name"] == TIMESTAMP_SECRET_NAME
    assert manifest["snapshot"]["secret_name"] != manifest["timestamp"]["secret_name"]


def test_committed_public_package_matches_returned_zero_cost_material() -> None:
    public_manifest = json.loads(PUBLIC_KEYS.read_text(encoding="utf-8"))
    rotation_manifest = json.loads(ROTATION_MANIFEST.read_text(encoding="utf-8"))
    acceptance = json.loads(PUBLIC_ACCEPTANCE.read_text(encoding="utf-8"))
    current = Metadata.from_bytes(PRODUCTION_ROOT.read_bytes())
    proposed = Metadata.from_bytes(UNSIGNED_ROOT.read_bytes())

    assert _sha256(PRODUCTION_ROOT) == (
        "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
    )
    assert _sha256(PUBLIC_KEYS) == (
        "4da09ab071e3efea2e831871c752a4469fb126caf05172d911983ad115308030"
    )
    assert _sha256(UNSIGNED_ROOT) == (
        "7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d"
    )
    assert _sha256(ROTATION_MANIFEST) == (
        "f691dfa880d85fdf92f1b4ad2cc3167b81b1920ea4267494865d0b6460334188"
    )
    assert acceptance["uploaded_zip_sha256"] == (
        "4b26dbf702f93e1c2e6f813eae7c22771a06e97fd9d77bd6d57bff1b6c22b1db"
    )

    keyids: dict[str, str] = {}
    for role in ("snapshot", "timestamp"):
        entry = public_manifest[role]
        public_hex = entry["public_key"]["keyval"]["public"]
        crypto_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        derived = SSlibKey.from_crypto(crypto_key)
        assert derived.keyid == entry["keyid"]
        assert derived.to_dict() == entry["public_key"]
        assert hashlib.sha256(public_hex.encode("utf-8")).hexdigest() == entry[
            "public_sha256"
        ]
        keyids[role] = derived.keyid

    assert keyids["snapshot"] != keyids["timestamp"]
    assert isinstance(current.signed, Root)
    assert isinstance(proposed.signed, Root)
    assert proposed.signatures == {}
    assert proposed.signed.version == 2
    assert proposed.signed.roles["root"] == current.signed.roles["root"]
    assert proposed.signed.roles["targets"] == current.signed.roles["targets"]
    assert proposed.signed.roles["snapshot"].keyids == [keyids["snapshot"]]
    assert proposed.signed.roles["timestamp"].keyids == [keyids["timestamp"]]
    assert current.signed.roles["snapshot"].keyids[0] not in proposed.signed.keys
    assert current.signed.roles["timestamp"].keyids[0] not in proposed.signed.keys

    assert rotation_manifest["package_id"] == public_manifest[
        "root_rotation_package_id"
    ]
    assert rotation_manifest["current_root"]["version"] == 1
    assert rotation_manifest["proposed_root"]["version"] == 2
    assert rotation_manifest["proposed_root"]["signed"] is False
    assert rotation_manifest["offline_root_signatures_required"] == 2
    assert rotation_manifest["new_root_self_threshold_required"] == 2
    assert rotation_manifest["online_roles"]["snapshot"]["replacement_keyid"] == (
        keyids["snapshot"]
    )
    assert rotation_manifest["online_roles"]["timestamp"]["replacement_keyid"] == (
        keyids["timestamp"]
    )

    assert acceptance["replacement_keyids_derived_from_public_keys"] is True
    assert acceptance["replacement_keyids_distinct"] is True
    assert acceptance["root_policy_preserved"] is True
    assert acceptance["targets_policy_preserved"] is True
    assert acceptance["private_material_detected"] is False
    assert acceptance["paid_provider_required"] is False
    assert acceptance["production_effect"] is False
    assert acceptance["status"] == "pass"


def test_generate_online_key_rejects_any_role_except_snapshot_timestamp() -> None:
    with pytest.raises(OnlineSigningError, match="unsupported zero-cost online role"):
        generate_online_key("root")
