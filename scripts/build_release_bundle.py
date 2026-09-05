from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.release.bundle import build_release_bundle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the deterministic Kodepoia R18.2/R18.3 release bundle."
    )
    parser.add_argument("--installer", required=True)
    parser.add_argument("--installer-manifest", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--repository")
    parser.add_argument("--workflow-ref")
    parser.add_argument("--run-id")
    parser.add_argument("--run-attempt")
    parser.add_argument("--sbom")
    parser.add_argument("--provenance")
    args = parser.parse_args()
    if (args.sbom is None) != (args.provenance is None):
        parser.error("--sbom and --provenance must be supplied together")

    result = build_release_bundle(
        installer_path=Path(args.installer),
        installer_manifest_path=Path(args.installer_manifest),
        source_sha=args.source_sha,
        output_dir=Path(args.output_dir),
        repo_root=Path(args.repo_root),
        repository=args.repository,
        workflow_ref=args.workflow_ref,
        run_id=args.run_id,
        run_attempt=args.run_attempt,
        sbom_path=Path(args.sbom) if args.sbom else None,
        provenance_path=Path(args.provenance) if args.provenance else None,
    )
    print(
        json.dumps(
            {
                "archive": str(result.archive_path),
                "archive_sha256": result.archive_sha256,
                "archive_size": result.archive_size,
                "manifest_sha256": result.manifest_sha256,
                "payload_sha256": result.payload_sha256,
                "semantic_sha256": result.semantic_sha256,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
