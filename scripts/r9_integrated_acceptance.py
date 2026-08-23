from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from kodepoia.comfyui.acceptance import (
    R9IntegrationReport,
    R9IntegrationStatus,
    R9ManualState,
    build_subdivision_evidence,
    expected_r9_subdivisions,
    validate_repository_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
GENERATED_AT = "2026-08-23T18:40:00Z"
R9_11_IMPLEMENTATION_HEAD = "e8e7e83c107bdb8bcb29882936720bc9eeb1c246"
R98_LOCAL_EVIDENCE_SHA256 = "a8412a92ea2d1f456fdc3fdf47aa1a3ac63257a69df8854d36162128e6f0a967"
R98_LOCAL_EVIDENCE_BYTES = 5744

ACCEPTED_HEADS: dict[str, str] = {
    "R9.1": "dfde39746f0ec909a865a9f0ef75b6856e77c88f",
    "R9.2": "15186ced206f05d8baf764738615e6625aa6d459",
    "R9.3": "915075149fa81b31308c3eedcfa35e74f8a9b7a4",
    "R9.4": "e158fd643ecf55a1ed9022193a48d2d1ee1716ed",
    "R9.5": "525a4c48ae0ff714fe4b3ee7bca34b2e8c62c112",
    "R9.6": "f453db0c5ec5705b4dea8ae00a5937583f466fa1",
    "R9.7": "20cc4bbc93e547fac9fee28d7be44268358d29e4",
    "R9.8": "86777ddc7a87ad6041ddc599e20e93af38512a19",
    "R9.9": "85f8aacf8baf0f8dba6d28ba07fcfc0dbc37a324",
    "R9.10": "dda09a1728ba63640f68a979af57d70f12b4c603",
    "R9.11": R9_11_IMPLEMENTATION_HEAD,
}

MANUAL_STATES: dict[str, R9ManualState] = {
    "R9.1": R9ManualState.NONE,
    "R9.2": R9ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R9.3": R9ManualState.NONE,
    "R9.4": R9ManualState.NONE,
    "R9.5": R9ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R9.6": R9ManualState.NONE,
    "R9.7": R9ManualState.NONE,
    "R9.8": R9ManualState.REQUIRED_SATISFIED,
    "R9.9": R9ManualState.CONDITIONAL_NOT_TRIGGERED,
    "R9.10": R9ManualState.NONE,
    "R9.11": R9ManualState.CONDITIONAL_NOT_TRIGGERED,
}

MANUAL_REASONS: dict[str, str] = {
    "R9.1": "No manual intervention is defined for the transport-independent R9.1 foundation.",
    "R9.2": "The R9.2 conditional was not triggered; hosted deterministic transport fixtures exercised the accepted client paths.",
    "R9.3": "No manual intervention is defined for deterministic capability inventory normalization.",
    "R9.4": "No manual intervention is defined for workflow catalog validation and governed model resolution.",
    "R9.5": "The R9.5 conditional was not triggered; hosted queue/history fixtures exercised execution and reconciliation without a new authoritative local path.",
    "R9.6": "No manual intervention is defined for deterministic generated-output capture and R8 lineage bridging.",
    "R9.7": "No manual intervention is defined for targeted lifecycle and conservative free-memory semantics.",
    "R9.8": "The frozen REQUIRED local GPU acceptance was reviewed and satisfied on the accepted implementation head.",
    "R9.9": "The R9.9 conditional was not triggered because the mandatory production packs introduced no new real node/model family beyond accepted R9.8 evidence.",
    "R9.10": "No manual intervention is defined for the governed CLI and non-blocking KodeStudio façade.",
    "R9.11": "The R9.11 conditional was not triggered because adversarial hardening changes no hardware-facing semantics and inherited manual gates are resolved.",
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


def build_report() -> R9IntegrationReport:
    evidence = []
    for subdivision in expected_r9_subdivisions():
        index = subdivision.split(".", 1)[1]
        source = f"docs/roadmap/R9_{index}_ACCEPTANCE.md"
        manual_kwargs = {}
        if subdivision == "R9.8":
            manual_kwargs = {
                "manual_evidence_sha256": R98_LOCAL_EVIDENCE_SHA256,
                "manual_evidence_bytes": R98_LOCAL_EVIDENCE_BYTES,
            }
        evidence.append(
            build_subdivision_evidence(
                subdivision,
                accepted_head=ACCEPTED_HEADS[subdivision],
                manual_state=MANUAL_STATES[subdivision],
                manual_reason=MANUAL_REASONS[subdivision],
                canonical_bytes=git_blob_bytes(source),
                **manual_kwargs,
            )
        )
    report = R9IntegrationReport(
        generated_at=GENERATED_AT,
        source_sha=R9_11_IMPLEMENTATION_HEAD,
        subdivisions=tuple(evidence),
        status=R9IntegrationStatus.PASS,
        blockers=(),
    )
    validate_repository_evidence(report, git_blob_bytes)
    return report


def serialized_report(report: R9IntegrationReport) -> str:
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
        print("R9_INTEGRATED_ACCEPTANCE_CANDIDATE_BEGIN")
        print(expected, end="")
        print("R9_INTEGRATED_ACCEPTANCE_CANDIDATE_END")
        return 0

    observed = target.read_text(encoding="utf-8")
    if observed != expected:
        raise SystemExit(
            "R9 integrated acceptance evidence differs from canonical Git-blob regeneration"
        )
    loaded = R9IntegrationReport.from_dict(json.loads(observed))
    validate_repository_evidence(loaded, git_blob_bytes)
    if loaded.status is not R9IntegrationStatus.PASS or loaded.blockers:
        raise SystemExit("R9 integrated acceptance is not PASS or contains blockers")
    print("R9 integrated acceptance: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or validate R9 integrated acceptance evidence")
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
