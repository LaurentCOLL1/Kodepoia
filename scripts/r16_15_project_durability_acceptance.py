from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kodepoia.project.r16_15_acceptance import (  # noqa: E402
    FIXTURE_RELATIVE,
    build_project_durability_report,
)


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--platform", default="CI")
    parser.add_argument(
        "--output",
        default="artifacts/r16_15_project_durability_acceptance.json",
    )
    parser.add_argument(
        "--require-extended-local-soak",
        action="store_true",
        help=(
            "Record that the optional extended local/wall-clock soak was requested; "
            "core CI then reports MANUAL_REQUIRED."
        ),
    )
    args = parser.parse_args()
    report = build_project_durability_report(
        ROOT,
        source_sha=args.source_sha,
        platform=args.platform,
        require_extended_local_soak=args.require_extended_local_soak,
    )
    policy_payload = json.loads(
        (ROOT / "configs/r16_supply_chain_policy.json").read_text(encoding="utf-8")
    )
    fixture_payload = json.loads((ROOT / FIXTURE_RELATIVE).read_text(encoding="utf-8"))
    report["policy_sha256"] = _canonical_digest(policy_payload)
    report["authority_sha256"] = _canonical_digest(fixture_payload["authority"])
    report["runtime"] = {
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
    }
    report["evidence_sha256"] = _canonical_digest(
        {
            key: value
            for key, value in report.items()
            if key not in {"elapsed_seconds", "evidence_sha256"}
        }
    )
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    core_ok = (
        report["durability_claim"]
        and not report["critical_veto"]
        and report["secret_free"]
    )
    if args.require_extended_local_soak:
        return 1
    return 0 if core_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
