from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from kodepoia.capability_truth import (
    PUBLIC_DISTRIBUTION_SHA,
    PUBLIC_DISTRIBUTION_TAG,
    capability_documentation_payload,
    capability_matrix_payload,
)
from kodepoia.kodestudio.research_panel import research_capability_rows


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip().lower()


def _projection(rows: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    fields = (
        "capability_id",
        "classifications",
        "runtime_state",
        "network_state",
        "authentication_state",
        "accelerator_state",
    )
    return [{field: row[field] for field in fields} for row in rows]


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "detail": detail}


def build_report(root: Path, *, source_sha: str) -> dict[str, Any]:
    expected_documentation = capability_documentation_payload()
    matrix_path = root / "docs" / "roadmap" / "V2_0_CAPABILITY_MATRIX.json"
    actual_documentation = json.loads(matrix_path.read_text(encoding="utf-8"))
    runtime = capability_matrix_payload()
    runtime_by_id = {row["capability_id"]: row for row in runtime["capabilities"]}

    ui_rows = research_capability_rows()
    documented_research = [
        row
        for row in actual_documentation["capabilities"]
        if row["capability_id"].startswith("research.")
    ]
    ui_source = (
        root / "src" / "kodepoia" / "kodestudio" / "research_panel.py"
    ).read_text(encoding="utf-8")

    checks = [
        _check(
            "documentation-runtime-parity",
            actual_documentation == expected_documentation,
            "Committed V2 capability matrix equals the canonical runtime projection.",
        ),
        _check(
            "ui-runtime-parity",
            _projection(ui_rows) == documented_research,
            "KodeStudio research diagnostics consume the same canonical research rows.",
        ),
        _check(
            "ui-wiring",
            "researchCapabilityDiagnostics" in ui_source
            and "researchQueryScope" in ui_source
            and "research_capability_diagnostics_text(" in ui_source,
            "Research UI visibly wires capability diagnostics and persisted-query scope.",
        ),
        _check(
            "public-distribution-boundary",
            actual_documentation["public_distribution"]
            == {"tag": PUBLIC_DISTRIBUTION_TAG, "source_sha": PUBLIC_DISTRIBUTION_SHA},
            "Public authority remains v1.1.0-rc8 and is not inferred from live main.",
        ),
        _check(
            "saved-search-honesty",
            runtime_by_id["research.saved-reports-search"]["runtime_state"] == "ready"
            and "persisted" in runtime_by_id["research.saved-reports-search"]["action"].lower()
            and "internet discovery"
            in runtime_by_id["research.saved-reports-search"]["details"].lower(),
            "Zero matches may be a successful local persisted-report query, never Web discovery.",
        ),
        _check(
            "provider-failure-states",
            runtime_by_id["research.web-discovery"]["runtime_state"] == "not-implemented"
            and runtime_by_id["research.github-authenticated-resource"]["runtime_state"]
            == "auth-required"
            and runtime_by_id["research.vision-provider"]["runtime_state"] == "unavailable"
            and runtime_by_id["research.explicit-web-fetch"]["runtime_state"]
            == "network-restricted",
            "Unavailable/auth/network/not-implemented providers remain distinct from empty results.",
        ),
        _check(
            "accelerator-policy",
            runtime_by_id["accelerator.kaggle-t4x2"]["accelerator_state"] == "priority"
            and "acceptance-proven"
            in runtime_by_id["accelerator.kaggle-t4x2"]["classifications"]
            and runtime_by_id["accelerator.tpu-v5e-8"]["accelerator_state"] == "deferred"
            and runtime_by_id["accelerator.tpu-v5e-8"]["runtime_state"] == "not-implemented",
            "Kaggle T4 x2 stays priority and TPU v5e-8 stays deferred without XLA proof.",
        ),
    ]
    failed = [check["name"] for check in checks if check["status"] != "PASS"]
    return {
        "schema": "kodepoia.v2.capability-acceptance",
        "schema_version": 1,
        "source_sha": source_sha,
        "status": "PASS" if not failed else "FAIL",
        "checks_total": len(checks),
        "checks_passed": len(checks) - len(failed),
        "failed_checks": failed,
        "checks": checks,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V2.0 capability-truth exact-head acceptance")
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

    report = build_report(root, source_sha=expected)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
