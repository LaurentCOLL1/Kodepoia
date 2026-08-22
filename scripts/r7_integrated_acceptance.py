from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.intelligence.research.acceptance import (
    R7IntegrationReport,
    R7IntegrationStatus,
    R7ManualState,
    build_subdivision_evidence,
    validate_repository_evidence,
)

GENERATED_AT = "2026-08-22T21:17:00Z"
R7_11_ACCEPTED_HEAD = "52330ca576fe294956a8fb601bdfda1d72dc3f92"
DEFAULT_REPORT = Path("docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json")

ACCEPTED = (
    ("R7.1", "a6e9cf9f6db717155c311f4ded1ad5fb744b70ca", R7ManualState.NONE),
    ("R7.2", "9101e686a32b24bb33a23d7ac578bf25570e115e", R7ManualState.NONE),
    ("R7.3", "4efd2cb016e774fa3ef06590ffda377606d875e9", R7ManualState.NONE),
    ("R7.4", "be6f1d5d2f7d9a16c1c295a51905fcd22e9835be", R7ManualState.CONDITIONAL_NOT_TRIGGERED),
    ("R7.5", "12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5", R7ManualState.NONE),
    ("R7.6", "b623836b8f5bd39fce101eca7fe4653a996a9562", R7ManualState.CONDITIONAL_NOT_TRIGGERED),
    ("R7.7", "04cef94c82fdacafe7313d27c8cf516e8e765295", R7ManualState.REQUIRED_SATISFIED),
    ("R7.8", "deb5de415541004fb07bfbc6d955e9d76d717533", R7ManualState.NONE),
    ("R7.9", "80390f95a11e5b3d4353b16eada26f10204bb4fa", R7ManualState.NONE),
    ("R7.10", "cfd0f7ba02af04b456993f686827f10810b3a61a", R7ManualState.NONE),
    ("R7.11", R7_11_ACCEPTED_HEAD, R7ManualState.CONDITIONAL_NOT_TRIGGERED),
)


def git_blob_bytes(repository_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{repository_path}"],
        check=True,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def build_report() -> R7IntegrationReport:
    subdivisions = []
    for subdivision, accepted_head, manual_state in ACCEPTED:
        source = f"docs/roadmap/R7_{subdivision.split('.')[1]}_ACCEPTANCE.md"
        subdivisions.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=accepted_head,
                manual_state=manual_state,
                canonical_bytes=git_blob_bytes(source),
            )
        )
    report = R7IntegrationReport(
        generated_at=GENERATED_AT,
        source_sha=R7_11_ACCEPTED_HEAD,
        subdivisions=tuple(subdivisions),
        status=R7IntegrationStatus.PASS,
        blockers=(),
    )
    validate_repository_evidence(report, git_blob_bytes)
    return report


def serialized(report: R7IntegrationReport) -> str:
    return json.dumps(
        report.to_dict(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-or-print", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = serialized(build_report())
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")
        print(args.output.as_posix())
        return 0

    target = args.check_or_print
    if target is None:
        print(payload, end="")
        return 0
    if not target.is_file():
        print("R7_INTEGRATED_ACCEPTANCE_CANDIDATE_BEGIN")
        print(payload, end="")
        print("R7_INTEGRATED_ACCEPTANCE_CANDIDATE_END")
        return 0
    observed = target.read_text(encoding="utf-8")
    if observed != payload:
        raise SystemExit("R7 integrated acceptance file does not match canonical regenerated evidence")
    print("R7 integrated acceptance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
