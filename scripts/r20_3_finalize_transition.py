from __future__ import annotations

import argparse
import base64
import json
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from securesystemslib.signer import CryptoSigner

from kodepoia.update.root_transition import (
    RootTransitionError,
    build_root_online_role_transition,
    transition_manifest_bytes,
)

SNAPSHOT_SECRET_FILE = "TUF_SNAPSHOT_ED25519_SEED_B64.txt"
TIMESTAMP_SECRET_FILE = "TUF_TIMESTAMP_ED25519_SEED_B64.txt"
_PRIVATE_MARKERS = (
    b"PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"ENCRYPTED PRIVATE KEY",
    b"PASSPHRASE",
    b"PASSWORD",
)


def _load_seed_signer(path: Path, *, expected_keyid: str) -> CryptoSigner:
    if not path.is_file():
        raise RootTransitionError(f"required online seed file is missing: {path.name}")
    text = path.read_text(encoding="utf-8").strip()
    try:
        seed = base64.b64decode(text, validate=True)
    except Exception as exc:
        raise RootTransitionError(f"{path.name} is not strict base64") from exc
    if len(seed) != 32:
        raise RootTransitionError(f"{path.name} must decode to exactly 32 bytes")
    signer = CryptoSigner(Ed25519PrivateKey.from_private_bytes(seed))
    if signer.public_key.keyid != expected_keyid:
        raise RootTransitionError(f"{path.name} does not match the accepted public keyid")
    return signer


def _assert_public_only(payloads: dict[str, bytes]) -> None:
    for name, data in payloads.items():
        upper = data.upper()
        if any(marker in upper for marker in _PRIVATE_MARKERS):
            raise RootTransitionError(f"public transition output contains a forbidden marker in {name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Finalize the R20.3 trust transition using signed Root v2 and the two locally "
            "generated online seeds. Emits Root v2 + Snapshot v4 + Timestamp v4 only."
        )
    )
    parser.add_argument(
        "--current-metadata-dir",
        type=Path,
        default=Path("update-repository/metadata"),
    )
    parser.add_argument("--signed-root-v2", type=Path, required=True)
    parser.add_argument("--online-private-dir", type=Path, required=True)
    parser.add_argument(
        "--public-keys",
        type=Path,
        default=Path("docs/roadmap/R20_3_PUBLIC_KEYS.json"),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    metadata_dir = args.current_metadata_dir.resolve()
    signed_root_v2 = args.signed_root_v2.expanduser().resolve()
    private_dir = args.online_private_dir.expanduser().resolve()
    public_keys_path = args.public_keys.resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not private_dir.is_dir():
        print("ERROR: online private directory does not exist", file=sys.stderr)
        return 1
    if output_dir.exists() and any(output_dir.iterdir()):
        print("ERROR: output directory is not empty", file=sys.stderr)
        return 1
    if output_dir == private_dir or private_dir in output_dir.parents:
        print("ERROR: public output must not be inside the online private directory", file=sys.stderr)
        return 1

    try:
        public_keys = json.loads(public_keys_path.read_text(encoding="utf-8"))
        snapshot_keyid = public_keys["snapshot"]["keyid"]
        timestamp_keyid = public_keys["timestamp"]["keyid"]
        if not isinstance(snapshot_keyid, str) or not isinstance(timestamp_keyid, str):
            raise RootTransitionError("accepted public keyids are malformed")
        if snapshot_keyid == timestamp_keyid:
            raise RootTransitionError("accepted online role keyids unexpectedly match")

        snapshot_signer = _load_seed_signer(
            private_dir / SNAPSHOT_SECRET_FILE,
            expected_keyid=snapshot_keyid,
        )
        timestamp_signer = _load_seed_signer(
            private_dir / TIMESTAMP_SECRET_FILE,
            expected_keyid=timestamp_keyid,
        )

        result = build_root_online_role_transition(
            current_root_bytes=(metadata_dir / "root.json").read_bytes(),
            signed_root_v2_bytes=signed_root_v2.read_bytes(),
            targets_bytes=(metadata_dir / "targets.json").read_bytes(),
            current_snapshot_bytes=(metadata_dir / "snapshot.json").read_bytes(),
            current_timestamp_bytes=(metadata_dir / "timestamp.json").read_bytes(),
            snapshot_signer=snapshot_signer,
            timestamp_signer=timestamp_signer,
            reference_time=datetime.now(UTC),
        )
        payloads = {
            "root.json": result.root_bytes,
            "snapshot.json": result.snapshot_bytes,
            "timestamp.json": result.timestamp_bytes,
            "TRANSITION_MANIFEST.json": transition_manifest_bytes(result.manifest),
        }
        _assert_public_only(payloads)

        output_dir.mkdir(parents=True, exist_ok=True)
        for name, data in payloads.items():
            (output_dir / name).write_bytes(data)

        zip_path = output_dir.parent / "R20_3_FULL_TRANSITION_PUBLIC_PACKAGE.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in payloads:
                archive.write(output_dir / name, arcname=name)

        print(json.dumps({**result.manifest, "public_zip": str(zip_path)}, indent=2, sort_keys=True))
        print("\nSUCCESS")
        print("SAFE TO UPLOAD HERE:", zip_path)
        return 0
    except (RootTransitionError, OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
