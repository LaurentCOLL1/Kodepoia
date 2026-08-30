from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from kodepoia.bench.baseline import BenchTask
from kodepoia.bench.kodebench import (
    BenchmarkSuite,
    BenchmarkTaskSpec,
    KodeBenchError,
    KodeBenchRunner,
    ModelIdentity,
    OutcomeCategory,
    RepositoryScorerRegistry,
    RunConfig,
    ScorerKind,
    ScorerSpec,
    baseline_compat_suite,
    compare_report_payloads,
    compare_saved_reports,
)
from kodepoia.brain.base import BrainResponse
from kodepoia.experience.dedup import (
    DedupPolicy,
    ProtectedHoldout,
    ProtectedHoldoutRegistry,
)


class FakeBrain:
    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def preload(self, model: str, **kwargs: object) -> dict[str, object]:
        return {
            "done_reason": "load",
            "load_duration": 500_000_000,
            "total_duration": 550_000_000,
        }

    def unload(self, model: str) -> None:
        return None

    def running_models(self) -> list[dict[str, object]]:
        return [
            {
                "name": "candidate",
                "size": 1234,
                "size_vram": 512,
                "details": {"family": "fixture", "parameter_size": "tiny"},
            }
        ]

    def show_model(self, model: str) -> dict[str, object]:
        return {"capabilities": ["completion"], "details": {"family": "fixture"}}

    def chat(self, model: str, messages: list[object], **kwargs: object) -> BrainResponse:
        prompt = str(messages[0].content)
        self.calls.append((model, prompt, kwargs))
        content = self.responses.get(f"{model}:{prompt}", self.responses.get(prompt, "OK"))
        tool_calls = ()
        if "tool please" in prompt:
            tool_calls = ({"function": {"name": "fixture_tool", "arguments": {}}},)
        return BrainResponse(
            content,
            model,
            tool_calls=tool_calls,
            metrics={
                "eval_count": 4,
                "eval_duration": 1_000_000_000,
                "load_duration": 100_000_000,
                "total_duration": 1_500_000_000,
            },
        )


def _exact_task(
    task_id: str,
    prompt: str,
    expected: str,
    *,
    domain: str = "general",
    critical: bool = False,
    protected_holdout_id: str | None = None,
) -> BenchmarkTaskSpec:
    return BenchmarkTaskSpec(
        task_id=task_id,
        domain=domain,
        critical=critical,
        prompt=prompt,
        scorer=ScorerSpec.create(
            ScorerKind.EXACT,
            version="fixture-v1",
            config={"expected": expected},
        ),
        protected_holdout_id=protected_holdout_id,
    )


def test_suite_and_scorer_digests_are_deterministic_and_order_independent() -> None:
    first = _exact_task("a", "prompt-a", "A", domain="python", critical=True)
    second = BenchmarkTaskSpec(
        task_id="b",
        domain="structured",
        critical=False,
        prompt="prompt-b",
        scorer=ScorerSpec.create(
            ScorerKind.REGEX,
            version="fixture-v1",
            config={"pattern": r"^B+$"},
        ),
    )
    left = BenchmarkSuite("suite", "v1", (first, second))
    right = BenchmarkSuite("suite", "v1", (second, first))
    assert left.digest == right.digest
    assert first.digest == _exact_task(
        "a",
        "prompt-a",
        "A",
        domain="python",
        critical=True,
    ).digest
    same = _exact_task(
        "a",
        "prompt-a",
        "A",
        domain="python",
        critical=True,
    )
    assert first.scorer.digest == same.scorer.digest


def test_scorer_config_must_be_canonical_json() -> None:
    with pytest.raises(KodeBenchError, match="canonical JSON"):
        ScorerSpec(ScorerKind.EXACT, "v1", '{"expected": "OK"}')


def test_runner_scores_domains_critical_tasks_and_resource_metrics() -> None:
    suite = BenchmarkSuite(
        "fixture-suite",
        "v1",
        (
            _exact_task("critical", "critical prompt", "YES", domain="python", critical=True),
            BenchmarkTaskSpec(
                task_id="regex",
                domain="godot",
                critical=False,
                prompt="regex prompt",
                scorer=ScorerSpec.create(
                    ScorerKind.REGEX,
                    version="fixture-v1",
                    config={"pattern": r"^GODOT4$"},
                ),
            ),
        ),
    )
    brain = FakeBrain(
        {
            "critical prompt": "YES",
            "regex prompt": "GODOT4",
        }
    )
    report = KodeBenchRunner(brain).run(
        ["candidate", "base"],
        suite,
        config=RunConfig(repeats=2),
        identities={
            "candidate": ModelIdentity(
                "candidate",
                "a" * 64,
                runtime="fixture",
                runtime_version="1",
            ),
            "base": ModelIdentity(
                "base",
                "b" * 64,
                runtime="fixture",
                runtime_version="1",
            ),
        },
    )
    assert len(report.outcomes) == 8
    assert all(item.passed for item in report.outcomes)
    summary = report.summary()
    candidate = summary["candidate"]
    assert candidate["score"] == 1.0
    assert candidate["critical_score"] == 1.0
    assert candidate["domains"]["godot"]["score"] == 1.0
    assert candidate["domains"]["python"]["score"] == 1.0
    assert candidate["tokens_per_second_mean"] == 4.0
    resource = next(item.resources for item in report.outcomes if item.model_ref == "candidate")
    assert resource.load_s == 0.1
    assert resource.total_s == 1.5
    assert resource.vram_bytes == 512
    assert resource.model_size_bytes == 1234


def test_json_schema_tool_call_and_contains_scorers() -> None:
    tool = {"type": "function", "function": {"name": "fixture_tool", "parameters": {}}}
    suite = BenchmarkSuite(
        "multi-scorer",
        "v1",
        (
            BenchmarkTaskSpec(
                "json",
                "structured",
                True,
                "json prompt",
                ScorerSpec.create(
                    ScorerKind.JSON_SCHEMA,
                    version="v1",
                    config={
                        "schema": {
                            "type": "object",
                            "properties": {"status": {"type": "string", "enum": ["ok"]}},
                            "required": ["status"],
                            "additionalProperties": False,
                        }
                    },
                ),
            ),
            BenchmarkTaskSpec(
                "tool",
                "tools",
                True,
                "tool please",
                ScorerSpec.create(ScorerKind.TOOL_CALL, version="v1"),
                tools=(tool,),
            ),
            BenchmarkTaskSpec(
                "contains",
                "general",
                False,
                "contains prompt",
                ScorerSpec.create(
                    ScorerKind.CONTAINS,
                    version="v1",
                    config={"expected": ["safe"], "forbidden": ["unsafe"]},
                ),
            ),
        ),
    )
    report = KodeBenchRunner(
        FakeBrain(
            {
                "json prompt": '{"status":"ok"}',
                "contains prompt": "SAFE response",
                "tool please": "",
            }
        )
    ).run(["base", "candidate"], suite)
    assert all(item.passed for item in report.outcomes)


def test_custom_scorer_failure_is_isolated_from_model_failure() -> None:
    registry = RepositoryScorerRegistry()

    def exploding(
        content: str,
        task: BenchmarkTaskSpec,
        legacy: object,
    ) -> bool:
        raise RuntimeError("fixture scorer exploded")

    registry.register("explode", "v1", exploding)
    suite = BenchmarkSuite(
        "custom-suite",
        "v1",
        (
            _exact_task("good", "good prompt", "OK"),
            BenchmarkTaskSpec(
                "custom",
                "custom",
                False,
                "custom prompt",
                ScorerSpec.create(
                    ScorerKind.CUSTOM,
                    name="explode",
                    version="v1",
                ),
            ),
        ),
    )
    report = KodeBenchRunner(FakeBrain(), custom_scorers=registry).run(
        ["base", "candidate"],
        suite,
    )
    custom_rows = [item for item in report.outcomes if item.task_id == "custom"]
    good_rows = [item for item in report.outcomes if item.task_id == "good"]
    assert all(item.category is OutcomeCategory.SCORER_FAILURE for item in custom_rows)
    assert all(not item.passed for item in custom_rows)
    assert all(item.category is OutcomeCategory.PASS for item in good_rows)
    assert report.summary()["base"]["scorer_failures"] == 1
    assert report.summary()["base"]["model_failures"] == 0


def test_protected_holdout_binding_fails_closed_and_report_has_no_raw_prompt(
    tmp_path: Path,
) -> None:
    policy = DedupPolicy()
    registry = ProtectedHoldoutRegistry(policy.digest)
    registry.register(ProtectedHoldout.from_text("holdout-alpha", "SECRET_HOLDOUT_TEXT", policy))
    suite = BenchmarkSuite(
        "protected",
        "v1",
        (
            _exact_task(
                "protected-task",
                "SECRET_HOLDOUT_TEXT",
                "OK",
                critical=True,
                protected_holdout_id="holdout-alpha",
            ),
        ),
    )
    with pytest.raises(KodeBenchError, match="holdout registry"):
        KodeBenchRunner(FakeBrain()).run(["base", "candidate"], suite)

    report = KodeBenchRunner(FakeBrain()).run(
        ["base", "candidate"],
        suite,
        holdout_registry=registry,
    )
    destination = tmp_path / "report.json"
    report.save(destination)
    text = destination.read_text(encoding="utf-8")
    assert "SECRET_HOLDOUT_TEXT" not in text
    payload = json.loads(text)
    schema = json.loads(
        Path("schemas/kodebench-v2-report.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)
    assert payload["protection_manifest_digest"] == suite.validate_protected_holdouts(
        registry
    )
    assert payload["suite"]["tasks"][0]["protected_holdout_id"] == "holdout-alpha"
    assert len(payload["suite"]["tasks"][0]["prompt_digest"]) == 64


def test_missing_registered_holdout_id_is_rejected() -> None:
    policy = DedupPolicy()
    registry = ProtectedHoldoutRegistry(policy.digest)
    suite = BenchmarkSuite(
        "protected",
        "v1",
        (
            _exact_task(
                "protected-task",
                "prompt",
                "OK",
                protected_holdout_id="missing",
            ),
        ),
    )
    with pytest.raises(KodeBenchError, match="absent"):
        suite.validate_protected_holdouts(registry)


def test_baseline_compat_suite_preserves_r3_task_contracts() -> None:
    legacy = (
        BenchTask("exact", "reply", exact_response="OK"),
        BenchTask("regex", "regex", response_regex=r"^OK$"),
        BenchTask("contains", "contains", ("yes",), ("no",)),
    )
    suite = baseline_compat_suite(legacy)
    assert [task.task_id for task in suite.tasks] == ["exact", "regex", "contains"]
    assert [task.scorer.kind for task in suite.tasks] == [
        ScorerKind.EXACT,
        ScorerKind.REGEX,
        ScorerKind.CONTAINS,
    ]


def test_compare_reports_detects_critical_regression_and_rejects_mismatch(
    tmp_path: Path,
) -> None:
    suite = BenchmarkSuite(
        "compare-suite",
        "v1",
        (
            _exact_task("critical", "critical", "OK", critical=True),
            _exact_task("normal", "normal", "OK"),
        ),
    )
    base = KodeBenchRunner(FakeBrain()).run(["base", "other"], suite)
    candidate = KodeBenchRunner(
        FakeBrain({"candidate:critical": "WRONG"})
    ).run(["candidate", "other"], suite)

    comparison = compare_report_payloads(
        base.safe_descriptor(),
        candidate.safe_descriptor(),
        base_model="base",
        candidate_model="candidate",
    )
    assert comparison["comparable"] is True
    assert comparison["critical_regressions"] == ["critical"]
    assert comparison["task_deltas"]["critical"]["delta"] == -1.0

    base_path = tmp_path / "base.json"
    candidate_path = tmp_path / "candidate.json"
    base.save(base_path)
    candidate.save(candidate_path)
    assert compare_saved_reports(
        base_path,
        candidate_path,
        base_model="base",
        candidate_model="candidate",
    )["critical_regressions"] == ["critical"]

    incompatible = dict(candidate.safe_descriptor())
    incompatible["config_digest"] = "f" * 64
    with pytest.raises(KodeBenchError, match="config_digest differs"):
        compare_report_payloads(
            base.safe_descriptor(),
            incompatible,
            base_model="base",
            candidate_model="candidate",
        )
