from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.bench.decision import (
    BackendCapability,
    BudgetStatus,
    DecisionDisposition,
    DecisionEvidence,
    DiagnosticComponent,
    DiagnosticProbe,
    ExpectedImpact,
    GapDecisionEngine,
    GapDecisionError,
    ProbeStatus,
    evaluate_saved_decision,
)
from kodepoia.experience.contracts import PolicyDecision


def _report(*, passing: bool = False, scorer_failure: bool = False) -> dict[str, object]:
    outcomes: list[dict[str, object]] = []
    for repeat in range(2):
        outcomes.append(
            {
                "category": (
                    "scorer_failure"
                    if scorer_failure
                    else ("pass" if passing else "wrong_answer")
                ),
                "critical": True,
                "domain": "python",
                "error": "fixture scorer" if scorer_failure else None,
                "model_ref": "base",
                "passed": passing,
                "repeat": repeat,
                "resources": {},
                "response_digest": "1" * 64,
                "scorer_digest": "2" * 64,
                "seed": 101 + repeat,
                "task_id": "python-gap",
            }
        )
    return {
        "config_digest": "3" * 64,
        "model_identities": [
            {
                "model_digest": "4" * 64,
                "model_ref": "base",
                "resolved": True,
                "runtime": "fixture",
                "runtime_version": "1",
            }
        ],
        "outcomes": outcomes,
        "protection_manifest_digest": "5" * 64,
        "suite_digest": "6" * 64,
    }


def _dataset(count: int = 4) -> dict[str, object]:
    return {
        "dataset_digest": "7" * 64,
        "dataset_id": "fixture-dataset",
        "entries": [
            {
                "domain": "python",
                "example_id": f"example-{index}",
                "split": "train",
            }
            for index in range(count)
        ],
    }


def _diagnostics(
    *,
    defect: DiagnosticComponent | None = None,
    unknown: DiagnosticComponent | None = None,
) -> tuple[DiagnosticProbe, ...]:
    probes = []
    for index, component in enumerate(
        (
            DiagnosticComponent.TOOL,
            DiagnosticComponent.RETRIEVAL,
            DiagnosticComponent.ROUTER,
            DiagnosticComponent.CONTEXT,
        )
    ):
        status = ProbeStatus.PASS
        if component is defect:
            status = ProbeStatus.DEFECT
        elif component is unknown:
            status = ProbeStatus.UNKNOWN
        probes.append(
            DiagnosticProbe(
                component,
                status,
                f"{index + 8:x}" * 64,
                ("python",) if status is ProbeStatus.DEFECT else (),
            )
        )
    return tuple(probes)


def _evidence() -> DecisionEvidence:
    return DecisionEvidence(
        benchmark_reproducible=True,
        contamination_valid=True,
        dataset_license=PolicyDecision.ALLOW,
        base_model_license=PolicyDecision.ALLOW,
        backend_capability=BackendCapability.SUPPORTED,
        budget_status=BudgetStatus.WITHIN_BUDGET,
        rollback_ready=True,
        expected_impact=ExpectedImpact.MEANINGFUL,
        diagnostics=_diagnostics(),
        evidence_digests=(("system", "c" * 64),),
    )


def test_train_requires_all_ordered_gates_and_is_deterministic() -> None:
    engine = GapDecisionEngine()
    first = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=_evidence(),
        dataset=_dataset(),
    )
    second = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=_evidence(),
        dataset=_dataset(),
    )
    assert first.disposition is DecisionDisposition.TRAIN
    assert first.adapter_method == "qlora_sft"
    assert first.target_domains == ("python",)
    assert first.targets[0].critical is True
    assert first.targets[0].minimum_score == 1.0
    assert first.train_examples_by_domain == (("python", 4),)
    assert first.digest == second.digest


def test_no_gap_is_truthful_no_train_without_dataset() -> None:
    decision = GapDecisionEngine().evaluate(
        _report(passing=True),
        base_model_ref="base",
        evidence=_evidence(),
    )
    assert decision.disposition is DecisionDisposition.NO_TRAIN
    assert decision.gaps == ()
    assert decision.adapter_method is None


def test_system_defect_wins_before_data_and_license_gates() -> None:
    evidence = replace(
        _evidence(),
        diagnostics=_diagnostics(defect=DiagnosticComponent.RETRIEVAL),
        dataset_license=PolicyDecision.DENY,
    )
    decision = GapDecisionEngine().evaluate(
        _report(),
        base_model_ref="base",
        evidence=evidence,
    )
    assert decision.disposition is DecisionDisposition.FIX_SYSTEM_FIRST
    assert decision.blockers == ("system_defect:retrieval",)


def test_missing_or_small_dataset_is_insufficient_data() -> None:
    engine = GapDecisionEngine()
    missing = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=_evidence(),
    )
    small = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=_evidence(),
        dataset=_dataset(3),
    )
    assert missing.disposition is DecisionDisposition.INSUFFICIENT_DATA
    assert small.disposition is DecisionDisposition.INSUFFICIENT_DATA
    assert small.blockers == ("insufficient_domain:python",)


@pytest.mark.parametrize("decision", [PolicyDecision.DENY, PolicyDecision.REVIEW, PolicyDecision.UNKNOWN])
def test_unknown_or_disallowed_license_fails_closed(decision: PolicyDecision) -> None:
    evidence = replace(_evidence(), base_model_license=decision)
    result = GapDecisionEngine().evaluate(
        _report(),
        base_model_ref="base",
        evidence=evidence,
        dataset=_dataset(),
    )
    assert result.disposition is DecisionDisposition.LICENSE_BLOCKED
    assert result.adapter_method is None


def test_backend_and_budget_terminal_states_are_separate() -> None:
    engine = GapDecisionEngine()
    unsupported = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(
            _evidence(),
            backend_capability=BackendCapability.UNSUPPORTED,
        ),
        dataset=_dataset(),
    )
    budget = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(_evidence(), budget_status=BudgetStatus.EXCEEDED),
        dataset=_dataset(),
    )
    assert unsupported.disposition is DecisionDisposition.UNSUPPORTED
    assert budget.disposition is DecisionDisposition.BUDGET_BLOCKED


def test_unknown_backend_missing_probe_and_rollback_are_inconclusive() -> None:
    engine = GapDecisionEngine()
    unknown_backend = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(_evidence(), backend_capability=BackendCapability.UNKNOWN),
        dataset=_dataset(),
    )
    missing_probe = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(_evidence(), diagnostics=_diagnostics()[:-1]),
        dataset=_dataset(),
    )
    rollback = engine.evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(_evidence(), rollback_ready=None),
        dataset=_dataset(),
    )
    assert unknown_backend.disposition is DecisionDisposition.INCONCLUSIVE
    assert missing_probe.disposition is DecisionDisposition.INCONCLUSIVE
    assert rollback.disposition is DecisionDisposition.INCONCLUSIVE


def test_low_expected_impact_is_no_train() -> None:
    result = GapDecisionEngine().evaluate(
        _report(),
        base_model_ref="base",
        evidence=replace(_evidence(), expected_impact=ExpectedImpact.LOW),
        dataset=_dataset(),
    )
    assert result.disposition is DecisionDisposition.NO_TRAIN


def test_scorer_failure_and_unresolved_base_identity_are_rejected() -> None:
    with pytest.raises(GapDecisionError, match="scorer failure"):
        GapDecisionEngine().evaluate(
            _report(scorer_failure=True),
            base_model_ref="base",
            evidence=_evidence(),
            dataset=_dataset(),
        )

    unresolved = _report()
    identity = unresolved["model_identities"][0]
    assert isinstance(identity, dict)
    identity["model_digest"] = None
    result = GapDecisionEngine().evaluate(
        unresolved,
        base_model_ref="base",
        evidence=_evidence(),
        dataset=_dataset(),
    )
    assert result.disposition is DecisionDisposition.INCONCLUSIVE
    assert result.blockers == ("base_model_identity_unresolved",)


def test_saved_decision_schema_and_superseding_lineage(tmp_path: Path) -> None:
    benchmark_path = tmp_path / "benchmark.json"
    dataset_path = tmp_path / "dataset.json"
    evidence_path = tmp_path / "evidence.json"
    benchmark_path.write_text(json.dumps(_report()), encoding="utf-8")
    dataset_path.write_text(json.dumps(_dataset()), encoding="utf-8")
    evidence_payload = _evidence().descriptor()
    evidence_payload["supersedes_decision_digest"] = "d" * 64
    evidence_path.write_text(json.dumps(evidence_payload), encoding="utf-8")

    decision = evaluate_saved_decision(
        benchmark_path,
        evidence_path,
        base_model_ref="base",
        dataset_path=dataset_path,
    )
    destination = tmp_path / "decision.json"
    decision.save(destination)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    schema = json.loads(
        Path("schemas/r15-7-gap-decision.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    assert payload["disposition"] == "train"
    assert payload["evidence"]["supersedes_decision_digest"] == "d" * 64
    assert payload["decision_digest"] == decision.digest
