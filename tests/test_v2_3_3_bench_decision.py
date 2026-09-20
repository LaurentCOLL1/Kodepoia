from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from kodepoia.bench.decision import (
    BackendCapability,
    BudgetStatus,
    DecisionEvidence,
    DiagnosticComponent,
    DiagnosticProbe,
    ExpectedImpact,
    GapDecisionEngine,
    ProbeStatus,
)
from kodepoia.bench.kodebench import (
    BenchmarkSuite,
    BenchmarkTaskSpec,
    KodeBenchRunner,
    ModelIdentity,
    RunConfig,
    ScorerKind,
    ScorerSpec,
)
from kodepoia.brain.base import BrainResponse
from kodepoia.experience.contracts import PolicyDecision
from kodepoia.kodestudio.model_lab_bench import ModelLabBenchDecisionService
from kodepoia.tuning.r15_ux import R15UXPolicyError, R15UXService, R15WorkflowRequest


class FakeBrain:
    def preload(self, model: str, **kwargs: object) -> dict[str, object]:
        return {"done_reason": "load"}

    def unload(self, model: str) -> None:
        return None

    def running_models(self) -> list[dict[str, object]]:
        return []

    def show_model(self, model: str) -> dict[str, object]:
        return {"capabilities": ["completion"]}

    def chat(self, model: str, messages: list[object], **kwargs: object) -> BrainResponse:
        prompt = str(messages[0].content)
        return BrainResponse(
            "WRONG" if "gap" in prompt else "OK",
            model,
            metrics={"eval_count": 1, "eval_duration": 1_000_000_000},
        )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _suite() -> BenchmarkSuite:
    return BenchmarkSuite(
        "v233-fixture",
        "v1",
        (
            BenchmarkTaskSpec(
                task_id="python-gap",
                domain="python",
                critical=True,
                prompt="gap prompt never persisted raw",
                scorer=ScorerSpec.create(
                    ScorerKind.EXACT,
                    version="fixture-v1",
                    config={"expected": "OK"},
                ),
            ),
        ),
    )


def _evidence(
    *,
    prompt_status: ProbeStatus = ProbeStatus.PASS,
) -> DecisionEvidence:
    components = (
        DiagnosticComponent.TOOL,
        DiagnosticComponent.RETRIEVAL,
        DiagnosticComponent.ROUTER,
        DiagnosticComponent.CONTEXT,
        DiagnosticComponent.PROMPT,
        DiagnosticComponent.PRODUCT,
    )
    probes = tuple(
        DiagnosticProbe(
            component=component,
            status=prompt_status if component is DiagnosticComponent.PROMPT else ProbeStatus.PASS,
            evidence_digest=_digest(f"probe:{component.value}"),
            affected_domains=("python",)
            if component is DiagnosticComponent.PROMPT and prompt_status is ProbeStatus.DEFECT
            else (),
        )
        for component in components
    )
    return DecisionEvidence(
        benchmark_reproducible=True,
        contamination_valid=True,
        dataset_license=PolicyDecision.ALLOW,
        base_model_license=PolicyDecision.ALLOW,
        backend_capability=BackendCapability.SUPPORTED,
        budget_status=BudgetStatus.WITHIN_BUDGET,
        rollback_ready=True,
        expected_impact=ExpectedImpact.MEANINGFUL,
        diagnostics=probes,
        evidence_digests=(("system", _digest("system")),),
    )


def _dataset() -> dict[str, object]:
    return {
        "dataset_id": "fixture-dataset",
        "dataset_digest": _digest("dataset"),
        "entries": [
            {"domain": "python", "example_id": f"example-{index}", "split": "train"}
            for index in range(4)
        ],
    }


def _project(tmp_path: Path) -> tuple[Path, str, str]:
    root = tmp_path / "project"
    evidence_root = root / ".kodepoia" / "benchmarks"
    evidence_root.mkdir(parents=True)

    report = KodeBenchRunner(FakeBrain()).run(
        ["base", "fixture-peer"],
        _suite(),
        config=RunConfig(repeats=2),
        identities={
            "base": ModelIdentity(
                "base",
                _digest("base-model"),
                runtime="fixture",
                runtime_version="1",
            ),
            "fixture-peer": ModelIdentity(
                "fixture-peer",
                _digest("fixture-peer-model"),
                runtime="fixture",
                runtime_version="1",
            ),
        },
    )
    report_path = evidence_root / "baseline.json"
    report.save(report_path)
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))

    decision = GapDecisionEngine().evaluate(
        report_payload,
        base_model_ref="base",
        evidence=_evidence(),
        dataset=_dataset(),
    )
    decision_path = evidence_root / "decision.json"
    decision.save(decision_path)
    return root, report.digest, decision.digest


def test_snapshot_exposes_structured_bench_and_exact_decision_lineage(tmp_path: Path) -> None:
    root, report_digest, decision_digest = _project(tmp_path)
    snapshot = ModelLabBenchDecisionService(root).snapshot()

    assert snapshot["schema"] == ModelLabBenchDecisionService.schema
    assert snapshot["summary"]["report_count"] == 1
    assert snapshot["summary"]["decision_count"] == 1

    report = snapshot["reports"][0]
    assert report["integrity"] == "ready"
    assert report["report_digest"] == report_digest
    assert report["raw_prompts_exposed"] is False
    assert report["raw_responses_exposed"] is False
    assert report["models"][0]["model_digest"] == _digest("base-model")
    assert report["task_results"][0]["domain"] == "python"
    assert report["task_results"][0]["score"] == 0.0
    assert len(str(report["suite_tasks"][0]["scorer_digest"])) == 64

    decision = snapshot["decisions"][0]
    assert decision["decision_digest"] == decision_digest
    assert decision["integrity"] == "ready"
    assert decision["benchmark_bound"] is True
    assert decision["dataset_bound"] is True
    assert decision["disposition"] == "train"
    assert decision["target_domains"] == ["python"]
    assert decision["train_evidence_bound"] is True
    assert decision["training_launch_exposed"] is False
    components = {item["component"]: item["status"] for item in decision["diagnostics"]}
    assert components["tool"] == "pass"
    assert components["prompt"] == "pass"
    assert components["product"] == "pass"


def test_prompt_defect_uses_existing_gap_engine_and_blocks_training(tmp_path: Path) -> None:
    root, _report_digest, _decision_digest = _project(tmp_path)
    report_payload = json.loads(
        (root / ".kodepoia" / "benchmarks" / "baseline.json").read_text(encoding="utf-8")
    )
    decision = GapDecisionEngine().evaluate(
        report_payload,
        base_model_ref="base",
        evidence=_evidence(prompt_status=ProbeStatus.DEFECT),
        dataset=_dataset(),
    )
    assert decision.disposition.value == "fix_system_first"
    assert decision.blockers == ("system_defect:prompt",)
    assert decision.adapter_method is None


def test_tampered_report_and_decision_are_explicit_and_fail_binding(tmp_path: Path) -> None:
    root, _report_digest, _decision_digest = _project(tmp_path)
    report_path = root / ".kodepoia" / "benchmarks" / "baseline.json"
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    report_payload["config"]["temperature"] = 0.5
    report_path.write_text(json.dumps(report_payload), encoding="utf-8")

    decision_path = root / ".kodepoia" / "benchmarks" / "decision.json"
    decision_payload = json.loads(decision_path.read_text(encoding="utf-8"))
    decision_payload["reasons"] = ["tampered"]
    decision_path.write_text(json.dumps(decision_payload), encoding="utf-8")

    snapshot = ModelLabBenchDecisionService(root).snapshot()
    assert snapshot["reports"][0]["integrity"] == "tampered"
    decision = snapshot["decisions"][0]
    assert decision["integrity"] == "tampered"
    assert decision["benchmark_bound"] is False
    assert decision["train_evidence_bound"] is False


def test_typed_r15_actions_preserve_dry_run_confirmation_and_no_training_surface(
    tmp_path: Path,
) -> None:
    root, _report_digest, decision_digest = _project(tmp_path)
    calls: list[R15WorkflowRequest] = []

    def handler(request: R15WorkflowRequest) -> dict[str, object]:
        calls.append(request)
        return {"status": "ok", "decision_id": request.identifier, "secret": "hidden"}

    r15 = R15UXService(
        root,
        handlers={
            "bench.status": handler,
            "bench.run": handler,
            "gap.diagnose": handler,
        },
    )
    service = ModelLabBenchDecisionService(root, r15_service=r15)

    preview = service.preview_benchmark_run()
    assert preview["status"] == "dry_run"
    assert preview["would_mutate"] is True
    assert calls == []

    with pytest.raises(R15UXPolicyError, match="confirmation"):
        service.run_benchmark(confirmed=False)
    assert calls == []

    applied = service.run_benchmark(confirmed=True)
    assert applied["workflow"] == "bench.run"
    assert len(calls) == 1 and calls[0].key == "bench.run"

    inspected = service.inspect_gap_decision(decision_digest)
    assert inspected["workflow"] == "gap.diagnose"
    assert inspected["secret"] == "<redacted>"

    snapshot = service.snapshot()
    assert snapshot["mutations"]["benchmark_run"] is True
    assert snapshot["mutations"]["training"] is False
    assert snapshot["mutations"]["conversion"] is False
    assert snapshot["mutations"]["promotion"] is False
    assert snapshot["reference_context"]["instruction_authority"] is False
    assert snapshot["reference_context"]["auto_training_ingest"] is False


def test_cross_project_r15_binding_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "project-a"
    other = tmp_path / "project-b"
    with pytest.raises(ValueError, match="project root"):
        ModelLabBenchDecisionService(root, r15_service=R15UXService(other))
