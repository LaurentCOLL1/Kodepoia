from __future__ import annotations

import contextlib
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Protocol

from kodepoia.core.kill_switch import GLOBAL_KILL_SWITCH, KillSwitch
from kodepoia.core.sandbox import ProcessSandbox

from .contracts import CapabilityReport, RuntimeDisposition
from .runtime import HostResourceProbe, SandboxRunner, redact_runtime_text
from .training_contracts import (
    CheckpointRecord,
    TrainingEngine,
    TrainingPlan,
    TrainingPlanError,
    TrainingRunReport,
    TrainingRunState,
)

_MAX_CAPTURE_CHARS = 8192


class ResourceSampler(Protocol):
    def sample(self, root: Path): ...


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise TrainingPlanError("training path escapes the runtime root") from exc
    return candidate


def _checkpoint_from_dict(value: object) -> CheckpointRecord:
    if not isinstance(value, dict):
        raise TrainingPlanError("checkpoint evidence must be an object")
    allowed = {
        "base_model_digest",
        "checkpoint_path",
        "dataset_manifest_digest",
        "plan_digest",
        "state_digest",
        "step",
        "tokenizer_digest",
        "train_split_digest",
    }
    if set(value) != allowed:
        raise TrainingPlanError("checkpoint evidence fields are invalid")
    return CheckpointRecord(**value)


def _safe_worker_output(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TrainingPlanError("training worker output must be an object")
    allowed = {
        "adapter_digest",
        "adapter_path",
        "checkpoint",
        "eval_loss",
        "packages",
        "state",
        "steps_completed",
        "train_loss",
    }
    unknown = set(value) - allowed
    if unknown:
        raise TrainingPlanError("training worker output contains unsupported fields")
    packages = value.get("packages", {})
    if not isinstance(packages, dict) or not all(
        isinstance(name, str) and (version is None or isinstance(version, str))
        for name, version in packages.items()
    ):
        raise TrainingPlanError("training worker package evidence is invalid")
    return value


class TrainingOrchestrator:
    """R15.9 bounded launcher; dataset/model text never becomes argv or shell input."""

    def __init__(
        self,
        root: Path,
        *,
        kill_switch: KillSwitch | None = None,
        sandbox: SandboxRunner | None = None,
        resource_probe: ResourceSampler | None = None,
    ) -> None:
        self.root = root.resolve(strict=False)
        self.root.mkdir(parents=True, exist_ok=True)
        self.kill_switch = kill_switch or GLOBAL_KILL_SWITCH
        self.sandbox = sandbox or ProcessSandbox(
            self.root,
            allowed_executables={Path(sys.executable).name},
            kill_switch=self.kill_switch,
        )
        self.resource_probe = resource_probe or HostResourceProbe()

    def run(
        self,
        plan: TrainingPlan,
        *,
        capability: CapabilityReport | None = None,
        resume_checkpoint: str | None = None,
    ) -> TrainingRunReport:
        run_id = hashlib.sha256(
            f"{plan.digest}:{resume_checkpoint or 'start'}".encode("utf-8")
        ).hexdigest()[:16]

        host = self.resource_probe.sample(self.root)
        blockers: list[str] = []
        if host.disk_free_bytes is None:
            blockers.append("storage_budget_unknown")
        elif host.disk_free_bytes < plan.budget.disk_limit_bytes:
            blockers.append("storage_budget_exceeded")
        if host.ram_free_bytes is None:
            blockers.append("ram_budget_unknown")
        elif host.ram_free_bytes < plan.budget.ram_limit_bytes:
            blockers.append("ram_budget_exceeded")
        if blockers:
            return self._terminal(plan, run_id, TrainingRunState.BUDGET_BLOCKED, tuple(sorted(blockers)))

        split_blocker = self._validate_dataset_bindings(plan)
        if split_blocker is not None:
            return self._terminal(plan, run_id, TrainingRunState.FAILED, (split_blocker,))

        if plan.engine is TrainingEngine.TRL_PEFT:
            capability_blocker = self._validate_capability(plan, capability)
            if capability_blocker is not None:
                return self._terminal(plan, run_id, TrainingRunState.UNSUPPORTED, (capability_blocker,))

        if resume_checkpoint is not None:
            resume_blocker = self._validate_resume(plan, resume_checkpoint)
            if resume_blocker is not None:
                return self._terminal(plan, run_id, TrainingRunState.FAILED, (resume_blocker,))

        output_dir = f"runs/{run_id}"
        payload = plan.worker_payload(output_dir=output_dir, resume_checkpoint=resume_checkpoint)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="r15_9_",
            dir=self.root,
            delete=False,
        ) as handle:
            config_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        try:
            with contextlib.suppress(OSError):
                config_path.chmod(0o600)
            argv = [sys.executable, "-m", "kodepoia.tuning.training_worker", config_path.name]
            try:
                result = self.sandbox.run(
                    argv,
                    cwd=self.root,
                    timeout=float(plan.budget.timeout_seconds),
                    env={},
                )
            except RuntimeError as exc:
                state = TrainingRunState.CANCELLED if self.kill_switch.triggered else TrainingRunState.FAILED
                return self._terminal(plan, run_id, state, (state.value,), stderr=str(exc))
        finally:
            config_path.unlink(missing_ok=True)

        stderr = redact_runtime_text(result.stderr)[:_MAX_CAPTURE_CHARS]
        if result.timed_out:
            return self._terminal(plan, run_id, TrainingRunState.TIMED_OUT, ("timed_out",), stderr=stderr)
        if result.cancelled:
            return self._terminal(plan, run_id, TrainingRunState.CANCELLED, ("cancelled",), stderr=stderr)
        if result.returncode != 0:
            combined = redact_runtime_text("\n".join(filter(None, (stderr, result.stdout))))[:_MAX_CAPTURE_CHARS]
            return self._terminal(plan, run_id, TrainingRunState.FAILED, ("worker_failed",), stderr=combined)

        try:
            evidence = _safe_worker_output(json.loads(result.stdout))
            state = TrainingRunState(str(evidence["state"]))
            checkpoint = (
                None
                if evidence.get("checkpoint") is None
                else _checkpoint_from_dict(evidence["checkpoint"])
            )
            adapter_path = None if evidence.get("adapter_path") is None else str(evidence["adapter_path"])
            adapter_digest = None if evidence.get("adapter_digest") is None else str(evidence["adapter_digest"])
            if adapter_path is not None:
                adapter_file = _inside(self.root, adapter_path)
                if not adapter_file.is_file() or _sha256_file(adapter_file) != adapter_digest:
                    raise TrainingPlanError("adapter artifact digest mismatch")
            if checkpoint is not None:
                checkpoint_dir = _inside(self.root, checkpoint.checkpoint_path)
                metadata = checkpoint_dir / "kodepoia_checkpoint.json"
                state_file = checkpoint_dir / "fixture_state.json"
                if not state_file.is_file():
                    state_file = checkpoint_dir / "trainer_state.json"
                if not checkpoint_dir.is_dir() or not metadata.is_file() or not state_file.is_file():
                    raise TrainingPlanError("checkpoint artifact is incomplete")
                if _sha256_file(state_file) != checkpoint.state_digest:
                    raise TrainingPlanError("checkpoint state digest mismatch")
                recorded = _checkpoint_from_dict(json.loads(metadata.read_text(encoding="utf-8")))
                if recorded != checkpoint:
                    raise TrainingPlanError("checkpoint metadata mismatch")
            packages = tuple(sorted((str(k), None if v is None else str(v)) for k, v in dict(evidence.get("packages", {})).items()))
            return TrainingRunReport(
                state=state,
                plan_digest=plan.digest,
                source_sha=plan.source_sha,
                run_id=run_id,
                adapter_path=adapter_path,
                adapter_digest=adapter_digest,
                checkpoint=checkpoint,
                train_loss=None if evidence.get("train_loss") is None else float(evidence["train_loss"]),
                eval_loss=None if evidence.get("eval_loss") is None else float(evidence["eval_loss"]),
                steps_completed=int(evidence.get("steps_completed", 0)),
                packages=packages,
                blockers=(),
                stderr=stderr,
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, TrainingPlanError) as exc:
            combined = redact_runtime_text("\n".join(filter(None, (stderr, str(exc), result.stdout))))[:_MAX_CAPTURE_CHARS]
            return self._terminal(plan, run_id, TrainingRunState.FAILED, ("invalid_worker_evidence",), stderr=combined)

    def _validate_dataset_bindings(self, plan: TrainingPlan) -> str | None:
        train = _inside(self.root, plan.train_path)
        if not train.is_file():
            return "train_split_missing"
        if _sha256_file(train) != plan.train_split_digest:
            return "train_split_digest_mismatch"
        if plan.validation_path is not None:
            validation = _inside(self.root, plan.validation_path)
            if not validation.is_file():
                return "validation_split_missing"
            if _sha256_file(validation) != plan.validation_split_digest:
                return "validation_split_digest_mismatch"
        return None

    def _validate_capability(self, plan: TrainingPlan, capability: CapabilityReport | None) -> str | None:
        if capability is None:
            return "r15_8_capability_required"
        if capability.disposition is not RuntimeDisposition.READY:
            return "r15_8_capability_not_ready"
        if capability.backend is not plan.backend:
            return "backend_capability_mismatch"
        if plan.quantization.value != "none" and capability.four_bit_supported is not True:
            return "four_bit_capability_missing"
        if capability.dtype_supported is not True:
            return "dtype_capability_missing"
        if plan.backend.value != "cpu" and plan.budget.vram_limit_bytes > 0:
            free = capability.resources.vram_free_bytes
            if free is None or free < plan.budget.vram_limit_bytes:
                return "vram_budget_not_admitted"
        return None

    def _validate_resume(self, plan: TrainingPlan, relative: str) -> str | None:
        checkpoint_path = _inside(self.root, relative)
        metadata = checkpoint_path / "kodepoia_checkpoint.json"
        if not checkpoint_path.is_dir() or not metadata.is_file():
            return "resume_checkpoint_missing"
        try:
            payload = json.loads(metadata.read_text(encoding="utf-8"))
            record = _checkpoint_from_dict(payload)
            state_file = checkpoint_path / "fixture_state.json"
            if not state_file.is_file():
                state_file = checkpoint_path / "trainer_state.json"
            if not state_file.is_file() or _sha256_file(state_file) != record.state_digest:
                return "resume_checkpoint_state_mismatch"
        except (OSError, json.JSONDecodeError, TypeError, ValueError, TrainingPlanError):
            return "resume_checkpoint_invalid"
        expected = (
            record.plan_digest == plan.digest
            and record.base_model_digest == plan.base_model_digest
            and record.tokenizer_digest == plan.tokenizer_digest
            and record.dataset_manifest_digest == plan.dataset_manifest_digest
            and record.train_split_digest == plan.train_split_digest
        )
        return None if expected else "resume_lineage_mismatch"

    def _terminal(
        self,
        plan: TrainingPlan,
        run_id: str,
        state: TrainingRunState,
        blockers: tuple[str, ...],
        *,
        stderr: str = "",
    ) -> TrainingRunReport:
        return TrainingRunReport(
            state=state,
            plan_digest=plan.digest,
            source_sha=plan.source_sha,
            run_id=run_id,
            adapter_path=None,
            adapter_digest=None,
            checkpoint=None,
            train_loss=None,
            eval_loss=None,
            steps_completed=0,
            packages=(),
            blockers=blockers,
            stderr=redact_runtime_text(stderr)[:_MAX_CAPTURE_CHARS],
        )
