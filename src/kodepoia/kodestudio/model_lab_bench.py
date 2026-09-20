from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from kodepoia.bench.decision import DECISION_SCHEMA, DiagnosticComponent
from kodepoia.bench.kodebench import KODEBENCH_SCHEMA
from kodepoia.tuning.r15_ux import (
    R15UXService,
    R15WorkflowMode,
    R15WorkflowRequest,
)

BENCH_DECISION_SCHEMA = "kodepoia.v2.3.3.model-lab-bench-decision"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_JSON_FILES = 512
_DIGEST_LENGTH = 64
_EVIDENCE_ROOTS = (
    ".kodepoia/benchmarks",
    ".kodepoia/tuning",
)
_DIAGNOSTIC_COMPONENTS = (
    DiagnosticComponent.TOOL.value,
    DiagnosticComponent.RETRIEVAL.value,
    DiagnosticComponent.ROUTER.value,
    DiagnosticComponent.CONTEXT.value,
    DiagnosticComponent.PROMPT.value,
    DiagnosticComponent.PRODUCT.value,
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError:
        return "<external-path>"


def _bounded_json(path: Path) -> tuple[dict[str, object] | None, str]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        return None, f"unavailable:{exc}"
    if size > _MAX_JSON_BYTES:
        return None, "oversized"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid:{exc}"
    if not isinstance(payload, dict):
        return None, "invalid:root_not_object"
    return payload, "ready"


def _digest_is_valid(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == _DIGEST_LENGTH
        and all(char in "0123456789abcdef" for char in value)
    )


def _safe_mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _safe_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _report_summary(
    payload: Mapping[str, object],
    *,
    path: str,
) -> dict[str, object]:
    descriptor = dict(payload)
    claimed_report_digest = descriptor.pop("report_digest", None)
    observed_report_digest = _sha256_json(descriptor)

    suite = _safe_mapping(payload.get("suite"))
    config = _safe_mapping(payload.get("config"))
    claimed_suite_digest = payload.get("suite_digest")
    claimed_config_digest = payload.get("config_digest")
    observed_suite_digest = _sha256_json(dict(suite))
    observed_config_digest = _sha256_json(dict(config))

    report_integrity = (
        claimed_report_digest == observed_report_digest
        and claimed_suite_digest == observed_suite_digest
        and claimed_config_digest == observed_config_digest
        and _digest_is_valid(claimed_report_digest)
        and _digest_is_valid(claimed_suite_digest)
        and _digest_is_valid(claimed_config_digest)
        and payload.get("schema") == KODEBENCH_SCHEMA
    )

    identities: list[dict[str, object]] = []
    for raw in _safe_list(payload.get("model_identities")):
        if not isinstance(raw, Mapping):
            continue
        identities.append(
            {
                "model_ref": str(raw.get("model_ref", "")),
                "model_digest": raw.get("model_digest"),
                "resolved": bool(raw.get("resolved")),
                "runtime": str(raw.get("runtime", "")),
                "runtime_version": str(raw.get("runtime_version", "")),
            }
        )

    task_rows: dict[tuple[str, str, str], dict[str, object]] = {}
    for raw in _safe_list(payload.get("outcomes")):
        if not isinstance(raw, Mapping):
            continue
        model_ref = str(raw.get("model_ref", ""))
        task_id = str(raw.get("task_id", ""))
        domain = str(raw.get("domain", ""))
        key = (model_ref, task_id, domain)
        row = task_rows.setdefault(
            key,
            {
                "model_ref": model_ref,
                "task_id": task_id,
                "domain": domain,
                "critical": bool(raw.get("critical")),
                "passed": 0,
                "total": 0,
                "categories": set(),
                "errors": 0,
            },
        )
        row["passed"] = int(row["passed"]) + int(bool(raw.get("passed")))
        row["total"] = int(row["total"]) + 1
        categories = row["categories"]
        if isinstance(categories, set):
            categories.add(str(raw.get("category", "unknown")))
        if raw.get("error") is not None:
            row["errors"] = int(row["errors"]) + 1

    tasks: list[dict[str, object]] = []
    for key in sorted(task_rows):
        row = task_rows[key]
        total = int(row["total"])
        categories = row["categories"]
        tasks.append(
            {
                "model_ref": row["model_ref"],
                "task_id": row["task_id"],
                "domain": row["domain"],
                "critical": row["critical"],
                "passed": row["passed"],
                "total": total,
                "score": round(int(row["passed"]) / total, 4) if total else 0.0,
                "categories": sorted(categories) if isinstance(categories, set) else [],
                "errors": row["errors"],
            }
        )

    suite_tasks: list[dict[str, object]] = []
    for raw in _safe_list(suite.get("tasks")):
        if not isinstance(raw, Mapping):
            continue
        scorer = _safe_mapping(raw.get("scorer"))
        suite_tasks.append(
            {
                "task_id": str(raw.get("task_id", "")),
                "domain": str(raw.get("domain", "")),
                "critical": bool(raw.get("critical")),
                "prompt_digest": raw.get("prompt_digest"),
                "protected_holdout_id": raw.get("protected_holdout_id"),
                "scorer_digest": raw.get("scorer_digest", scorer.get("digest")),
            }
        )

    return {
        "report_digest": claimed_report_digest,
        "observed_report_digest": observed_report_digest,
        "integrity": "ready" if report_integrity else "tampered",
        "suite_id": str(suite.get("suite_id", "")),
        "suite_version": str(suite.get("version", "")),
        "suite_digest": claimed_suite_digest,
        "config_digest": claimed_config_digest,
        "protection_manifest_digest": payload.get("protection_manifest_digest"),
        "config": dict(config),
        "models": sorted(identities, key=lambda item: str(item["model_ref"])),
        "suite_tasks": sorted(
            suite_tasks,
            key=lambda item: (str(item["domain"]), str(item["task_id"])),
        ),
        "task_results": tasks,
        "summary": dict(_safe_mapping(payload.get("summary"))),
        "path": path,
        "raw_prompts_exposed": False,
        "raw_responses_exposed": False,
    }


def _decision_summary(
    payload: Mapping[str, object],
    *,
    path: str,
    accepted_report_digests: set[str],
) -> dict[str, object]:
    descriptor = dict(payload)
    claimed_decision_digest = descriptor.pop("decision_digest", None)
    observed_decision_digest = _sha256_json(descriptor)
    integrity = (
        claimed_decision_digest == observed_decision_digest
        and _digest_is_valid(claimed_decision_digest)
        and payload.get("schema") == DECISION_SCHEMA
    )

    benchmark = _safe_mapping(payload.get("benchmark"))
    report_digest = benchmark.get("report_digest")
    benchmark_bound = (
        isinstance(report_digest, str)
        and report_digest in accepted_report_digests
    )

    base_model = dict(_safe_mapping(payload.get("base_model")))
    dataset = dict(_safe_mapping(payload.get("dataset")))
    evidence = _safe_mapping(payload.get("evidence"))

    diagnostic_rows: dict[str, dict[str, object]] = {
        component: {
            "component": component,
            "status": "not_evidenced",
            "affected_domains": [],
            "evidence_digest": None,
        }
        for component in _DIAGNOSTIC_COMPONENTS
    }
    for raw in _safe_list(evidence.get("diagnostics")):
        if not isinstance(raw, Mapping):
            continue
        component = str(raw.get("component", ""))
        diagnostic_rows.setdefault(
            component,
            {
                "component": component,
                "status": "not_evidenced",
                "affected_domains": [],
                "evidence_digest": None,
            },
        )
        diagnostic_rows[component] = {
            "component": component,
            "status": str(raw.get("status", "unknown")),
            "affected_domains": [
                str(value)
                for value in _safe_list(raw.get("affected_domains"))
                if isinstance(value, str)
            ],
            "evidence_digest": raw.get("evidence_digest"),
        }

    gaps = [
        {
            "task_id": str(raw.get("task_id", "")),
            "domain": str(raw.get("domain", "")),
            "critical": bool(raw.get("critical")),
            "passed": raw.get("passed"),
            "total": raw.get("total"),
            "score": raw.get("score"),
            "categories": [
                str(value)
                for value in _safe_list(raw.get("categories"))
                if isinstance(value, str)
            ],
        }
        for raw in _safe_list(payload.get("gaps"))
        if isinstance(raw, Mapping)
    ]
    targets = [
        {
            "domain": str(raw.get("domain", "")),
            "baseline_score": raw.get("baseline_score"),
            "minimum_score": raw.get("minimum_score"),
            "critical": bool(raw.get("critical")),
        }
        for raw in _safe_list(payload.get("targets"))
        if isinstance(raw, Mapping)
    ]
    disposition = str(payload.get("disposition", "inconclusive"))

    model_diagnosis = "no_measured_gap"
    if gaps:
        defect = any(row.get("status") == "defect" for row in diagnostic_rows.values())
        unknown = any(row.get("status") == "unknown" for row in diagnostic_rows.values())
        if defect:
            model_diagnosis = "system_explained_gap"
        elif unknown:
            model_diagnosis = "inconclusive_gap"
        else:
            model_diagnosis = "measured_model_gap_candidate"

    blockers = [
        str(value)
        for value in _safe_list(payload.get("blockers"))
        if isinstance(value, str)
    ]
    reasons = [
        str(value)
        for value in _safe_list(payload.get("reasons"))
        if isinstance(value, str)
    ]
    target_domains = [
        str(value)
        for value in _safe_list(payload.get("target_domains"))
        if isinstance(value, str)
    ]

    dataset_digest = dataset.get("dataset_digest")
    base_digest = base_model.get("model_digest")
    train_bound = (
        disposition == "train"
        and integrity
        and benchmark_bound
        and _digest_is_valid(base_digest)
        and isinstance(dataset.get("dataset_id"), str)
        and bool(str(dataset.get("dataset_id", "")).strip())
        and _digest_is_valid(dataset_digest)
    )

    return {
        "decision_digest": claimed_decision_digest,
        "observed_decision_digest": observed_decision_digest,
        "integrity": "ready" if integrity else "tampered",
        "disposition": disposition,
        "base_model": base_model,
        "benchmark": dict(benchmark),
        "benchmark_bound": benchmark_bound,
        "dataset": dataset,
        "dataset_bound": bool(
            isinstance(dataset.get("dataset_id"), str)
            and str(dataset.get("dataset_id", "")).strip()
            and _digest_is_valid(dataset_digest)
        ),
        "gaps": gaps,
        "target_domains": target_domains,
        "targets": targets,
        "diagnostics": [
            diagnostic_rows[key]
            for key in _DIAGNOSTIC_COMPONENTS
            if key in diagnostic_rows
        ],
        "model_diagnosis": model_diagnosis,
        "blockers": blockers,
        "reasons": reasons,
        "evidence_digest": payload.get("evidence_digest"),
        "policy_digest": payload.get("policy_digest"),
        "train_evidence_bound": train_bound,
        "training_launch_exposed": False,
        "path": path,
    }


class ModelLabBenchDecisionService:
    """V2.3.3 projection of accepted KodeBench and GapDecision evidence.

    The facade never reimplements the R15.7 decision gates. Persisted dispositions
    are inspected as immutable evidence, while typed actions delegate exclusively
    to R15UXService. Training, conversion and promotion controls are intentionally
    absent in this subdivision.
    """

    schema = BENCH_DECISION_SCHEMA

    def __init__(
        self,
        project_root: Path,
        *,
        r15_service: R15UXService | None = None,
    ) -> None:
        self.root = Path(project_root).resolve(strict=False)
        self.r15 = r15_service or R15UXService.for_project(self.root)
        if self.r15.root != self.root:
            raise ValueError(
                "R15 UX service project root does not match Bench & Decision project root"
            )

    @classmethod
    def for_project(cls, project_root: Path) -> "ModelLabBenchDecisionService":
        return cls(project_root)

    def _evidence(self) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
        reports: list[dict[str, object]] = []
        raw_decisions: list[tuple[Mapping[str, object], str]] = []
        invalid: list[dict[str, object]] = []
        remaining = _MAX_JSON_FILES

        for relative_root in _EVIDENCE_ROOTS:
            root = self.root / relative_root
            if not root.is_dir() or remaining <= 0:
                continue
            files = sorted(
                (path for path in root.rglob("*.json") if path.is_file()),
                key=lambda path: path.as_posix(),
            )[:remaining]
            remaining -= len(files)
            for path in files:
                payload, state = _bounded_json(path)
                relative = _relative(self.root, path)
                if payload is None:
                    invalid.append(
                        {
                            "path": relative,
                            "state": state,
                            "kind": "invalid_json",
                        }
                    )
                    continue
                schema = str(payload.get("schema", ""))
                if schema == KODEBENCH_SCHEMA:
                    reports.append(_report_summary(payload, path=relative))
                elif schema == DECISION_SCHEMA:
                    raw_decisions.append((payload, relative))

        accepted_report_digests = {
            str(item.get("report_digest"))
            for item in reports
            if item.get("integrity") == "ready"
            and isinstance(item.get("report_digest"), str)
        }
        decisions = [
            _decision_summary(
                payload,
                path=path,
                accepted_report_digests=accepted_report_digests,
            )
            for payload, path in raw_decisions
        ]
        reports.sort(key=lambda item: (str(item.get("suite_id")), str(item.get("report_digest"))))
        decisions.sort(key=lambda item: str(item.get("decision_digest")))
        return reports, decisions, invalid

    def _action_state(self, domain: str, action: str) -> dict[str, object]:
        spec = self.r15.action(domain, action)
        return {
            "workflow": spec.key,
            "mutation": spec.mutation,
            "available": spec.key in self.r15.handlers,
            "terminal_mode": spec.terminal_mode.value,
            "identifier_required": spec.identifier_required,
        }

    def snapshot(self) -> dict[str, object]:
        reports, decisions, invalid = self._evidence()
        disposition_counts: dict[str, int] = {}
        for item in decisions:
            disposition = str(item.get("disposition", "inconclusive"))
            disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1

        return {
            "schema": self.schema,
            "status": "ok",
            "project_root": ".",
            "reports": reports,
            "decisions": decisions,
            "invalid_evidence": invalid,
            "summary": {
                "report_count": len(reports),
                "ready_reports": sum(item.get("integrity") == "ready" for item in reports),
                "decision_count": len(decisions),
                "ready_decisions": sum(item.get("integrity") == "ready" for item in decisions),
                "benchmark_bound_decisions": sum(bool(item.get("benchmark_bound")) for item in decisions),
                "dispositions": dict(sorted(disposition_counts.items())),
            },
            "actions": {
                "bench_status": self._action_state("bench", "status"),
                "bench_run": self._action_state("bench", "run"),
                "gap_diagnose": self._action_state("gap", "diagnose"),
            },
            "reference_context": {
                "state": "data_only",
                "project_knowledge": "reference_only",
                "research_packs": "reference_only",
                "retrieved_context": "reference_only",
                "instruction_authority": False,
                "auto_training_ingest": False,
            },
            "mutations": {
                "benchmark_run": True,
                "training": False,
                "training_cancel": False,
                "training_recovery": False,
                "conversion": False,
                "promotion": False,
                "rollback": False,
            },
        }

    def inspect_benchmark_status(self) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="bench",
                action="status",
                mode=R15WorkflowMode.INSPECT,
            )
        )

    def preview_benchmark_run(self) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="bench",
                action="run",
                mode=R15WorkflowMode.DRY_RUN,
            )
        )

    def run_benchmark(self, *, confirmed: bool = False) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="bench",
                action="run",
                mode=R15WorkflowMode.APPLY,
                confirmed=confirmed,
            )
        )

    def inspect_gap_decision(self, decision_id: str) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="gap",
                action="diagnose",
                mode=R15WorkflowMode.INSPECT,
                identifier=decision_id,
            )
        )


__all__ = ["BENCH_DECISION_SCHEMA", "ModelLabBenchDecisionService"]
