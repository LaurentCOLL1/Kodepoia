from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from securesystemslib.signer import Signer
from tuf.api.metadata import Metadata, Root, Snapshot, Targets, Timestamp

import tuf_release_ceremony as base


def _build_online_pair_preserving_snapshot_meta(
    *,
    root: Root,
    current_snapshot: Metadata[Snapshot],
    current_timestamp: Metadata[Timestamp],
    targets_bytes: bytes,
    targets_md: Metadata[Targets],
    snapshot_signer: Signer,
    timestamp_signer: Signer,
    now: datetime,
    report: base.Report,
) -> tuple[bytes, bytes]:
    """Refresh Snapshot/Timestamp without dropping existing delegated metadata entries."""

    snapshot_expiry = now + timedelta(hours=base.SNAPSHOT_EXPIRY_HOURS)
    timestamp_expiry = now + timedelta(hours=base.TIMESTAMP_EXPIRY_HOURS)
    authority_expiry = min(
        root.expires.astimezone(UTC),
        targets_md.signed.expires.astimezone(UTC),
    )
    if snapshot_expiry >= authority_expiry or timestamp_expiry >= authority_expiry:
        raise base.CeremonyError(
            "ONLINE_EXPIRY_EXCEEDS_AUTHORITY",
            "new online metadata would expire after Root/Targets authority",
            resolution="Refresh the governing offline authority through its separate process before publishing.",
        )

    snapshot_payload = current_snapshot.signed.to_dict()
    snapshot_meta = snapshot_payload.get("meta")
    if not isinstance(snapshot_meta, dict):
        raise base.CeremonyError(
            "SNAPSHOT_PAYLOAD_INVALID",
            "current Snapshot metadata has an invalid meta mapping",
            resolution="Restore the last known-good Snapshot metadata before retrying.",
        )
    preserved_entries = set(snapshot_meta)
    snapshot_meta["targets.json"] = {
        "hashes": {"sha256": base._sha256(targets_bytes)},
        "length": len(targets_bytes),
        "version": targets_md.signed.version,
    }
    snapshot_payload["expires"] = base._iso(snapshot_expiry)
    snapshot_payload["version"] = current_snapshot.signed.version + 1

    snapshot_bytes = base._new_signed_metadata(snapshot_payload, [snapshot_signer])
    snapshot_md = base._parse(snapshot_bytes, Snapshot, "new snapshot.json")
    base._verify_role(root, "snapshot", snapshot_md)
    base._verify_reference(
        snapshot_md.signed.meta["targets.json"],
        targets_bytes,
        "new targets.json",
    )
    if not preserved_entries.issubset(set(snapshot_md.signed.meta)):
        raise base.CeremonyError(
            "SNAPSHOT_META_PRESERVATION_FAILURE",
            "new Snapshot metadata dropped an existing metadata entry",
            resolution="Discard staged output and inspect the ceremony before publication.",
        )

    timestamp_payload = current_timestamp.signed.to_dict()
    timestamp_meta = timestamp_payload.get("meta")
    if not isinstance(timestamp_meta, dict):
        raise base.CeremonyError(
            "TIMESTAMP_PAYLOAD_INVALID",
            "current Timestamp metadata has an invalid meta mapping",
            resolution="Restore the last known-good Timestamp metadata before retrying.",
        )
    timestamp_meta["snapshot.json"] = {
        "hashes": {"sha256": base._sha256(snapshot_bytes)},
        "length": len(snapshot_bytes),
        "version": snapshot_md.signed.version,
    }
    timestamp_payload["expires"] = base._iso(timestamp_expiry)
    timestamp_payload["version"] = current_timestamp.signed.version + 1

    timestamp_bytes = base._new_signed_metadata(timestamp_payload, [timestamp_signer])
    timestamp_md = base._parse(timestamp_bytes, Timestamp, "new timestamp.json")
    base._verify_role(root, "timestamp", timestamp_md)
    base._verify_reference(
        timestamp_md.signed.snapshot_meta,
        snapshot_bytes,
        "new snapshot.json",
    )
    report.check(
        "online-transition",
        (
            f"Snapshot v{current_snapshot.signed.version} -> v{snapshot_md.signed.version}; "
            f"Timestamp v{current_timestamp.signed.version} -> v{timestamp_md.signed.version}; "
            f"preserved {len(preserved_entries)} existing Snapshot meta entrie(s)"
        ),
    )
    return snapshot_bytes, timestamp_bytes


def _transactional_apply(
    metadata_dir: Path,
    staged: dict[str, bytes],
    report: base.Report,
) -> None:
    """Apply one coherent generation and restore originals if any replacement fails."""

    names = ("targets.json", "snapshot.json", "timestamp.json")
    missing = [name for name in names if not (metadata_dir / name).is_file()]
    if missing:
        raise base.CeremonyError(
            "CURRENT_METADATA_MISSING",
            "cannot apply ceremony because current metadata is incomplete: " + ", ".join(missing),
            resolution="Restore the last known-good metadata generation before retrying.",
        )

    temp_paths: list[Path] = []
    backup_paths: dict[str, Path] = {}
    replaced: list[str] = []
    try:
        for name in names:
            tmp = metadata_dir / f".{name}.ceremony.tmp"
            backup = metadata_dir / f".{name}.ceremony.bak"
            tmp.write_bytes(staged[name])
            backup.write_bytes((metadata_dir / name).read_bytes())
            temp_paths.append(tmp)
            backup_paths[name] = backup

        try:
            for name in names:
                os.replace(metadata_dir / f".{name}.ceremony.tmp", metadata_dir / name)
                replaced.append(name)
        except Exception as exc:
            rollback_failures: list[str] = []
            for name in reversed(replaced):
                try:
                    os.replace(backup_paths[name], metadata_dir / name)
                    backup_paths.pop(name, None)
                except Exception as rollback_exc:  # pragma: no cover - catastrophic filesystem failure
                    rollback_failures.append(f"{name}: {rollback_exc}")
            if rollback_failures:
                raise base.CeremonyError(
                    "METADATA_APPLY_ROLLBACK_FAILED",
                    "metadata apply failed and rollback was incomplete: " + "; ".join(rollback_failures),
                    resolution=(
                        "STOP publication. Preserve every .ceremony.bak file, restore the last known-good "
                        "Targets/Snapshot/Timestamp generation manually, then rerun verification."
                    ),
                ) from exc
            raise base.CeremonyError(
                "METADATA_APPLY_ROLLED_BACK",
                f"metadata apply failed after {len(replaced)} replacement(s); originals were restored: {exc}",
                resolution="Inspect filesystem/permission errors, correct them, then rerun the same ceremony.",
                auto_fixable=True,
            ) from exc

        report.check(
            "transactional-apply",
            "Targets/Snapshot/Timestamp replaced after complete verification; rollback backups were held for the duration of the transaction",
        )
    finally:
        for path in temp_paths:
            path.unlink(missing_ok=True)
        for path in backup_paths.values():
            path.unlink(missing_ok=True)


def _requested_path(flag: str, default: str) -> Path:
    try:
        index = sys.argv.index(flag)
        value = sys.argv[index + 1]
    except (ValueError, IndexError):
        value = default
    return Path(value).expanduser().resolve()


def _read_existing(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _ensure_redacted_blocked_report(previous_report: bytes | None) -> None:
    report_path = _requested_path("--report", "artifacts/tuf_ceremony/ceremony-report.json")
    summary_path = _requested_path("--summary", "artifacts/tuf_ceremony/ceremony-summary.txt")
    current_report = _read_existing(report_path)
    if current_report is not None and current_report != previous_report:
        return
    issue = {
        "code": "UNEXPECTED_CEREMONY_ERROR",
        "message": "The ceremony stopped because of an unexpected internal or operating-system error. Details were intentionally omitted from this shareable report.",
        "auto_fixable": False,
        "resolution": (
            "Share only this ceremony-report.json with ChatGPT. Keep the private custody directory, PEM files, seeds and passphrases private."
        ),
    }
    payload = {
        "format": base.FORMAT,
        "schema_version": base.SCHEMA_VERSION,
        "status": "BLOCKED",
        "generation": None,
        "checks": [],
        "errors_encountered": [issue],
        "automatic_fixes": [],
        "private_material_in_report": False,
        "private_key_paths_in_report": False,
        "secret_values_emitted": False,
    }
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            "Kodepoia TUF release ceremony: BLOCKED\n"
            "Erreur inattendue expurgée. Consultez ceremony-report.json et partagez uniquement ce rapport avec ChatGPT.\n",
            encoding="utf-8",
        )
    except OSError:
        pass


def main() -> int:
    # Keep the proven ceremony engine and replace only the hardening-sensitive operations.
    base._build_online_pair = _build_online_pair_preserving_snapshot_meta
    base._atomic_apply = _transactional_apply
    report_path = _requested_path("--report", "artifacts/tuf_ceremony/ceremony-report.json")
    previous_report = _read_existing(report_path)
    try:
        exit_code = base.main()
    except Exception:  # noqa: BLE001 - final fail-closed boundary intentionally redacts details
        _ensure_redacted_blocked_report(previous_report)
        print(
            "CEREMONIE BLOQUEE: une erreur inattendue a été expurgée. "
            "Partagez uniquement ceremony-report.json avec ChatGPT.",
            file=sys.stderr,
        )
        return 1
    if exit_code != 0:
        _ensure_redacted_blocked_report(previous_report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
