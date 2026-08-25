from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from kodepoia.desktop.integrated_acceptance import (
    build_repository_report,
    validate_repository_evidence,
)

ROOT = Path(__file__).resolve().parents[1]


def _read_repository_bytes(source: str) -> bytes:
    path = (ROOT / source).resolve(strict=True)
    root = ROOT.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"repository source escapes root: {source}")
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"repository source is not a regular owned file: {source}")
    return path.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Build canonical anti-circular R12 integrated acceptance")
    parser.add_argument("--source-sha", required=True, help="Immutable accepted R12.16 implementation SHA")
    parser.add_argument(
        "--manual-state",
        choices=("conditional_not_triggered", "conditional_satisfied"),
        default="conditional_not_triggered",
    )
    parser.add_argument(
        "--output",
        default="docs/roadmap/R12_INTEGRATED_ACCEPTANCE.json",
    )
    args = parser.parse_args()
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = build_repository_report(
        source_sha=args.source_sha,
        generated_at=generated_at,
        read_bytes=_read_repository_bytes,
        manual_state=args.manual_state,
    )
    validate_repository_evidence(report, _read_repository_bytes)
    output = (ROOT / args.output).resolve(strict=False)
    root = ROOT.resolve()
    if output != root and root not in output.parents:
        raise ValueError("output escapes repository root")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
