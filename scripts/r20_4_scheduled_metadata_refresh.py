from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from securesystemslib.signer import SSlibKey

from kodepoia.update.online_signing import OnlineSignerConfig, resolve_online_signers
from kodepoia.update.steady_state_refresh import (
    REFRESH_THRESHOLD_HOURS,
    SteadyStateRefreshError,
    evaluate_refresh,
    refresh_if_due,
)
from kodepoia.update.zero_cost_signing import (
    ZERO_COST_PROVIDER,
    GitHubEnvironmentSecretResolver,
)

EXPECTED_ENVIRONMENT = "tuf-production-signing"


def _config_from_public_manifest(role: str, entry: dict[str, object]) -> OnlineSignerConfig:
    public_key = entry.get("public_key")
    if not isinstance(public_key, dict):
        raise SteadyStateRefreshError(f"missing public key for {role}")
    keyval = public_key.get("keyval")
    if not isinstance(keyval, dict) or not isinstance(keyval.get("public"), str):
        raise SteadyStateRefreshError(f"invalid public key payload for {role}")
    try:
        crypto_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(keyval["public"]))
        sslib_key = SSlibKey.from_crypto(crypto_key)
    except (ValueError, TypeError) as exc:
        raise SteadyStateRefreshError(f"invalid Ed25519 public key for {role}") from exc
    expected_keyid = entry.get("keyid")
    if sslib_key.keyid != expected_keyid:
        raise SteadyStateRefreshError(f"public keyid mismatch for {role}")
    secret_name = entry.get("secret_name")
    if not isinstance(secret_name, str) or not secret_name:
        raise SteadyStateRefreshError(f"missing secret resource for {role}")
    return OnlineSignerConfig(
        role=role,
        provider=ZERO_COST_PROVIDER,
        resource=secret_name,
        public_key=sslib_key,
    )


def _now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC).replace(microsecond=0)
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise SteadyStateRefreshError("reference time must include a timezone")
    return parsed.astimezone(UTC).replace(microsecond=0)


def _load_metadata(metadata_dir: Path) -> dict[str, bytes]:
    names = ("root.json", "targets.json", "snapshot.json", "timestamp.json")
    result: dict[str, bytes] = {}
    for name in names:
        path = metadata_dir / name
        if not path.is_file():
            raise SteadyStateRefreshError(f"required metadata file is missing: {path}")
        result[name] = path.read_bytes()
    return result


def _write_github_output(values: dict[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for name, value in values.items():
            if "\n" in name or "\r" in name or "\n" in value or "\r" in value:
                raise SteadyStateRefreshError("GitHub output values must be single-line")
            handle.write(f"{name}={value}\n")


def _check(metadata: dict[str, bytes], reference_time: datetime) -> dict[str, object]:
    decision = evaluate_refresh(
        root_bytes=metadata["root.json"],
        targets_bytes=metadata["targets.json"],
        snapshot_bytes=metadata["snapshot.json"],
        timestamp_bytes=metadata["timestamp.json"],
        reference_time=reference_time,
    )
    report = {
        "format": "kodepoia-r20-4-refresh-check",
        "schema_version": 1,
        "reference_time": reference_time.isoformat().replace("+00:00", "Z"),
        "threshold_hours": REFRESH_THRESHOLD_HOURS,
        **decision.to_dict(),
        "secrets_loaded": False,
        "metadata_modified": False,
        "status": "refresh-required" if decision.refresh_required else "fresh",
    }
    _write_github_output(
        {
            "refresh_required": str(decision.refresh_required).lower(),
            "snapshot_version": str(decision.snapshot_version),
            "timestamp_version": str(decision.timestamp_version),
        }
    )
    return report


def _refresh(
    *,
    metadata_dir: Path,
    metadata: dict[str, bytes],
    public_keys_path: Path,
    reference_time: datetime,
) -> dict[str, object]:
    decision = evaluate_refresh(
        root_bytes=metadata["root.json"],
        targets_bytes=metadata["targets.json"],
        snapshot_bytes=metadata["snapshot.json"],
        timestamp_bytes=metadata["timestamp.json"],
        reference_time=reference_time,
    )
    if not decision.refresh_required:
        result = refresh_if_due(
            root_bytes=metadata["root.json"],
            targets_bytes=metadata["targets.json"],
            current_snapshot_bytes=metadata["snapshot.json"],
            current_timestamp_bytes=metadata["timestamp.json"],
            reference_time=reference_time,
        )
        return {
            **result.manifest,
            "secrets_loaded": False,
            "metadata_modified": False,
            "status": "fresh-noop",
        }

    manifest = json.loads(public_keys_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SteadyStateRefreshError("public key manifest must be a JSON object")
    if manifest.get("provider") != ZERO_COST_PROVIDER:
        raise SteadyStateRefreshError("public key manifest provider mismatch")
    if manifest.get("environment") != EXPECTED_ENVIRONMENT:
        raise SteadyStateRefreshError("public key manifest environment mismatch")
    snapshot_entry = manifest.get("snapshot")
    timestamp_entry = manifest.get("timestamp")
    if not isinstance(snapshot_entry, dict) or not isinstance(timestamp_entry, dict):
        raise SteadyStateRefreshError("public key manifest online-role entries are malformed")

    snapshot = _config_from_public_manifest("snapshot", snapshot_entry)
    timestamp = _config_from_public_manifest("timestamp", timestamp_entry)
    resolved = resolve_online_signers(
        [snapshot, timestamp],
        GitHubEnvironmentSecretResolver(),
    )
    result = refresh_if_due(
        root_bytes=metadata["root.json"],
        targets_bytes=metadata["targets.json"],
        current_snapshot_bytes=metadata["snapshot.json"],
        current_timestamp_bytes=metadata["timestamp.json"],
        reference_time=reference_time,
        snapshot_signer=resolved.snapshot,
        timestamp_signer=resolved.timestamp,
    )
    if not result.refreshed:
        raise SteadyStateRefreshError("refresh decision changed unexpectedly after signer resolution")

    snapshot_tmp = metadata_dir / ".snapshot.r20-4.tmp"
    timestamp_tmp = metadata_dir / ".timestamp.r20-4.tmp"
    snapshot_tmp.write_bytes(result.snapshot_bytes)
    timestamp_tmp.write_bytes(result.timestamp_bytes)
    try:
        verification = evaluate_refresh(
            root_bytes=metadata["root.json"],
            targets_bytes=metadata["targets.json"],
            snapshot_bytes=snapshot_tmp.read_bytes(),
            timestamp_bytes=timestamp_tmp.read_bytes(),
            reference_time=reference_time,
        )
        if verification.refresh_required:
            raise SteadyStateRefreshError(
                "new online metadata is still at or below the refresh threshold"
            )
        os.replace(snapshot_tmp, metadata_dir / "snapshot.json")
        os.replace(timestamp_tmp, metadata_dir / "timestamp.json")
    finally:
        snapshot_tmp.unlink(missing_ok=True)
        timestamp_tmp.unlink(missing_ok=True)

    report = {
        **result.manifest,
        "decision_before_refresh": decision.to_dict(),
        "secrets_loaded": True,
        "secret_values_emitted": False,
        "metadata_modified": True,
        "status": "refreshed",
    }
    _write_github_output(
        {
            "refresh_required": "true",
            "refreshed": "true",
            "snapshot_version": str(result.manifest["snapshot"]["version"]),
            "timestamp_version": str(result.manifest["timestamp"]["version"]),
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R20.4 scheduled Snapshot/Timestamp freshness check and renewal."
    )
    parser.add_argument("--mode", choices=("check", "refresh"), required=True)
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("update-repository/metadata"),
    )
    parser.add_argument(
        "--public-keys",
        type=Path,
        default=Path("docs/roadmap/R20_3_PUBLIC_KEYS.json"),
    )
    parser.add_argument(
        "--reference-time",
        help="UTC/offset ISO-8601 time for deterministic acceptance; defaults to current UTC time.",
    )
    args = parser.parse_args()

    try:
        metadata_dir = args.metadata_dir.resolve()
        metadata = _load_metadata(metadata_dir)
        reference_time = _now(args.reference_time)
        if args.mode == "check":
            report = _check(metadata, reference_time)
        else:
            report = _refresh(
                metadata_dir=metadata_dir,
                metadata=metadata,
                public_keys_path=args.public_keys.resolve(),
                reference_time=reference_time,
            )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (SteadyStateRefreshError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
