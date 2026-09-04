from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from kodepoia.quality import integrated_rc_acceptance as base
from kodepoia.quality.integrated_rc_execution import (
    aggregate_integrated_reports,
    load_execution_policy,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_POLICY = ROOT / "configs" / "r16_18_integrated_rc_policy.json"
EXECUTION_POLICY = ROOT / "configs" / "r16_18_phase_execution_policy.json"


def _digest(value: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _green_reports(tmp_path: Path, source_sha: str) -> Path:
    base_policy = base.load_policy(BASE_POLICY)
    execution = load_execution_policy(EXECUTION_POLICY, base_policy=base_policy)
    execution_digest = _digest(execution)
    integrated_digest = _digest(
        {"base_policy": base_policy, "execution_policy": execution}
    )
    directory = tmp_path / "reports"
    directory.mkdir()
    for entry in base.matrix_from_policy(base_policy)["include"]:
        artifacts = {}
        if entry["case_id"] == "r16.17-release-readiness":
            artifacts = {
                "kodepoia-1.0.0rc1-py3-none-any.whl": "a" * 64,
                "kodepoia-1.0.0rc1.tar.gz": "b" * 64,
            }
        semantic = {
            "case_id": entry["case_id"],
            "phase": entry["phase"],
            "critical": True,
            "source_sha": source_sha,
            "platform": entry["platform"],
            "fresh_execution": True,
            "historical_evidence_used_for_verdict": False,
            "selectors": ["tests/example.py"],
            "pytest_returncode": 0,
            "counts": {"tests": 1, "failures": 0, "errors": 0, "skipped": 0},
            "base_policy_sha256": _digest(base_policy),
            "execution_policy_sha256": execution_digest,
            "integrated_contract_sha256": integrated_digest,
            "phase_acceptance_script": "scripts/example.py",
            "phase_acceptance_returncode": 0,
            "phase_evidence_source_bound": True,
            "phase_evidence_verdict": True,
            "phase_manual_required": False,
            "phase_critical_veto": False,
            "phase_evidence_sha256": "c" * 64,
            "preparation": "none",
            "artifact_hashes": artifacts,
            "same_source_rebuild_identical": (
                True if entry["case_id"] == "r16.17-release-readiness" else None
            ),
            "pass": True,
        }
        report = {**semantic, "semantic_sha256": _digest(semantic)}
        (directory / f"{entry['case_id']}-{entry['platform']}.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return directory


def test_r16_18_execution_policy_exactly_extends_base_frozen_case_set() -> None:
    base_policy = base.load_policy(BASE_POLICY)
    execution = load_execution_policy(EXECUTION_POLICY, base_policy=base_policy)
    assert execution["base_policy_id"] == base_policy["policy_id"]
    assert len(execution["cases"]) == 17
    assert {item["id"] for item in execution["cases"]} == {
        item["id"] for item in base_policy["cases"]
    }
    assert all((ROOT / item["script"]).is_file() for item in execution["cases"])
    release = next(item for item in execution["cases"] if item["phase"] == "R16.17")
    assert release["preparation"] == "release_package"
    assert release["verdict"] == {
        "mode": "path_equals",
        "path": "release_claim",
        "value": True,
    }


def test_r16_18_execution_policy_rejects_coverage_drift(tmp_path: Path) -> None:
    base_policy = base.load_policy(BASE_POLICY)
    execution = load_execution_policy(EXECUTION_POLICY, base_policy=base_policy)
    drifted = copy.deepcopy(execution)
    drifted["cases"].pop()
    path = tmp_path / "execution.json"
    path.write_text(json.dumps(drifted), encoding="utf-8")
    with pytest.raises(base.IntegratedRCAcceptanceError, match="exactly cover"):
        load_execution_policy(path, base_policy=base_policy)


def test_r16_18_integrated_aggregate_requires_phase_evidence_and_cross_os_rc_bytes(
    tmp_path: Path,
) -> None:
    source = "1" * 40
    reports = _green_reports(tmp_path, source)
    summary = aggregate_integrated_reports(
        base_policy_path=BASE_POLICY,
        execution_policy_path=EXECUTION_POLICY,
        source_sha=source,
        reports_dir=reports,
    )
    assert summary["rc_acceptance_claim"] is True
    assert summary["critical_veto"] is False
    assert summary["expected_case_platform_count"] == 33
    assert summary["cross_platform_rc_packages_identical"] is True
    assert summary["core_manual_required"] is False
    assert summary["historical_evidence_used_for_verdict"] is False


@pytest.mark.parametrize(
    ("mutation", "blocker"),
    [
        ("phase_stale", "phase_acceptance_missing_stale_failed_or_manual"),
        ("manual", "phase_acceptance_missing_stale_failed_or_manual"),
        ("contract", "phase_execution_contract_binding_mismatch"),
        ("package", "cross_platform_rc_package_bytes_differ_or_missing"),
    ],
)
def test_r16_18_integrated_aggregate_fails_closed(
    tmp_path: Path,
    mutation: str,
    blocker: str,
) -> None:
    source = "2" * 40
    reports = _green_reports(tmp_path, source)
    files = sorted(reports.glob("*.json"))
    if mutation == "package":
        target = next(path for path in files if path.name == "r16.17-release-readiness-Linux.json")
        payload = json.loads(target.read_text(encoding="utf-8"))
        payload["artifact_hashes"]["kodepoia-1.0.0rc1.tar.gz"] = "f" * 64
    else:
        target = files[0]
        payload = json.loads(target.read_text(encoding="utf-8"))
        if mutation == "phase_stale":
            payload["phase_evidence_source_bound"] = False
        elif mutation == "manual":
            payload["phase_manual_required"] = True
        else:
            payload["integrated_contract_sha256"] = "0" * 64
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = aggregate_integrated_reports(
        base_policy_path=BASE_POLICY,
        execution_policy_path=EXECUTION_POLICY,
        source_sha=source,
        reports_dir=reports,
    )
    assert summary["rc_acceptance_claim"] is False
    assert summary["critical_veto"] is True
    assert blocker in summary["blockers"]
