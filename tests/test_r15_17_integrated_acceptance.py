from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.tuning.integrated_acceptance import (
    CHECK_NAMES,
    canonical_sha256,
    run_integrated_scenario,
    validate_integrated_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "a" * 40


def _run(tmp_path: Path) -> dict[str, object]:
    return run_integrated_scenario(SOURCE_SHA, tmp_path)


def test_integrated_scenario_executes_exact_fourteen_invariants(tmp_path: Path) -> None:
    evidence = _run(tmp_path)
    assert evidence["status"] == "pass"
    assert evidence["blockers"] == []
    assert evidence["check_count"] == 14
    assert tuple(evidence["checks"]) == CHECK_NAMES  # type: ignore[arg-type]
    assert all(evidence["checks"].values())  # type: ignore[union-attr]
    assert evidence["manual_state"] == "conditional_not_triggered"
    assert evidence["optional_capability_state"] == "unavailable"
    assert evidence["secrets_exposed"] is False
    validate_integrated_evidence(evidence)


def test_integrated_evidence_validates_draft_2020_12_schema(tmp_path: Path) -> None:
    evidence = _run(tmp_path)
    schema = json.loads(
        (ROOT / "schemas/r15/r15-integrated-evidence.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)


def test_integrated_scenario_is_path_independent_and_deterministic(tmp_path: Path) -> None:
    first = run_integrated_scenario(SOURCE_SHA, tmp_path / "first")
    second = run_integrated_scenario(SOURCE_SHA, tmp_path / "second")
    assert first == second


def test_checked_in_pass_field_cannot_make_failed_check_authoritative(tmp_path: Path) -> None:
    evidence = deepcopy(_run(tmp_path))
    checks = evidence["checks"]
    assert isinstance(checks, dict)
    checks[CHECK_NAMES[0]] = False
    evidence["status"] = "pass"
    evidence["blockers"] = []
    evidence["semantic_digest"] = canonical_sha256(
        {key: value for key, value in evidence.items() if key != "semantic_digest"}
    )
    with pytest.raises(ValueError, match="adversarial check"):
        validate_integrated_evidence(evidence)


def test_identity_tamper_is_rejected_even_when_status_stays_pass(tmp_path: Path) -> None:
    evidence = deepcopy(_run(tmp_path))
    identities = evidence["identities"]
    assert isinstance(identities, dict)
    identities["dataset"] = "f" * 64
    with pytest.raises(ValueError, match="semantic digest mismatch"):
        validate_integrated_evidence(evidence)


def test_missing_optional_capability_cannot_be_relabelled_pass(tmp_path: Path) -> None:
    evidence = deepcopy(_run(tmp_path))
    evidence["optional_capability_state"] = "pass"
    evidence["semantic_digest"] = canonical_sha256(
        {key: value for key, value in evidence.items() if key != "semantic_digest"}
    )
    with pytest.raises(ValueError, match="truthful unavailable"):
        validate_integrated_evidence(evidence)


def test_source_sha_is_exact_and_secret_fixture_never_reaches_evidence(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="source_sha"):
        run_integrated_scenario("short", tmp_path / "invalid")

    evidence = _run(tmp_path / "valid")
    rendered = json.dumps(evidence, sort_keys=True)
    assert "R15_17_SYNTHETIC_SECRET" not in rendered
