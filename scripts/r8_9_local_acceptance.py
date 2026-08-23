from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.assets.r8_9_acceptance import R89LocalAcceptanceRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="r8_9_local_acceptance")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--godot", required=True)
    parser.add_argument("--expected-head", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    runner = R89LocalAcceptanceRunner(
        Path(args.repo_root),
        executable=args.godot,
        expected_head=args.expected_head,
    )
    payload = runner.run()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["metadata"]["acceptance_completed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
