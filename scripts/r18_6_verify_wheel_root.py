from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT_MEMBER = "kodepoia/update/trusted_root.synthetic.json"
MANIFEST_MEMBER = "kodepoia/update/trusted_root.synthetic.manifest.json"
EXPECTED_ROOT_SHA256 = "885bc87c3a5e9fe8b378cac85eb89fc37f99fcd8ba0bc7c494ee1e407da96670"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that a built Kodepoia wheel embeds the R18.6 synthetic root resources."
    )
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()

    if not args.wheel.is_file():
        raise SystemExit(f"wheel does not exist: {args.wheel}")

    with zipfile.ZipFile(args.wheel) as archive:
        names = set(archive.namelist())
        missing = {ROOT_MEMBER, MANIFEST_MEMBER} - names
        if missing:
            raise SystemExit(f"wheel is missing packaged TUF resources: {sorted(missing)}")
        root_bytes = archive.read(ROOT_MEMBER)
        manifest = json.loads(archive.read(MANIFEST_MEMBER).decode("utf-8"))

    digest = hashlib.sha256(root_bytes).hexdigest()
    if digest != EXPECTED_ROOT_SHA256:
        raise SystemExit(f"wheel packaged root digest drifted: {digest}")
    if manifest.get("root_sha256") != digest or manifest.get("root_version") != 1:
        raise SystemExit("wheel packaged root manifest does not match embedded root")
    if manifest.get("purpose") != "synthetic-acceptance-only":
        raise SystemExit("wheel packaged root purpose is not synthetic acceptance")
    if manifest.get("production_trust_claim") is not False:
        raise SystemExit("wheel synthetic root unexpectedly claims production trust")
    if manifest.get("private_keys_persisted") is not False:
        raise SystemExit("wheel synthetic root manifest claims persisted private keys")

    print(
        json.dumps(
            {
                "wheel": args.wheel.name,
                "root_member": ROOT_MEMBER,
                "manifest_member": MANIFEST_MEMBER,
                "root_version": 1,
                "root_sha256": digest,
                "purpose": "synthetic-acceptance-only",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
