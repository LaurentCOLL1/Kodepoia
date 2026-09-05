from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from kodepoia.release.provenance import write_release_evidence


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate deterministic SPDX 2.3 SBOM and release provenance evidence."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "LaurentCOLL1/Kodepoia"))
    parser.add_argument("--workflow-ref", default=os.getenv("GITHUB_WORKFLOW_REF", "local"))
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "local"))
    parser.add_argument("--run-attempt", default=os.getenv("GITHUB_RUN_ATTEMPT", "local"))
    parser.add_argument("--created-at")
    parser.add_argument("--optional-group", action="append", dest="optional_groups")
    args = parser.parse_args()

    optional_groups = tuple(args.optional_groups or ("ui", "code"))
    result = write_release_evidence(
        repo_root=Path(args.repo_root),
        output_dir=Path(args.output_dir),
        source_sha=args.source_sha,
        repository=args.repository,
        workflow_ref=args.workflow_ref,
        run_id=args.run_id,
        run_attempt=args.run_attempt,
        optional_groups=optional_groups,
        created_at=args.created_at,
    )
    print(
        json.dumps(
            {
                "sbom": str(result.sbom_path),
                "sbom_sha256": result.sbom_sha256,
                "provenance": str(result.provenance_path),
                "provenance_sha256": result.provenance_sha256,
                "packages_total": result.packages_total,
                "runtime_roots": list(result.runtime_roots),
                "unresolved_roots": list(result.unresolved_roots),
                "inventory_complete": False,
                "attestation_semantics": "provenance_only_not_security_verdict",
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
