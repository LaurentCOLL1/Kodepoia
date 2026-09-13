from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from securesystemslib.signer import CryptoSigner, SSlibKey, Signer
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

from kodepoia.update.online_signing import OnlineSignerConfig, resolve_online_signers
from kodepoia.update.zero_cost_signing import (
    ZERO_COST_PROVIDER,
    GitHubEnvironmentSecretResolver,
)

SCHEMA_VERSION = 1
FORMAT = "kodepoia-tuf-release-ceremony"
EXPECTED_ENVIRONMENT = "tuf-production-signing"
SNAPSHOT_EXPIRY_HOURS = 72
TIMESTAMP_EXPIRY_HOURS = 48
PRIVATE_MARKERS = (
    b"PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"ENCRYPTED PRIVATE KEY",
    b"PASSPHRASE",
    b"PASSWORD",
)
PUBLIC_VERSION_RE = re.compile(r"^(?P<base>\d+\.\d+\.\d+)-rc(?P<rc>\d+)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class CeremonyError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        resolution: str,
        auto_fixable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.resolution = resolution
        self.auto_fixable = auto_fixable


class Report:
    def __init__(self) -> None:
        self.issues: list[dict[str, object]] = []
        self.fixes: list[dict[str, object]] = []
        self.checks: list[dict[str, object]] = []

    def check(self, name: str, detail: str) -> None:
        self.checks.append({"name": name, "status": "pass", "detail": detail})

    def issue(self, exc: CeremonyError) -> None:
        self.issues.append(
            {
                "code": exc.code,
                "message": str(exc),
                "auto_fixable": exc.auto_fixable,
                "resolution": exc.resolution,
            }
        )

    def fix(self, code: str, where: str, how: str) -> None:
        self.fixes.append({"code": code, "where": where, "how": how})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(data: bytes, expected: type[Any], label: str) -> Metadata[Any]:
    try:
        metadata = Metadata.from_bytes(data)
    except Exception as exc:
        raise CeremonyError(
            "INVALID_METADATA",
            f"{label} is not valid TUF metadata: {exc}",
            resolution="Restore the last known-good public metadata and rerun the ceremony.",
        ) from exc
    if not isinstance(metadata.signed, expected):
        raise CeremonyError(
            "WRONG_METADATA_ROLE",
            f"{label} has an unexpected TUF role.",
            resolution="Restore the correct metadata file for this role before continuing.",
        )
    return metadata


def _verify_role(root: Root, role: str, metadata: Metadata[Any]) -> None:
    try:
        root.verify_delegate(role, metadata.signed_bytes, metadata.signatures)
    except Exception as exc:
        raise CeremonyError(
            "SIGNATURE_THRESHOLD_FAILURE",
            f"{role} signature threshold failed: {exc}",
            resolution=(
                "Do not regenerate keys. Restore or re-sign the metadata with the already-authorized "
                f"{role} authority and rerun."
            ),
        ) from exc


def _verify_reference(reference: Any, data: bytes, label: str) -> None:
    try:
        reference.verify_length_and_hashes(data)
    except Exception as exc:
        raise CeremonyError(
            "METADATA_BINDING_FAILURE",
            f"{label} hash/length binding failed: {exc}",
            resolution="Stop publication, restore a coherent metadata generation, then rerun.",
        ) from exc


def _serialize(metadata: Metadata[Any]) -> bytes:
    return metadata.to_bytes() + b"\n"


def _new_signed_metadata(payload: dict[str, object], signers: list[Signer]) -> bytes:
    envelope = Metadata.from_dict({"signatures": [], "signed": payload})
    for index, signer in enumerate(signers):
        envelope.sign(signer, append=index > 0)
    return _serialize(envelope)


def _assert_public_only(payloads: dict[str, bytes]) -> None:
    for name, data in payloads.items():
        upper = data.upper()
        if any(marker in upper for marker in PRIVATE_MARKERS):
            raise CeremonyError(
                "PRIVATE_MATERIAL_OUTPUT",
                f"forbidden private-material marker detected in public output {name}",
                resolution="Delete the staged output, inspect the generating code, and do not publish it.",
            )


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        output = getattr(exc, "output", "") or ""
        raise CeremonyError(
            "GIT_CHECK_FAILED",
            f"git {' '.join(args)} failed: {output.strip() or exc}",
            resolution="Run the ceremony from a complete Kodepoia Git checkout and verify the source SHA.",
        ) from exc


def _verify_source_identity(source_sha: str, public_version: str, report: Report) -> None:
    if not SHA_RE.fullmatch(source_sha):
        raise CeremonyError(
            "INVALID_SOURCE_SHA",
            "source SHA must be exactly 40 lowercase hexadecimal characters",
            resolution="Use the exact qualified release commit SHA and rerun.",
        )
    _git("cat-file", "-e", f"{source_sha}^{{commit}}")
    pyproject = _git("show", f"{source_sha}:pyproject.toml")
    match = PUBLIC_VERSION_RE.fullmatch(public_version)
    if match is None:
        raise CeremonyError(
            "INVALID_PUBLIC_VERSION",
            f"unsupported public version format: {public_version}",
            resolution="Use the canonical form such as 1.1.0-rc6.",
        )
    expected_pep440 = f"{match.group('base')}rc{match.group('rc')}"
    version_line = f'version = "{expected_pep440}"'
    if version_line not in pyproject:
        raise CeremonyError(
            "SOURCE_VERSION_MISMATCH",
            f"{source_sha} does not declare {version_line}",
            resolution="Use the exact version-only release commit or correct the release identity before signing.",
        )
    report.check("source-identity", f"{source_sha} declares {expected_pep440}")


def _load_current_metadata(metadata_dir: Path) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name in ("root.json", "targets.json", "snapshot.json", "timestamp.json"):
        path = metadata_dir / name
        if not path.is_file():
            raise CeremonyError(
                "MISSING_METADATA",
                f"required metadata file is missing: {name}",
                resolution="Restore the canonical update-repository metadata before running the ceremony.",
            )
        result[name] = path.read_bytes()
    return result


def _verify_current_state(
    metadata: dict[str, bytes], reference_time: datetime, report: Report
) -> tuple[Metadata[Root], Metadata[Targets], Metadata[Snapshot], Metadata[Timestamp]]:
    root_md = _parse(metadata["root.json"], Root, "root.json")
    targets_md = _parse(metadata["targets.json"], Targets, "targets.json")
    snapshot_md = _parse(metadata["snapshot.json"], Snapshot, "snapshot.json")
    timestamp_md = _parse(metadata["timestamp.json"], Timestamp, "timestamp.json")
    root = root_md.signed

    for role, item in (
        ("root", root_md),
        ("targets", targets_md),
        ("snapshot", snapshot_md),
        ("timestamp", timestamp_md),
    ):
        _verify_role(root, role, item)

    if root.is_expired(reference_time):
        raise CeremonyError(
            "ROOT_EXPIRED",
            "Root authority is expired.",
            resolution="A separately governed Root ceremony is required; do not continue this release ceremony.",
        )
    if targets_md.signed.is_expired(reference_time):
        raise CeremonyError(
            "TARGETS_EXPIRED",
            "Targets authority is expired.",
            resolution="Re-sign Targets with the existing authorized offline authority before continuing.",
        )

    targets_ref = snapshot_md.signed.meta.get("targets.json")
    if targets_ref is None or targets_ref.version != targets_md.signed.version:
        raise CeremonyError(
            "SNAPSHOT_TARGETS_VERSION_MISMATCH",
            "current Snapshot does not bind the current Targets version",
            resolution="Restore the last coherent public generation before attempting a release transition.",
        )
    _verify_reference(targets_ref, metadata["targets.json"], "current targets.json")
    if timestamp_md.signed.snapshot_meta.version != snapshot_md.signed.version:
        raise CeremonyError(
            "TIMESTAMP_SNAPSHOT_VERSION_MISMATCH",
            "current Timestamp does not bind the current Snapshot version",
            resolution="Restore the last coherent public generation before attempting a release transition.",
        )
    _verify_reference(timestamp_md.signed.snapshot_meta, metadata["snapshot.json"], "current snapshot.json")

    report.check(
        "current-tuf-chain",
        (
            f"Root v{root.version}, Targets v{targets_md.signed.version}, "
            f"Snapshot v{snapshot_md.signed.version}, Timestamp v{timestamp_md.signed.version}"
        ),
    )
    return root_md, targets_md, snapshot_md, timestamp_md


def _discover_pem_signers(
    private_key_dir: Path,
    *,
    passphrase: bytes,
    root: Root,
    role: str,
) -> list[Signer]:
    if not private_key_dir.is_dir():
        raise CeremonyError(
            "OFFLINE_KEY_DIR_MISSING",
            "offline private-key directory does not exist",
            resolution="Provide the local custody directory containing the already-authorized Targets key(s).",
        )
    authorized = set(root.roles[role].keyids)
    threshold = root.roles[role].threshold
    found: dict[str, Signer] = {}
    for path in sorted(private_key_dir.rglob("*.pem")):
        if not path.is_file():
            continue
        try:
            private_key = load_pem_private_key(path.read_bytes(), password=passphrase)
            signer = CryptoSigner(private_key)
        except Exception:
            continue
        if signer.public_key.keyid in authorized:
            found.setdefault(signer.public_key.keyid, signer)
    if len(found) < threshold:
        raise CeremonyError(
            "TARGETS_SIGNER_UNAVAILABLE",
            f"not enough authorized {role} signers were unlocked; need {threshold}, found {len(found)}",
            resolution=(
                "Use the existing custody material for the already-authorized Targets role. "
                "Do not generate a replacement key merely to unblock this release."
            ),
        )
    return list(found.values())[:threshold]


def _config_from_manifest(role: str, entry: dict[str, object]) -> OnlineSignerConfig:
    public_key = entry.get("public_key")
    if not isinstance(public_key, dict):
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            f"missing public key entry for {role}",
            resolution="Restore the accepted R20 online public-key manifest.",
        )
    keyval = public_key.get("keyval")
    if not isinstance(keyval, dict) or not isinstance(keyval.get("public"), str):
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            f"invalid public key payload for {role}",
            resolution="Restore the accepted R20 online public-key manifest.",
        )
    try:
        crypto_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(keyval["public"]))
        sslib_key = SSlibKey.from_crypto(crypto_key)
    except (ValueError, TypeError) as exc:
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            f"invalid Ed25519 public key for {role}",
            resolution="Restore the accepted R20 online public-key manifest.",
        ) from exc
    expected_keyid = entry.get("keyid")
    secret_name = entry.get("secret_name")
    if sslib_key.keyid != expected_keyid or not isinstance(secret_name, str) or not secret_name:
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            f"public key identity or secret resource mismatch for {role}",
            resolution="Restore the accepted R20 online public-key manifest.",
        )
    return OnlineSignerConfig(
        role=role,
        provider=ZERO_COST_PROVIDER,
        resource=secret_name,
        public_key=sslib_key,
    )


def _resolve_online_signers(public_keys_path: Path, root: Root, report: Report) -> tuple[Signer, Signer]:
    try:
        manifest = json.loads(public_keys_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CeremonyError(
            "ONLINE_SIGNER_MANIFEST_MISSING",
            "cannot load the accepted online signer public manifest",
            resolution="Restore docs/roadmap/R20_3_PUBLIC_KEYS.json or supply the correct public manifest.",
        ) from exc
    if not isinstance(manifest, dict):
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            "online signer manifest must be a JSON object",
            resolution="Restore the accepted online signer public manifest.",
        )
    if manifest.get("provider") != ZERO_COST_PROVIDER or manifest.get("environment") != EXPECTED_ENVIRONMENT:
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            "online signer provider/environment does not match production policy",
            resolution="Use the accepted production public-key manifest; do not generate replacement keys.",
        )
    snapshot_entry = manifest.get("snapshot")
    timestamp_entry = manifest.get("timestamp")
    if not isinstance(snapshot_entry, dict) or not isinstance(timestamp_entry, dict):
        raise CeremonyError(
            "ONLINE_PUBLIC_MANIFEST_INVALID",
            "online role entries are malformed",
            resolution="Restore the accepted online signer public manifest.",
        )
    try:
        configs = [
            _config_from_manifest("snapshot", snapshot_entry),
            _config_from_manifest("timestamp", timestamp_entry),
        ]
        resolved = resolve_online_signers(configs, GitHubEnvironmentSecretResolver())
    except Exception as exc:
        raise CeremonyError(
            "ONLINE_SIGNERS_UNAVAILABLE",
            f"authorized Snapshot/Timestamp signers are unavailable in this environment: {exc}",
            resolution=(
                "Run this same file in the approved tuf-production-signing environment where the existing "
                "Snapshot/Timestamp secrets are available. Do not paste secret values into ChatGPT or Git."
            ),
        ) from exc
    if resolved.snapshot.public_key.keyid not in set(root.roles["snapshot"].keyids):
        raise CeremonyError(
            "SNAPSHOT_SIGNER_UNAUTHORIZED",
            "resolved Snapshot signer is not authorized by Root",
            resolution="Restore the existing authorized Snapshot secret/configuration.",
        )
    if resolved.timestamp.public_key.keyid not in set(root.roles["timestamp"].keyids):
        raise CeremonyError(
            "TIMESTAMP_SIGNER_UNAUTHORIZED",
            "resolved Timestamp signer is not authorized by Root",
            resolution="Restore the existing authorized Timestamp secret/configuration.",
        )
    report.check("online-signers", "existing authorized Snapshot/Timestamp signers resolved")
    return resolved.snapshot, resolved.timestamp


def _asset_identity(asset: Path, expected_sha: str | None, expected_size: int | None, report: Report) -> tuple[int, str]:
    if not asset.is_file():
        raise CeremonyError(
            "ASSET_MISSING",
            f"release asset is missing: {asset.name}",
            resolution="Build or download the exact installer from the qualified source SHA and rerun.",
        )
    data = asset.read_bytes()
    size = len(data)
    digest = _sha256(data)
    if expected_size is not None and size != expected_size:
        raise CeremonyError(
            "ASSET_SIZE_MISMATCH",
            f"installer size is {size}, expected {expected_size}",
            resolution="Do not sign this asset. Re-obtain the exact qualified installer and verify its provenance.",
        )
    if expected_sha is not None and digest != expected_sha.lower():
        raise CeremonyError(
            "ASSET_SHA256_MISMATCH",
            f"installer SHA-256 is {digest}, expected {expected_sha.lower()}",
            resolution="Do not sign this asset. Re-obtain the exact qualified installer and verify its provenance.",
        )
    report.check("asset-identity", f"{asset.name}: {size} bytes, sha256={digest}")
    return size, digest


def _build_targets(
    *,
    current: Metadata[Targets],
    root: Root,
    signers: list[Signer],
    public_version: str,
    source_sha: str,
    filename: str,
    size: int,
    digest: str,
    channel: str,
    platform: str,
    payload_url: str,
    release_notes_summary: str,
    report: Report,
) -> tuple[bytes, bool, str]:
    target_path = f"channels/{channel}/{platform}/{public_version}/{source_sha}/{filename}"
    targets = dict(current.signed.targets)
    existing = targets.get(target_path)
    expected_custom = {
        "channel": channel,
        "payload_url": payload_url,
        "provenance_status": "exact-source-r18-provenance-required-before-publication",
        "public_version": public_version,
        "release_notes_summary": release_notes_summary,
        "signing_status": "unsigned; production trust is not claimed",
        "source_sha": source_sha,
        "withdrawn": False,
    }
    expected = {
        "hashes": {"sha256": digest},
        "length": size,
        "custom": expected_custom,
    }
    if existing is not None:
        existing_dict = existing.to_dict()
        if existing_dict != expected:
            raise CeremonyError(
                "TARGET_ALREADY_EXISTS_DIFFERENT",
                f"target path already exists with different identity: {target_path}",
                resolution="Stop and inspect the existing authorization. Never overwrite a conflicting target silently.",
            )
        report.check("targets-idempotency", "exact release target is already authorized")
        return _serialize(current), False, target_path

    payload = current.signed.to_dict()
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, dict):
        raise CeremonyError(
            "TARGETS_PAYLOAD_INVALID",
            "current Targets payload is malformed",
            resolution="Restore the last known-good Targets metadata.",
        )
    before_keys = set(raw_targets)
    raw_targets[target_path] = expected
    payload["version"] = current.signed.version + 1
    new_bytes = _new_signed_metadata(payload, signers)
    new_md = _parse(new_bytes, Targets, "new targets.json")
    _verify_role(root, "targets", new_md)
    after_keys = set(new_md.signed.targets)
    if not before_keys.issubset(after_keys) or after_keys - before_keys != {target_path}:
        raise CeremonyError(
            "TARGET_PRESERVATION_FAILURE",
            "new Targets metadata does not preserve every prior target plus exactly the new release target",
            resolution="Discard the staged metadata and inspect the transition logic before retrying.",
        )
    report.check(
        "targets-transition",
        f"Targets v{current.signed.version} -> v{new_md.signed.version}; prior targets preserved; one target added",
    )
    return new_bytes, True, target_path


def _build_online_pair(
    *,
    root: Root,
    current_snapshot: Metadata[Snapshot],
    current_timestamp: Metadata[Timestamp],
    targets_bytes: bytes,
    targets_md: Metadata[Targets],
    snapshot_signer: Signer,
    timestamp_signer: Signer,
    now: datetime,
    report: Report,
) -> tuple[bytes, bytes]:
    snapshot_expiry = now + timedelta(hours=SNAPSHOT_EXPIRY_HOURS)
    timestamp_expiry = now + timedelta(hours=TIMESTAMP_EXPIRY_HOURS)
    authority_expiry = min(root.expires.astimezone(UTC), targets_md.signed.expires.astimezone(UTC))
    if snapshot_expiry >= authority_expiry or timestamp_expiry >= authority_expiry:
        raise CeremonyError(
            "ONLINE_EXPIRY_EXCEEDS_AUTHORITY",
            "new online metadata would expire after Root/Targets authority",
            resolution="Refresh the governing offline authority through its separate process before publishing.",
        )

    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": _iso(snapshot_expiry),
        "meta": {
            "targets.json": {
                "hashes": {"sha256": _sha256(targets_bytes)},
                "length": len(targets_bytes),
                "version": targets_md.signed.version,
            }
        },
        "spec_version": current_snapshot.signed.spec_version,
        "version": current_snapshot.signed.version + 1,
    }
    snapshot_bytes = _new_signed_metadata(snapshot_payload, [snapshot_signer])
    snapshot_md = _parse(snapshot_bytes, Snapshot, "new snapshot.json")
    _verify_role(root, "snapshot", snapshot_md)
    _verify_reference(snapshot_md.signed.meta["targets.json"], targets_bytes, "new targets.json")

    timestamp_payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": _iso(timestamp_expiry),
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": _sha256(snapshot_bytes)},
                "length": len(snapshot_bytes),
                "version": snapshot_md.signed.version,
            }
        },
        "spec_version": current_timestamp.signed.spec_version,
        "version": current_timestamp.signed.version + 1,
    }
    timestamp_bytes = _new_signed_metadata(timestamp_payload, [timestamp_signer])
    timestamp_md = _parse(timestamp_bytes, Timestamp, "new timestamp.json")
    _verify_role(root, "timestamp", timestamp_md)
    _verify_reference(timestamp_md.signed.snapshot_meta, snapshot_bytes, "new snapshot.json")
    report.check(
        "online-transition",
        (
            f"Snapshot v{current_snapshot.signed.version} -> v{snapshot_md.signed.version}; "
            f"Timestamp v{current_timestamp.signed.version} -> v{timestamp_md.signed.version}"
        ),
    )
    return snapshot_bytes, timestamp_bytes


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_stage(staging_dir: Path, payloads: dict[str, bytes], report: Report) -> None:
    if staging_dir.exists():
        stale = list(staging_dir.iterdir())
        if stale:
            shutil.rmtree(staging_dir)
            report.fix(
                "STALE_STAGING_OUTPUT",
                staging_dir.name,
                "removed stale staged public output before regenerating the verified generation",
            )
    staging_dir.mkdir(parents=True, exist_ok=True)
    _assert_public_only(payloads)
    for name, data in payloads.items():
        (staging_dir / name).write_bytes(data)


def _atomic_apply(metadata_dir: Path, staged: dict[str, bytes], report: Report) -> None:
    temp_paths: list[Path] = []
    try:
        for name, data in staged.items():
            tmp = metadata_dir / f".{name}.ceremony.tmp"
            tmp.write_bytes(data)
            temp_paths.append(tmp)
        for name in ("targets.json", "snapshot.json", "timestamp.json"):
            os.replace(metadata_dir / f".{name}.ceremony.tmp", metadata_dir / name)
        report.fix(
            "ATOMIC_METADATA_APPLY",
            "update-repository/metadata",
            "replaced Targets/Snapshot/Timestamp only after complete signature and binding verification",
        )
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)


def _summary_text(status: str, report: Report, generation: dict[str, object] | None) -> str:
    lines = [f"TUF CEREMONY: {status}"]
    if generation:
        lines.append(
            "Generation: "
            f"Targets v{generation['targets_version']}, "
            f"Snapshot v{generation['snapshot_version']}, "
            f"Timestamp v{generation['timestamp_version']}"
        )
    if report.fixes:
        lines.append("Corrections automatiques effectuées:")
        for item in report.fixes:
            lines.append(f"- {item['where']}: {item['how']}")
    if report.issues:
        lines.append("Erreurs bloquantes:")
        for item in report.issues:
            lines.append(f"- [{item['code']}] {item['message']}")
            lines.append(f"  Solution: {item['resolution']}")
    if not report.fixes and not report.issues:
        lines.append("Aucune erreur détectée et aucune correction nécessaire.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one fail-closed Kodepoia release TUF ceremony: validate current trust, "
            "authorize one release target with existing Targets custody, create monotonic "
            "Snapshot/Timestamp metadata, verify everything, stage public output, and optionally apply it."
        )
    )
    parser.add_argument("--public-version", required=True, help="Public version, e.g. 1.1.0-rc6")
    parser.add_argument("--source-sha", required=True, help="Exact qualified 40-character source commit")
    parser.add_argument("--asset", type=Path, required=True, help="Exact installer to authorize")
    parser.add_argument("--offline-key-dir", type=Path, required=True, help="Local offline custody directory")
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("update-repository/metadata"),
    )
    parser.add_argument(
        "--online-public-keys",
        type=Path,
        default=Path("docs/roadmap/R20_3_PUBLIC_KEYS.json"),
    )
    parser.add_argument("--channel", default="beta")
    parser.add_argument("--platform", default="windows-x86_64")
    parser.add_argument("--expected-asset-sha256")
    parser.add_argument("--expected-asset-size", type=int)
    parser.add_argument("--expected-root-sha256")
    parser.add_argument(
        "--release-notes-summary",
        default="Kodepoia validation-only release candidate for updater end-to-end acceptance.",
    )
    parser.add_argument(
        "--payload-url",
        help="Final public installer URL; defaults to the canonical GitHub release URL.",
    )
    parser.add_argument(
        "--staging-dir",
        type=Path,
        default=Path("artifacts/tuf_ceremony/staged_metadata"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("artifacts/tuf_ceremony/ceremony-report.json"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("artifacts/tuf_ceremony/ceremony-summary.txt"),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Atomically replace repository Targets/Snapshot/Timestamp after successful staging verification.",
    )
    args = parser.parse_args()

    report = Report()
    generation: dict[str, object] | None = None
    status = "BLOCKED"
    passphrase = b""

    try:
        now = datetime.now(UTC).replace(microsecond=0)
        metadata_dir = args.metadata_dir.resolve()
        asset = args.asset.expanduser().resolve()
        staging_dir = args.staging_dir.resolve()
        report_path = args.report.resolve()
        summary_path = args.summary.resolve()
        private_dir = args.offline_key_dir.expanduser().resolve()

        _verify_source_identity(args.source_sha.lower(), args.public_version, report)
        current = _load_current_metadata(metadata_dir)
        root_md, targets_md, snapshot_md, timestamp_md = _verify_current_state(current, now, report)
        root = root_md.signed

        if args.expected_root_sha256:
            actual_root_sha = _sha256(current["root.json"])
            if actual_root_sha != args.expected_root_sha256.lower():
                raise CeremonyError(
                    "ROOT_DRIFT",
                    f"Root SHA-256 is {actual_root_sha}, expected {args.expected_root_sha256.lower()}",
                    resolution="Stop and review the Root change under a separate governed Root ceremony.",
                )
            report.check("root-pin", f"Root sha256={actual_root_sha}")

        size, digest = _asset_identity(
            asset,
            args.expected_asset_sha256,
            args.expected_asset_size,
            report,
        )
        payload_url = args.payload_url or (
            f"https://github.com/LaurentCOLL1/Kodepoia/releases/download/"
            f"v{args.public_version}/{asset.name}"
        )

        target_path = (
            f"channels/{args.channel}/{args.platform}/{args.public_version}/"
            f"{args.source_sha.lower()}/{asset.name}"
        )
        already_authorized = target_path in targets_md.signed.targets
        targets_signers: list[Signer] = []
        if not already_authorized:
            passphrase_text = getpass.getpass("Existing TUF offline custody passphrase: ")
            if not passphrase_text:
                raise CeremonyError(
                    "EMPTY_CUSTODY_PASSPHRASE",
                    "offline custody passphrase was empty",
                    resolution="Unlock the existing authorized Targets custody and rerun; do not create a replacement key.",
                )
            passphrase = passphrase_text.encode("utf-8")
            passphrase_text = ""
            targets_signers = _discover_pem_signers(
                private_dir,
                passphrase=passphrase,
                root=root,
                role="targets",
            )
            report.check(
                "targets-signers",
                f"resolved {len(targets_signers)} authorized Targets signer(s); private paths not recorded",
            )

        new_targets_bytes, targets_changed, target_path = _build_targets(
            current=targets_md,
            root=root,
            signers=targets_signers,
            public_version=args.public_version,
            source_sha=args.source_sha.lower(),
            filename=asset.name,
            size=size,
            digest=digest,
            channel=args.channel,
            platform=args.platform,
            payload_url=payload_url,
            release_notes_summary=args.release_notes_summary,
            report=report,
        )
        new_targets_md = _parse(new_targets_bytes, Targets, "new targets.json")

        if targets_changed:
            snapshot_signer, timestamp_signer = _resolve_online_signers(
                args.online_public_keys.resolve(), root, report
            )
            new_snapshot_bytes, new_timestamp_bytes = _build_online_pair(
                root=root,
                current_snapshot=snapshot_md,
                current_timestamp=timestamp_md,
                targets_bytes=new_targets_bytes,
                targets_md=new_targets_md,
                snapshot_signer=snapshot_signer,
                timestamp_signer=timestamp_signer,
                now=now,
                report=report,
            )
        else:
            new_snapshot_bytes = current["snapshot.json"]
            new_timestamp_bytes = current["timestamp.json"]
            report.check("online-transition", "no metadata transition needed; exact target already authorized")

        final_snapshot = _parse(new_snapshot_bytes, Snapshot, "final snapshot.json")
        final_timestamp = _parse(new_timestamp_bytes, Timestamp, "final timestamp.json")
        _verify_role(root, "targets", new_targets_md)
        _verify_role(root, "snapshot", final_snapshot)
        _verify_role(root, "timestamp", final_timestamp)
        _verify_reference(final_snapshot.signed.meta["targets.json"], new_targets_bytes, "final targets.json")
        _verify_reference(final_timestamp.signed.snapshot_meta, new_snapshot_bytes, "final snapshot.json")
        report.check("final-verification", "all signatures, thresholds, versions, hashes and lengths verify")

        payloads = {
            "targets.json": new_targets_bytes,
            "snapshot.json": new_snapshot_bytes,
            "timestamp.json": new_timestamp_bytes,
        }
        _safe_stage(staging_dir, payloads, report)
        if args.apply and targets_changed:
            _atomic_apply(metadata_dir, payloads, report)
        elif args.apply:
            report.check("apply", "repository metadata already matched the exact authorized target")

        generation = {
            "root_version": root.version,
            "root_sha256": _sha256(current["root.json"]),
            "targets_previous_version": targets_md.signed.version,
            "targets_version": new_targets_md.signed.version,
            "targets_sha256": _sha256(new_targets_bytes),
            "targets_length": len(new_targets_bytes),
            "snapshot_previous_version": snapshot_md.signed.version,
            "snapshot_version": final_snapshot.signed.version,
            "snapshot_sha256": _sha256(new_snapshot_bytes),
            "snapshot_length": len(new_snapshot_bytes),
            "timestamp_previous_version": timestamp_md.signed.version,
            "timestamp_version": final_timestamp.signed.version,
            "timestamp_sha256": _sha256(new_timestamp_bytes),
            "timestamp_length": len(new_timestamp_bytes),
            "target_path": target_path,
            "asset_name": asset.name,
            "asset_size": size,
            "asset_sha256": digest,
            "source_sha": args.source_sha.lower(),
            "public_version": args.public_version,
            "payload_url": payload_url,
            "applied": bool(args.apply),
        }
        status = "SUCCESS_WITH_RECOVERY" if report.fixes else "SUCCESS"
        result: dict[str, object] = {
            "format": FORMAT,
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "reference_time": _iso(now),
            "generation": generation,
            "checks": report.checks,
            "errors_encountered": report.issues,
            "automatic_fixes": report.fixes,
            "private_material_in_report": False,
            "private_key_paths_in_report": False,
            "secret_values_emitted": False,
        }
        _write_report(report_path, result)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(_summary_text(status, report, generation), encoding="utf-8")
        print(_summary_text(status, report, generation), end="")
        print(f"Rapport: {report_path}")
        print(f"Résumé: {summary_path}")
        return 0
    except CeremonyError as exc:
        report.issue(exc)
        result = {
            "format": FORMAT,
            "schema_version": SCHEMA_VERSION,
            "status": "BLOCKED",
            "generation": generation,
            "checks": report.checks,
            "errors_encountered": report.issues,
            "automatic_fixes": report.fixes,
            "private_material_in_report": False,
            "private_key_paths_in_report": False,
            "secret_values_emitted": False,
        }
        try:
            _write_report(args.report.resolve(), result)
            args.summary.resolve().parent.mkdir(parents=True, exist_ok=True)
            args.summary.resolve().write_text(_summary_text("BLOCKED", report, generation), encoding="utf-8")
        except OSError:
            pass
        print(_summary_text("BLOCKED", report, generation), file=sys.stderr, end="")
        print(
            "Copiez uniquement ceremony-report.json dans ChatGPT pour le diagnostic; "
            "n'envoyez jamais les clés, seeds ou passphrases.",
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        wrapped = CeremonyError(
            "UNEXPECTED_CEREMONY_ERROR",
            str(exc),
            resolution="Share only the generated ceremony report with ChatGPT for diagnosis; never share private keys or passphrases.",
        )
        report.issue(wrapped)
        print(_summary_text("BLOCKED", report, generation), file=sys.stderr, end="")
        return 1
    finally:
        passphrase = b""


if __name__ == "__main__":
    raise SystemExit(main())
