from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from kodepoia.bench.baseline import (
    DEFAULT_TASKS,
    BaselineBench,
    BenchmarkRole,
    BenchResult,
    BenchTask,
)
from kodepoia.experience.dedup import ProtectedHoldoutRegistry

KODEBENCH_SCHEMA = "kodepoia.kodebench.v2.report"
KODEBENCH_SCHEMA_VERSION = 1
KODEBENCH_SUITE_VERSION = "r15.6-kodebench-v2"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class KodeBenchError(ValueError):
    """Base error for KodeBench v2 registry, scoring and comparison failures."""


class ScorerKind(StrEnum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    JSON_SCHEMA = "json_schema"
    TOOL_CALL = "tool_call"
    CUSTOM = "custom"


class OutcomeCategory(StrEnum):
    PASS = "pass"
    MODEL_FAILURE = "model_failure"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    SCORER_FAILURE = "scorer_failure"
    WRONG_ANSWER = "wrong_answer"


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require_safe_id(label: str, value: str) -> None:
    if _SAFE_ID.fullmatch(value) is None:
        raise KodeBenchError(f"{label} must be a stable safe identifier")


def _require_digest(label: str, value: str) -> None:
    if _DIGEST.fullmatch(value) is None:
        raise KodeBenchError(f"{label} must be 64 lowercase hex characters")


@dataclass(frozen=True, slots=True)
class ScorerSpec:
    kind: ScorerKind
    version: str
    config_json: str = "{}"
    name: str = "builtin"

    def __post_init__(self) -> None:
        _require_safe_id("scorer version", self.version)
        _require_safe_id("scorer name", self.name)
        try:
            config = json.loads(self.config_json)
        except json.JSONDecodeError as exc:
            raise KodeBenchError("scorer config_json must contain valid JSON") from exc
        if not isinstance(config, dict):
            raise KodeBenchError("scorer config_json must encode an object")
        if self.config_json != _canonical_json(config):
            raise KodeBenchError("scorer config_json must use canonical JSON")

    @classmethod
    def create(
        cls,
        kind: ScorerKind | str,
        *,
        version: str = "1",
        name: str = "builtin",
        config: Mapping[str, object] | None = None,
    ) -> ScorerSpec:
        return cls(
            kind=ScorerKind(kind),
            version=version,
            name=name,
            config_json=_canonical_json(dict(config or {})),
        )

    @property
    def config(self) -> dict[str, object]:
        return dict(json.loads(self.config_json))

    def descriptor(self) -> dict[str, object]:
        return {
            "config": self.config,
            "kind": self.kind.value,
            "name": self.name,
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


@dataclass(frozen=True, slots=True)
class BenchmarkTaskSpec:
    task_id: str
    domain: str
    critical: bool
    prompt: str
    scorer: ScorerSpec
    tools: tuple[Mapping[str, object], ...] = ()
    protected_holdout_id: str | None = None

    def __post_init__(self) -> None:
        _require_safe_id("task_id", self.task_id)
        _require_safe_id("domain", self.domain)
        if not self.prompt:
            raise KodeBenchError("benchmark prompt must not be empty")
        if self.protected_holdout_id is not None:
            _require_safe_id("protected_holdout_id", self.protected_holdout_id)
        for tool in self.tools:
            if not isinstance(tool, Mapping):
                raise KodeBenchError("task tools must be mappings")
            _canonical_json(dict(tool))

    @property
    def prompt_digest(self) -> str:
        return _text_digest(self.prompt)

    @property
    def tools_digest(self) -> str:
        return _digest([dict(tool) for tool in self.tools])

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "critical": self.critical,
            "domain": self.domain,
            "prompt_digest": self.prompt_digest,
            "protected_holdout_id": self.protected_holdout_id,
            "scorer": self.scorer.descriptor(),
            "scorer_digest": self.scorer.digest,
            "task_id": self.task_id,
            "tools_digest": self.tools_digest,
        }

    @property
    def digest(self) -> str:
        return _digest(self.safe_descriptor())


@dataclass(frozen=True, slots=True)
class BenchmarkSuite:
    suite_id: str
    version: str
    tasks: tuple[BenchmarkTaskSpec, ...]

    def __post_init__(self) -> None:
        _require_safe_id("suite_id", self.suite_id)
        _require_safe_id("suite version", self.version)
        if not self.tasks:
            raise KodeBenchError("benchmark suite must contain at least one task")
        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise KodeBenchError("benchmark task_id values must be unique")

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "suite_id": self.suite_id,
            "tasks": [
                task.safe_descriptor()
                for task in sorted(self.tasks, key=lambda item: item.task_id)
            ],
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return _digest(self.safe_descriptor())

    def task(self, task_id: str) -> BenchmarkTaskSpec:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise KodeBenchError(f"unknown benchmark task: {task_id}")

    def validate_protected_holdouts(
        self,
        registry: ProtectedHoldoutRegistry,
    ) -> str:
        registered = {item.holdout_id for item in registry.entries()}
        required = {
            task.protected_holdout_id
            for task in self.tasks
            if task.protected_holdout_id is not None
        }
        missing = sorted(required - registered)
        if missing:
            raise KodeBenchError(
                "suite references holdout ids absent from R15.4 registry: "
                + ", ".join(missing)
            )
        return _digest(registry.safe_manifest())


@dataclass(frozen=True, slots=True)
class RunConfig:
    role: BenchmarkRole = BenchmarkRole.BASELINE
    repeats: int = 1
    seed_base: int = 101
    temperature: float = 0.0
    num_predict: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "role", BenchmarkRole(self.role))
        if not 1 <= self.repeats <= 8:
            raise KodeBenchError("repeats must be between 1 and 8")
        if not isinstance(self.seed_base, int):
            raise KodeBenchError("seed_base must be an integer")
        if not math.isfinite(self.temperature) or self.temperature < 0:
            raise KodeBenchError("temperature must be finite and >= 0")
        if self.num_predict is not None and self.num_predict <= 0:
            raise KodeBenchError("num_predict must be > 0")

    @property
    def resolved_num_predict(self) -> int:
        if self.num_predict is not None:
            return self.num_predict
        return BaselineBench.num_predict_for_role(self.role)

    def descriptor(self) -> dict[str, object]:
        return {
            "num_predict": self.resolved_num_predict,
            "repeats": self.repeats,
            "role": self.role.value,
            "seed_base": self.seed_base,
            "temperature": self.temperature,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


@dataclass(frozen=True, slots=True)
class ModelIdentity:
    model_ref: str
    model_digest: str | None = None
    runtime: str = "unknown"
    runtime_version: str = "unknown"

    def __post_init__(self) -> None:
        if not self.model_ref:
            raise KodeBenchError("model_ref must not be empty")
        if self.model_digest is not None:
            _require_digest("model_digest", self.model_digest)
        if not self.runtime:
            raise KodeBenchError("runtime must not be empty")
        if not self.runtime_version:
            raise KodeBenchError("runtime_version must not be empty")

    @property
    def resolved(self) -> bool:
        return self.model_digest is not None

    def descriptor(self) -> dict[str, object]:
        return {
            "model_digest": self.model_digest,
            "model_ref": self.model_ref,
            "resolved": self.resolved,
            "runtime": self.runtime,
            "runtime_version": self.runtime_version,
        }


@dataclass(frozen=True, slots=True)
class ResourceMetrics:
    elapsed_s: float
    tokens_per_second: float | None
    load_s: float | None
    total_s: float | None
    eval_count: int | None
    prompt_eval_count: int | None
    vram_bytes: int | None
    model_size_bytes: int | None

    @classmethod
    def from_legacy(cls, result: BenchResult) -> ResourceMetrics:
        metrics = result.metrics

        def seconds(key: str) -> float | None:
            value = metrics.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                return float(value) / 1_000_000_000.0
            return None

        def integer(key: str) -> int | None:
            value = metrics.get(key)
            if isinstance(value, int) and value >= 0:
                return value
            return None

        return cls(
            elapsed_s=result.elapsed_s,
            tokens_per_second=result.tokens_per_second,
            load_s=seconds("load_duration"),
            total_s=seconds("total_duration"),
            eval_count=integer("eval_count"),
            prompt_eval_count=integer("prompt_eval_count"),
            vram_bytes=integer("ollama_size_vram"),
            model_size_bytes=integer("ollama_size"),
        )

    def descriptor(self) -> dict[str, object]:
        return {
            "elapsed_s": self.elapsed_s,
            "eval_count": self.eval_count,
            "load_s": self.load_s,
            "model_size_bytes": self.model_size_bytes,
            "prompt_eval_count": self.prompt_eval_count,
            "tokens_per_second": self.tokens_per_second,
            "total_s": self.total_s,
            "vram_bytes": self.vram_bytes,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkOutcome:
    model_ref: str
    task_id: str
    domain: str
    critical: bool
    repeat: int
    seed: int
    passed: bool
    category: OutcomeCategory
    scorer_digest: str
    response_digest: str
    resources: ResourceMetrics
    error: str | None = None

    def __post_init__(self) -> None:
        _require_safe_id("task_id", self.task_id)
        _require_safe_id("domain", self.domain)
        _require_digest("scorer_digest", self.scorer_digest)
        _require_digest("response_digest", self.response_digest)

    def descriptor(self) -> dict[str, object]:
        return {
            "category": self.category.value,
            "critical": self.critical,
            "domain": self.domain,
            "error": self.error,
            "model_ref": self.model_ref,
            "passed": self.passed,
            "repeat": self.repeat,
            "resources": self.resources.descriptor(),
            "response_digest": self.response_digest,
            "scorer_digest": self.scorer_digest,
            "seed": self.seed,
            "task_id": self.task_id,
        }


ScorerFunction = Callable[[str, BenchmarkTaskSpec, BenchResult], bool]


class RepositoryScorerRegistry:
    """Code-owned scorer registry; benchmark data cannot import arbitrary callables."""

    def __init__(self) -> None:
        self._scorers: dict[tuple[str, str], ScorerFunction] = {}

    def register(self, name: str, version: str, scorer: ScorerFunction) -> None:
        _require_safe_id("custom scorer name", name)
        _require_safe_id("custom scorer version", version)
        key = (name, version)
        if key in self._scorers and self._scorers[key] is not scorer:
            raise KodeBenchError(f"custom scorer already registered: {name}@{version}")
        self._scorers[key] = scorer

    def score(
        self,
        spec: ScorerSpec,
        content: str,
        task: BenchmarkTaskSpec,
        legacy: BenchResult,
    ) -> bool:
        key = (spec.name, spec.version)
        try:
            scorer = self._scorers[key]
        except KeyError as exc:
            raise KodeBenchError(
                f"repository custom scorer is not registered: {spec.name}@{spec.version}"
            ) from exc
        return bool(scorer(content, task, legacy))


def _score_json_schema(content: str, schema: Mapping[str, object]) -> bool:
    return BaselineBench._structured_matches(content, dict(schema))


def score_response(
    task: BenchmarkTaskSpec,
    content: str,
    legacy: BenchResult,
    custom_scorers: RepositoryScorerRegistry | None = None,
) -> bool:
    spec = task.scorer
    config = spec.config
    if spec.kind is ScorerKind.EXACT:
        expected = config.get("expected")
        if not isinstance(expected, str):
            raise KodeBenchError("exact scorer requires string 'expected'")
        return content.strip() == expected
    if spec.kind is ScorerKind.CONTAINS:
        expected = config.get("expected", [])
        forbidden = config.get("forbidden", [])
        if not isinstance(expected, list) or not all(isinstance(item, str) for item in expected):
            raise KodeBenchError("contains scorer expected must be a string list")
        if not isinstance(forbidden, list) or not all(
            isinstance(item, str) for item in forbidden
        ):
            raise KodeBenchError("contains scorer forbidden must be a string list")
        lowered = content.strip().lower()
        return all(item.lower() in lowered for item in expected) and not any(
            item.lower() in lowered for item in forbidden
        )
    if spec.kind is ScorerKind.REGEX:
        pattern = config.get("pattern")
        if not isinstance(pattern, str):
            raise KodeBenchError("regex scorer requires string 'pattern'")
        return re.search(pattern, content.strip()) is not None
    if spec.kind is ScorerKind.JSON_SCHEMA:
        schema = config.get("schema")
        if not isinstance(schema, dict):
            raise KodeBenchError("json_schema scorer requires object 'schema'")
        return _score_json_schema(content, schema)
    if spec.kind is ScorerKind.TOOL_CALL:
        return legacy.tool_called is True
    if spec.kind is ScorerKind.CUSTOM:
        if custom_scorers is None:
            raise KodeBenchError("custom scorer registry is required")
        return custom_scorers.score(spec, content, task, legacy)
    raise KodeBenchError(f"unsupported scorer kind: {spec.kind}")


def _legacy_task(task: BenchmarkTaskSpec) -> BenchTask:
    spec = task.scorer
    config = spec.config
    kwargs: dict[str, object] = {}
    if spec.kind is ScorerKind.EXACT:
        kwargs["exact_response"] = config.get("expected")
    elif spec.kind is ScorerKind.CONTAINS:
        kwargs["expected_contains"] = tuple(config.get("expected", []))
        kwargs["forbidden_contains"] = tuple(config.get("forbidden", []))
    elif spec.kind is ScorerKind.REGEX:
        kwargs["response_regex"] = config.get("pattern")
    elif spec.kind is ScorerKind.JSON_SCHEMA:
        kwargs["response_schema"] = config.get("schema")
    elif spec.kind is ScorerKind.TOOL_CALL:
        kwargs["expect_tool_call"] = True
    return BenchTask(
        id=task.task_id,
        prompt=task.prompt,
        tools=tuple(dict(tool) for tool in task.tools),
        **kwargs,
    )


class KodeBenchRunner:
    def __init__(
        self,
        client: object,
        *,
        custom_scorers: RepositoryScorerRegistry | None = None,
    ) -> None:
        self.client = client
        self.custom_scorers = custom_scorers

    def run(
        self,
        models: Sequence[str],
        suite: BenchmarkSuite,
        *,
        config: RunConfig | None = None,
        identities: Mapping[str, ModelIdentity] | None = None,
        holdout_registry: ProtectedHoldoutRegistry | None = None,
    ) -> KodeBenchReport:
        resolved_config = config or RunConfig()
        protection_digest = None
        if any(task.protected_holdout_id for task in suite.tasks):
            if holdout_registry is None:
                raise KodeBenchError(
                    "protected benchmark suite requires the R15.4 holdout registry"
                )
            protection_digest = suite.validate_protected_holdouts(holdout_registry)

        legacy_tasks = tuple(_legacy_task(task) for task in suite.tasks)
        legacy_results = BaselineBench(self.client, legacy_tasks).run(
            list(models),
            role=resolved_config.role,
            repeats=resolved_config.repeats,
            seed_base=resolved_config.seed_base,
            temperature=resolved_config.temperature,
            num_predict=resolved_config.resolved_num_predict,
        )
        outcomes: list[BenchmarkOutcome] = []
        for legacy in legacy_results:
            task = suite.task(legacy.task_id)
            response_digest = _text_digest(legacy.response)
            category: OutcomeCategory
            passed = False
            error = legacy.error
            if legacy.error is not None:
                lowered_error = legacy.error.lower()
                if "unsupported" in lowered_error or "unavailable" in lowered_error:
                    category = OutcomeCategory.CAPABILITY_UNAVAILABLE
                else:
                    category = OutcomeCategory.MODEL_FAILURE
            else:
                try:
                    passed = score_response(
                        task,
                        legacy.response,
                        legacy,
                        custom_scorers=self.custom_scorers,
                    )
                except Exception as exc:
                    category = OutcomeCategory.SCORER_FAILURE
                    error = f"{type(exc).__name__}: {exc}"
                else:
                    category = OutcomeCategory.PASS if passed else OutcomeCategory.WRONG_ANSWER
            outcomes.append(
                BenchmarkOutcome(
                    model_ref=legacy.model,
                    task_id=task.task_id,
                    domain=task.domain,
                    critical=task.critical,
                    repeat=legacy.repeat,
                    seed=legacy.seed,
                    passed=passed,
                    category=category,
                    scorer_digest=task.scorer.digest,
                    response_digest=response_digest,
                    resources=ResourceMetrics.from_legacy(legacy),
                    error=error,
                )
            )

        resolved_identities: list[ModelIdentity] = []
        for model in dict.fromkeys(models):
            identity = identities.get(model) if identities is not None else None
            if identity is None:
                identity = ModelIdentity(model_ref=model)
            if identity.model_ref != model:
                raise KodeBenchError(f"model identity mismatch for {model}")
            resolved_identities.append(identity)

        return KodeBenchReport(
            suite=suite,
            config=resolved_config,
            model_identities=tuple(resolved_identities),
            outcomes=tuple(outcomes),
            protection_manifest_digest=protection_digest,
        )


@dataclass(frozen=True, slots=True)
class KodeBenchReport:
    suite: BenchmarkSuite
    config: RunConfig
    model_identities: tuple[ModelIdentity, ...]
    outcomes: tuple[BenchmarkOutcome, ...]
    protection_manifest_digest: str | None = None

    def __post_init__(self) -> None:
        if self.protection_manifest_digest is not None:
            _require_digest("protection_manifest_digest", self.protection_manifest_digest)
        model_refs = [item.model_ref for item in self.model_identities]
        if len(model_refs) != len(set(model_refs)):
            raise KodeBenchError("model identities must be unique")
        allowed_models = set(model_refs)
        for outcome in self.outcomes:
            if outcome.model_ref not in allowed_models:
                raise KodeBenchError("outcome references model absent from model identities")
            task = self.suite.task(outcome.task_id)
            if (
                outcome.domain != task.domain
                or outcome.critical != task.critical
                or outcome.scorer_digest != task.scorer.digest
            ):
                raise KodeBenchError("outcome task metadata does not match immutable suite")

    def summary(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for identity in self.model_identities:
            rows = [item for item in self.outcomes if item.model_ref == identity.model_ref]
            repeat_ids = sorted({item.repeat for item in rows})
            repeat_scores = []
            for repeat in repeat_ids:
                current = [item for item in rows if item.repeat == repeat]
                repeat_scores.append(
                    sum(item.passed for item in current) / len(current) if current else 0.0
                )
            domains: dict[str, object] = {}
            for domain in sorted({item.domain for item in rows}):
                current = [item for item in rows if item.domain == domain]
                domains[domain] = {
                    "passed": sum(item.passed for item in current),
                    "score": round(
                        sum(item.passed for item in current) / len(current), 4
                    )
                    if current
                    else 0.0,
                    "total": len(current),
                }
            critical = [item for item in rows if item.critical]
            speeds = [
                item.resources.tokens_per_second
                for item in rows
                if item.resources.tokens_per_second is not None
            ]
            payload[identity.model_ref] = {
                "capability_unavailable": sum(
                    item.category is OutcomeCategory.CAPABILITY_UNAVAILABLE for item in rows
                ),
                "critical_passed": sum(item.passed for item in critical),
                "critical_score": round(
                    sum(item.passed for item in critical) / len(critical), 4
                )
                if critical
                else None,
                "critical_total": len(critical),
                "domains": domains,
                "errors": sum(item.error is not None for item in rows),
                "model_failures": sum(
                    item.category is OutcomeCategory.MODEL_FAILURE for item in rows
                ),
                "passed": sum(item.passed for item in rows),
                "repeat_scores": [round(value, 4) for value in repeat_scores],
                "score": round(sum(item.passed for item in rows) / len(rows), 4)
                if rows
                else 0.0,
                "score_stddev": round(statistics.pstdev(repeat_scores), 4)
                if len(repeat_scores) > 1
                else 0.0,
                "scorer_failures": sum(
                    item.category is OutcomeCategory.SCORER_FAILURE for item in rows
                ),
                "tokens_per_second_mean": round(statistics.mean(speeds), 3)
                if speeds
                else None,
                "total": len(rows),
            }
        return payload

    def safe_descriptor(self) -> dict[str, object]:
        return {
            "config": self.config.descriptor(),
            "config_digest": self.config.digest,
            "model_identities": [item.descriptor() for item in self.model_identities],
            "outcomes": [item.descriptor() for item in self.outcomes],
            "protection_manifest_digest": self.protection_manifest_digest,
            "schema": KODEBENCH_SCHEMA,
            "schema_version": KODEBENCH_SCHEMA_VERSION,
            "suite": self.suite.safe_descriptor(),
            "suite_digest": self.suite.digest,
            "summary": self.summary(),
        }

    @property
    def digest(self) -> str:
        return _digest(self.safe_descriptor())

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {**self.safe_descriptor(), "report_digest": self.digest}
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _legacy_scorer(task: BenchTask) -> ScorerSpec:
    if task.exact_response is not None:
        return ScorerSpec.create(
            ScorerKind.EXACT,
            version="r3-v2",
            config={"expected": task.exact_response},
        )
    if task.response_regex is not None:
        return ScorerSpec.create(
            ScorerKind.REGEX,
            version="r3-v2",
            config={"pattern": task.response_regex},
        )
    if task.response_schema is not None:
        return ScorerSpec.create(
            ScorerKind.JSON_SCHEMA,
            version="r3-v2",
            config={"schema": task.response_schema},
        )
    if task.expect_tool_call:
        return ScorerSpec.create(ScorerKind.TOOL_CALL, version="r3-v2")
    return ScorerSpec.create(
        ScorerKind.CONTAINS,
        version="r3-v2",
        config={
            "expected": list(task.expected_contains),
            "forbidden": list(task.forbidden_contains),
        },
    )


_BASELINE_DOMAINS = {
    "debugging": ("python", True),
    "exact-instruction": ("instruction", True),
    "gdscript-typing": ("godot", True),
    "godot-awareness": ("godot", True),
    "python-reasoning": ("python", True),
    "software-engineering": ("engineering", False),
    "structured-output": ("structured", True),
    "tool-calling": ("tools", True),
}


def baseline_compat_suite(tasks: Sequence[BenchTask] = DEFAULT_TASKS) -> BenchmarkSuite:
    converted = []
    for task in tasks:
        domain, critical = _BASELINE_DOMAINS.get(task.id, ("legacy", False))
        converted.append(
            BenchmarkTaskSpec(
                task_id=task.id,
                domain=domain,
                critical=critical,
                prompt=task.prompt,
                scorer=_legacy_scorer(task),
                tools=tuple(task.tools),
            )
        )
    return BenchmarkSuite(
        suite_id="r3-baseline-compat",
        version=KODEBENCH_SUITE_VERSION,
        tasks=tuple(converted),
    )


def compare_report_payloads(
    base: Mapping[str, object],
    candidate: Mapping[str, object],
    *,
    base_model: str,
    candidate_model: str,
) -> dict[str, object]:
    for key in ("suite_digest", "config_digest", "protection_manifest_digest"):
        if base.get(key) != candidate.get(key):
            raise KodeBenchError(f"reports are not comparable: {key} differs")

    def rows(payload: Mapping[str, object], model: str) -> list[Mapping[str, object]]:
        raw = payload.get("outcomes")
        if not isinstance(raw, list):
            raise KodeBenchError("report outcomes must be a list")
        selected = [
            row for row in raw if isinstance(row, Mapping) and row.get("model_ref") == model
        ]
        if not selected:
            raise KodeBenchError(f"report has no outcomes for model: {model}")
        return selected

    base_rows = rows(base, base_model)
    candidate_rows = rows(candidate, candidate_model)
    task_ids = sorted(
        {str(row["task_id"]) for row in base_rows}
        | {str(row["task_id"]) for row in candidate_rows}
    )
    task_deltas: dict[str, object] = {}
    critical_regressions: list[str] = []
    for task_id in task_ids:
        left = [row for row in base_rows if row.get("task_id") == task_id]
        right = [row for row in candidate_rows if row.get("task_id") == task_id]
        if not left or not right or len(left) != len(right):
            raise KodeBenchError(f"reports have incompatible repetitions for task: {task_id}")
        left_score = sum(bool(row.get("passed")) for row in left) / len(left)
        right_score = sum(bool(row.get("passed")) for row in right) / len(right)
        critical = bool(left[0].get("critical"))
        if critical != bool(right[0].get("critical")):
            raise KodeBenchError(f"critical label differs for task: {task_id}")
        delta = right_score - left_score
        if critical and delta < 0:
            critical_regressions.append(task_id)
        task_deltas[task_id] = {
            "base_score": round(left_score, 4),
            "candidate_score": round(right_score, 4),
            "critical": critical,
            "delta": round(delta, 4),
        }

    return {
        "base_model": base_model,
        "candidate_model": candidate_model,
        "comparable": True,
        "config_digest": base.get("config_digest"),
        "critical_regressions": critical_regressions,
        "protection_manifest_digest": base.get("protection_manifest_digest"),
        "suite_digest": base.get("suite_digest"),
        "task_deltas": task_deltas,
    }


def compare_saved_reports(
    base_path: Path,
    candidate_path: Path,
    *,
    base_model: str,
    candidate_model: str,
) -> dict[str, object]:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(base, dict) or not isinstance(candidate, dict):
        raise KodeBenchError("saved reports must contain JSON objects")
    return compare_report_payloads(
        base,
        candidate,
        base_model=base_model,
        candidate_model=candidate_model,
    )
