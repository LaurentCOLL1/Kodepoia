from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import MetaFile, Metadata, Root, Snapshot, Targets, Timestamp


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import tuf_release_ceremony as base  # noqa: E402
import tuf_release_ceremony_safe as safe  # noqa: E402


def _signer() -> CryptoSigner:
    return CryptoSigner(Ed25519PrivateKey.generate())


def _root_with_roles(
    *, targets: CryptoSigner, snapshot: CryptoSigner, timestamp: CryptoSigner
) -> Root:
    root = Root(expires=datetime.now(UTC) + timedelta(days=365))
    root.add_key(targets.public_key, "targets")
    root.add_key(snapshot.public_key, "snapshot")
    root.add_key(timestamp.public_key, "timestamp")
    return root


def test_hardened_online_pair_preserves_existing_snapshot_meta() -> None:
    now = datetime.now(UTC)
    targets_signer = _signer()
    snapshot_signer = _signer()
    timestamp_signer = _signer()
    root = _root_with_roles(
        targets=targets_signer,
        snapshot=snapshot_signer,
        timestamp=timestamp_signer,
    )

    targets_md = Metadata(Targets(version=6, expires=now + timedelta(days=300)))
    targets_md.sign(targets_signer)
    targets_bytes = base._serialize(targets_md)

    snapshot_md = Metadata(
        Snapshot(
            version=8,
            expires=now + timedelta(days=2),
            meta={
                "targets.json": MetaFile(version=5),
                "delegated-role.json": MetaFile(version=4),
            },
        )
    )
    snapshot_md.sign(snapshot_signer)
    timestamp_md = Metadata(
        Timestamp(
            version=8,
            expires=now + timedelta(days=1),
            snapshot_meta=MetaFile(version=8),
        )
    )
    timestamp_md.sign(timestamp_signer)

    report = base.Report()
    snapshot_bytes, timestamp_bytes = safe._build_online_pair_preserving_snapshot_meta(
        root=root,
        current_snapshot=snapshot_md,
        current_timestamp=timestamp_md,
        targets_bytes=targets_bytes,
        targets_md=targets_md,
        snapshot_signer=snapshot_signer,
        timestamp_signer=timestamp_signer,
        now=now,
        report=report,
    )

    refreshed_snapshot = Metadata.from_bytes(snapshot_bytes)
    refreshed_timestamp = Metadata.from_bytes(timestamp_bytes)
    assert isinstance(refreshed_snapshot.signed, Snapshot)
    assert isinstance(refreshed_timestamp.signed, Timestamp)
    assert "delegated-role.json" in refreshed_snapshot.signed.meta
    assert refreshed_snapshot.signed.meta["delegated-role.json"].version == 4
    assert refreshed_snapshot.signed.meta["targets.json"].version == 6
    refreshed_snapshot.signed.meta["targets.json"].verify_length_and_hashes(targets_bytes)
    refreshed_timestamp.signed.snapshot_meta.verify_length_and_hashes(snapshot_bytes)


def test_transactional_apply_restores_originals_on_mid_apply_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    originals = {
        "targets.json": b"old-targets",
        "snapshot.json": b"old-snapshot",
        "timestamp.json": b"old-timestamp",
    }
    staged = {
        "targets.json": b"new-targets",
        "snapshot.json": b"new-snapshot",
        "timestamp.json": b"new-timestamp",
    }
    for name, data in originals.items():
        (metadata_dir / name).write_bytes(data)

    real_replace = safe.os.replace
    failed = False

    def replace_once_then_recover(src: str | Path, dst: str | Path) -> None:
        nonlocal failed
        destination = Path(dst)
        if destination.name == "snapshot.json" and not failed:
            failed = True
            raise OSError("synthetic replace failure")
        real_replace(src, dst)

    monkeypatch.setattr(safe.os, "replace", replace_once_then_recover)
    report = base.Report()
    with pytest.raises(base.CeremonyError) as captured:
        safe._transactional_apply(metadata_dir, staged, report)

    assert captured.value.code == "METADATA_APPLY_ROLLED_BACK"
    assert captured.value.auto_fixable is True
    for name, data in originals.items():
        assert (metadata_dir / name).read_bytes() == data
    assert not list(metadata_dir.glob(".*.ceremony.*"))


def test_transactional_apply_commits_complete_generation_without_recovery_status(
    tmp_path: Path,
) -> None:
    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    staged = {
        "targets.json": b"new-targets",
        "snapshot.json": b"new-snapshot",
        "timestamp.json": b"new-timestamp",
    }
    for name in staged:
        (metadata_dir / name).write_bytes(b"old")

    report = base.Report()
    safe._transactional_apply(metadata_dir, staged, report)

    for name, data in staged.items():
        assert (metadata_dir / name).read_bytes() == data
    assert any(item["name"] == "transactional-apply" for item in report.checks)
    assert report.fixes == []
    assert not list(metadata_dir.glob(".*.ceremony.*"))


def test_unexpected_exception_emits_redacted_shareable_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_path = tmp_path / "ceremony-report.json"
    summary_path = tmp_path / "ceremony-summary.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tuf_release_ceremony_safe.py",
            "--report",
            str(report_path),
            "--summary",
            str(summary_path),
        ],
    )

    def explode() -> int:
        raise RuntimeError("PRIVATE /secret/custody/location must not leak")

    monkeypatch.setattr(base, "main", explode)
    assert safe.main() == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert payload["private_material_in_report"] is False
    assert payload["private_key_paths_in_report"] is False
    serialized = json.dumps(payload)
    assert "/secret/custody/location" not in serialized
    assert "PRIVATE" not in serialized
    assert summary_path.is_file()


def test_nonzero_exit_without_report_gets_redacted_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_path = tmp_path / "ceremony-report.json"
    summary_path = tmp_path / "ceremony-summary.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "tuf_release_ceremony_safe.py",
            "--report",
            str(report_path),
            "--summary",
            str(summary_path),
        ],
    )
    monkeypatch.setattr(base, "main", lambda: 1)
    assert safe.main() == 1
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "BLOCKED"
    assert payload["errors_encountered"][0]["code"] == "UNEXPECTED_CEREMONY_ERROR"


def test_windows_launcher_routes_through_hardened_engine() -> None:
    source = (SCRIPTS_DIR / "Run-TufReleaseCeremony.ps1").read_text(encoding="utf-8")
    assert '"scripts/tuf_release_ceremony_safe.py"' in source
    assert '"scripts/tuf_release_ceremony.py"' not in source
