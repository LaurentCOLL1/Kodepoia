from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.assets.acceptance import (
    R8IntegrationReport,
    R8IntegrationStatus,
    R8ManualState,
    build_subdivision_evidence,
    expected_r8_subdivisions,
    validate_repository_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
GENERATED_AT = "2026-08-23T05:55:00Z"
R8_11_IMPLEMENTATION_HEAD = "d1589cf94545b854f995e7b6706c4b67e9b7ac1a"

ACCEPTED_HEADS: dict[str, str] = {
    "R8.1": "0e382bcdc82c5d289a9007c40d4a4b6c72120e5c",
    "R8.2": "2046b981cb9506999c40e3fee1a22608efecaa80",
    "R8.3": "a1b0b6b4e07b15521acdd3a86dd963ebe4acc9c8",
    "R8.4": "4bf9cbd4892208084cd8ce6554edfd96a971bc04",
    "R8.5": "08c90bd8d52a7dd2dfc8da6ce94f6731701469f6",
    "R8.6": "8c88aeb8a32abce2e9ecb670da3c2acbb4a31cfe",
    "R8.7": "c52c54ae8b4c1eee386b4dbbdec945fa04afa0f3",
    "R8.8": "32e5ace263546d85ee662c5ba333caaaefaa8bcc",
    "R8.9": "da8b4aedd280dadffcf4099bfa2b902cb70d81a7",
    "R8.10": "6a78b05575ff3ba675b94ebbcbfb45dabf6dbd22",
    "R8.11": R8_11_IMPLEMENTATION_HEAD,
}

MANUAL_STATES: dict[str, R8ManualState] = {
    "R8.1": R8ManualState.NONE,
    "R8.2": R8ManualState.NONE,
    "R8.3": R8ManualState.NONE,
    "R8.4": R8ManualState.NONE,
    "R8.5": R8ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R8.6": R8ManualState.NONE,
    "R8.7": R8ManualState.NONE,
    "R8.8": R8ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R8.9": R8ManualState.REQUIRED_SATISFIED,
    "R8.10": R8ManualState.NONE,
    "R8.11": R8ManualState.CONDITIONAL_NOT_TRIGGERED,
}

MANUAL_REASONS: dict[str, str] = {
    "R8.1": "No manual intervention is defined for R8.1.",
    "R8.2": "No manual intervention is defined for R8.2.",
    "R8.3": "No manual intervention is defined for R8.3.",
    "R8.4": "No manual intervention is defined for R8.4.",
    "R8.5": "Embedding conditional was not triggered; no new authoritative embedding contract/model was required.",
    "R8.6": "No manual intervention is defined for R8.6.",
    "R8.7": "No manual intervention is defined for R8.7.",
    "R8.8": "Git LFS conditional was not triggered; hosted CI exercised the accepted local LFS surface without an inherited unresolved manual gate.",
    "R8.9": "Required Godot 4.7.2 local rebuild acceptance is already authoritative and satisfied.",
    "R8.10": "No manual intervention is defined for R8.10.",
    "R8.11": "R8.11 conditional was not triggered because inherited environment-specific gates are resolved and hosted CI can execute integrated acceptance.",
}


def git_blob_bytes(repository_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"HEAD:{repository_path}"],
        cwd=ROOT,
        check=True,
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def build_report() -> R8IntegrationReport:
    evidence = []
    for subdivision in expected_r8_subdivisions():
        index = subdivision.split(".", 1)[1]
        source = f"docs/roadmap/R8_{index}_ACCEPTANCE.md"
        evidence.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=ACCEPTED_HEADS[subdivision],
                manual_state=MANUAL_STATES[subdivision],
                manual_reason=MANUAL_REASONS[subdivision],
                canonical_bytes=git_blob_bytes(source),
            )
        )
    report = R8IntegrationReport(
        generated_at=GENERATED_AT,
        source_sha=R8_11_IMPLEMENTATION_HEAD,
        subdivisions=tuple(evidence),
        status=R8IntegrationStatus.PASS,
        blockers=(),
    )
    validate_repository_evidence(report, git_blob_bytes)
    return report


def serialized_report(report: R8IntegrationReport) -> str:
    return json.dumps(
        report.to_dict(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"


def check_or_print(target: Path) -> int:
    report = build_report()
    expected = serialized_report(report)
    if not target.is_file():
        print("R8_INTEGRATED_ACCEPTANCE_CANDIDATE_BEGIN")
        print(expected, end="")
        print("R8_INTEGRATED_ACCEPTANCE_CANDIDATE_END")
        return 0

    observed = target.read_text(encoding="utf-8")
    if observed != expected:
        raise SystemExit(
            "R8 integrated acceptance evidence differs from canonical Git-blob regeneration"
        )
    loaded = R8IntegrationReport.from_dict(json.loads(observed))
    validate_repository_evidence(loaded, git_blob_bytes)
    if loaded.status is not R8IntegrationStatus.PASS or loaded.blockers:
        raise SystemExit("R8 integrated acceptance is not PASS or contains blockers")
    print("R8 integrated acceptance: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate R8 integrated acceptance evidence")
    parser.add_argument(
        "--check-or-print",
        metavar="PATH",
        type=Path,
        required=True,
        help="Validate PATH if present; otherwise print the canonical candidate JSON.",
    )
    args = parser.parse_args()
    target = args.check_or_print
    if not target.is_absolute():
        target = ROOT / target
    return check_or_print(target)


if __name__ == "__main__":
    raise SystemExit(main())
