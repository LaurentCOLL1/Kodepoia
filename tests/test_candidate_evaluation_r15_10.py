from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.bench.evaluation import (
    BaseAdapterEvaluator,
    CandidateBinding,
    CandidateDisposition,
    CandidateEvaluationError,
    CandidateEvaluationPolicy,
    TrainingLossContext,
    evaluate_saved_reports,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64
F = "f" * 64
P = "1" * 64
SCORER = "2" * 64
RESPONSE = "3" * 64


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _outcome(
    model_ref: str,
    task_id: str,
    domain: str,
    *,
    critical: bool,
    repeat: int,
    seed: int,
    passed: bool,
    elapsed_s: float = 1.0,
    vram_bytes: int | None = 100,
    error: str | None = None,
) -> dict[str, object]:
    return {
        "category": "pass" if passed and error is None else "wrong_answer",
        "critical": critical,
        "domain": domain,
        "error": error,
        "model_ref": model_ref,
        "passed": passed,
        "repeat": repeat,
        "resources": {
            "elapsed_s": elapsed_s,
            "eval_count": 4,
            "load_s": 0.1,
            "model_size_bytes": 512,
            "prompt_eval_count": 2,
            "tokens_per_second": 4.0,
            "total_s": elapsed_s,
            "vram_bytes": vram_bytes,
        },
        "response_digest": RESPONSE,
        "scorer_digest": SCORER,
        "seed": seed,
        "task_id": task_id,
    }


def _report(
    model_ref: str,
    model_digest: str,
    *,
    rows: list[dict[str, object]],
    protection_digest: str | None = P,
) -> dict[str, object]:
    suite = {
        "suite_id": "r15-10-fixture",
        "tasks": [
            {"critical": True, "domain": "critical", "task_id": "critical"},
            {"critical": False, "domain": "target", "task_id": "target"},
            {"critical": False, "domain": "general", "task_id": "general"},
        ],
        "version": "v1",
    }
    config = {
        "num_predict": 64,
        "repeats": 2,
        "role": "baseline",
        "seed_base": 101,
        "temperature": 0.0,
    }
    payload: dict[str, object] = {
        "config": config,
        "config_digest": _digest(config),
        "model_identities": [
            {
                "model_digest": model_digest,
                "model_ref": model_ref,
                "resolved": True,
                "runtime": "fixture",
                "runtime_version": "1",
            }
        ],
        "outcomes": rows,
        "protection_manifest_digest": protection_digest,
        "schema": "kodepoia.kodebench.v2.report",
        "schema_version": 1,
        "suite": suite,
        "suite_digest": _digest(suite),
        "summary": {},
    }
    payload["report_digest"] = _digest(payload)
    return payload


def _rows(
    model_ref: str,
    *,
    critical: tuple[bool, bool] = (True, True),
    target: tuple[bool, bool] = (False, False),
    general: tuple[bool, bool] = (True, True),
    elapsed_s: float = 1.0,
    vram_bytes: int | None = 100,
    error_task: str | None = None,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    task_specs = (
        ("critical", "critical", True, critical),
        ("target", "target", False, target),
        ("general", "general", False, general),
    )
    for task_id, domain, critical_flag, passes in task_specs:
        for repeat, passed in enumerate(passes, start=1):
            result.append(
                _outcome(
                    model_ref,
                    task_id,
                    domain,
                    critical=critical_flag,
                    repeat=repeat,
                    seed=100 + repeat,
                    passed=passed,
                    elapsed_s=elapsed_s,
                    vram_bytes=vram_bytes,
                    error="fixture failure" if error_task == task_id and repeat == 1 else None,
                )
            )
    return result


def _binding() -> CandidateBinding:
    return CandidateBinding(
        candidate_id="candidate-v1",
        base_model_ref="base",
        base_model_digest=A,
        candidate_model_ref="candidate",
        candidate_model_digest=B,
        adapter_digest=C,
        training_plan_digest=D,
        dataset_digest=E,
    )


def _policy(**overrides: object) -> CandidateEvaluationPolicy:
    values: dict[str, object] = {
        "target_domains": ("target",),
        "min_target_gain": 0.05,
        "require_protected_benchmark": True,
    }
    values.update(overrides)
    return CandidateEvaluationPolicy(**values)


def _evaluate(
    *,
    base_rows: list[dict[str, object]] | None = None,
    candidate_rows: list[dict[str, object]] | None = None,
    policy: CandidateEvaluationPolicy | None = None,
    training_loss: TrainingLossContext | None = None,
    protection_digest: str | None = P,
):
    base = _report(
        "base",
        A,
        rows=base_rows or _rows("base"),
        protection_digest=protection_digest,
    )
    candidate = _report(
        "candidate",
        B,
        rows=candidate_rows or _rows("candidate", target=(True, True)),
        protection_digest=protection_digest,
    )
    return BaseAdapterEvaluator().evaluate(
        base,
        candidate,
        binding=_binding(),
        policy=policy or _policy(),
        training_loss=training_loss or TrainingLossContext(0.2, 0.3),
    )


def test_target_gain_promotes_and_export_guard_opens() -> None:
    result = _evaluate()
    assert result.disposition is CandidateDisposition.PROMOTE_TO_EXPORT
    assert result.can_export is True
    assert result.aggregate_delta > 0
    assert result.target_gain == 1.0
    assert result.critical_regressions == ()
    result.require_exportable()


def test_critical_regression_rejects_even_when_aggregate_improves() -> None:
    base = _rows(
        "base",
        critical=(True, True),
        target=(False, False),
        general=(False, False),
    )
    candidate = _rows(
        "candidate",
        critical=(True, False),
        target=(True, True),
        general=(True, True),
    )
    result = _evaluate(base_rows=base, candidate_rows=candidate)
    assert result.aggregate_delta > 0
    assert result.disposition is CandidateDisposition.REJECT
    assert result.critical_regressions == ("critical",)
    assert "critical_regression" in result.reasons
    with pytest.raises(CandidateEvaluationError, match="cannot feed R15.11"):
        result.require_exportable()


def test_target_tie_is_inconclusive_not_promotable() -> None:
    result = _evaluate(
        base_rows=_rows("base", target=(True, False)),
        candidate_rows=_rows("candidate", target=(True, False)),
    )
    assert result.disposition is CandidateDisposition.INCONCLUSIVE
    assert result.target_gain == 0.0
    assert "target_gain_below_promotion_threshold" in result.reasons


@pytest.mark.parametrize(
    ("base_mutation", "candidate_mutation", "message"),
    [
        ("suite", None, "suite_digest differs"),
        ("config", None, "config_digest differs"),
        ("protection", None, "protection_manifest_digest differs"),
        (None, "model", "candidate report model digest"),
    ],
)
def test_mixed_suite_config_protection_or_model_identity_is_rejected(
    base_mutation: str | None,
    candidate_mutation: str | None,
    message: str,
) -> None:
    base = _report("base", A, rows=_rows("base"))
    candidate = _report("candidate", B, rows=_rows("candidate", target=(True, True)))

    if base_mutation == "suite":
        base["suite"] = {**dict(base["suite"]), "version": "different"}  # type: ignore[arg-type]
        base["suite_digest"] = _digest(base["suite"])
        base["report_digest"] = _digest({key: value for key, value in base.items() if key != "report_digest"})
    elif base_mutation == "config":
        base["config"] = {**dict(base["config"]), "temperature": 0.5}  # type: ignore[arg-type]
        base["config_digest"] = _digest(base["config"])
        base["report_digest"] = _digest({key: value for key, value in base.items() if key != "report_digest"})
    elif base_mutation == "protection":
        base["protection_manifest_digest"] = F
        base["report_digest"] = _digest({key: value for key, value in base.items() if key != "report_digest"})

    if candidate_mutation == "model":
        identities = list(candidate["model_identities"])  # type: ignore[arg-type]
        identities[0] = {**dict(identities[0]), "model_digest": F}
        candidate["model_identities"] = identities
        candidate["report_digest"] = _digest(
            {key: value for key, value in candidate.items() if key != "report_digest"}
        )

    with pytest.raises(CandidateEvaluationError, match=message):
        BaseAdapterEvaluator().evaluate(
            base,
            candidate,
            binding=_binding(),
            policy=_policy(),
            training_loss=TrainingLossContext(0.2, 0.3),
        )


def test_report_digest_tamper_and_pair_seed_drift_fail_closed() -> None:
    base = _report("base", A, rows=_rows("base"))
    candidate = _report("candidate", B, rows=_rows("candidate", target=(True, True)))

    tampered = deepcopy(candidate)
    rows = list(tampered["outcomes"])  # type: ignore[arg-type]
    rows[0] = {**dict(rows[0]), "passed": False}
    tampered["outcomes"] = rows
    with pytest.raises(CandidateEvaluationError, match="report digest does not match"):
        BaseAdapterEvaluator().evaluate(
            base,
            tampered,
            binding=_binding(),
            policy=_policy(),
            training_loss=TrainingLossContext(0.2, 0.3),
        )

    drifted = deepcopy(candidate)
    rows = list(drifted["outcomes"])  # type: ignore[arg-type]
    rows[0] = {**dict(rows[0]), "seed": 999}
    drifted["outcomes"] = rows
    drifted["report_digest"] = _digest(
        {key: value for key, value in drifted.items() if key != "report_digest"}
    )
    with pytest.raises(CandidateEvaluationError, match="same task/repeat/seed pairs"):
        BaseAdapterEvaluator().evaluate(
            base,
            drifted,
            binding=_binding(),
            policy=_policy(),
            training_loss=TrainingLossContext(0.2, 0.3),
        )


def test_duplicate_pair_is_rejected() -> None:
    candidate_rows = _rows("candidate", target=(True, True))
    candidate_rows.append(deepcopy(candidate_rows[0]))
    with pytest.raises(CandidateEvaluationError, match="duplicate task/repeat/seed"):
        _evaluate(candidate_rows=candidate_rows)


def test_latency_vram_and_error_budgets_hard_reject() -> None:
    result = _evaluate(
        base_rows=_rows("base", elapsed_s=1.0, vram_bytes=100),
        candidate_rows=_rows(
            "candidate",
            target=(True, True),
            elapsed_s=2.0,
            vram_bytes=200,
            error_task="general",
        ),
        policy=_policy(require_vram_evidence=True),
    )
    assert result.disposition is CandidateDisposition.REJECT
    assert {
        "error_budget_exceeded",
        "latency_budget_exceeded",
        "vram_budget_exceeded",
    }.issubset(result.reasons)


def test_instability_and_overfit_yield_inconclusive_without_hard_regression() -> None:
    candidate = _rows(
        "candidate",
        critical=(True, True),
        target=(True, False),
        general=(True, False),
    )
    result = _evaluate(
        base_rows=_rows(
            "base",
            critical=(True, True),
            target=(False, False),
            general=(False, False),
        ),
        candidate_rows=candidate,
        policy=_policy(max_score_stddev=0.1),
        training_loss=TrainingLossContext(0.1, 0.3),
    )
    assert result.disposition is CandidateDisposition.INCONCLUSIVE
    assert "candidate_instability" in result.reasons
    assert "validation_overfit_risk" in result.reasons
    assert result.overfit_risk is True


def test_missing_protected_benchmark_or_required_vram_is_inconclusive() -> None:
    no_protection = _evaluate(protection_digest=None)
    assert no_protection.disposition is CandidateDisposition.INCONCLUSIVE
    assert "protected_benchmark_evidence_missing" in no_protection.reasons

    no_vram = _evaluate(
        base_rows=_rows("base", vram_bytes=None),
        candidate_rows=_rows("candidate", target=(True, True), vram_bytes=None),
        policy=_policy(require_vram_evidence=True),
    )
    assert no_vram.disposition is CandidateDisposition.INCONCLUSIVE
    assert "vram_evidence_missing" in no_vram.reasons


def test_evaluation_is_deterministic_under_outcome_row_reordering() -> None:
    base_rows = _rows("base")
    candidate_rows = _rows("candidate", target=(True, True))
    first = _evaluate(base_rows=base_rows, candidate_rows=candidate_rows)

    base_report = _report("base", A, rows=list(reversed(base_rows)))
    candidate_report = _report("candidate", B, rows=list(reversed(candidate_rows)))
    second = BaseAdapterEvaluator().evaluate(
        base_report,
        candidate_report,
        binding=_binding(),
        policy=_policy(),
        training_loss=TrainingLossContext(0.2, 0.3),
    )
    assert first.task_deltas == second.task_deltas
    assert first.domain_deltas == second.domain_deltas
    assert first.disposition == second.disposition
    assert first.reasons == second.reasons


def test_saved_evaluation_validates_r15_10_schema(tmp_path: Path) -> None:
    base_path = tmp_path / "base.json"
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "evaluation.json"

    base_path.write_text(
        json.dumps(_report("base", A, rows=_rows("base")), sort_keys=True),
        encoding="utf-8",
    )
    candidate_path.write_text(
        json.dumps(
            _report("candidate", B, rows=_rows("candidate", target=(True, True))),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    result = evaluate_saved_reports(
        base_path,
        candidate_path,
        binding=_binding(),
        policy=_policy(),
        training_loss=TrainingLossContext(0.2, 0.3),
    )
    result.save(output_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    schema = json.loads(
        Path("schemas/r15-10-candidate-evaluation.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    assert payload["disposition"] == "promote_to_export"
    assert payload["can_export"] is True
    assert payload["binding_digest"] == result.binding.digest
    assert payload["policy_digest"] == result.policy.digest
    assert payload["evaluation_digest"] == result.digest
