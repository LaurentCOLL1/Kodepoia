from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from kodepoia.quality.resource_soak import (
    ResourceSoakGovernanceError,
    build_resource_soak_report,
    canonical_sha256,
    classify_cpu_repeatability,
    load_fixture,
    load_policy,
    metrics_within_budget,
    required_capacities_satisfied,
    sanitize_diagnostic,
    validate_fixture_payload,
    validate_policy_payload,
)

ROOT = Path(__file__).resolve().parents[1]


def test_fixture_contract_and_canonical_digest_are_stable() -> None:
    fixture = load_fixture(ROOT)
    assert fixture["name"] == "r16.16-resource-concurrency-leak-diagnostics-soak"
    assert {item["id"] for item in fixture["profiles"]} == {
        "code",
        "godot",
        "comfyui",
        "media",
        "desktop",
    }
    assert len(canonical_sha256(fixture)) == 64


def test_fixture_rejects_unbounded_cycles() -> None:
    fixture = load_fixture(ROOT)
    bad = copy.deepcopy(fixture)
    bad["profiles"][0]["cycles"] = 100
    with pytest.raises(ResourceSoakGovernanceError, match="cycles"):
        validate_fixture_payload(bad)


def test_fixture_rejects_duplicate_profile_identity() -> None:
    fixture = load_fixture(ROOT)
    bad = copy.deepcopy(fixture)
    bad["profiles"][1]["id"] = bad["profiles"][0]["id"]
    with pytest.raises(ResourceSoakGovernanceError, match="identity"):
        validate_fixture_payload(bad)


def test_policy_contract_requires_vram_to_remain_optional() -> None:
    policy = load_policy(ROOT)
    bad = copy.deepcopy(policy)
    bad["optional_capacities"] = []
    bad["required_capacities"].append("vram")
    with pytest.raises(ResourceSoakGovernanceError, match="VRAM"):
        validate_policy_payload(bad)


def test_policy_rejects_unbounded_wall_clock() -> None:
    policy = load_policy(ROOT)
    bad = copy.deepcopy(policy)
    bad["budgets"]["max_wall_ms"] = 120000.0
    with pytest.raises(ResourceSoakGovernanceError, match="wall-clock"):
        validate_policy_payload(bad)


def test_policy_rejects_diagnostic_privacy_weakening() -> None:
    policy = load_policy(ROOT)
    bad = copy.deepcopy(policy)
    bad["diagnostics"]["persist_absolute_paths"] = True
    with pytest.raises(ResourceSoakGovernanceError, match="privacy-safe"):
        validate_policy_payload(bad)


def test_required_capacity_unknown_fails_closed() -> None:
    availability = {
        "cpu": {"state": "PASS"},
        "vram": {"state": "INCONCLUSIVE"},
    }
    ok, missing = required_capacities_satisfied(["cpu", "vram"], availability)
    assert ok is False
    assert missing == ("vram",)


def test_budget_evaluator_rejects_overrun() -> None:
    policy = load_policy(ROOT)
    budgets = policy["budgets"]
    metrics = {
        "wall_ms": budgets["max_wall_ms"] + 1,
        "cpu_ms": 0,
        "rss_growth_bytes": 0,
        "heap_growth_bytes": 0,
        "peak_heap_bytes": 0,
        "peak_temp_bytes": 0,
        "temp_bytes_after": 0,
        "temp_files_after": 0,
        "thread_delta_after": 0,
    }
    assert metrics_within_budget(metrics, budgets) is False


def test_cpu_repeatability_is_inconclusive_below_significance_floor() -> None:
    budgets = load_policy(ROOT)["budgets"]
    result = classify_cpu_repeatability([31.25, 0.0], budgets)
    assert result["state"] == "INCONCLUSIVE"
    assert result["ratio"] is None
    assert result["significance_floor_ms"] == 50.0


def test_cpu_repeatability_fails_when_significant_samples_regress() -> None:
    budgets = load_policy(ROOT)["budgets"]
    result = classify_cpu_repeatability([50.0, 1100.0], budgets)
    assert result["state"] == "FAIL"
    assert result["ratio"] == 22.0


def test_diagnostics_redact_sensitive_values_and_paths() -> None:
    canary = load_fixture(ROOT)["synthetic_secret_token"]
    diagnostic = sanitize_diagnostic(
        {
            "token": canary,
            "message": f"secret={canary}",
            "repo_path": str(ROOT.resolve()),
            "count": 2,
        }
    )
    rendered = json.dumps(diagnostic, sort_keys=True)
    assert canary not in rendered
    assert str(ROOT.resolve()) not in rendered
    assert "<redacted>" in rendered
    assert "<redacted-path>" in rendered


def test_full_bounded_resource_soak_acceptance() -> None:
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
    report = build_resource_soak_report(ROOT, source_sha=source_sha, platform="pytest")
    assert report["phase"] == "R16.16"
    assert report["source_sha"] == source_sha
    assert report["resource_claim"] is True
    assert report["critical_veto"] is False
    assert report["secret_free"] is True
    assert report["manual_state"] == "NONE"
    assert report["availability"]["vram"]["state"] == "INCONCLUSIVE"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["passed"] == report["summary"]["total"]
    assert report["concurrency"]["post_cancel_mutations"] == 0
    assert report["process_cleanup"]["active_after"] == 0
    assert len(report["fixture_sha256"]) == 64
    assert len(report["policy_sha256"]) == 64
    assert len(report["semantic_sha256"]) == 64
    assert len(report["authority_sha256"]) == 64
    assert len(report["evidence_sha256"]) == 64
    canary = load_fixture(ROOT)["synthetic_secret_token"]
    assert canary not in json.dumps(report, sort_keys=True)
