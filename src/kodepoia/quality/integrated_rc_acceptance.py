from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_PHASES = {f"R16.{index}" for index in range(1, 18)}


class IntegratedRCAcceptanceError(ValueError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _git_head(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
    ).strip().lower()


def load_policy(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "schema_version",
        "policy_id",
        "non_circular",
        "historical_evidence_may_decide_verdict",
        "reject_skipped_tests",
        "require_exact_source_sha",
        "require_all_cases",
        "cases",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise IntegratedRCAcceptanceError("policy schema keys drifted")
    if payload["schema_version"] != 1:
        raise IntegratedRCAcceptanceError("unsupported policy schema")
    if payload["non_circular"] is not True:
        raise IntegratedRCAcceptanceError("non-circular authority must be explicit")
    if payload["historical_evidence_may_decide_verdict"] is not False:
        raise IntegratedRCAcceptanceError("historical evidence cannot decide the verdict")
    if payload["reject_skipped_tests"] is not True:
        raise IntegratedRCAcceptanceError("skipped tests must be rejected")
    if payload["require_exact_source_sha"] is not True:
        raise IntegratedRCAcceptanceError("exact source binding is mandatory")
    if payload["require_all_cases"] is not True:
        raise IntegratedRCAcceptanceError("all frozen cases are mandatory")

    cases = payload["cases"]
    if not isinstance(cases, list) or not cases:
        raise IntegratedRCAcceptanceError("cases must be a non-empty list")
    ids: set[str] = set()
    phases: set[str] = set()
    pairs: set[tuple[str, str]] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "critical",
            "id",
            "phase",
            "pytest",
            "targets",
        }:
            raise IntegratedRCAcceptanceError("case schema drifted")
        case_id = case["id"]
        phase = case["phase"]
        if not isinstance(case_id, str) or not case_id:
            raise IntegratedRCAcceptanceError("case id must be non-empty")
        if case_id in ids:
            raise IntegratedRCAcceptanceError(f"duplicate case id: {case_id}")
        ids.add(case_id)
        if not isinstance(phase, str):
            raise IntegratedRCAcceptanceError("case phase must be a string")
        phases.add(phase)
        if case["critical"] is not True:
            raise IntegratedRCAcceptanceError(f"all frozen cases must be critical: {case_id}")
        tests = case["pytest"]
        if (
            not isinstance(tests, list)
            or not tests
            or any(
                not isinstance(item, str) or not item.startswith("tests/")
                for item in tests
            )
        ):
            raise IntegratedRCAcceptanceError(f"invalid pytest selectors for {case_id}")
        targets = case["targets"]
        if not isinstance(targets, list) or not targets:
            raise IntegratedRCAcceptanceError(f"case has no execution targets: {case_id}")
        for target in targets:
            if not isinstance(target, dict) or set(target) != {"platform", "runner"}:
                raise IntegratedRCAcceptanceError(f"target schema drifted: {case_id}")
            runner = target["runner"]
            platform = target["platform"]
            if runner not in {"ubuntu-latest", "windows-latest"}:
                raise IntegratedRCAcceptanceError(f"unsupported runner: {runner}")
            if platform not in {"Linux", "Windows"}:
                raise IntegratedRCAcceptanceError(f"unsupported platform: {platform}")
            if (runner == "ubuntu-latest") != (platform == "Linux"):
                raise IntegratedRCAcceptanceError(f"runner/platform mismatch: {case_id}")
            pair = (case_id, platform)
            if pair in pairs:
                raise IntegratedRCAcceptanceError(f"duplicate case/platform pair: {pair}")
            pairs.add(pair)
    if phases != _REQUIRED_PHASES:
        raise IntegratedRCAcceptanceError(
            "frozen phase coverage drifted: "
            f"expected {sorted(_REQUIRED_PHASES)}, got {sorted(phases)}"
        )
    return payload


def matrix_from_policy(policy: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    include: list[dict[str, str]] = []
    for case in policy["cases"]:
        for target in case["targets"]:
            include.append(
                {
                    "case_id": case["id"],
                    "phase": case["phase"],
                    "runner": target["runner"],
                    "platform": target["platform"],
                }
            )
    return {"include": include}


def _case_by_id(policy: dict[str, Any], case_id: str) -> dict[str, Any]:
    matches = [case for case in policy["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise IntegratedRCAcceptanceError(f"unknown or duplicate case id: {case_id}")
    return matches[0]


def _junit_counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    if root.tag not in {"testsuite", "testsuites"}:
        raise IntegratedRCAcceptanceError("unexpected JUnit root")
    keys = ("tests", "failures", "errors", "skipped")
    if all(key in root.attrib for key in keys):
        return {key: int(root.attrib.get(key, "0")) for key in keys}
    suites = root.findall(".//testsuite")
    if not suites:
        raise IntegratedRCAcceptanceError("JUnit contains no test suites")
    return {
        key: sum(int(suite.attrib.get(key, "0")) for suite in suites)
        for key in keys
    }


def run_fresh_case(
    repo_root: str | Path,
    *,
    policy_path: str | Path,
    source_sha: str,
    case_id: str,
    platform: str,
) -> dict[str, Any]:
    root = Path(repo_root).resolve(strict=True)
    source = source_sha.strip().lower()
    if _SHA40_RE.fullmatch(source) is None:
        raise IntegratedRCAcceptanceError("source_sha must be a 40-character Git SHA")
    actual = _git_head(root)
    if actual != source:
        raise IntegratedRCAcceptanceError(
            f"exact checkout mismatch: expected {source}, got {actual}"
        )
    policy = load_policy(policy_path)
    case = _case_by_id(policy, case_id)
    allowed_platforms = {target["platform"] for target in case["targets"]}
    if platform not in allowed_platforms:
        raise IntegratedRCAcceptanceError(
            f"platform {platform!r} is not frozen for {case_id}"
        )
    selectors = [str(item) for item in case["pytest"]]
    for selector in selectors:
        if not (root / selector).is_file():
            raise IntegratedRCAcceptanceError(f"frozen selector missing: {selector}")

    with tempfile.TemporaryDirectory(prefix="kodepoia-r16-18-junit-") as raw:
        junit = Path(raw) / "report.xml"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                *selectors,
                f"--junitxml={junit}",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        counts = (
            _junit_counts(junit)
            if junit.is_file()
            else {"tests": 0, "failures": 0, "errors": 1, "skipped": 0}
        )

    passed = (
        completed.returncode == 0
        and counts["tests"] > 0
        and counts["failures"] == 0
        and counts["errors"] == 0
        and counts["skipped"] == 0
    )
    semantic = {
        "case_id": case_id,
        "phase": case["phase"],
        "critical": True,
        "source_sha": source,
        "platform": platform,
        "fresh_execution": True,
        "historical_evidence_used_for_verdict": False,
        "selectors": selectors,
        "pytest_returncode": completed.returncode,
        "counts": counts,
        "pass": passed,
    }
    return {
        **semantic,
        "semantic_sha256": _digest(semantic),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def _expected_pairs(policy: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (case["id"], target["platform"])
        for case in policy["cases"]
        for target in case["targets"]
    }


def aggregate_fresh_reports(
    *,
    policy_path: str | Path,
    source_sha: str,
    reports_dir: str | Path,
) -> dict[str, Any]:
    source = source_sha.strip().lower()
    if _SHA40_RE.fullmatch(source) is None:
        raise IntegratedRCAcceptanceError("source_sha must be a 40-character Git SHA")
    policy = load_policy(policy_path)
    reports: list[dict[str, Any]] = []
    for path in sorted(Path(reports_dir).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and "case_id" in payload:
            reports.append(payload)

    expected = _expected_pairs(policy)
    actual_pairs = [
        (str(report.get("case_id", "")), str(report.get("platform", "")))
        for report in reports
    ]
    actual = set(actual_pairs)
    missing = sorted(
        f"{case_id}@{platform}" for case_id, platform in expected - actual
    )
    unexpected = sorted(
        f"{case_id}@{platform}" for case_id, platform in actual - expected
    )
    source_mismatches = sorted(
        {
            str(report.get("source_sha", ""))
            for report in reports
            if str(report.get("source_sha", "")).lower() != source
        }
    )
    non_fresh = sorted(
        str(report.get("case_id", ""))
        for report in reports
        if report.get("fresh_execution") is not True
        or report.get("historical_evidence_used_for_verdict") is not False
    )
    failed = sorted(
        f"{report.get('case_id')}@{report.get('platform')}"
        for report in reports
        if report.get("pass") is not True
        or int((report.get("counts") or {}).get("skipped", 0)) != 0
    )

    blockers: list[str] = []
    if len(actual_pairs) != len(actual):
        blockers.append("duplicate_case_platform_reports")
    if missing:
        blockers.append("missing_frozen_case_platform_reports")
    if unexpected:
        blockers.append("unexpected_case_platform_reports")
    if source_mismatches:
        blockers.append("mixed_or_stale_source_sha")
    if non_fresh:
        blockers.append("non_fresh_or_circular_verdict_source")
    if failed:
        blockers.append("critical_case_failure_or_skip")

    summary = {
        "schema_version": 1,
        "authority": "R16.18",
        "policy_id": policy["policy_id"],
        "policy_sha256": _digest(policy),
        "source_sha": source,
        "non_circular": True,
        "historical_evidence_used_for_verdict": False,
        "fresh_execution_required": True,
        "expected_case_platform_count": len(expected),
        "received_case_platform_count": len(actual_pairs),
        "missing": missing,
        "unexpected": unexpected,
        "source_mismatches": source_mismatches,
        "non_fresh": non_fresh,
        "failed": failed,
        "critical_veto": bool(blockers),
        "blockers": blockers,
        "rc_acceptance_claim": not blockers,
        "manual_state": "CONDITIONAL_NOT_TRIGGERED",
        "public_release_performed": False,
        "production_signing_performed": False,
        "case_semantic_digests": sorted(
            str(report.get("semantic_sha256", "")) for report in reports
        ),
    }
    summary["authority_sha256"] = _digest(summary)
    return summary


def write_report(path: str | Path, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
