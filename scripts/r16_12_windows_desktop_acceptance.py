from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.desktop.windows_beta_acceptance import build_windows_desktop_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", default="Windows")
    parser.add_argument(
        "--output",
        default="artifacts/r16_12_windows_desktop_acceptance.json",
    )
    args = parser.parse_args()
    report = build_windows_desktop_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["security_claim"] and not report["critical_veto"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
