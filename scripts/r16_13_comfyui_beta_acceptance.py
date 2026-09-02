from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.comfyui.beta_acceptance import build_comfyui_beta_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", default="CI")
    parser.add_argument(
        "--output",
        default="artifacts/r16_13_comfyui_beta_acceptance.json",
    )
    parser.add_argument(
        "--live-endpoint",
        default=None,
        help="Optional explicit-port loopback ComfyUI origin for supplementary local qualification.",
    )
    parser.add_argument(
        "--require-live-local",
        action="store_true",
        help="Fail if the optional real local ComfyUI/GPU qualification is not exercised successfully.",
    )
    args = parser.parse_args()
    if args.require_live_local and not args.live_endpoint:
        parser.error("--require-live-local requires --live-endpoint")

    report = build_comfyui_beta_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
        live_endpoint=args.live_endpoint,
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    core_ok = report["security_claim"] and not report["critical_veto"]
    if args.require_live_local:
        return 0 if core_ok and report["live_local_qualification"]["claim_satisfied"] else 1
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
