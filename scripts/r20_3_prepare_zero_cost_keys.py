from __future__ import annotations

import argparse
import json
import os
import stat
import zipfile
from pathlib import Path

from kodepoia.update.zero_cost_signing import prepare_zero_cost_rotation


def _write_private_secret(path: Path, value: str) -> None:
    path.write_text(value + "\n", encoding="ascii")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def _canonical_json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the two R20.3 low-authority online Ed25519 keys locally, "
            "plus a public-only unsigned Root-v2 rotation package."
        )
    )
    parser.add_argument(
        "--metadata-dir",
        default="update-repository/metadata",
        help="Directory containing current production root.json",
    )
    parser.add_argument(
        "--private-output-dir",
        required=True,
        help="Private local directory OUTSIDE the repository; never upload or commit it",
    )
    parser.add_argument(
        "--public-output-dir",
        required=True,
        help="Directory for public-only R20.3 material that may be returned for integration",
    )
    args = parser.parse_args()

    repository_root = Path(__file__).resolve().parents[1]
    private_dir = Path(args.private_output_dir).expanduser().resolve()
    public_dir = Path(args.public_output_dir).expanduser().resolve()
    metadata_dir = Path(args.metadata_dir).expanduser().resolve()

    if _is_within(private_dir, repository_root):
        raise SystemExit(
            "ERROR: --private-output-dir must be outside the Kodepoia repository."
        )
    if private_dir == public_dir or _is_within(private_dir, public_dir):
        raise SystemExit("ERROR: private and public output directories must be separate.")

    root_path = metadata_dir / "root.json"
    if not root_path.is_file():
        raise SystemExit(f"ERROR: current Root metadata not found: {root_path}")

    private_dir.mkdir(parents=True, exist_ok=False)
    public_dir.mkdir(parents=True, exist_ok=False)

    material = prepare_zero_cost_rotation(current_root_bytes=root_path.read_bytes())

    snapshot_secret = private_dir / "TUF_SNAPSHOT_ED25519_SEED_B64.txt"
    timestamp_secret = private_dir / "TUF_TIMESTAMP_ED25519_SEED_B64.txt"
    _write_private_secret(snapshot_secret, material.snapshot.secret_value_b64)
    _write_private_secret(timestamp_secret, material.timestamp.secret_value_b64)

    manifest_path = public_dir / "R20_3_PUBLIC_KEYS.json"
    unsigned_root_path = public_dir / "root.v2.unsigned.json"
    rotation_manifest_path = public_dir / "ROOT_ROTATION_MANIFEST.json"
    manifest_path.write_text(_canonical_json(material.public_manifest()), encoding="utf-8")
    unsigned_root_path.write_bytes(material.rotation.unsigned_root_bytes)
    rotation_manifest_path.write_bytes(material.rotation.manifest_bytes)

    zip_path = public_dir.parent / "R20_3_ZERO_COST_PUBLIC_PACKAGE.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in (manifest_path, unsigned_root_path, rotation_manifest_path):
            archive.write(path, arcname=path.name)

    print("R20.3 zero-cost key generation: SUCCESS")
    print("Two distinct low-authority Ed25519 online keys were generated locally.")
    print("Root and Targets private keys were not used.")
    print("PRIVATE — never upload, commit, paste into ChatGPT, or attach to an issue:")
    print(f"  {snapshot_secret}")
    print(f"  {timestamp_secret}")
    print("PUBLIC — safe to return for repository integration:")
    print(f"  {zip_path}")
    print("Next manual action will be to place the two PRIVATE values into the")
    print("GitHub environment 'tuf-production-signing' under their matching names.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
