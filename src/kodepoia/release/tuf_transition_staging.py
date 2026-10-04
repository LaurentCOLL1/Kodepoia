from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.release.identity import ReleaseIdentity
from kodepoia.update.bootstrap import load_production_packaged_root
from kodepoia.update.corrective import (
    AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
    parse_authenticode_policy,
)
from kodepoia.update.discovery import UpdateDiscoveryService
from kodepoia.update.trust import (
    MemoryUpdateTransport,
    PackagedRootPin,
    SyntheticUpdateRepositoryBuilder,
    UpdateClient,
    UpdateTargetSpec,
)

CANDIDATE_SOURCE_SHA = "46ed800888b4f19da9e984232dd1ad6cdb639cc1"
CANDIDATE_PUBLIC_VERSION = "1.1.0"
CANDIDATE_CHANNEL = "stable"
CANDIDATE_PLATFORM = "windows-x86_64"
CANDIDATE_FILENAME = "KodepoiaSetup.exe"
CANDIDATE_INSTALLER_BYTES = 38_834_833
CANDIDATE_INSTALLER_SHA256 = (
    "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"
)
PUBLIC_BASELINE_VERSION = "1.1.0-rc8"
PUBLIC_BASELINE_SOURCE_SHA = "fa787ab7ef76f2556b56ac1f058916a1425455af"
REFERENCE_TIME = datetime(2026, 10, 4, 0, 0, tzinfo=UTC)
METADATA_NAMES = ("root.json", "targets.json", "snapshot.json", "timestamp.json")


def _canonical_digest(payload: dict[str, object]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _read_metadata(metadata_dir: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name in METADATA_NAMES:
        path = metadata_dir / name
        if not path.is_file():
            raise ValueError(f"required production metadata is missing: {path}")
        result[name] = path.read_bytes()
    return result


def _parse(data: bytes, expected: type[Any], label: str) -> Metadata[Any]:
    metadata = Metadata.from_bytes(data)
    if not isinstance(metadata.signed, expected):
        raise ValueError(f"{label} has unexpected signed type")
    return metadata


def production_observation(
    metadata_dir: Path,
    *,
    reference_time: datetime = REFERENCE_TIME,
) -> dict[str, object]:
    metadata = _read_metadata(metadata_dir)
    root_md = _parse(metadata["root.json"], Root, "root")
    targets_md = _parse(metadata["targets.json"], Targets, "targets")
    snapshot_md = _parse(metadata["snapshot.json"], Snapshot, "snapshot")
    timestamp_md = _parse(metadata["timestamp.json"], Timestamp, "timestamp")

    packaged = load_production_packaged_root()
    packaged.pin.verify(packaged.root_bytes)
    packaged_root_md = _parse(packaged.root_bytes, Root, "packaged root")
    packaged_root = packaged_root_md.signed

    root = root_md.signed
    if root.version == packaged_root.version:
        if metadata["root.json"] != packaged.root_bytes:
            raise ValueError("public Root changed without a version increment")
        root_continuity = "exact-packaged-root"
    elif root.version == packaged_root.version + 1:
        packaged_root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
        root_continuity = "verified-sequential-successor"
    else:
        raise ValueError("public Root is not the packaged Root or its next sequential successor")

    root.verify_delegate("root", root_md.signed_bytes, root_md.signatures)
    root.verify_delegate("targets", targets_md.signed_bytes, targets_md.signatures)
    root.verify_delegate("snapshot", snapshot_md.signed_bytes, snapshot_md.signatures)
    root.verify_delegate("timestamp", timestamp_md.signed_bytes, timestamp_md.signatures)
    snapshot_md.signed.meta["targets.json"].verify_length_and_hashes(metadata["targets.json"])
    timestamp_md.signed.snapshot_meta.verify_length_and_hashes(metadata["snapshot.json"])

    roles = {
        "root": root_md.signed,
        "targets": targets_md.signed,
        "snapshot": snapshot_md.signed,
        "timestamp": timestamp_md.signed,
    }
    expired = [name for name, signed in roles.items() if signed.is_expired(reference_time)]
    target_paths = sorted(targets_md.signed.targets)
    stable_prefix = (
        f"channels/{CANDIDATE_CHANNEL}/{CANDIDATE_PLATFORM}/"
        f"{CANDIDATE_PUBLIC_VERSION}/"
    )
    rc8_path = (
        f"channels/beta/{CANDIDATE_PLATFORM}/{PUBLIC_BASELINE_VERSION}/"
        f"{PUBLIC_BASELINE_SOURCE_SHA}/{CANDIDATE_FILENAME}"
    )
    return {
        "reference_time": reference_time.isoformat().replace("+00:00", "Z"),
        "versions": {name: int(signed.version) for name, signed in roles.items()},
        "expires": {
            name: signed.expires.isoformat().replace("+00:00", "Z")
            for name, signed in roles.items()
        },
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in metadata.items()},
        "packaged_root": {
            "version": packaged.pin.version,
            "sha256": packaged.pin.sha256,
            "production_trust_claim": packaged.production_trust_claim,
            "private_keys_persisted": packaged.private_keys_persisted,
        },
        "public_root": {
            "version": root.version,
            "sha256": hashlib.sha256(metadata["root.json"]).hexdigest(),
            "continuity": root_continuity,
        },
        "root_threshold": root.roles["root"].threshold,
        "root_key_count": len(root.roles["root"].keyids),
        "expired_roles": expired,
        "fail_closed_required": bool(expired),
        "target_paths": target_paths,
        "targets_count": len(target_paths),
        "rc8_target_present": rc8_path in targets_md.signed.targets,
        "stable_candidate_target_present": any(
            path.startswith(stable_prefix) for path in target_paths
        ),
    }


def candidate_target() -> UpdateTargetSpec:
    return UpdateTargetSpec(
        channel=CANDIDATE_CHANNEL,
        platform=CANDIDATE_PLATFORM,
        public_version=CANDIDATE_PUBLIC_VERSION,
        source_sha=CANDIDATE_SOURCE_SHA,
        filename=CANDIDATE_FILENAME,
    )


def build_transition_request(
    development_sha: str,
    observation: dict[str, object],
) -> dict[str, object]:
    target = candidate_target()
    custom = {
        "source_sha": CANDIDATE_SOURCE_SHA,
        "channel": CANDIDATE_CHANNEL,
        "public_version": CANDIDATE_PUBLIC_VERSION,
        "release_notes_summary": "Kodepoia 1.1.0 stable terminal V2 release.",
        "signing_status": "unsigned; production trust is not claimed",
        "provenance_status": "exact-source V2.6.3 candidate evidence",
        "withdrawn": False,
        "payload_url": (
            "https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
            f"v{CANDIDATE_PUBLIC_VERSION}/{CANDIDATE_FILENAME}"
        ),
        "authenticode_policy": AUTHENTICODE_POLICY_ALLOW_UNSIGNED,
    }
    versions = dict(observation["versions"])
    payload: dict[str, object] = {
        "format": "kodepoia-v2-6-4-production-tuf-transition-request",
        "schema_version": 1,
        "development_source_sha": development_sha.lower(),
        "release_candidate_source_sha": CANDIDATE_SOURCE_SHA,
        "public_baseline": {
            "public_version": PUBLIC_BASELINE_VERSION,
            "source_sha": PUBLIC_BASELINE_SOURCE_SHA,
        },
        "production_observation": {
            "versions": versions,
            "sha256": dict(observation["sha256"]),
            "expired_roles": list(observation["expired_roles"]),
            "root_pin_sha256": dict(observation["packaged_root"])["sha256"],
        },
        "requested_target": {
            "path": target.path,
            "length": CANDIDATE_INSTALLER_BYTES,
            "sha256": CANDIDATE_INSTALLER_SHA256,
            "custom": custom,
        },
        "requested_role_versions": {
            "root": int(versions["root"]),
            "targets": int(versions["targets"]) + 1,
            "snapshot": int(versions["snapshot"]) + 1,
            "timestamp": int(versions["timestamp"]) + 1,
        },
        "target_history": {
            "preserve": list(observation["target_paths"]),
            "revoke": [],
        },
        "signing_requirements": {
            "root": "unchanged-packaged-production-root",
            "targets": "existing-production-targets-role-signature-required-later",
            "snapshot": "existing-production-online-role-signature-required-later",
            "timestamp": "existing-production-online-role-signature-required-later",
            "synthetic_keys_permitted_as_production_proof": False,
            "signing_secrets_resolved_in_v2_6_4": False,
        },
        "freshness_requirements": {
            "existing_expired_online_metadata_must_remain_rejected": True,
            "future_signed_snapshot_timestamp_must_be_fresh": True,
            "existing_expiry_may_not_be_artificially_extended": True,
        },
        "effect_boundary": {
            "live_repository_mutated": False,
            "public_release_published": False,
            "public_tag_created_or_repointed": False,
            "public_assets_uploaded": False,
            "live_updater_activated": False,
            "production_signing_claimed": False,
            "winget_submitted": False,
        },
    }
    payload["request_sha256"] = _canonical_digest(payload)
    return payload


def validate_transition_request(request: dict[str, object]) -> None:
    target = dict(request.get("requested_target") or {})
    custom = dict(target.get("custom") or {})
    expected = candidate_target()
    if request.get("release_candidate_source_sha") != CANDIDATE_SOURCE_SHA:
        raise ValueError("release candidate source binding mismatch")
    if target.get("path") != expected.path:
        raise ValueError("stable target path mismatch")
    if target.get("length") != CANDIDATE_INSTALLER_BYTES:
        raise ValueError("candidate installer length mismatch")
    if target.get("sha256") != CANDIDATE_INSTALLER_SHA256:
        raise ValueError("candidate installer SHA-256 mismatch")
    if custom.get("source_sha") != CANDIDATE_SOURCE_SHA:
        raise ValueError("target custom source SHA mismatch")
    if custom.get("channel") != CANDIDATE_CHANNEL:
        raise ValueError("target channel mismatch")
    if custom.get("public_version") != CANDIDATE_PUBLIC_VERSION:
        raise ValueError("target public version mismatch")
    if parse_authenticode_policy(custom) != AUTHENTICODE_POLICY_ALLOW_UNSIGNED:
        raise ValueError("candidate Authenticode policy mismatch")
    history = dict(request.get("target_history") or {})
    if history.get("revoke") != []:
        raise ValueError("V2.6.4 may not revoke historical targets")
    boundary = dict(request.get("effect_boundary") or {})
    if any(bool(value) for value in boundary.values()):
        raise ValueError("V2.6.4 transition request contains a forbidden live effect")
    expected_digest = request.get("request_sha256")
    unsigned = dict(request)
    unsigned.pop("request_sha256", None)
    if expected_digest != _canonical_digest(unsigned):
        raise ValueError("transition request digest mismatch")


def _rc8_identity() -> ReleaseIdentity:
    return ReleaseIdentity(
        schema_version=1,
        product="Kodepoia",
        package="kodepoia",
        channel="beta",
        build_type="prerelease",
        source_binding="exact-head",
        major=1,
        minor=1,
        patch=0,
        stage="rc",
        serial=8,
    )


def isolated_updater_rehearsal(
    *,
    reference_time: datetime = REFERENCE_TIME,
) -> dict[str, object]:
    fixture = b"v2.6.4 isolated updater compatibility rehearsal\n"
    target = candidate_target()
    builder = SyntheticUpdateRepositoryBuilder()
    repository = builder.build(
        target,
        fixture,
        timestamp_version=11,
        snapshot_version=11,
        targets_version=9,
    )
    pin = PackagedRootPin.from_root(repository.root)
    results: dict[str, object] = {
        "fixture_only": True,
        "production_proof": False,
        "fixture_matches_release_candidate_binary": False,
        "target_identity_matches_release_candidate": True,
    }

    with tempfile.TemporaryDirectory() as temp:
        transport = MemoryUpdateTransport.from_repository(repository)
        discovery = UpdateDiscoveryService(
            Path(temp) / "discovery",
            root_pin=pin,
            transport=transport,
            platform=CANDIDATE_PLATFORM,
            installed_release=_rc8_identity(),
            reference_time=reference_time,
        )
        stable = discovery.check("stable")
        wrong = discovery.check("beta")
        results["rc8_to_stable_discovery"] = stable.status
        results["wrong_channel"] = wrong.status
        results["stable_candidate_path"] = (
            stable.candidate.target.path if stable.candidate is not None else None
        )

    with tempfile.TemporaryDirectory() as temp:
        transport = MemoryUpdateTransport.from_repository(repository)
        client = UpdateClient(Path(temp), root_pin=pin, reference_time=reference_time)
        verified = client.check(transport, target)
        results["target_validation_before_eligibility"] = verified.status
        transport.targets[target.path] = b"tampered-v2.6.4-fixture\n"
        tampered = client.check(transport, target)
        results["tampered_target"] = tampered.status
        transport.targets[target.path] = fixture
        transport.online = False
        offline = client.check(transport, target)
        results["offline_after_verified_cache"] = offline.status

    with tempfile.TemporaryDirectory() as temp:
        expired_repository = builder.build(
            target,
            fixture,
            timestamp_version=12,
            snapshot_version=12,
            targets_version=10,
            timestamp_expires=datetime(2026, 10, 3, 0, 0, tzinfo=UTC),
        )
        expired = UpdateDiscoveryService(
            Path(temp),
            root_pin=PackagedRootPin.from_root(expired_repository.root),
            transport=MemoryUpdateTransport.from_repository(expired_repository),
            platform=CANDIDATE_PLATFORM,
            installed_release=_rc8_identity(),
            reference_time=reference_time,
        ).check("stable")
        results["expired_metadata"] = expired.status

    with tempfile.TemporaryDirectory() as temp:
        high = builder.build(
            target,
            fixture,
            timestamp_version=20,
            snapshot_version=20,
            targets_version=20,
        )
        service = UpdateDiscoveryService(
            Path(temp),
            root_pin=PackagedRootPin.from_root(high.root),
            transport=MemoryUpdateTransport.from_repository(high),
            platform=CANDIDATE_PLATFORM,
            installed_release=_rc8_identity(),
            reference_time=reference_time,
        )
        first = service.check("stable")
        low = builder.build(
            target,
            fixture,
            timestamp_version=19,
            snapshot_version=21,
            targets_version=21,
        )
        service.transport = MemoryUpdateTransport.from_repository(low)
        rollback = service.check("stable")
        results["rollback_baseline"] = first.status
        results["timestamp_rollback"] = rollback.status

    with tempfile.TemporaryDirectory() as temp:
        corrupt_transport = MemoryUpdateTransport.from_repository(repository)
        corrupt_transport.metadata["snapshot.json"] = b"{}\n"
        corrupt = UpdateDiscoveryService(
            Path(temp),
            root_pin=pin,
            transport=corrupt_transport,
            platform=CANDIDATE_PLATFORM,
            installed_release=_rc8_identity(),
            reference_time=reference_time,
        ).check("stable")
        results["corrupt_metadata"] = corrupt.status

    with tempfile.TemporaryDirectory() as temp:
        attacker = SyntheticUpdateRepositoryBuilder().build(target, fixture)
        wrong_root = UpdateDiscoveryService(
            Path(temp),
            root_pin=pin,
            transport=MemoryUpdateTransport.from_repository(attacker),
            platform=CANDIDATE_PLATFORM,
            installed_release=_rc8_identity(),
            reference_time=reference_time,
        ).check("stable")
        results["wrong_root_pin"] = wrong_root.status

    return results


def build_v2_6_4_report(
    development_sha: str,
    *,
    repository_root: Path,
    reference_time: datetime = REFERENCE_TIME,
) -> dict[str, object]:
    observation = production_observation(
        repository_root / "update-repository" / "metadata",
        reference_time=reference_time,
    )
    request = build_transition_request(development_sha, observation)
    validate_transition_request(request)
    rehearsal = isolated_updater_rehearsal(reference_time=reference_time)

    expected_rehearsal = {
        "rc8_to_stable_discovery": "update-available",
        "wrong_channel": "channel-unavailable",
        "target_validation_before_eligibility": "verified",
        "tampered_target": "verification-failed",
        "offline_after_verified_cache": "offline-cached",
        "expired_metadata": "metadata-expired",
        "rollback_baseline": "update-available",
        "timestamp_rollback": "verification-failed",
        "corrupt_metadata": "verification-failed",
        "wrong_root_pin": "verification-failed",
    }
    checks = {
        "candidate_binding_exact": request["release_candidate_source_sha"] == CANDIDATE_SOURCE_SHA,
        "candidate_hash_exact": (
            dict(request["requested_target"])["sha256"] == CANDIDATE_INSTALLER_SHA256
        ),
        "candidate_length_exact": (
            dict(request["requested_target"])["length"] == CANDIDATE_INSTALLER_BYTES
        ),
        "production_root_packaged_pin": (
            dict(observation["packaged_root"])["production_trust_claim"] is True
            and dict(observation["packaged_root"])["private_keys_persisted"] is False
            and dict(observation["public_root"])["continuity"]
            in {"exact-packaged-root", "verified-sequential-successor"}
        ),
        "production_root_threshold": (
            observation["root_threshold"] == 2 and observation["root_key_count"] == 3
        ),
        "production_online_metadata_expired_fail_closed": (
            set(observation["expired_roles"]) == {"snapshot", "timestamp"}
            and observation["fail_closed_required"] is True
        ),
        "historical_rc8_preserved": observation["rc8_target_present"] is True,
        "stable_target_not_live_yet": observation["stable_candidate_target_present"] is False,
        "history_preserved_without_revocation": (
            len(dict(request["target_history"])["preserve"]) == observation["targets_count"]
            and dict(request["target_history"])["revoke"] == []
        ),
        "unsigned_policy_exact_target": (
            parse_authenticode_policy(dict(dict(request["requested_target"])["custom"]))
            == AUTHENTICODE_POLICY_ALLOW_UNSIGNED
        ),
        "isolated_fixture_not_production_proof": (
            rehearsal["fixture_only"] is True
            and rehearsal["production_proof"] is False
            and rehearsal["fixture_matches_release_candidate_binary"] is False
        ),
        "isolated_updater_adversarial_rehearsal": all(
            rehearsal[name] == expected for name, expected in expected_rehearsal.items()
        ),
        "no_live_effect": not any(dict(request["effect_boundary"]).values()),
        "no_production_signing_claim": (
            dict(request["signing_requirements"])["synthetic_keys_permitted_as_production_proof"]
            is False
            and dict(request["signing_requirements"])["signing_secrets_resolved_in_v2_6_4"]
            is False
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    report: dict[str, object] = {
        "schema_version": 1,
        "subdivision": "V2.6.4",
        "title": "Production TUF transition and updater compatibility staging",
        "development_source_sha": development_sha.lower(),
        "release_candidate_source_sha": CANDIDATE_SOURCE_SHA,
        "reference_time": reference_time.isoformat().replace("+00:00", "Z"),
        "production_observation": observation,
        "transition_request": request,
        "isolated_updater_rehearsal": rehearsal,
        "checks": checks,
        "summary": {"passed": len(checks) - len(failed), "total": len(checks), "failed": failed},
        "status": "PASS" if not failed else "FAIL",
        "production_tuf_mutation_triggered": False,
        "public_release_triggered": False,
        "public_tag_triggered": False,
        "public_asset_upload_triggered": False,
        "live_updater_activation_triggered": False,
        "signing_secret_provisioned": False,
        "winget_submission_triggered": False,
    }
    report["evidence_sha256"] = _canonical_digest(report)
    return report


__all__ = [
    "CANDIDATE_INSTALLER_BYTES",
    "CANDIDATE_INSTALLER_SHA256",
    "CANDIDATE_SOURCE_SHA",
    "REFERENCE_TIME",
    "build_transition_request",
    "build_v2_6_4_report",
    "candidate_target",
    "isolated_updater_rehearsal",
    "production_observation",
    "validate_transition_request",
]
