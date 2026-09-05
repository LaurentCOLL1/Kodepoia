from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from kodepoia.release.tuf_security import SyntheticTufRepositoryBuilder


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a one-time synthetic R18.6 packaged TUF root for acceptance."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    repository = SyntheticTufRepositoryBuilder(root_threshold=2).build(root_version=1)
    root_bytes = repository.root
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(root_bytes)

    manifest = {
        "schema_version": 1,
        "purpose": "synthetic-acceptance-only",
        "production_trust_claim": False,
        "root_version": 1,
        "root_sha256": hashlib.sha256(root_bytes).hexdigest(),
        "private_keys_persisted": False,
    }
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
