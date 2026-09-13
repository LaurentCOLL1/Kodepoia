from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Snapshot, Targets, Timestamp


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYTHON_RUNNER = REPOSITORY_ROOT / "scripts" / "tuf_release_ceremony.py"
POWERSHELL_LAUNCHER = REPOSITORY_ROOT / "scripts" / "Run-TufReleaseCeremony.ps1"


def _signed_bytes(payload: dict[str, object], signer: CryptoSigner) -> bytes:
    envelope = Metadata.from_dict({"signatures": [], "signed": payload})
    envelope.sign(signer)
    return envelope.to_bytes() + b"\n"


def _seed_b64(private_key: Ed25519PrivateKey) -> str:
    seed = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    return base64.b64encode(seed).decode("ascii")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_runner_module() -> object:
    spec = importlib.util.spec_from_file_location("tuf_release_ceremony_test_module", PYTHON_RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_python_ceremony_runner_compiles_and_exposes_help(tmp_path: Path) -> None:
    py_compile.compile(
        str(PYTHON_RUNNER),
        cfile=str(tmp_path / "tuf_release_ceremony.pyc"),
        doraise=True,
    )
    completed = subprocess.run(
        [sys.executable, str(PYTHON_RUNNER), "--help"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "fail-closed" in completed.stdout
    assert "--offline-key-dir" in completed.stdout
    assert "--expected-root-sha256" in completed.stdout
    assert "--apply" in completed.stdout


def test_ceremony_sources_preserve_private_material_boundary() -> None:
    python_source = PYTHON_RUNNER.read_text(encoding="utf-8")
    powershell_source = POWERSHELL_LAUNCHER.read_text(encoding="utf-8")

    assert '"secret_values_emitted": False' in python_source
    assert '"private_key_paths_in_report": False' in python_source
    assert "Do not generate a replacement key" in python_source
    assert "n'envoyez jamais les clés, seeds ou passphrases" in python_source

    assert "TUF_SNAPSHOT_ED25519_SEED_B64.txt" in powershell_source
    assert "TUF_TIMESTAMP_ED25519_SEED_B64.txt" in powershell_source
    assert "Remove-Item Env:TUF_SNAPSHOT_ED25519_SEED_B64" in powershell_source
    assert "Remove-Item Env:TUF_TIMESTAMP_ED25519_SEED_B64" in powershell_source
    assert "Les clés/seeds privés ne seront jamais affichés" in powershell_source


def test_windows_launcher_parses_when_pwsh_is_available() -> None:
    pwsh = shutil.which("pwsh")
    if pwsh is None:
        return
    command = (
        "$tokens=$null; $errors=$null; "
        "[System.Management.Automation.Language.Parser]::ParseFile("
        f"'{POWERSHELL_LAUNCHER.as_posix()}', [ref]$tokens, [ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    completed = subprocess.run(
        [pwsh, "-NoProfile", "-Command", command],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_synthetic_ceremony_signs_verifies_and_applies_atomically(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(REPOSITORY_ROOT)
    module = _load_runner_module()
    now = datetime.now(UTC).replace(microsecond=0)

    root_private = Ed25519PrivateKey.generate()
    targets_private = Ed25519PrivateKey.generate()
    snapshot_private = Ed25519PrivateKey.generate()
    timestamp_private = Ed25519PrivateKey.generate()
    root_signer = CryptoSigner(root_private)
    targets_signer = CryptoSigner(targets_private)
    snapshot_signer = CryptoSigner(snapshot_private)
    timestamp_signer = CryptoSigner(timestamp_private)

    keys = {
        signer.public_key.keyid: signer.public_key.to_dict()
        for signer in (root_signer, targets_signer, snapshot_signer, timestamp_signer)
    }
    root_payload: dict[str, object] = {
        "_type": "root",
        "consistent_snapshot": False,
        "expires": (now + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "keys": keys,
        "roles": {
            "root": {"keyids": [root_signer.public_key.keyid], "threshold": 1},
            "targets": {"keyids": [targets_signer.public_key.keyid], "threshold": 1},
            "snapshot": {"keyids": [snapshot_signer.public_key.keyid], "threshold": 1},
            "timestamp": {"keyids": [timestamp_signer.public_key.keyid], "threshold": 1},
        },
        "spec_version": "1.0.31",
        "version": 1,
    }
    root_bytes = _signed_bytes(root_payload, root_signer)

    targets_payload: dict[str, object] = {
        "_type": "targets",
        "expires": (now + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "spec_version": "1.0.31",
        "targets": {},
        "version": 1,
    }
    targets_bytes = _signed_bytes(targets_payload, targets_signer)

    snapshot_payload: dict[str, object] = {
        "_type": "snapshot",
        "expires": (now + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "targets.json": {
                "hashes": {"sha256": _sha256(targets_bytes)},
                "length": len(targets_bytes),
                "version": 1,
            }
        },
        "spec_version": "1.0.31",
        "version": 1,
    }
    snapshot_bytes = _signed_bytes(snapshot_payload, snapshot_signer)

    timestamp_payload: dict[str, object] = {
        "_type": "timestamp",
        "expires": (now + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {
            "snapshot.json": {
                "hashes": {"sha256": _sha256(snapshot_bytes)},
                "length": len(snapshot_bytes),
                "version": 1,
            }
        },
        "spec_version": "1.0.31",
        "version": 1,
    }
    timestamp_bytes = _signed_bytes(timestamp_payload, timestamp_signer)

    metadata_dir = tmp_path / "metadata"
    metadata_dir.mkdir()
    (metadata_dir / "root.json").write_bytes(root_bytes)
    (metadata_dir / "targets.json").write_bytes(targets_bytes)
    (metadata_dir / "snapshot.json").write_bytes(snapshot_bytes)
    (metadata_dir / "timestamp.json").write_bytes(timestamp_bytes)

    custody_dir = tmp_path / "private-custody"
    custody_dir.mkdir()
    passphrase = b"synthetic-test-passphrase"
    targets_pem = targets_private.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        BestAvailableEncryption(passphrase),
    )
    (custody_dir / "targets-authority.pem").write_bytes(targets_pem)

    public_manifest = {
        "provider": "github-environment-secret",
        "environment": "tuf-production-signing",
        "snapshot": {
            "public_key": snapshot_signer.public_key.to_dict(),
            "keyid": snapshot_signer.public_key.keyid,
            "secret_name": "TUF_SNAPSHOT_ED25519_SEED_B64",
        },
        "timestamp": {
            "public_key": timestamp_signer.public_key.to_dict(),
            "keyid": timestamp_signer.public_key.keyid,
            "secret_name": "TUF_TIMESTAMP_ED25519_SEED_B64",
        },
    }
    public_manifest_path = tmp_path / "online-public-keys.json"
    public_manifest_path.write_text(json.dumps(public_manifest), encoding="utf-8")

    asset = tmp_path / "KodepoiaSetup.exe"
    asset.write_bytes(b"synthetic installer bytes for TUF ceremony acceptance\n")
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPOSITORY_ROOT, text=True
    ).strip()

    monkeypatch.setenv("TUF_SNAPSHOT_ED25519_SEED_B64", _seed_b64(snapshot_private))
    monkeypatch.setenv("TUF_TIMESTAMP_ED25519_SEED_B64", _seed_b64(timestamp_private))
    monkeypatch.setattr(module.getpass, "getpass", lambda _prompt: passphrase.decode("ascii"))

    report_path = tmp_path / "ceremony-report.json"
    summary_path = tmp_path / "ceremony-summary.txt"
    staging_dir = tmp_path / "staged"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(PYTHON_RUNNER),
            "--public-version",
            "1.1.0-rc5",
            "--source-sha",
            source_sha,
            "--asset",
            str(asset),
            "--offline-key-dir",
            str(custody_dir),
            "--metadata-dir",
            str(metadata_dir),
            "--online-public-keys",
            str(public_manifest_path),
            "--expected-root-sha256",
            _sha256(root_bytes),
            "--staging-dir",
            str(staging_dir),
            "--report",
            str(report_path),
            "--summary",
            str(summary_path),
            "--apply",
        ],
    )

    assert module.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] in {"SUCCESS", "SUCCESS_WITH_RECOVERY"}
    assert report["errors_encountered"] == []
    assert report["private_material_in_report"] is False
    assert report["secret_values_emitted"] is False
    assert report["generation"]["targets_version"] == 2
    assert report["generation"]["snapshot_version"] == 2
    assert report["generation"]["timestamp_version"] == 2

    final_targets = Metadata.from_bytes((metadata_dir / "targets.json").read_bytes())
    final_snapshot = Metadata.from_bytes((metadata_dir / "snapshot.json").read_bytes())
    final_timestamp = Metadata.from_bytes((metadata_dir / "timestamp.json").read_bytes())
    assert isinstance(final_targets.signed, Targets)
    assert isinstance(final_snapshot.signed, Snapshot)
    assert isinstance(final_timestamp.signed, Timestamp)
    expected_target = f"channels/beta/windows-x86_64/1.1.0-rc5/{source_sha}/KodepoiaSetup.exe"
    assert expected_target in final_targets.signed.targets
    final_snapshot.signed.meta["targets.json"].verify_length_and_hashes(
        (metadata_dir / "targets.json").read_bytes()
    )
    final_timestamp.signed.snapshot_meta.verify_length_and_hashes(
        (metadata_dir / "snapshot.json").read_bytes()
    )
