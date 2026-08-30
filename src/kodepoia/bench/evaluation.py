from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

EVALUATION_SCHEMA = "kodepoia.r15.10.candidate-evaluation"
EVALUATION_SCHEMA_VERSION = 1
EVALUATION_POLICY_VERSION = "r15.10-candidate-evaluation-v1"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class CandidateEvaluationError(ValueError):
    """Raised when R15.10 comparison evidence is invalid or non-comparable."""


class CandidateDisposition(StrEnum):
    PROMOTE_TO_EXPORT = "promote_to_export"
    REJECT = "reject"
    INCONCLUSIVE = "inconclusive"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_digest(label: str, value: str) -> str:
    if _DIGEST.fullmatch(value) is None:
        raise CandidateEvaluationError(f"{label} must be 64 lowercase hex characters")
    return value


def _require_safe_id(label: str, value: str) -> str:
    if _SAFE_ID.fullmatch(value) is None:
        raise CandidateEvaluationError(f"{label} must be a stable safe identifier")
    return value


def _require_model_ref(label: str, value: str) -> str:
    value = value.strip()
    if not value or len(value) > 256 or any(ord(char) < 32 for char in value):
        raise CandidateEvaluationError(f"{label} must be a bounded non-empty model reference")
    return value


def _finite(label: str, value: object, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CandidateEvaluationError(f"{label} must be numeric")
    resolved = float(value)
    if not math.isfinite(resolved) or (minimum is not None and resolved < minimum):
        suffix = " and non-negative" if minimum == 0 else ""
        raise CandidateEvaluationError(f"{label} must be finite{suffix}")
    return resolved


@dataclass(frozen=True, slots=True)
class CandidateBinding:
    candidate_id: str
    base_model_ref: str
    base_model_digest: str
    candidate_model_ref: str
    candidate_model_digest: str
    adapter_digest: str
    training_plan_digest: str
    dataset_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_id", _require_safe_id("candidate_id", self.candidate_id))
        object.__setattr__(
            self,
            "base_model_ref",
            _require_model_ref("base_model_ref", self.base_model_ref),
        )
        object.__setattr__(
            self,
            "candidate_model_ref",
            _require_model_ref("candidate_model_ref", self.candidate_model_ref),
        )
        for name in (
            "base_model_digest",
            "candidate_model_digest",
            "adapter_digest",
            "training_plan_digest",
            "dataset_digest",
        ):
            _require_digest(name, getattr(self, name))
        if self.base_model_digest == self.candidate_model_digest:
            raise CandidateEvaluationError("candidate model digest must differ from base model digest")

    def descriptor(self) -> dict[str, str]:
        return {
            "adapter_digest": self.adapter_digest,
            "base_model_digest": self.base_model_digest,
            "base_model_ref": self.base_model_ref,
            "candidate_id": self.candidate_id,
            "candidate_model_digest": self.candidate_model_digest,
            "candidate_model_ref": self.candidate_model_ref,
            "dataset_digest": self.dataset_digest,
            "training_plan_digest": self.training_plan_digest,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


@dataclass(frozen=True, slots=True)
class TrainingLossContext:
    train_loss: float
    validation_loss: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "train_loss", _finite("train_loss", self.train_loss, minimum=0))
        object.__setattr__(
            self,
            "validation_loss",
            _finite("validation_loss", self.validation_loss, minimum=0),
        )

    @property
    def validation_to_train_ratio(self) -> float | None:
        if self.train_loss == 0:
            return 1.0 if self.validation_loss == 0 else None
        return self.validation_loss / self.train_loss

    def descriptor(self) -> dict[str, float | None]:
        ratio = self.validation_to_train_ratio
        return {
            "train_loss": self.train_loss,
            "validation_loss": self.validation_loss,
            "validation_to_train_ratio": None if ratio is None else round(ratio, 6),
        }


@dataclass(frozen=True, slots=True)
class CandidateEvaluationPolicy:
    target_domains: tuple[str, ...]
    min_target_gain: float = 0.05
    min_aggregate_delta: float = 0.0
    max_error_increase: int = 0
    max_latency_ratio: float = 1.5
    max_vram_ratio: float = 1.25
    max_score_stddev: float = 0.2
    max_validation_train_loss_ratio: float = 2.0
    require_protected_benchmark: bool = True
    require_vram_evidence: bool = False
    version: str = EVALUATION_POLICY_VERSION

    def __post_init__(self) -> None:
        if not self.target_domains or tuple(sorted(set(self.target_domains))) != self.target_domains:
            raise CandidateEvaluationError("target_domains must be non-empty, unique and sorted")
        for domain in self.target_domains:
            _require_safe_id("target domain", domain)
        object.__setattr__(
            self,
            "min_target_gain",
            _finite("min_target_gain", self.min_target_gain),
        )
        if not 0 <= self.min_target_gain <= 1:
            raise CandidateEvaluationError("min_target_gain must be in [0, 1]")
        object.__setattr__(
            self,
            "min_aggregate_delta",
            _finite("min_aggregate_delta", self.min_aggregate_delta),
        )
        if not -1 <= self.min_aggregate_delta <= 1:
            raise CandidateEvaluationError("min_aggregate_delta must be in [-1, 1]")
        if isinstance(self.max_error_increase, bool) or not isinstance(self.max_error_increase, int):
            raise CandidateEvaluationError("max_error_increase must be an integer")
        if self.max_error_increase < 0:
            raise CandidateEvaluationError("max_error_increase must be >= 0")
        for name in ("max_latency_ratio", "max_vram_ratio", "max_validation_train_loss_ratio"):
            value = _finite(name, getattr(self, name), minimum=1)
            object.__setattr__(self, name, value)
        score_stddev = _finite("max_score_stddev", self.max_score_stddev, minimum=0)
        if score_stddev > 1:
            raise CandidateEvaluationError("max_score_stddev must be in [0, 1]")
        object.__setattr__(self, "max_score_stddev", score_stddev)
        object.__setattr__(self, "version", _require_safe_id("policy version", self.version))

    def descriptor(self) -> dict[str, object]:
        return {
            "max_error_increase": self.max_error_increase,
            "max_latency_ratio": self.max_latency_ratio,
            "max_score_stddev": self.max_score_stddev,
            "max_validation_train_loss_ratio": self.max_validation_train_loss_ratio,
            "max_vram_ratio": self.max_vram_ratio,
            "min_aggregate_delta": self.min_aggregate_delta,
            "min_target_gain": self.min_target_gain,
            "require_protected_benchmark": self.require_protected_benchmark,
            "require_vram_evidence": self.require_vram_evidence,
            "target_domains": list(self.target_domains),
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


def _verify_report(payload: Mapping[str, object], label: str) -> str:
    report_digest = payload.get("report_digest")
    if not isinstance(report_digest, str):
        raise CandidateEvaluationError(f"{label} report_digest is required")
    _require_digest(f"{label} report_digest", report_digest)
    descriptor = {key: value for key, value in payload.items() if key != "report_digest"}
    if _digest(descriptor) != report_digest:
        raise CandidateEvaluationError(f"{label} report digest does not match report content")

    suite = payload.get("suite")
    suite_digest = payload.get("suite_digest")
    config = payload.get("config")
    config_digest = payload.get("config_digest")
    if not isinstance(suite, Mapping) or not isinstance(suite_digest, str):
        raise CandidateEvaluationError(f"{label} suite evidence is invalid")
    if not isinstance(config, Mapping) or not isinstance(config_digest, str):
        raise CandidateEvaluationError(f"{label} config evidence is invalid")
    _require_digest(f"{label} suite_digest", suite_digest)
    _require_digest(f"{label} config_digest", config_digest)
    if _digest(dict(suite)) != suite_digest:
        raise CandidateEvaluationError(f"{label} suite_digest does not match suite descriptor")
    if _digest(dict(config)) != config_digest:
        raise CandidateEvaluationError(f"{label} config_digest does not match config descriptor")

    protection = payload.get("protection_manifest_digest")
    if protection is not None:
        if not isinstance(protection, str):
            raise CandidateEvaluationError(f"{label} protection manifest digest must be a string or null")
        _require_digest(f"{label} protection_manifest_digest", protection)
    return report_digest


def _model_digest(payload: Mapping[str, object], model_ref: str, label: str) -> str:
    raw = payload.get("model_identities")
    if not isinstance(raw, list):
        raise CandidateEvaluationError(f"{label} model_identities must be a list")
    selected = [item for item in raw if isinstance(item, Mapping) and item.get("model_ref") == model_ref]
    if len(selected) != 1:
        raise CandidateEvaluationError(f"{label} must contain exactly one identity for {model_ref}")
    digest = selected[0].get("model_digest")
    if not isinstance(digest, str):
        raise CandidateEvaluationError(f"{label} selected model identity must be digest-resolved")
    return _require_digest(f"{label} model_digest", digest)


def _outcomes(payload: Mapping[str, object], model_ref: str, label: str) -> list[Mapping[str, object]]:
    raw = payload.get("outcomes")
    if not isinstance(raw, list):
        raise CandidateEvaluationError(f"{label} outcomes must be a list")
    selected = [item for item in raw if isinstance(item, Mapping) and item.get("model_ref") == model_ref]
    if not selected:
        raise CandidateEvaluationError(f"{label} has no outcomes for {model_ref}")
    return selected


def _pair_key(row: Mapping[str, object]) -> tuple[str, int, int]:
    task_id = row.get("task_id")
    repeat = row.get("repeat")
    seed = row.get("seed")
    if not isinstance(task_id, str) or not isinstance(repeat, int) or not isinstance(seed, int):
        raise CandidateEvaluationError("outcome pairing fields task_id/repeat/seed are invalid")
    _require_safe_id("outcome task_id", task_id)
    return task_id, repeat, seed


def _passed(row: Mapping[str, object]) -> bool:
    value = row.get("passed")
    if not isinstance(value, bool):
        raise CandidateEvaluationError("outcome passed must be boolean")
    return value


def _resource(row: Mapping[str, object], name: str) -> float | None:
    resources = row.get("resources")
    if not isinstance(resources, Mapping):
        raise CandidateEvaluationError("outcome resources must be an object")
    value = resources.get(name)
    if value is None:
        return None
    return _finite(f"resource {name}", value, minimum=0)


def _mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def _ratio(candidate: float | None, base: float | None) -> float | None:
    if candidate is None or base is None:
        return None
    if base == 0:
        return 1.0 if candidate == 0 else None
    return candidate / base


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    binding: CandidateBinding
    policy: CandidateEvaluationPolicy
    training_loss: TrainingLossContext
    base_report_digest: str
    candidate_report_digest: str
    suite_digest: str
    config_digest: str
    protection_manifest_digest: str | None
    task_deltas: tuple[tuple[str, Mapping[str, object]], ...]
    domain_deltas: tuple[tuple[str, Mapping[str, object]], ...]
    critical_regressions: tuple[str, ...]
    base_score: float
    candidate_score: float
    aggregate_delta: float
    target_gain: float | None
    base_errors: int
    candidate_errors: int
    error_delta: int
    base_repeat_stddev: float
    candidate_repeat_stddev: float
    resources: Mapping[str, object]
    overfit_risk: bool
    disposition: CandidateDisposition
    reasons: tuple[str, ...]
    schema: str = EVALUATION_SCHEMA
    schema_version: int = EVALUATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("base_report_digest", "candidate_report_digest", "suite_digest", "config_digest"):
            _require_digest(name, getattr(self, name))
        if self.protection_manifest_digest is not None:
            _require_digest("protection_manifest_digest", self.protection_manifest_digest)
        if tuple(sorted(set(self.critical_regressions))) != self.critical_regressions:
            raise CandidateEvaluationError("critical_regressions must be unique and sorted")
        if tuple(sorted(set(self.reasons))) != self.reasons:
            raise CandidateEvaluationError("reasons must be unique and sorted")
        task_names = [name for name, _ in self.task_deltas]
        domain_names = [name for name, _ in self.domain_deltas]
        if task_names != sorted(task_names) or len(task_names) != len(set(task_names)):
            raise CandidateEvaluationError("task_deltas must be unique and sorted")
        if domain_names != sorted(domain_names) or len(domain_names) != len(set(domain_names)):
            raise CandidateEvaluationError("domain_deltas must be unique and sorted")

    @property
    def can_export(self) -> bool:
        return self.disposition is CandidateDisposition.PROMOTE_TO_EXPORT

    def require_exportable(self) -> None:
        if not self.can_export:
            raise CandidateEvaluationError(
                f"candidate {self.binding.candidate_id} cannot feed R15.11: {self.disposition.value}"
            )

    def descriptor(self) -> dict[str, object]:
        return {
            "aggregate": {
                "base_score": round(self.base_score, 6),
                "candidate_score": round(self.candidate_score, 6),
                "delta": round(self.aggregate_delta, 6),
                "target_gain": None if self.target_gain is None else round(self.target_gain, 6),
            },
            "binding": self.binding.descriptor(),
            "binding_digest": self.binding.digest,
            "can_export": self.can_export,
            "config_digest": self.config_digest,
            "critical_regressions": list(self.critical_regressions),
            "disposition": self.disposition.value,
            "domain_deltas": {name: dict(value) for name, value in self.domain_deltas},
            "errors": {
                "base": self.base_errors,
                "candidate": self.candidate_errors,
                "delta": self.error_delta,
            },
            "overfit_risk": self.overfit_risk,
            "policy": self.policy.descriptor(),
            "policy_digest": self.policy.digest,
            "protection_manifest_digest": self.protection_manifest_digest,
            "reasons": list(self.reasons),
            "repeat_stddev": {
                "base": round(self.base_repeat_stddev, 6),
                "candidate": round(self.candidate_repeat_stddev, 6),
            },
            "reports": {
                "base": self.base_report_digest,
                "candidate": self.candidate_report_digest,
            },
            "resources": dict(self.resources),
            "schema": self.schema,
            "schema_version": self.schema_version,
            "suite_digest": self.suite_digest,
            "task_deltas": {name: dict(value) for name, value in self.task_deltas},
            "training_loss": self.training_loss.descriptor(),
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "evaluation_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


class BaseAdapterEvaluator:
    """Fail-closed R15.10 paired evaluator for immutable KodeBench reports."""

    def evaluate(
        self,
        base_report: Mapping[str, object],
        candidate_report: Mapping[str, object],
        *,
        binding: CandidateBinding,
        policy: CandidateEvaluationPolicy,
        training_loss: TrainingLossContext,
    ) -> CandidateEvaluation:
        base_report_digest = _verify_report(base_report, "base")
        candidate_report_digest = _verify_report(candidate_report, "candidate")

        for key in ("suite_digest", "config_digest", "protection_manifest_digest"):
            if base_report.get(key) != candidate_report.get(key):
                raise CandidateEvaluationError(f"reports are not comparable: {key} differs")
        if base_report.get("config") != candidate_report.get("config"):
            raise CandidateEvaluationError("reports are not comparable: run config differs")
        if base_report.get("suite") != candidate_report.get("suite"):
            raise CandidateEvaluationError("reports are not comparable: benchmark suite differs")

        base_digest = _model_digest(base_report, binding.base_model_ref, "base")
        candidate_digest = _model_digest(candidate_report, binding.candidate_model_ref, "candidate")
        if base_digest != binding.base_model_digest:
            raise CandidateEvaluationError("base report model digest does not match candidate binding")
        if candidate_digest != binding.candidate_model_digest:
            raise CandidateEvaluationError("candidate report model digest does not match candidate binding")

        base_rows = _outcomes(base_report, binding.base_model_ref, "base")
        candidate_rows = _outcomes(candidate_report, binding.candidate_model_ref, "candidate")
        base_pairs = {_pair_key(row): row for row in base_rows}
        candidate_pairs = {_pair_key(row): row for row in candidate_rows}
        if len(base_pairs) != len(base_rows) or len(candidate_pairs) != len(candidate_rows):
            raise CandidateEvaluationError("duplicate task/repeat/seed outcome pair detected")
        if set(base_pairs) != set(candidate_pairs):
            raise CandidateEvaluationError("reports do not contain the same task/repeat/seed pairs")

        by_task_base: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        by_task_candidate: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        by_domain_base: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        by_domain_candidate: dict[str, list[Mapping[str, object]]] = defaultdict(list)
        for key in sorted(base_pairs):
            left = base_pairs[key]
            right = candidate_pairs[key]
            for field in ("task_id", "domain", "critical", "scorer_digest"):
                if left.get(field) != right.get(field):
                    raise CandidateEvaluationError(f"paired outcome metadata differs: {field}")
            domain = left.get("domain")
            task_id = left.get("task_id")
            if not isinstance(domain, str) or not isinstance(task_id, str):
                raise CandidateEvaluationError("paired task/domain metadata must be strings")
            _require_safe_id("outcome domain", domain)
            by_task_base[task_id].append(left)
            by_task_candidate[task_id].append(right)
            by_domain_base[domain].append(left)
            by_domain_candidate[domain].append(right)

        task_deltas: list[tuple[str, Mapping[str, object]]] = []
        critical_regressions: list[str] = []
        for task_id in sorted(by_task_base):
            left = by_task_base[task_id]
            right = by_task_candidate[task_id]
            base_score = sum(_passed(row) for row in left) / len(left)
            candidate_score = sum(_passed(row) for row in right) / len(right)
            delta = candidate_score - base_score
            critical = bool(left[0].get("critical"))
            domain = str(left[0].get("domain"))
            if critical and delta < 0:
                critical_regressions.append(task_id)
            task_deltas.append(
                (
                    task_id,
                    {
                        "base_score": round(base_score, 6),
                        "candidate_score": round(candidate_score, 6),
                        "critical": critical,
                        "delta": round(delta, 6),
                        "domain": domain,
                        "pairs": len(left),
                    },
                )
            )

        domain_deltas: list[tuple[str, Mapping[str, object]]] = []
        domain_delta_values: dict[str, float] = {}
        for domain in sorted(by_domain_base):
            left = by_domain_base[domain]
            right = by_domain_candidate[domain]
            base_score = sum(_passed(row) for row in left) / len(left)
            candidate_score = sum(_passed(row) for row in right) / len(right)
            delta = candidate_score - base_score
            domain_delta_values[domain] = delta
            domain_deltas.append(
                (
                    domain,
                    {
                        "base_score": round(base_score, 6),
                        "candidate_score": round(candidate_score, 6),
                        "delta": round(delta, 6),
                        "pairs": len(left),
                    },
                )
            )

        base_score = sum(_passed(row) for row in base_rows) / len(base_rows)
        candidate_score = sum(_passed(row) for row in candidate_rows) / len(candidate_rows)
        aggregate_delta = candidate_score - base_score

        target_values = [
            domain_delta_values[domain] for domain in policy.target_domains if domain in domain_delta_values
        ]
        target_gain = (
            statistics.mean(target_values) if len(target_values) == len(policy.target_domains) else None
        )

        base_errors = sum(row.get("error") is not None for row in base_rows)
        candidate_errors = sum(row.get("error") is not None for row in candidate_rows)
        error_delta = candidate_errors - base_errors

        def repeat_stddev(rows: list[Mapping[str, object]]) -> float:
            grouped: dict[int, list[Mapping[str, object]]] = defaultdict(list)
            for row in rows:
                repeat = row.get("repeat")
                if not isinstance(repeat, int):
                    raise CandidateEvaluationError("outcome repeat must be integer")
                grouped[repeat].append(row)
            values = [
                sum(_passed(row) for row in grouped[index]) / len(grouped[index]) for index in sorted(grouped)
            ]
            return statistics.pstdev(values) if len(values) > 1 else 0.0

        base_repeat_stddev = repeat_stddev(base_rows)
        candidate_repeat_stddev = repeat_stddev(candidate_rows)

        base_elapsed = _mean(
            [value for row in base_rows if (value := _resource(row, "elapsed_s")) is not None]
        )
        candidate_elapsed = _mean(
            [value for row in candidate_rows if (value := _resource(row, "elapsed_s")) is not None]
        )
        base_vram = _mean([value for row in base_rows if (value := _resource(row, "vram_bytes")) is not None])
        candidate_vram = _mean(
            [value for row in candidate_rows if (value := _resource(row, "vram_bytes")) is not None]
        )
        base_tps = _mean(
            [value for row in base_rows if (value := _resource(row, "tokens_per_second")) is not None]
        )
        candidate_tps = _mean(
            [value for row in candidate_rows if (value := _resource(row, "tokens_per_second")) is not None]
        )
        latency_ratio = _ratio(candidate_elapsed, base_elapsed)
        vram_ratio = _ratio(candidate_vram, base_vram)
        throughput_ratio = _ratio(candidate_tps, base_tps)
        resources = {
            "elapsed_s_mean": {
                "base": None if base_elapsed is None else round(base_elapsed, 6),
                "candidate": None if candidate_elapsed is None else round(candidate_elapsed, 6),
                "ratio": None if latency_ratio is None else round(latency_ratio, 6),
            },
            "tokens_per_second_mean": {
                "base": None if base_tps is None else round(base_tps, 6),
                "candidate": None if candidate_tps is None else round(candidate_tps, 6),
                "ratio": None if throughput_ratio is None else round(throughput_ratio, 6),
            },
            "vram_bytes_mean": {
                "base": None if base_vram is None else round(base_vram, 3),
                "candidate": None if candidate_vram is None else round(candidate_vram, 3),
                "ratio": None if vram_ratio is None else round(vram_ratio, 6),
            },
        }

        ratio = training_loss.validation_to_train_ratio
        overfit_risk = (ratio is None and training_loss.validation_loss > 0) or (
            ratio is not None and ratio > policy.max_validation_train_loss_ratio
        )

        hard_reject: set[str] = set()
        inconclusive: set[str] = set()
        if critical_regressions:
            hard_reject.add("critical_regression")
        if aggregate_delta < policy.min_aggregate_delta:
            hard_reject.add("aggregate_regression")
        if error_delta > policy.max_error_increase:
            hard_reject.add("error_budget_exceeded")
        if latency_ratio is None:
            inconclusive.add("latency_evidence_missing")
        elif latency_ratio > policy.max_latency_ratio:
            hard_reject.add("latency_budget_exceeded")
        if policy.require_vram_evidence and vram_ratio is None:
            inconclusive.add("vram_evidence_missing")
        elif vram_ratio is not None and vram_ratio > policy.max_vram_ratio:
            hard_reject.add("vram_budget_exceeded")
        if candidate_repeat_stddev > policy.max_score_stddev:
            inconclusive.add("candidate_instability")
        if target_gain is None:
            inconclusive.add("target_domain_evidence_missing")
        elif target_gain < 0:
            hard_reject.add("target_domain_regression")
        elif target_gain < policy.min_target_gain:
            inconclusive.add("target_gain_below_promotion_threshold")
        protection = base_report.get("protection_manifest_digest")
        if policy.require_protected_benchmark and protection is None:
            inconclusive.add("protected_benchmark_evidence_missing")
        if overfit_risk:
            inconclusive.add("validation_overfit_risk")

        if hard_reject:
            disposition = CandidateDisposition.REJECT
            reasons = tuple(sorted(hard_reject | inconclusive))
        elif inconclusive:
            disposition = CandidateDisposition.INCONCLUSIVE
            reasons = tuple(sorted(inconclusive))
        else:
            disposition = CandidateDisposition.PROMOTE_TO_EXPORT
            reasons = ("promotion_thresholds_satisfied",)

        suite_digest = base_report.get("suite_digest")
        config_digest = base_report.get("config_digest")
        if not isinstance(suite_digest, str) or not isinstance(config_digest, str):
            raise CandidateEvaluationError("validated report digests unexpectedly missing")
        protection_digest = protection if isinstance(protection, str) else None

        return CandidateEvaluation(
            binding=binding,
            policy=policy,
            training_loss=training_loss,
            base_report_digest=base_report_digest,
            candidate_report_digest=candidate_report_digest,
            suite_digest=suite_digest,
            config_digest=config_digest,
            protection_manifest_digest=protection_digest,
            task_deltas=tuple(task_deltas),
            domain_deltas=tuple(domain_deltas),
            critical_regressions=tuple(sorted(critical_regressions)),
            base_score=base_score,
            candidate_score=candidate_score,
            aggregate_delta=aggregate_delta,
            target_gain=target_gain,
            base_errors=base_errors,
            candidate_errors=candidate_errors,
            error_delta=error_delta,
            base_repeat_stddev=base_repeat_stddev,
            candidate_repeat_stddev=candidate_repeat_stddev,
            resources=resources,
            overfit_risk=overfit_risk,
            disposition=disposition,
            reasons=reasons,
        )


def evaluate_saved_reports(
    base_path: Path,
    candidate_path: Path,
    *,
    binding: CandidateBinding,
    policy: CandidateEvaluationPolicy,
    training_loss: TrainingLossContext,
) -> CandidateEvaluation:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(base, Mapping) or not isinstance(candidate, Mapping):
        raise CandidateEvaluationError("saved KodeBench reports must contain JSON objects")
    return BaseAdapterEvaluator().evaluate(
        base,
        candidate,
        binding=binding,
        policy=policy,
        training_loss=training_loss,
    )
