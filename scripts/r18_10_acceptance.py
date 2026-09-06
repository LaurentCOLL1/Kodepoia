from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from kodepoia.release.incident import (
    run_synthetic_incident_drills,
    write_incident_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run R18.10 synthetic incident/recovery drills."
    )
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with tempfile.TemporaryDirectory(prefix="kodepoia-r18-10-") as temp:
        report = run_synthetic_incident_drills(
            source_sha=args.source_sha,
            work_dir=Path(temp),
        )
    output = write_incident_report(report, args.output)
    payload = json.loads(output.read_text(encoding="utf-8"))
    if payload.get("status") != "PASS":
        raise SystemExit("R18.10 critical incident drill veto")
    if payload.get("critical_bypass_count") != 0:
        raise SystemExit("R18.10 unexpected critical bypass")
    if payload.get("provider_effect_count") != 0:
        raise SystemExit("R18.10 provider-side effect was unexpectedly executed")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
