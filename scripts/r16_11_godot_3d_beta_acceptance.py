from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.kodegodot.beta_3d_acceptance import build_3d_report

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R16.11 exact-source representative Godot 3D beta acceptance"
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--godot",
        default=None,
        help="Optional Godot executable/path. Empty string forces capability-absent mode.",
    )
    args = parser.parse_args()

    report = build_3d_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
        godot_executable=args.godot,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["security_claim"] and not report["critical_veto"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
