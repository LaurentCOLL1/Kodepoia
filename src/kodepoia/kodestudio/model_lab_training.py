from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from kodepoia.kodestudio.model_lab_bench import ModelLabBenchDecisionService
from kodepoia.tuning.contracts import CAPABILITY_SCHEMA
from kodepoia.tuning.kaggle_remote import load_training_plan
from kodepoia.tuning.r15_ux import R15UXService, R15WorkflowMode, R15WorkflowRequest
from kodepoia.tuning.training import TRAINING_SCHEMA, TrainingAuthorization

TRAINING_WORKSPACE_SCHEMA = "kodepoia.v2.3.4.model-lab-training"
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_JSON_FILES = 512
_EVIDENCE_ROOTS = (".kodepoia/tuning", "tuning-runs")


class TrainingUXError(RuntimeError):
    """Raised when a V2.3.4 training UX operation fails closed."""


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
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid:{exc}"
    if not isinstance(raw, dict):
        return None, "invalid:root_not_object"
    return raw, "ready"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _digest_ready(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _report_integrity(payload: Mapping[str, object], digest_key: str) -> tuple[str, str | None]:
    descriptor = dict(payload)
    claimed = descriptor.pop(digest_key, None)
    observed = _sha256_json(descriptor)
    if claimed == observed and _digest_ready(claimed):
        return "ready", observed
    return "tampered", observed


class ModelLabTrainingService:
    """V2.3.4 facade over accepted R15 training/runtime contracts."""

    schema = TRAINING_WORKSPACE_SCHEMA

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
                "R15 UX service project root does not match Training workspace project root"
            )

    @classmethod
    def for_project(cls, project_root: Path) -> "ModelLabTrainingService":
        return cls(project_root)

    def _files(self) -> list[Path]:
        files: list[Path] = []
        remaining = _MAX_JSON_FILES
        for relative_root in _EVIDENCE_ROOTS:
            root = self.root / relative_root
            if not root.is_dir() or remaining <= 0:
                continue
            found = sorted(
                (path for path in root.rglob("*.json") if path.is_file()),
                key=lambda path: path.as_posix(),
            )[:remaining]
            files.extend(found)
            remaining -= len(found)
        return files

    def _capabilities(
        self,
        files: list[Path],
    ) -> tuple[list[dict[str, object]], set[str], list[dict[str, object]]]:
        rows: list[dict[str, object]] = []
        ready_digests: set[str] = set()
        invalid: list[dict[str, object]] = []
        for path in files:
            payload, state = _bounded_json(path)
            if payload is None:
                invalid.append(
                    {"kind": "invalid_json", "path": _relative(self.root, path), "state": state}
                )
                continue
            if payload.get("schema") != CAPABILITY_SCHEMA:
                continue
            integrity, observed = _report_integrity(payload, "report_digest")
            digest = payload.get("report_digest")
            if integrity == "ready" and isinstance(digest, str):
                ready_digests.add(digest)
            rows.append(
                {
                    "report_digest": digest,
                    "observed_report_digest": observed,
                    "integrity": integrity,
                    "disposition": str(payload.get("disposition", "unknown")),
                    "backend": str(payload.get("backend", "unknown")),
                    "backend_capability": str(payload.get("backend_capability", "unknown")),
                    "dtype_supported": payload.get("dtype_supported"),
                    "four_bit_supported": payload.get("four_bit_supported"),
                    "model_load": payload.get("model_load"),
                    "resources": dict(_mapping(payload.get("resources"))),
                    "blockers": [str(item) for item in _list(payload.get("blockers"))],
                    "path": _relative(self.root, path),
                }
            )
        rows.sort(key=lambda item: str(item.get("report_digest")))
        return rows, ready_digests, invalid

    def _decisions(self) -> list[dict[str, object]]:
        payload = ModelLabBenchDecisionService(self.root, r15_service=self.r15).snapshot()
        return [item for item in _list(payload.get("decisions")) if isinstance(item, dict)]

    def _plan_decision(
        self,
        *,
        model: Mapping[str, object],
        dataset: Mapping[str, object],
        decisions: list[dict[str, object]],
    ) -> dict[str, object] | None:
        matches: list[dict[str, object]] = []
        for item in decisions:
            base = _mapping(item.get("base_model"))
            bound_dataset = _mapping(item.get("dataset"))
            if (
                item.get("integrity") == "ready"
                and item.get("disposition") == "train"
                and bool(item.get("train_evidence_bound"))
                and base.get("model_ref") == model.get("model_ref")
                and base.get("model_digest") == model.get("model_digest")
                and bound_dataset.get("dataset_id") == dataset.get("dataset_id")
                and bound_dataset.get("dataset_digest") == dataset.get("dataset_digest")
            ):
                matches.append(item)
        if not matches:
            return None
        matches.sort(key=lambda item: str(item.get("decision_digest")))
        return matches[0]

    def _plans(
        self,
        files: list[Path],
        *,
        ready_capability_digests: set[str],
        decisions: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        seen: set[str] = set()
        for path in files:
            payload, _state = _bounded_json(path)
            if payload is None:
                continue
            if "plan_digest" not in payload or "model" not in payload or "dataset_paths" not in payload:
                continue
            try:
                plan = load_training_plan(path)
            except Exception as exc:
                rows.append(
                    {
                        "plan_digest": payload.get("plan_digest"),
                        "run_id": payload.get("run_id"),
                        "integrity": "tampered",
                        "authorized": False,
                        "blockers": [f"invalid_training_plan:{type(exc).__name__}"],
                        "path": _relative(self.root, path),
                    }
                )
                continue
            if plan.digest in seen:
                continue
            seen.add(plan.digest)
            integrity = (
                "ready"
                if payload.get("plan_digest") == plan.digest
                and payload.get("run_id") in {None, plan.run_id}
                else "tampered"
            )
            model = plan.model.to_dict()
            dataset = plan.dataset.to_dict()
            decision = self._plan_decision(model=model, dataset=dataset, decisions=decisions)
            capability_bound = (
                plan.capability_report_digest is not None
                and plan.capability_report_digest in ready_capability_digests
            )
            blockers: list[str] = []
            if integrity != "ready":
                blockers.append("plan_integrity_invalid")
            if plan.authorization is not TrainingAuthorization.TRAIN:
                blockers.append("train_authorization_missing")
            if decision is None:
                blockers.append("accepted_train_decision_missing")
            if plan.capability_report_digest is None:
                blockers.append("capability_report_missing")
            elif not capability_bound:
                blockers.append("capability_report_unverified")
            if plan.dataset.train_path is None or plan.dataset.validation_path is None:
                blockers.append("governed_dataset_paths_missing")
            rows.append(
                {
                    "plan_digest": plan.digest,
                    "run_id": plan.run_id,
                    "integrity": integrity,
                    "authorization": plan.authorization.value,
                    "authorized": not blockers,
                    "blockers": blockers,
                    "decision_digest": None if decision is None else decision.get("decision_digest"),
                    "mode": plan.mode.value,
                    "model": model,
                    "dataset": dataset,
                    "dataset_paths_bound": (
                        plan.dataset.train_path is not None
                        and plan.dataset.validation_path is not None
                    ),
                    "lora": plan.lora.to_dict(),
                    "sft": plan.sft.to_dict(),
                    "quantization": plan.quantization.value,
                    "seeds": plan.seeds.to_dict(),
                    "resources": plan.resources.to_dict(),
                    "timeout_seconds": float(plan.timeout_seconds),
                    "capability_report_digest": plan.capability_report_digest,
                    "capability_bound": capability_bound,
                    "path": _relative(self.root, path),
                }
            )
        rows.sort(key=lambda item: str(item.get("plan_digest")))
        return rows

    def _runs(
        self,
        files: list[Path],
        plans_by_digest: Mapping[str, dict[str, object]],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        seen: set[tuple[str, str]] = set()
        for path in files:
            payload, _state = _bounded_json(path)
            if payload is None or payload.get("schema") != TRAINING_SCHEMA:
                continue
            plan_digest = str(payload.get("plan_digest", ""))
            run_id = str(payload.get("run_id", ""))
            key = (run_id, str(payload.get("report_digest", "")))
            if key in seen:
                continue
            seen.add(key)
            integrity, observed = _report_integrity(payload, "report_digest")
            plan_bound = (
                plan_digest in plans_by_digest
                and plans_by_digest[plan_digest].get("integrity") == "ready"
            )
            checkpoints: list[dict[str, object]] = []
            for raw in _list(payload.get("checkpoints")):
                if not isinstance(raw, Mapping):
                    continue
                checkpoint = {
                    "checkpoint_id": str(raw.get("checkpoint_id", "")),
                    "plan_digest": str(raw.get("plan_digest", "")),
                    "step": raw.get("step"),
                    "artifact_digest": raw.get("artifact_digest"),
                    "train_loss": raw.get("train_loss"),
                    "eval_loss": raw.get("eval_loss"),
                }
                checkpoint["lineage_bound"] = (
                    checkpoint["plan_digest"] == plan_digest
                    and plan_bound
                    and _digest_ready(checkpoint["artifact_digest"])
                )
                checkpoints.append(checkpoint)
            checkpoints.sort(key=lambda item: int(item.get("step") or 0))
            rows.append(
                {
                    "report_digest": payload.get("report_digest"),
                    "observed_report_digest": observed,
                    "integrity": integrity,
                    "plan_digest": plan_digest,
                    "plan_bound": plan_bound,
                    "run_id": run_id,
                    "state": str(payload.get("state", "unknown")),
                    "completed_steps": payload.get("completed_steps"),
                    "train_loss": payload.get("train_loss"),
                    "eval_loss": payload.get("eval_loss"),
                    "checkpoints": checkpoints,
                    "resumed_from": payload.get("resumed_from"),
                    "resource_maxima": dict(_mapping(payload.get("resource_maxima"))),
                    "blockers": [str(item) for item in _list(payload.get("blockers"))],
                    "path": _relative(self.root, path),
                }
            )
        rows.sort(key=lambda item: (str(item.get("run_id")), str(item.get("report_digest"))))
        return rows

    def _action_state(self, action: str) -> dict[str, object]:
        spec = self.r15.action("training", action)
        return {
            "workflow": spec.key,
            "mutation": spec.mutation,
            "available": spec.key in self.r15.handlers,
            "terminal_mode": spec.terminal_mode.value,
            "identifier_required": spec.identifier_required,
        }

    def snapshot(self) -> dict[str, object]:
        files = self._files()
        capabilities, ready_capability_digests, invalid = self._capabilities(files)
        decisions = self._decisions()
        plans = self._plans(
            files,
            ready_capability_digests=ready_capability_digests,
            decisions=decisions,
        )
        plans_by_digest = {
            str(item["plan_digest"]): item
            for item in plans
            if isinstance(item.get("plan_digest"), str)
        }
        runs = self._runs(files, plans_by_digest)
        return {
            "schema": self.schema,
            "status": "ok",
            "project_root": ".",
            "plans": plans,
            "capabilities": capabilities,
            "runs": runs,
            "invalid_evidence": invalid,
            "summary": {
                "plan_count": len(plans),
                "authorized_plans": sum(bool(item.get("authorized")) for item in plans),
                "capability_count": len(capabilities),
                "run_count": len(runs),
                "active_runs": sum(
                    str(item.get("state"))
                    not in {
                        "completed",
                        "cancelled",
                        "timed_out",
                        "failed",
                        "budget_blocked",
                        "unsupported",
                    }
                    for item in runs
                ),
            },
            "actions": {
                key: self._action_state(key)
                for key in ("doctor", "plan", "run", "status", "cancel", "resume")
            },
            "backends": [
                {"id": "local", "label": "Local", "readiness": "requires_training_doctor"},
                {
                    "id": "kaggle",
                    "label": "Kaggle T4",
                    "readiness": "requires_training_doctor",
                    "accelerator": "NvidiaTeslaT4",
                    "gpu_count_claim": None,
                    "aggregate_vram_claim": None,
                },
            ],
            "reference_context": {
                "state": "data_only",
                "project_knowledge": "reference_only",
                "research_packs": "reference_only",
                "retrieved_context": "reference_only",
                "instruction_authority": False,
                "auto_training_ingest": False,
            },
            "later_mutations": {
                "conversion": False,
                "candidate_evaluation": False,
                "promotion": False,
                "rollback": False,
                "public_publish": False,
            },
        }

    @staticmethod
    def _backend(backend: str) -> str:
        normalized = backend.strip().lower()
        if normalized not in {"local", "kaggle"}:
            raise TrainingUXError("training backend must be local or kaggle")
        return normalized

    def _plan(self, plan_digest: str) -> dict[str, object]:
        for item in self.snapshot()["plans"]:
            if isinstance(item, dict) and item.get("plan_digest") == plan_digest:
                return item
        raise TrainingUXError("training plan identity is not available in governed evidence")

    def _authorized_plan(self, plan_digest: str) -> dict[str, object]:
        plan = self._plan(plan_digest)
        if not bool(plan.get("authorized")):
            blockers = ", ".join(str(item) for item in _list(plan.get("blockers")))
            raise TrainingUXError(f"training plan is not launch-authorized: {blockers}")
        return plan

    def _run(self, run_id: str) -> dict[str, object]:
        for item in self.snapshot()["runs"]:
            if isinstance(item, dict) and item.get("run_id") == run_id:
                return item
        raise TrainingUXError("training run identity is not available in governed evidence")

    def inspect_doctor(self, backend: str) -> dict[str, object]:
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="doctor",
                mode=R15WorkflowMode.INSPECT,
                backend=self._backend(backend),
            )
        )

    def inspect_plan(self, plan_digest: str) -> dict[str, object]:
        self._plan(plan_digest)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="plan",
                mode=R15WorkflowMode.INSPECT,
                identifier=plan_digest,
            )
        )

    def preview_run(self, plan_digest: str, backend: str) -> dict[str, object]:
        self._authorized_plan(plan_digest)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="run",
                mode=R15WorkflowMode.DRY_RUN,
                identifier=plan_digest,
                backend=self._backend(backend),
            )
        )

    def run_training(
        self,
        plan_digest: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        self._authorized_plan(plan_digest)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="run",
                mode=R15WorkflowMode.APPLY,
                identifier=plan_digest,
                backend=self._backend(backend),
                confirmed=confirmed,
            )
        )

    def inspect_run(self, run_id: str, backend: str) -> dict[str, object]:
        self._run(run_id)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="status",
                mode=R15WorkflowMode.INSPECT,
                identifier=run_id,
                backend=self._backend(backend),
            )
        )

    def cancel_run(
        self,
        run_id: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        self._run(run_id)
        return self.r15.execute(
            R15WorkflowRequest(
                domain="training",
                action="cancel",
                mode=R15WorkflowMode.CANCEL,
                identifier=run_id,
                backend=self._backend(backend),
                confirmed=confirmed,
            )
        )

    def resume_checkpoint(
        self,
        checkpoint_id: str,
        backend: str,
        *,
        confirmed: bool = False,
    ) -> dict[str, object]:
        for run in self.snapshot()["runs"]:
            if not isinstance(run, dict):
                continue
            for checkpoint in _list(run.get("checkpoints")):
                if not isinstance(checkpoint, dict):
                    continue
                if checkpoint.get("checkpoint_id") != checkpoint_id:
                    continue
                if not bool(checkpoint.get("lineage_bound")):
                    raise TrainingUXError("checkpoint lineage is not bound to a valid training plan")
                plan_digest = str(checkpoint.get("plan_digest", ""))
                self._authorized_plan(plan_digest)
                return self.r15.execute(
                    R15WorkflowRequest(
                        domain="training",
                        action="resume",
                        mode=R15WorkflowMode.APPLY,
                        identifier=checkpoint_id,
                        parent_identifier=plan_digest,
                        backend=self._backend(backend),
                        confirmed=confirmed,
                    )
                )
        raise TrainingUXError("checkpoint identity is not available in governed evidence")


__all__ = ["TRAINING_WORKSPACE_SCHEMA", "ModelLabTrainingService", "TrainingUXError"]
