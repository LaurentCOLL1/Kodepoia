from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.quality.release_readiness import build_release_readiness_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit exact-source R16.17 release-readiness evidence")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--baseline-build", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    report = build_release_readiness_report(
        root,
        source_sha=args.source_sha,
        platform=args.platform,
        baseline_build_path=args.baseline_build,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": output.as_posix(),
                "source_sha": report["source_sha"],
                "platform": report["platform"],
                "release_version": report["release_version"],
                "summary": report["summary"],
                "release_claim": report["release_claim"],
                "critical_veto": report["critical_veto"],
                "manual_state": report["manual_state"],
                "semantic_sha256": report["semantic_sha256"],
                "evidence_sha256": report["evidence_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
