from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.update.continuous_operations import build_continuous_operations_report


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip().lower()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="R20.6 long-offline and continuous-operations integrated acceptance"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = args.root.resolve(strict=True)
    expected = args.source_sha.strip().lower()
    actual = _git_head(root)
    if actual != expected:
        raise SystemExit(f"exact-source mismatch: expected {expected}, got {actual}")

    report = build_continuous_operations_report(root, source_sha=expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
