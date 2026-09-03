from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.media.r16_14_acceptance import build_media_beta_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", default="CI")
    parser.add_argument("--output", default="artifacts/r16_14_media_beta_acceptance.json")
    parser.add_argument(
        "--require-human-listening",
        action="store_true",
        help=(
            "Record that an optional human/device listening claim was requested; "
            "core CI then reports MANUAL_REQUIRED."
        ),
    )
    args = parser.parse_args()
    report = build_media_beta_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
        require_human_listening=args.require_human_listening,
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    core_ok = report["security_claim"] and not report["critical_veto"]
    if args.require_human_listening:
        return 1
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
