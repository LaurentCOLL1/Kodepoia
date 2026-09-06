from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.release.integrated_acceptance import (
    build_core_evidence,
    finalize_integrated_report,
    normalize_sha,
)


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip().lower()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _assert_exact_source(root: Path, source_sha: str) -> str:
    expected = normalize_sha(source_sha)
    actual = _git_head(root)
    if actual != expected:
        raise SystemExit(f"exact-source mismatch: expected {expected}, got {actual}")
    return expected


def _core(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    source = _assert_exact_source(root, args.source_sha)
    report = build_core_evidence(
        root,
        args.evidence_dir.resolve(),
        source,
        focused_regressions_passed=args.focused_regressions_passed,
    )
    _write_json(args.output, report)
    return 0 if not report["blockers"] and not report["critical_veto"] else 1


def _finalize(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    source = _assert_exact_source(root, args.source_sha)
    report = finalize_integrated_report(
        source,
        _read_json(args.core),
        _read_json(args.windows),
    )
    _write_json(args.output, report)
    return 0 if report["status"] == "PASS" else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="R18.11 integrated release/update acceptance"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    core = subparsers.add_parser(
        "core",
        help="emit exact-source R18.1-R18.10 core evidence",
    )
    core.add_argument("--source-sha", required=True)
    core.add_argument("--evidence-dir", type=Path, required=True)
    core.add_argument("--output", type=Path, required=True)
    core.add_argument("--focused-regressions-passed", action="store_true")
    core.set_defaults(func=_core)

    finalize = subparsers.add_parser(
        "finalize",
        help="combine core and Windows RC evidence",
    )
    finalize.add_argument("--source-sha", required=True)
    finalize.add_argument("--core", type=Path, required=True)
    finalize.add_argument("--windows", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    finalize.set_defaults(func=_finalize)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
