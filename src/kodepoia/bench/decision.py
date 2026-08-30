from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from kodepoia.experience.contracts import PolicyDecision

DECISION_SCHEMA = "kodepoia.r15.7.gap-decision"
DECISION_SCHEMA_VERSION = 1
DECISION_POLICY_VERSION = "r15.7-gap-decision-v1"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class GapDecisionError(ValueError):
    """Base error for R15.7 gap diagnosis and TRAIN/NO_TRAIN decisions."""


class DecisionDisposition(StrEnum):
    TRAIN = "train"
    NO_TRAIN = "no_train"
    FIX_SYSTEM_FIRST = "fix_system_first"
    INSUFFICIENT_DATA = "insufficient_data"
    UNSUPPORTED = "unsupported"
    LICENSE_BLOCKED = "license_blocked"
    BUDGET_BLOCKED = "budget_blocked"
    INCONCLUSIVE = "inconclusive"


class DiagnosticComponent(StrEnum):
    TOOL = "tool"
    RETRIEVAL = "retrieval"
    ROUTER = "router"
    CONTEXT = "context"
    PRODUCT = "product"


class ProbeStatus(StrEnum):
    PASS = "pass"
    DEFECT = "defect"
    UNKNOWN = "unknown"


class BackendCapability(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class BudgetStatus(StrEnum):
    WITHIN_BUDGET = "within_budget"
    EXCEEDED = "exceeded"
    UNKNOWN = "unknown"


class ExpectedImpact(StrEnum):
    MEANINGFUL = "meaningful"
    LOW = "low"
    UNKNOWN = "unknown"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _require_safe_id(label: str, value: str) -> None:
    if _SAFE_ID.fullmatch(value) is None:
        raise GapDecisionError(f"{label} must be a stable safe identifier")


def _require_digest(label: str, value: str) -> None:
    if _DIGEST.fullmatch(value) is None:
        raise GapDecisionError(f"{label} must be 64 lowercase hex characters")


def _require_optional_digest(label: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise GapDecisionError(f"{label} must be a digest string or null")
    _require_digest(label, value)
    return value


@dataclass(frozen=True, slots=True)
class DecisionPolicy:
    min_train_examples_per_domain: int = 4
    noncritical_target_gain: float = 0.1
    required_probe_components: tuple[DiagnosticComponent, ...] = (
        DiagnosticComponent.TOOL,
        DiagnosticComponent.RETRIEVAL,
        DiagnosticComponent.ROUTER,
        DiagnosticComponent.CONTEXT,
    )
    adapter_method: str = "qlora_sft"
    version: str = DECISION_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.min_train_examples_per_domain <= 0:
            raise GapDecisionError("min_train_examples_per_domain must be > 0")
        if not math.isfinite(self.noncritical_target_gain) or not (
            0 < self.noncritical_target_gain <= 1
        ):
            raise GapDecisionError("noncritical_target_gain must be in (0, 1]")
        _require_safe_id("adapter_method", self.adapter_method)
        _require_safe_id("policy version", self.version)
        if not self.required_probe_components:
            raise GapDecisionError("required_probe_components must not be empty")
        if len(set(self.required_probe_components)) != len(self.required_probe_components):
            raise GapDecisionError("required_probe_components must be unique")

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_method": self.adapter_method,
            "min_train_examples_per_domain": self.min_train_examples_per_domain,
            "noncritical_target_gain": self.noncritical_target_gain,
            "required_probe_components": [
                item.value for item in self.required_probe_components
            ],
            "version": self.version,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


@dataclass(frozen=True, slots=True)
class DiagnosticProbe:
    component: DiagnosticComponent
    status: ProbeStatus
    evidence_digest: str
    affected_domains: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "component", DiagnosticComponent(self.component))
        object.__setattr__(self, "status", ProbeStatus(self.status))
        _require_digest("diagnostic evidence_digest", self.evidence_digest)
        if tuple(sorted(set(self.affected_domains))) != self.affected_domains:
            raise GapDecisionError("affected_domains must be unique and sorted")
        for domain in self.affected_domains:
            _require_safe_id("affected domain", domain)

    def descriptor(self) -> dict[str, object]:
        return {
            "affected_domains": list(self.affected_domains),
            "component": self.component.value,
            "evidence_digest": self.evidence_digest,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class DecisionEvidence:
    benchmark_reproducible: bool | None
    contamination_valid: bool | None
    dataset_license: PolicyDecision = PolicyDecision.UNKNOWN
    base_model_license: PolicyDecision = PolicyDecision.UNKNOWN
    backend_capability: BackendCapability = BackendCapability.UNKNOWN
    budget_status: BudgetStatus = BudgetStatus.UNKNOWN
    rollback_ready: bool | None = None
    expected_impact: ExpectedImpact = ExpectedImpact.UNKNOWN
    diagnostics: tuple[DiagnosticProbe, ...] = ()
    evidence_digests: tuple[tuple[str, str], ...] = ()
    supersedes_decision_digest: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "dataset_license", PolicyDecision(self.dataset_license))
        object.__setattr__(
            self,
            "base_model_license",
            PolicyDecision(self.base_model_license),
        )
        object.__setattr__(
            self,
            "backend_capability",
            BackendCapability(self.backend_capability),
        )
        object.__setattr__(self, "budget_status", BudgetStatus(self.budget_status))
        object.__setattr__(self, "expected_impact", ExpectedImpact(self.expected_impact))
        components = [item.component for item in self.diagnostics]
        if len(components) != len(set(components)):
            raise GapDecisionError("diagnostic components must be unique")
        if tuple(sorted(self.evidence_digests)) != self.evidence_digests:
            raise GapDecisionError("evidence_digests must be unique and sorted")
        names = [name for name, _ in self.evidence_digests]
        if len(names) != len(set(names)):
            raise GapDecisionError("evidence digest names must be unique")
        for name, digest in self.evidence_digests:
            _require_safe_id("evidence digest name", name)
            _require_digest(f"evidence digest {name}", digest)
        if self.supersedes_decision_digest is not None:
            _require_digest(
                "supersedes_decision_digest",
                self.supersedes_decision_digest,
            )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> DecisionEvidence:
        diagnostics_raw = payload.get("diagnostics", [])
        if not isinstance(diagnostics_raw, list):
            raise GapDecisionError("diagnostics must be a list")
        diagnostics: list[DiagnosticProbe] = []
        for item in diagnostics_raw:
            if not isinstance(item, Mapping):
                raise GapDecisionError("diagnostic entries must be objects")
            domains_raw = item.get("affected_domains", [])
            if not isinstance(domains_raw, list) or not all(
                isinstance(value, str) for value in domains_raw
            ):
                raise GapDecisionError("affected_domains must be a string list")
            component = item.get("component")
            status = item.get("status")
            evidence_digest = item.get("evidence_digest")
            if not isinstance(component, str) or not isinstance(status, str):
                raise GapDecisionError("diagnostic component/status must be strings")
            if not isinstance(evidence_digest, str):
                raise GapDecisionError("diagnostic evidence_digest must be a string")
            diagnostics.append(
                DiagnosticProbe(
                    DiagnosticComponent(component),
                    ProbeStatus(status),
                    evidence_digest,
                    tuple(sorted(domains_raw)),
                )
            )
        digests_raw = payload.get("evidence_digests", {})
        if not isinstance(digests_raw, Mapping):
            raise GapDecisionError("evidence_digests must be an object")
        digests: list[tuple[str, str]] = []
        for name, digest in digests_raw.items():
            if not isinstance(name, str) or not isinstance(digest, str):
                raise GapDecisionError("evidence_digests entries must be strings")
            digests.append((name, digest))
        supersedes = payload.get("supersedes_decision_digest")
        if supersedes is not None and not isinstance(supersedes, str):
            raise GapDecisionError("supersedes_decision_digest must be string or null")

        def optional_bool(name: str) -> bool | None:
            value = payload.get(name)
            if value is None or isinstance(value, bool):
                return value
            raise GapDecisionError(f"{name} must be boolean or null")

        return cls(
            benchmark_reproducible=optional_bool("benchmark_reproducible"),
            contamination_valid=optional_bool("contamination_valid"),
            dataset_license=PolicyDecision(str(payload.get("dataset_license", "unknown"))),
            base_model_license=PolicyDecision(
                str(payload.get("base_model_license", "unknown"))
            ),
            backend_capability=BackendCapability(
                str(payload.get("backend_capability", "unknown"))
            ),
            budget_status=BudgetStatus(str(payload.get("budget_status", "unknown"))),
            rollback_ready=optional_bool("rollback_ready"),
            expected_impact=ExpectedImpact(str(payload.get("expected_impact", "unknown"))),
            diagnostics=tuple(sorted(diagnostics, key=lambda item: item.component.value)),
            evidence_digests=tuple(sorted(digests)),
            supersedes_decision_digest=supersedes,
        )

    def descriptor(self) -> dict[str, object]:
        return {
            "backend_capability": self.backend_capability.value,
            "base_model_license": self.base_model_license.value,
            "benchmark_reproducible": self.benchmark_reproducible,
            "budget_status": self.budget_status.value,
            "contamination_valid": self.contamination_valid,
            "dataset_license": self.dataset_license.value,
            "diagnostics": [item.descriptor() for item in self.diagnostics],
            "evidence_digests": dict(self.evidence_digests),
            "expected_impact": self.expected_impact.value,
            "rollback_ready": self.rollback_ready,
            "supersedes_decision_digest": self.supersedes_decision_digest,
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())


@dataclass(frozen=True, slots=True)
class GapRecord:
    task_id: str
    domain: str
    critical: bool
    passed: int
    total: int
    score: float
    categories: tuple[str, ...]

    def descriptor(self) -> dict[str, object]:
        return {
            "categories": list(self.categories),
            "critical": self.critical,
            "domain": self.domain,
            "passed": self.passed,
            "score": self.score,
            "task_id": self.task_id,
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class AcceptanceTarget:
    domain: str
    baseline_score: float
    minimum_score: float
    critical: bool

    def descriptor(self) -> dict[str, object]:
        return {
            "baseline_score": self.baseline_score,
            "critical": self.critical,
            "domain": self.domain,
            "minimum_score": self.minimum_score,
        }


@dataclass(frozen=True, slots=True)
class GapDecision:
    disposition: DecisionDisposition
    base_model: Mapping[str, object]
    benchmark_report_digest: str
    suite_digest: str
    config_digest: str
    protection_manifest_digest: str | None
    policy: DecisionPolicy
    evidence: DecisionEvidence
    gaps: tuple[GapRecord, ...]
    targets: tuple[AcceptanceTarget, ...]
    target_domains: tuple[str, ...]
    dataset_id: str | None
    dataset_digest: str | None
    dataset_file_digest: str | None
    train_examples_by_domain: tuple[tuple[str, int], ...]
    blockers: tuple[str, ...]
    reasons: tuple[str, ...]
    adapter_method: str | None
    schema: str = DECISION_SCHEMA
    schema_version: int = DECISION_SCHEMA_VERSION

    def descriptor(self) -> dict[str, object]:
        return {
            "adapter_method": self.adapter_method,
            "base_model": dict(self.base_model),
            "benchmark": {
                "config_digest": self.config_digest,
                "protection_manifest_digest": self.protection_manifest_digest,
                "report_digest": self.benchmark_report_digest,
                "suite_digest": self.suite_digest,
            },
            "blockers": list(self.blockers),
            "dataset": {
                "dataset_digest": self.dataset_digest,
                "dataset_file_digest": self.dataset_file_digest,
                "dataset_id": self.dataset_id,
                "train_examples_by_domain": dict(self.train_examples_by_domain),
            },
            "disposition": self.disposition.value,
            "evidence": self.evidence.descriptor(),
            "evidence_digest": self.evidence.digest,
            "gaps": [item.descriptor() for item in self.gaps],
            "policy": self.policy.descriptor(),
            "policy_digest": self.policy.digest,
            "reasons": list(self.reasons),
            "schema": self.schema,
            "schema_version": self.schema_version,
            "target_domains": list(self.target_domains),
            "targets": [item.descriptor() for item in self.targets],
        }

    @property
    def digest(self) -> str:
        return _digest(self.descriptor())

    def to_dict(self) -> dict[str, object]:
        return {**self.descriptor(), "decision_digest": self.digest}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )


def _normalize_report(report: Mapping[str, object]) -> tuple[dict[str, object], str]:
    payload = dict(report)
    claimed_digest = payload.pop("report_digest", None)
    digest = _digest(payload)
    if claimed_digest is not None:
        if not isinstance(claimed_digest, str):
            raise GapDecisionError("report_digest must be a string")
        _require_digest("report_digest", claimed_digest)
        if claimed_digest != digest:
            raise GapDecisionError("benchmark report_digest does not match report content")
    return payload, digest


def _normalize_dataset(
    dataset: Mapping[str, object] | None,
) -> tuple[str | None, str | None, str | None, Counter[str]]:
    if dataset is None:
        return None, None, None, Counter()
    payload = dict(dataset)
    dataset_id = payload.get("dataset_id")
    dataset_digest = payload.get("dataset_digest")
    if not isinstance(dataset_id, str):
        raise GapDecisionError("dataset_id must be a string")
    _require_safe_id("dataset_id", dataset_id)
    if not isinstance(dataset_digest, str):
        raise GapDecisionError("dataset_digest must be a string")
    _require_digest("dataset_digest", dataset_digest)
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise GapDecisionError("dataset entries must be a list")
    counts: Counter[str] = Counter()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise GapDecisionError("dataset entries must be objects")
        if entry.get("split") != "train":
            continue
        domain = entry.get("domain")
        if not isinstance(domain, str):
            raise GapDecisionError("training dataset entry domain must be a string")
        _require_safe_id("dataset entry domain", domain)
        counts[domain] += 1
    return dataset_id, dataset_digest, _digest(payload), counts


def _extract_model(report: Mapping[str, object], model_ref: str) -> dict[str, object]:
    identities = report.get("model_identities")
    if not isinstance(identities, list):
        raise GapDecisionError("benchmark model_identities must be a list")
    matches = [
        item
        for item in identities
        if isinstance(item, Mapping) and item.get("model_ref") == model_ref
    ]
    if len(matches) != 1:
        raise GapDecisionError("benchmark must contain exactly one selected base model identity")
    return dict(matches[0])


def _extract_gaps(
    report: Mapping[str, object], model_ref: str
) -> tuple[tuple[GapRecord, ...], tuple[AcceptanceTarget, ...], tuple[str, ...]]:
    outcomes = report.get("outcomes")
    if not isinstance(outcomes, list):
        raise GapDecisionError("benchmark outcomes must be a list")
    selected = [
        item
        for item in outcomes
        if isinstance(item, Mapping) and item.get("model_ref") == model_ref
    ]
    if not selected:
        raise GapDecisionError("benchmark has no outcomes for selected base model")
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in selected:
        task_id = row.get("task_id")
        domain = row.get("domain")
        if not isinstance(task_id, str) or not isinstance(domain, str):
            raise GapDecisionError("benchmark outcome task/domain must be strings")
        grouped[task_id].append(row)

    gaps: list[GapRecord] = []
    domain_rows: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for task_id, rows in sorted(grouped.items()):
        domains = {row.get("domain") for row in rows}
        critical_values = {bool(row.get("critical")) for row in rows}
        if len(domains) != 1 or len(critical_values) != 1:
            raise GapDecisionError("benchmark repetitions disagree on immutable task metadata")
        repeat_ids = [row.get("repeat") for row in rows]
        if any(not isinstance(value, int) for value in repeat_ids):
            raise GapDecisionError("benchmark repeat identifiers must be integers")
        if len(repeat_ids) != len(set(repeat_ids)):
            raise GapDecisionError("benchmark repeats must be unique per task")
        categories = tuple(sorted({str(row.get("category")) for row in rows}))
        if "scorer_failure" in categories:
            raise GapDecisionError("benchmark scorer failure makes diagnosis invalid")
        passed = sum(bool(row.get("passed")) for row in rows)
        score = round(passed / len(rows), 4)
        domain = str(next(iter(domains)))
        for row in rows:
            domain_rows[domain].append(row)
        if score < 1.0:
            gaps.append(
                GapRecord(
                    task_id=task_id,
                    domain=domain,
                    critical=next(iter(critical_values)),
                    passed=passed,
                    total=len(rows),
                    score=score,
                    categories=categories,
                )
            )

    target_domains = tuple(sorted({gap.domain for gap in gaps}))
    return tuple(gaps), (), target_domains


def _targets_for_gaps(
    report: Mapping[str, object],
    model_ref: str,
    gaps: Sequence[GapRecord],
    policy: DecisionPolicy,
) -> tuple[AcceptanceTarget, ...]:
    outcomes = report.get("outcomes")
    if not isinstance(outcomes, list):
        raise GapDecisionError("benchmark outcomes must be a list")
    targets: list[AcceptanceTarget] = []
    for domain in sorted({gap.domain for gap in gaps}):
        rows = [
            row
            for row in outcomes
            if isinstance(row, Mapping)
            and row.get("model_ref") == model_ref
            and row.get("domain") == domain
        ]
        if not rows:
            raise GapDecisionError("target domain has no benchmark rows")
        baseline = round(sum(bool(row.get("passed")) for row in rows) / len(rows), 4)
        critical = any(bool(row.get("critical")) for row in rows)
        minimum = 1.0 if critical else min(1.0, baseline + policy.noncritical_target_gain)
        targets.append(
            AcceptanceTarget(
                domain=domain,
                baseline_score=baseline,
                minimum_score=round(minimum, 4),
                critical=critical,
            )
        )
    return tuple(targets)


class GapDecisionEngine:
    """Deterministic ordered-gate authority for R15.7.

    The engine only consumes immutable/redacted evidence. It never executes training,
    mutates router/tool configuration, or interprets model/dataset text as commands.
    """

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self.policy = policy or DecisionPolicy()

    def evaluate(
        self,
        benchmark: Mapping[str, object],
        *,
        base_model_ref: str,
        evidence: DecisionEvidence,
        dataset: Mapping[str, object] | None = None,
    ) -> GapDecision:
        if not base_model_ref:
            raise GapDecisionError("base_model_ref must not be empty")
        report, report_digest = _normalize_report(benchmark)
        suite_digest = report.get("suite_digest")
        config_digest = report.get("config_digest")
        if not isinstance(suite_digest, str) or not isinstance(config_digest, str):
            raise GapDecisionError("benchmark suite/config digests are required")
        _require_digest("suite_digest", suite_digest)
        _require_digest("config_digest", config_digest)
        protection_digest = _require_optional_digest(
            "protection_manifest_digest",
            report.get("protection_manifest_digest"),
        )
        base_model = _extract_model(report, base_model_ref)
        gaps, _, target_domains = _extract_gaps(report, base_model_ref)
        targets = _targets_for_gaps(report, base_model_ref, gaps, self.policy)
        dataset_id, dataset_digest, dataset_file_digest, counts = _normalize_dataset(dataset)
        train_counts = tuple(sorted((domain, counts[domain]) for domain in target_domains))

        disposition, blockers, reasons = self._decide(
            base_model=base_model,
            evidence=evidence,
            gaps=gaps,
            target_domains=target_domains,
            train_counts=dict(train_counts),
            dataset_present=dataset is not None,
        )
        adapter_method = (
            self.policy.adapter_method if disposition is DecisionDisposition.TRAIN else None
        )
        return GapDecision(
            disposition=disposition,
            base_model=base_model,
            benchmark_report_digest=report_digest,
            suite_digest=suite_digest,
            config_digest=config_digest,
            protection_manifest_digest=protection_digest,
            policy=self.policy,
            evidence=evidence,
            gaps=gaps,
            targets=targets,
            target_domains=target_domains,
            dataset_id=dataset_id,
            dataset_digest=dataset_digest,
            dataset_file_digest=dataset_file_digest,
            train_examples_by_domain=train_counts,
            blockers=blockers,
            reasons=reasons,
            adapter_method=adapter_method,
        )

    def _decide(
        self,
        *,
        base_model: Mapping[str, object],
        evidence: DecisionEvidence,
        gaps: Sequence[GapRecord],
        target_domains: Sequence[str],
        train_counts: Mapping[str, int],
        dataset_present: bool,
    ) -> tuple[DecisionDisposition, tuple[str, ...], tuple[str, ...]]:
        # Gate 1: immutable/reproducible base benchmark.
        if evidence.benchmark_reproducible is not True:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("benchmark_not_proven_reproducible",),
                ("A reproducible immutable before-benchmark is required.",),
            )
        model_digest = base_model.get("model_digest")
        if not isinstance(model_digest, str) or _DIGEST.fullmatch(model_digest) is None:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("base_model_identity_unresolved",),
                ("The selected base model requires an immutable digest.",),
            )

        # Gate 2: train/evaluation contamination validity.
        if evidence.contamination_valid is not True:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("contamination_validity_not_proven",),
                ("Benchmark/data contamination evidence must be explicitly valid.",),
            )

        # No measured weakness means specialization is unnecessary.
        if not gaps:
            return (
                DecisionDisposition.NO_TRAIN,
                (),
                ("The selected base model has no measured KodeBench gap.",),
            )

        # Gate 3: diagnose system-vs-model causes without mutating benchmark authority.
        probes = {item.component: item for item in evidence.diagnostics}
        missing = [
            item.value
            for item in self.policy.required_probe_components
            if item not in probes
        ]
        if missing:
            return (
                DecisionDisposition.INCONCLUSIVE,
                tuple(f"missing_probe:{item}" for item in missing),
                ("Required system diagnostic evidence is incomplete.",),
            )
        unknown = [
            item.component.value
            for item in probes.values()
            if item.status is ProbeStatus.UNKNOWN
        ]
        if unknown:
            return (
                DecisionDisposition.INCONCLUSIVE,
                tuple(f"unknown_probe:{item}" for item in sorted(unknown)),
                ("Unknown system diagnostic state cannot authorize training.",),
            )
        defects = []
        target_set = set(target_domains)
        for probe in probes.values():
            if probe.status is not ProbeStatus.DEFECT:
                continue
            if not probe.affected_domains or target_set.intersection(probe.affected_domains):
                defects.append(probe.component.value)
        if defects:
            return (
                DecisionDisposition.FIX_SYSTEM_FIRST,
                tuple(f"system_defect:{item}" for item in sorted(defects)),
                ("A tool/retrieval/router/context/product defect explains a target gap.",),
            )
        if evidence.expected_impact is ExpectedImpact.LOW:
            return (
                DecisionDisposition.NO_TRAIN,
                (),
                ("Expected model-training impact is explicitly below policy value.",),
            )
        if evidence.expected_impact is ExpectedImpact.UNKNOWN:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("expected_impact_unknown",),
                ("Expected training impact must be explicitly assessed.",),
            )

        # Gate 4: eligible curated data sufficiency for every target domain.
        if not dataset_present:
            return (
                DecisionDisposition.INSUFFICIENT_DATA,
                ("dataset_missing",),
                ("No immutable eligible dataset was supplied.",),
            )
        insufficient = [
            domain
            for domain in target_domains
            if train_counts.get(domain, 0) < self.policy.min_train_examples_per_domain
        ]
        if insufficient:
            return (
                DecisionDisposition.INSUFFICIENT_DATA,
                tuple(f"insufficient_domain:{item}" for item in insufficient),
                ("Each target domain requires the policy minimum of train examples.",),
            )

        # Gate 5: dataset and immutable base-model licence evidence.
        if (
            evidence.dataset_license is not PolicyDecision.ALLOW
            or evidence.base_model_license is not PolicyDecision.ALLOW
        ):
            blockers = []
            if evidence.dataset_license is not PolicyDecision.ALLOW:
                blockers.append(f"dataset_license:{evidence.dataset_license.value}")
            if evidence.base_model_license is not PolicyDecision.ALLOW:
                blockers.append(f"base_model_license:{evidence.base_model_license.value}")
            return (
                DecisionDisposition.LICENSE_BLOCKED,
                tuple(blockers),
                ("Training is blocked until dataset and base-model licence evidence is ALLOW.",),
            )

        # Gate 6: backend capability and declared resource budget.
        if evidence.backend_capability is BackendCapability.UNSUPPORTED:
            return (
                DecisionDisposition.UNSUPPORTED,
                ("backend_unsupported",),
                ("The requested adapter-training path is not supported by current evidence.",),
            )
        if evidence.backend_capability is BackendCapability.UNKNOWN:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("backend_capability_unknown",),
                ("Unknown backend capability cannot authorize training.",),
            )
        if evidence.budget_status is BudgetStatus.EXCEEDED:
            return (
                DecisionDisposition.BUDGET_BLOCKED,
                ("budget_exceeded",),
                ("Declared training resource/time budget is exceeded.",),
            )
        if evidence.budget_status is BudgetStatus.UNKNOWN:
            return (
                DecisionDisposition.BUDGET_BLOCKED,
                ("budget_not_declared",),
                ("A bounded resource/time budget is required before training.",),
            )

        # Gate 7: rollback readiness.
        if evidence.rollback_ready is not True:
            return (
                DecisionDisposition.INCONCLUSIVE,
                ("rollback_not_ready",),
                ("Rollback to the immutable base model must be proven ready.",),
            )

        return (
            DecisionDisposition.TRAIN,
            (),
            ("All ordered R15.7 gates authorize bounded adapter training.",),
        )


def evaluate_saved_decision(
    benchmark_path: Path,
    evidence_path: Path,
    *,
    base_model_ref: str,
    dataset_path: Path | None = None,
    policy: DecisionPolicy | None = None,
) -> GapDecision:
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    evidence_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    dataset = (
        json.loads(dataset_path.read_text(encoding="utf-8"))
        if dataset_path is not None
        else None
    )
    if not isinstance(benchmark, Mapping):
        raise GapDecisionError("benchmark file must contain a JSON object")
    if not isinstance(evidence_payload, Mapping):
        raise GapDecisionError("evidence file must contain a JSON object")
    if dataset is not None and not isinstance(dataset, Mapping):
        raise GapDecisionError("dataset file must contain a JSON object")
    return GapDecisionEngine(policy).evaluate(
        benchmark,
        base_model_ref=base_model_ref,
        evidence=DecisionEvidence.from_mapping(evidence_payload),
        dataset=dataset,
    )


def run_gap_decision_from_files(
    benchmark_path: Path,
    evidence_path: Path,
    output_path: Path,
    *,
    base_model_ref: str,
    dataset_path: Path | None = None,
) -> GapDecision:
    decision = evaluate_saved_decision(
        benchmark_path,
        evidence_path,
        base_model_ref=base_model_ref,
        dataset_path=dataset_path,
    )
    decision.save(output_path)
    return decision
