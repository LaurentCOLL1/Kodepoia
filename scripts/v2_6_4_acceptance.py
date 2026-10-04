from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.release.tuf_transition_staging import build_v2_6_4_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit deterministic V2.6.4 production-TUF transition staging evidence."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    requested = args.source_sha.strip().lower()
    observed = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="utf-8"
    ).strip().lower()
    if requested != observed:
        raise SystemExit(f"exact-source mismatch: expected {requested}, got {observed}")

    report = build_v2_6_4_report(requested, repository_root=root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
