from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.release.windows_release_rehearsal import (
    build_contract_report,
    build_final_report,
    build_windows_preflight,
)
from kodepoia.update.corrective import (
    PowerShellAuthenticodeVerifier,
    PowerShellInstallerIdentityVerifier,
)

ROOT = Path(__file__).resolve().parents[1]


def _exact_head(expected: str) -> str:
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip().lower()
    requested = expected.strip().lower()
    if actual != requested:
        raise SystemExit(f"exact-source mismatch: expected {requested}, got {actual}")
    return actual


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="V2.6.5 installed Windows release rehearsal acceptance."
    )
    parser.add_argument("--mode", choices=("contract", "preflight", "final"), required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rc8-installer", type=Path)
    parser.add_argument("--candidate-installer", type=Path)
    parser.add_argument("--v263-evidence", type=Path)
    parser.add_argument("--stage-dir", type=Path)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--windows-evidence", type=Path)
    return parser


def _require(value: Path | None, name: str) -> Path:
    if value is None:
        raise SystemExit(f"{name} is required for this mode")
    return value


def main() -> int:
    args = build_parser().parse_args()
    source_sha = _exact_head(args.source_sha)

    if args.mode == "contract":
        report = build_contract_report(source_sha, repository_root=ROOT)
    elif args.mode == "preflight":
        report = build_windows_preflight(
            source_sha,
            repository_root=ROOT,
            rc8_installer=_require(args.rc8_installer, "--rc8-installer"),
            candidate_installer=_require(args.candidate_installer, "--candidate-installer"),
            v263_evidence=_require(args.v263_evidence, "--v263-evidence"),
            stage_dir=_require(args.stage_dir, "--stage-dir"),
            authenticode=PowerShellAuthenticodeVerifier(),
            identity=PowerShellInstallerIdentityVerifier(),
        )
    else:
        report = build_final_report(
            source_sha,
            repository_root=ROOT,
            preflight_path=_require(args.preflight, "--preflight"),
            windows_evidence_path=_require(args.windows_evidence, "--windows-evidence"),
            candidate_installer=_require(args.candidate_installer, "--candidate-installer"),
        )

    _write(args.output, report)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
