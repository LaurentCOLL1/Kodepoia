from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from tuf.api.metadata import Targets

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import tuf_release_ceremony as ceremony  # noqa: E402

EXPECTED_TARGETS_SHA256 = "76bdee21278f1a2b5efada1c1d568277f766ef0ed364bd512814611e3169a275"
EXPECTED_TARGETS_VERSION = 9
EXPECTED_SNAPSHOT_VERSION = 11
EXPECTED_TIMESTAMP_VERSION = 11
TARGET_PATH = (
    "channels/stable/windows-x86_64/1.1.0/"
    "46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe"
)
EXPECTED_TARGET = {
    "hashes": {"sha256": "8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef"},
    "length": 38834833,
    "custom": {
        "authenticode_policy": "allow-unsigned",
        "channel": "stable",
        "payload_url": "https://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.0/KodepoiaSetup.exe",
        "provenance_status": "exact-source-r18-provenance-required-before-publication",
        "public_version": "1.1.0",
        "release_notes_summary": "Kodepoia 1.1.0 stable terminal V2 release.",
        "signing_status": "unsigned; production trust is not claimed",
        "source_sha": "46ed800888b4f19da9e984232dd1ad6cdb639cc1",
        "withdrawn": False,
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact_head(expected: str, root: Path) -> None:
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip().lower()
    if actual != expected.lower():
        raise SystemExit(f"exact-source mismatch: expected {expected}, got {actual}")


def validate_staged_targets(*, root, current_targets, staged_bytes: bytes, report):
    if _sha256(staged_bytes) != EXPECTED_TARGETS_SHA256:
        raise ceremony.CeremonyError(
            "STAGED_TARGETS_DIGEST_MISMATCH",
            "staged Targets v9 digest does not match the operator-qualified Phase-A output",
            resolution="Use only the exact public Targets v9 returned by the offline ceremony.",
        )
    staged = ceremony._parse(staged_bytes, Targets, "staged targets.json")
    ceremony._verify_role(root, "targets", staged)
    if staged.signed.version != EXPECTED_TARGETS_VERSION:
        raise ceremony.CeremonyError(
            "STAGED_TARGETS_VERSION_MISMATCH",
            f"expected Targets v{EXPECTED_TARGETS_VERSION}, got v{staged.signed.version}",
            resolution="Do not regenerate or substitute the accepted offline Targets output.",
        )
    if staged.signed.expires != current_targets.signed.expires:
        raise ceremony.CeremonyError(
            "TARGETS_AUTHORITY_EXPIRY_DRIFT",
            "offline Targets transition changed authority expiry",
            resolution="Preserve the accepted Targets authority lifetime.",
        )
    before = set(current_targets.signed.targets)
    after = set(staged.signed.targets)
    if not before.issubset(after) or after - before != {TARGET_PATH}:
        raise ceremony.CeremonyError(
            "TARGETS_HISTORY_DRIFT",
            "Targets v9 does not preserve every prior target plus exactly stable 1.1.0",
            resolution="Use the exact Phase-A Targets v9 output.",
        )
    if staged.signed.targets[TARGET_PATH].to_dict() != EXPECTED_TARGET:
        raise ceremony.CeremonyError(
            "STABLE_TARGET_IDENTITY_MISMATCH",
            "stable 1.1.0 target identity differs from the frozen V2.6 candidate",
            resolution="Stop; never sign online metadata around a different target.",
        )
    report.check("staged-targets", f"verified exact Targets v9 sha256={EXPECTED_TARGETS_SHA256}")
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate V2.6.6 Snapshot/Timestamp v11 around accepted Targets v9."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--staged-targets", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, default=Path("update-repository/metadata"))
    parser.add_argument(
        "--online-public-keys",
        type=Path,
        default=Path("docs/roadmap/R20_3_PUBLIC_KEYS.json"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parents[1]
    _exact_head(args.source_sha, root_dir)
    report = ceremony.Report()
    now = datetime.now(UTC).replace(microsecond=0)
    current = ceremony._load_current_metadata(args.metadata_dir.resolve())
    root_md, targets_md, snapshot_md, timestamp_md = ceremony._verify_current_state(
        current, now, report
    )
    staged_bytes = args.staged_targets.read_bytes()
    staged_targets = validate_staged_targets(
        root=root_md.signed,
        current_targets=targets_md,
        staged_bytes=staged_bytes,
        report=report,
    )
    snapshot_signer, timestamp_signer = ceremony._resolve_online_signers(
        args.online_public_keys.resolve(), root_md.signed, report
    )
    snapshot_bytes, timestamp_bytes = ceremony._build_online_pair(
        root=root_md.signed,
        current_snapshot=snapshot_md,
        current_timestamp=timestamp_md,
        targets_bytes=staged_bytes,
        targets_md=staged_targets,
        snapshot_signer=snapshot_signer,
        timestamp_signer=timestamp_signer,
        now=now,
        report=report,
    )
    new_snapshot = ceremony._parse(snapshot_bytes, ceremony.Snapshot, "new snapshot.json")
    new_timestamp = ceremony._parse(timestamp_bytes, ceremony.Timestamp, "new timestamp.json")
    if new_snapshot.signed.version != EXPECTED_SNAPSHOT_VERSION:
        raise SystemExit("unexpected Snapshot version")
    if new_timestamp.signed.version != EXPECTED_TIMESTAMP_VERSION:
        raise SystemExit("unexpected Timestamp version")

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "targets.json").write_bytes(staged_bytes)
    (out / "snapshot.json").write_bytes(snapshot_bytes)
    (out / "timestamp.json").write_bytes(timestamp_bytes)

    payload = {
        "schema_version": 1,
        "subdivision": "V2.6.6",
        "status": "PASS",
        "source_sha": args.source_sha.lower(),
        "reference_time": ceremony._iso(now),
        "root_version": root_md.signed.version,
        "targets_previous_version": targets_md.signed.version,
        "targets_version": staged_targets.signed.version,
        "snapshot_previous_version": snapshot_md.signed.version,
        "snapshot_version": new_snapshot.signed.version,
        "timestamp_previous_version": timestamp_md.signed.version,
        "timestamp_version": new_timestamp.signed.version,
        "targets_sha256": _sha256(staged_bytes),
        "snapshot_sha256": _sha256(snapshot_bytes),
        "timestamp_sha256": _sha256(timestamp_bytes),
        "target_path": TARGET_PATH,
        "private_material_in_output": False,
        "secret_values_emitted": False,
        "production_metadata_mutated": False,
        "public_release_created": False,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
