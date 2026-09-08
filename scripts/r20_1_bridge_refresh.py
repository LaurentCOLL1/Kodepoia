from __future__ import annotations

import argparse
import getpass
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from securesystemslib.signer import CryptoSigner

from kodepoia.update.bridge_refresh import (
    BRIDGE_EXPIRY_DAYS,
    BridgeRefreshError,
    build_bridge_metadata,
    manifest_bytes,
)

_PRIVATE_MARKERS = (
    b"PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"ENCRYPTED PRIVATE KEY",
    b"PASSPHRASE",
    b"PASSWORD",
)


def _load_signer(path: Path, passphrase: bytes) -> CryptoSigner:
    if not path.is_file():
        raise BridgeRefreshError(f"private key not found: {path}")
    try:
        private_key = load_pem_private_key(path.read_bytes(), password=passphrase)
    except Exception as exc:
        raise BridgeRefreshError(f"cannot unlock {path.name}; verify the custody passphrase") from exc
    return CryptoSigner(private_key)


def _assert_public_only(payloads: dict[str, bytes]) -> None:
    for name, data in payloads.items():
        upper = data.upper()
        if any(marker in upper for marker in _PRIVATE_MARKERS):
            raise BridgeRefreshError(f"public output contains a forbidden secret marker in {name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create the R20.1 temporary Snapshot/Timestamp freshness bridge using the existing "
            "user-custodied role keys. Root and Targets are read-only and never re-signed."
        )
    )
    parser.add_argument(
        "--metadata-dir",
        type=Path,
        default=Path("update-repository/metadata"),
    )
    parser.add_argument("--private-key-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bridge-days", type=int, default=BRIDGE_EXPIRY_DAYS)
    args = parser.parse_args()

    metadata_dir = args.metadata_dir.resolve()
    private_key_dir = args.private_key_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"ERROR: output directory is not empty: {output_dir}", file=sys.stderr)
        return 1

    print("R20.1 bridge signing uses ONLY snapshot.pem and timestamp.pem.")
    print("Root and Targets remain byte-for-byte unchanged.")
    print("No private key is copied into the public output.")
    passphrase_text = getpass.getpass("Existing TUF custody passphrase: ")
    if not passphrase_text:
        print("ERROR: empty passphrase", file=sys.stderr)
        return 1
    passphrase = passphrase_text.encode("utf-8")
    passphrase_text = ""

    try:
        snapshot_signer = _load_signer(private_key_dir / "snapshot.pem", passphrase)
        timestamp_signer = _load_signer(private_key_dir / "timestamp.pem", passphrase)
        result = build_bridge_metadata(
            root_bytes=(metadata_dir / "root.json").read_bytes(),
            targets_bytes=(metadata_dir / "targets.json").read_bytes(),
            current_snapshot_bytes=(metadata_dir / "snapshot.json").read_bytes(),
            current_timestamp_bytes=(metadata_dir / "timestamp.json").read_bytes(),
            snapshot_signer=snapshot_signer,
            timestamp_signer=timestamp_signer,
            reference_time=datetime.now(UTC),
            bridge_days=args.bridge_days,
        )
        payloads = {
            "snapshot.json": result.snapshot_bytes,
            "timestamp.json": result.timestamp_bytes,
            "PUBLIC_MANIFEST.json": manifest_bytes(result.manifest),
        }
        _assert_public_only(payloads)
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, data in payloads.items():
            (output_dir / name).write_bytes(data)

        zip_path = output_dir.parent / "R20_1_BRIDGE_PUBLIC_OUTPUT.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in payloads:
                archive.write(output_dir / name, arcname=name)

        print(json.dumps({**result.manifest, "public_zip": str(zip_path)}, indent=2, sort_keys=True))
        print("\nSUCCESS")
        print("SAFE TO UPLOAD HERE:", zip_path)
        return 0
    except (BridgeRefreshError, OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        passphrase = b""


if __name__ == "__main__":
    raise SystemExit(main())
