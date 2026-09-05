from __future__ import annotations

import argparse
import json

from kodepoia.release.bundle import verify_bundle_archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a deterministic Kodepoia R18.2 release bundle."
    )
    parser.add_argument("bundle")
    parser.add_argument("--source-sha")
    args = parser.parse_args()

    result = verify_bundle_archive(
        args.bundle,
        expected_source_sha=args.source_sha,
    )
    manifest = result["manifest"]
    print(
        json.dumps(
            {
                "archive": result["archive_path"],
                "archive_sha256": result["archive_sha256"],
                "archive_size": result["archive_size"],
                "manifest_sha256": result["manifest_sha256"],
                "payload_sha256": manifest["payload_sha256"],
                "semantic_sha256": manifest["semantic_sha256"],
                "source_sha": result["source_sha"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
