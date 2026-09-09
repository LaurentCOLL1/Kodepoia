from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from securesystemslib.signer import CryptoSigner
from tuf.api.metadata import Metadata, Root

from kodepoia.update.online_signing import OnlineSigningError
from kodepoia.update.zero_cost_signing import sign_root_rotation

EXPECTED_CURRENT_ROOT_SHA256 = (
    "892442754966aa643bbe15a2910aa3fef59032c8f5eade34fed62efd96aefee5"
)
EXPECTED_UNSIGNED_ROOT_SHA256 = (
    "7ae909722149fe7f05380f93b7317c99347f8b3c1d102b7b6ddca64bbe1bbe1d"
)
_PRIVATE_MARKERS = (
    b"PRIVATE KEY",
    b"OPENSSH PRIVATE KEY",
    b"ENCRYPTED PRIVATE KEY",
    b"PASSPHRASE",
    b"PASSWORD",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _discover_root_signers(
    private_key_dir: Path,
    passphrase: bytes,
    current_root_bytes: bytes,
) -> list[CryptoSigner]:
    current = Metadata.from_bytes(current_root_bytes)
    if not isinstance(current.signed, Root):
        raise OnlineSigningError("current metadata is not Root")
    authorized = set(current.signed.roles["root"].keyids)
    threshold = current.signed.roles["root"].threshold
    signers: dict[str, CryptoSigner] = {}

    for path in sorted(private_key_dir.rglob("*.pem")):
        if not path.is_file():
            continue
        try:
            private_key = load_pem_private_key(path.read_bytes(), password=passphrase)
            signer = CryptoSigner(private_key)
        except Exception:
            continue
        if signer.public_key.keyid in authorized:
            signers.setdefault(signer.public_key.keyid, signer)

    if len(signers) < threshold:
        raise OnlineSigningError(
            "not enough current Root-authorized private keys could be unlocked; "
            f"need {threshold}, found {len(signers)}"
        )
    return list(signers.values())


def _assert_public_only(payloads: dict[str, bytes]) -> None:
    for name, data in payloads.items():
        upper = data.upper()
        if any(marker in upper for marker in _PRIVATE_MARKERS):
            raise OnlineSigningError(
                f"public Root signing output contains a forbidden marker in {name}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Perform the R20.3 offline Root v2 threshold-signing ceremony. "
            "The tool discovers Root-authorized PEM keys by public keyid and emits "
            "public signed metadata only."
        )
    )
    parser.add_argument(
        "--current-root",
        type=Path,
        default=Path("update-repository/metadata/root.json"),
    )
    parser.add_argument(
        "--unsigned-root",
        type=Path,
        default=Path("docs/roadmap/R20_3_ROOT_V2_UNSIGNED.json"),
    )
    parser.add_argument("--private-key-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    current_root_path = args.current_root.resolve()
    unsigned_root_path = args.unsigned_root.resolve()
    private_key_dir = args.private_key_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not private_key_dir.is_dir():
        print("ERROR: private-key directory does not exist", file=sys.stderr)
        return 1
    if output_dir.exists() and any(output_dir.iterdir()):
        print("ERROR: output directory is not empty", file=sys.stderr)
        return 1
    if output_dir == private_key_dir or private_key_dir in output_dir.parents:
        print("ERROR: public output must not be inside the private-key directory", file=sys.stderr)
        return 1

    try:
        current_root_bytes = current_root_path.read_bytes()
        unsigned_root_bytes = unsigned_root_path.read_bytes()
    except OSError as exc:
        print(f"ERROR: cannot read Root metadata: {exc}", file=sys.stderr)
        return 1

    if _sha256(current_root_bytes) != EXPECTED_CURRENT_ROOT_SHA256:
        print("ERROR: current Root v1 does not match the accepted R20.3 authority", file=sys.stderr)
        return 1
    if _sha256(unsigned_root_bytes) != EXPECTED_UNSIGNED_ROOT_SHA256:
        print("ERROR: unsigned Root v2 does not match the accepted public package", file=sys.stderr)
        return 1

    print("R20.3 offline Root v2 ceremony")
    print("The tool scans local PEM files but never records their paths in public output.")
    print("Only current Root-authorized keyids are eligible; threshold is enforced.")
    passphrase_text = getpass.getpass("Existing TUF custody passphrase: ")
    if not passphrase_text:
        print("ERROR: empty passphrase", file=sys.stderr)
        return 1
    passphrase = passphrase_text.encode("utf-8")
    passphrase_text = ""

    try:
        signers = _discover_root_signers(
            private_key_dir,
            passphrase,
            current_root_bytes,
        )
        result = sign_root_rotation(
            current_root_bytes=current_root_bytes,
            unsigned_root_bytes=unsigned_root_bytes,
            root_signers=signers,
        )
        manifest = result.public_manifest(unsigned_root_bytes=unsigned_root_bytes)
        manifest.update(
            {
                "current_root_sha256": EXPECTED_CURRENT_ROOT_SHA256,
                "candidate_root_version": 2,
                "private_key_paths_in_output": False,
                "status": "pass",
            }
        )
        payloads = {
            "root.v2.signed.json": result.signed_root_bytes,
            "ROOT_SIGNING_ACCEPTANCE.json": (
                json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            ),
        }
        _assert_public_only(payloads)

        output_dir.mkdir(parents=True, exist_ok=True)
        for name, data in payloads.items():
            (output_dir / name).write_bytes(data)

        zip_path = output_dir.parent / "R20_3_ROOT_V2_SIGNED_PUBLIC_PACKAGE.zip"
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in payloads:
                archive.write(output_dir / name, arcname=name)

        print(json.dumps({**manifest, "public_zip": str(zip_path)}, indent=2, sort_keys=True))
        print("\nSUCCESS")
        print("SAFE TO UPLOAD HERE:", zip_path)
        return 0
    except (OnlineSigningError, OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        passphrase = b""


if __name__ == "__main__":
    raise SystemExit(main())
