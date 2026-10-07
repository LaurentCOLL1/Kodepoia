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

RELEASE_SOURCE_SHA = "aa1c80389b10f5ef44737241bf192c04f847e4ec"
CURRENT_TARGETS_SHA256 = "76bdee21278f1a2b5efada1c1d568277f766ef0ed364bd512814611e3169a275"
EXPECTED_TARGETS_SHA256 = "94107eb8bba745603eb27dc04c2060796c15d3977bd1a68abb3cb1bf74c7148e"
CURRENT_TARGETS_VERSION = 9
EXPECTED_TARGETS_VERSION = 10
CURRENT_SNAPSHOT_VERSION = 11
EXPECTED_SNAPSHOT_VERSION = 12
CURRENT_TIMESTAMP_VERSION = 11
EXPECTED_TIMESTAMP_VERSION = 12
TARGET_PATH = (
    "channels/stable/windows-x86_64/1.1.1/"
    "aa1c80389b10f5ef44737241bf192c04f847e4ec/KodepoiaSetup.exe"
)
EXPECTED_TARGET = {
    "hashes": {"sha256": "c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd"},
    "length": 38880869,
    "custom": {
        "authenticode_policy": "allow-unsigned",
        "channel": "stable",
        "payload_url": "https://github.com/LaurentCOLL1/Kodepoia/releases/download/v1.1.1/KodepoiaSetup.exe",
        "provenance_status": "exact-source-r18-provenance-required-before-publication",
        "public_version": "1.1.1",
        "release_notes_summary": "Kodepoia 1.1.1 stable V2 terminal consolidation release.",
        "signing_status": "unsigned; production trust is not claimed",
        "source_sha": RELEASE_SOURCE_SHA,
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


def validate_staged_targets(*, root, current_targets, current_bytes: bytes, staged_bytes: bytes, report):
    if current_targets.signed.version != CURRENT_TARGETS_VERSION:
        raise ceremony.CeremonyError(
            "CURRENT_TARGETS_VERSION_MISMATCH",
            f"expected current Targets v{CURRENT_TARGETS_VERSION}, got v{current_targets.signed.version}",
            resolution="Stop and revalidate the live production metadata generation.",
        )
    if _sha256(current_bytes) != CURRENT_TARGETS_SHA256:
        raise ceremony.CeremonyError(
            "CURRENT_TARGETS_DIGEST_MISMATCH",
            "current Targets digest differs from the reviewed v9 predecessor",
            resolution="Stop and revalidate the exact production predecessor before continuing.",
        )
    if _sha256(staged_bytes) != EXPECTED_TARGETS_SHA256:
        raise ceremony.CeremonyError(
            "STAGED_TARGETS_DIGEST_MISMATCH",
            "staged Targets v10 digest does not match the operator-qualified offline output",
            resolution="Use only the exact Targets v10 returned by the accepted offline custody ceremony.",
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
            "Targets v10 does not preserve every prior target plus exactly stable 1.1.1",
            resolution="Use the exact operator-qualified Targets v10 output.",
        )
    for path in before:
        if staged.signed.targets[path].to_dict() != current_targets.signed.targets[path].to_dict():
            raise ceremony.CeremonyError(
                "PRIOR_TARGET_DRIFT",
                f"historical target changed during offline transition: {path}",
                resolution="Use the exact operator-qualified Targets v10 output.",
            )
    if staged.signed.targets[TARGET_PATH].to_dict() != EXPECTED_TARGET:
        raise ceremony.CeremonyError(
            "STABLE_TARGET_IDENTITY_MISMATCH",
            "stable 1.1.1 target identity differs from the qualified consolidation candidate",
            resolution="Stop; never sign online metadata around a different target.",
        )

    report.check("staged-targets", f"verified exact Targets v10 sha256={EXPECTED_TARGETS_SHA256}")
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Kodepoia 1.1.1 Snapshot/Timestamp v12 around accepted Targets v10."
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

    if snapshot_md.signed.version != CURRENT_SNAPSHOT_VERSION:
        raise SystemExit("unexpected current Snapshot version")
    if timestamp_md.signed.version != CURRENT_TIMESTAMP_VERSION:
        raise SystemExit("unexpected current Timestamp version")

    staged_bytes = args.staged_targets.read_bytes()
    staged_targets = validate_staged_targets(
        root=root_md.signed,
        current_targets=targets_md,
        current_bytes=current["targets.json"],
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
        "release": "1.1.1",
        "status": "PASS",
        "trigger_source_sha": args.source_sha.lower(),
        "release_source_sha": RELEASE_SOURCE_SHA,
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
        "winget_submission": False,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
