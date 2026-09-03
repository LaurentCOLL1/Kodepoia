from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.quality.resource_soak import (  # noqa: E402
    build_resource_soak_report,
    canonical_sha256,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", default="CI")
    parser.add_argument(
        "--output",
        default="artifacts/r16_16_resource_soak_acceptance.json",
    )
    args = parser.parse_args()
    report = build_resource_soak_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
    )
    report["runtime"] = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
    }
    report["evidence_sha256"] = canonical_sha256(
        {
            key: value
            for key, value in report.items()
            if key not in {"elapsed_seconds", "evidence_sha256"}
        }
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    core_ok = (
        report["resource_claim"]
        and not report["critical_veto"]
        and report["secret_free"]
        and report["external_network_calls"] == 0
        and report["destructive_host_actions"] == 0
        and report["manual_state"] == "NONE"
    )
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
