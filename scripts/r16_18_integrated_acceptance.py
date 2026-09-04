from __future__ import annotations

import argparse
import json
from pathlib import Path

from kodepoia.quality.integrated_rc_acceptance import load_policy, matrix_from_policy, write_report
from kodepoia.quality.integrated_rc_execution import (
    aggregate_integrated_reports,
    run_integrated_case,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_POLICY = ROOT / "configs" / "r16_18_integrated_rc_policy.json"
EXECUTION_POLICY = ROOT / "configs" / "r16_18_phase_execution_policy.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R16.18 non-circular integrated adversarial + real-project RC acceptance"
    )
    parser.add_argument("--policy", default=str(BASE_POLICY))
    parser.add_argument("--execution-policy", default=str(EXECUTION_POLICY))
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--source-sha")
    parser.add_argument("--case-id")
    parser.add_argument("--platform")
    parser.add_argument("--aggregate-dir")
    parser.add_argument("--output")
    args = parser.parse_args()

    base_policy = load_policy(args.policy)
    if args.matrix:
        print(json.dumps(matrix_from_policy(base_policy), separators=(",", ":"), sort_keys=True))
        return 0
    if not args.source_sha or not args.output:
        parser.error("--source-sha and --output are required outside --matrix mode")

    if args.aggregate_dir:
        report = aggregate_integrated_reports(
            base_policy_path=args.policy,
            execution_policy_path=args.execution_policy,
            source_sha=args.source_sha,
            reports_dir=args.aggregate_dir,
        )
    else:
        if not args.case_id or not args.platform:
            parser.error("--case-id and --platform are required for fresh case mode")
        report = run_integrated_case(
            ROOT,
            base_policy_path=args.policy,
            execution_policy_path=args.execution_policy,
            source_sha=args.source_sha,
            case_id=args.case_id,
            platform=args.platform,
            evidence_dir=Path(args.output).parent,
        )

    write_report(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report.get("pass", report.get("rc_acceptance_claim", False)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
