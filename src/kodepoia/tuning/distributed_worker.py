from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from .contracts import canonical_sha256
from .train_worker import _run_real


def _inside(root: Path, value: str) -> Path:
    path = (root / value).resolve(strict=False)
    if path != root and root not in path.parents:
        raise ValueError("distributed worker path escapes training root")
    return path


def _env_int(name: str) -> int:
    value = os.environ.get(name)
    if value is None or not value.isdigit():
        raise ValueError(f"trusted torchrun environment is missing {name}")
    return int(value)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rank_evidence(
    *,
    execution: dict[str, Any],
    rank: int,
    local_rank: int,
    device_ordinal: int,
    state: str,
    completed_steps: int,
    train_loss: float | None,
    eval_loss: float | None,
    peak_vram_bytes: int | None,
    canonical_output_digest: str | None,
    failure_type: str | None,
    recovery: dict[str, Any] | None = None,
    checkpoint_manifest: dict[str, Any] | None = None,
) -> dict[str, object]:
    seed = dict(execution["rank_seeds"][rank])
    record: dict[str, object] = {
        "canonical_output_digest": canonical_output_digest,
        "completed_steps": completed_steps,
        "data_seed": int(seed["data_seed"]),
        "device_ordinal": device_ordinal,
        "eval_loss": eval_loss,
        "execution_plan_digest": str(execution["execution_plan_digest"]),
        "failure_type": failure_type,
        "local_rank": local_rank,
        "peak_vram_bytes": peak_vram_bytes,
        "rank": rank,
        "seed": int(seed["seed"]),
        "shared_sampler_seed": int(execution["shared_sampler_seed"]),
        "state": state,
        "strategy_plan_digest": str(execution["strategy_plan_digest"]),
        "topology_digest": str(execution["topology_digest"]),
        "train_loss": train_loss,
        "training_plan_digest": str(execution["training_plan_digest"]),
        "world_size": int(execution["world_size"]),
    }
    if recovery is not None and checkpoint_manifest is not None:
        record.update(
            {
                "checkpoint_manifest_digest": str(recovery["checkpoint_manifest_digest"]),
                "recovery_plan_digest": str(recovery["recovery_plan_digest"]),
                "resumed_from_checkpoint_id": str(checkpoint_manifest["checkpoint_id"]),
                "resumed_from_step": int(checkpoint_manifest["step"]),
            }
        )
    return record


def _validate_recovery_checkpoint(
    root: Path,
    worker: dict[str, Any],
    recovery: dict[str, Any],
    checkpoint_manifest: dict[str, Any],
) -> None:
    if recovery.get("schema") != "kodepoia.v2.4.4.distributed-recovery-plan":
        raise ValueError("unsupported distributed recovery plan")
    if recovery.get("resume_authorized") is not True:
        raise ValueError("distributed recovery plan does not authorize resume")
    if checkpoint_manifest.get("schema") != "kodepoia.v2.4.4.distributed-checkpoint-manifest":
        raise ValueError("unsupported distributed checkpoint manifest")
    if recovery.get("checkpoint_manifest_digest") != checkpoint_manifest.get("manifest_digest"):
        raise ValueError("recovery checkpoint manifest digest mismatch")
    resume = worker.get("resume_checkpoint")
    if resume != checkpoint_manifest.get("checkpoint_metadata_path"):
        raise ValueError("worker resume path does not match checkpoint manifest")
    metadata = _inside(root, str(checkpoint_manifest["checkpoint_metadata_path"]))
    artifact = _inside(root, str(checkpoint_manifest["checkpoint_artifact_path"]))
    if not metadata.is_file() or _sha256(metadata) != checkpoint_manifest.get("checkpoint_metadata_digest"):
        raise ValueError("checkpoint metadata digest mismatch")
    if not artifact.is_file() or _sha256(artifact) != checkpoint_manifest.get("checkpoint_artifact_digest"):
        raise ValueError("checkpoint artifact digest mismatch")
    record = json.loads(metadata.read_text(encoding="utf-8"))
    if record.get("checkpoint_id") != checkpoint_manifest.get("checkpoint_id"):
        raise ValueError("checkpoint metadata identity mismatch")
    if int(record.get("step", -1)) != int(checkpoint_manifest.get("step", -2)):
        raise ValueError("checkpoint metadata step mismatch")
    if record.get("plan_digest") != recovery.get("training_plan_digest"):
        raise ValueError("checkpoint TrainingPlan lineage mismatch")
    if record.get("artifact_path") != checkpoint_manifest.get("checkpoint_artifact_path"):
        raise ValueError("checkpoint artifact path mismatch")
    if record.get("artifact_digest") != checkpoint_manifest.get("checkpoint_artifact_digest"):
        raise ValueError("checkpoint artifact lineage mismatch")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m kodepoia.tuning.distributed_worker <config.json>")

    root = Path.cwd().resolve(strict=False)
    config_path = _inside(root, sys.argv[1])
    rank: int | None = None
    local_rank: int | None = None
    device_ordinal: int | None = None
    evidence_path: Path | None = None
    execution: dict[str, Any] | None = None
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        schema = config.get("schema")
        if config.get("schema_version") != 1 or schema not in {
            "kodepoia.v2.4.3.distributed-worker-config",
            "kodepoia.v2.4.4.distributed-recovery-worker-config",
        }:
            raise ValueError("unsupported distributed worker config")
        is_recovery = schema == "kodepoia.v2.4.4.distributed-recovery-worker-config"
        execution = dict(config["execution_plan"])
        worker = dict(config["training_worker"])
        recovery = dict(config["recovery_plan"]) if is_recovery else None
        checkpoint_manifest = dict(config["checkpoint_manifest"]) if is_recovery else None
        if execution.get("schema") != "kodepoia.v2.4.3.distributed-execution-plan":
            raise ValueError("unsupported distributed execution plan")
        if execution.get("world_size") != 2:
            raise ValueError("distributed execution world_size must be 2")
        if is_recovery:
            assert recovery is not None and checkpoint_manifest is not None
            if recovery.get("execution_plan_digest") != execution.get("execution_plan_digest"):
                raise ValueError("recovery execution plan lineage mismatch")
            for key in (
                "training_plan_digest",
                "strategy_plan_digest",
                "benchmark_report_digest",
                "topology_digest",
            ):
                if recovery.get(key) != execution.get(key):
                    raise ValueError(f"recovery {key} mismatch")
            if recovery.get("world_size") != 2 or recovery.get("device_ordinals") != execution.get("device_ordinals"):
                raise ValueError("recovery topology/world-size identity mismatch")
            _validate_recovery_checkpoint(root, worker, recovery, checkpoint_manifest)
        elif execution.get("resume_authorized") is not False or worker.get("resume_checkpoint") is not None:
            raise ValueError("distributed resume remains unauthorized until V2.4.4")

        rank = _env_int("RANK")
        local_rank = _env_int("LOCAL_RANK")
        world_size = _env_int("WORLD_SIZE")
        local_world_size = _env_int("LOCAL_WORLD_SIZE")
        if world_size != 2 or local_world_size != 2:
            raise ValueError("torchrun world size does not match accepted execution plan")
        if rank not in (0, 1) or local_rank not in (0, 1) or rank != local_rank:
            raise ValueError("single-node trusted rank/local-rank identity is invalid")
        group_rank = os.environ.get("GROUP_RANK")
        if group_rank not in {None, "0"}:
            raise ValueError("V2.4.3 accepts a single torchrun node only")
        if os.environ.get("TORCHELASTIC_RESTART_COUNT", "0") != "0":
            raise ValueError("V2.4.3 forbids worker restarts")
        if os.environ.get("TORCHELASTIC_MAX_RESTARTS", "0") != "0":
            raise ValueError("V2.4.3 requires max_restarts=0")

        ordinals = tuple(int(item) for item in execution["device_ordinals"])
        if len(ordinals) != 2 or ordinals != tuple(sorted(set(ordinals))):
            raise ValueError("accepted device ordinals are invalid")
        visible = tuple(
            int(item.strip())
            for item in os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
            if item.strip()
        )
        if visible != ordinals:
            raise ValueError("CUDA_VISIBLE_DEVICES does not match accepted device ordinals")
        device_ordinal = ordinals[local_rank]

        if worker.get("plan_digest") != execution.get("training_plan_digest"):
            raise ValueError("worker TrainingPlan lineage does not match execution plan")
        sft = dict(worker["sft"])
        sft["train_batch_size"] = int(execution["per_device_batch_size"])
        sft["gradient_accumulation_steps"] = int(execution["gradient_accumulation_steps"])
        worker["sft"] = sft
        seed = dict(execution["rank_seeds"][rank])
        seeds = dict(worker["seeds"])
        seeds["seed"] = int(seed["seed"])
        seeds["data_seed"] = int(execution["shared_sampler_seed"])
        worker["seeds"] = seeds

        run_dir = _inside(root, str(worker["run_dir"]))
        evidence_dir = _inside(root, str(config["evidence_dir"]))
        evidence_path = evidence_dir / f"rank-{rank:05d}.json"
        canonical_path = _inside(root, str(config["canonical_output_path"]))

        import torch

        if not torch.cuda.is_available() or torch.cuda.device_count() < 2:
            raise ValueError("V2.4.3 requires two visible CUDA devices")
        torch.cuda.set_device(local_rank)

        output = _run_real(
            worker,
            root,
            run_dir,
            canonical_output=rank == 0,
            rank_seed_override=int(seed["seed"]),
            trusted_local_rank=local_rank,
        )
        resources = dict(output["resource_maxima"])
        canonical_digest: str | None = None
        if rank == 0:
            _write_json(canonical_path, output)
            canonical_digest = canonical_sha256(output)
        record = _rank_evidence(
            execution=execution,
            rank=rank,
            local_rank=local_rank,
            device_ordinal=device_ordinal,
            state="completed",
            completed_steps=int(output["completed_steps"]),
            train_loss=float(output["train_loss"]),
            eval_loss=float(output["eval_loss"]),
            peak_vram_bytes=(
                None
                if resources.get("peak_vram_bytes") is None
                else int(resources["peak_vram_bytes"])
            ),
            canonical_output_digest=canonical_digest,
            failure_type=None,
            recovery=recovery,
            checkpoint_manifest=checkpoint_manifest,
        )
        _write_json(evidence_path, record)
        print(json.dumps({"rank": rank, "state": "completed"}, sort_keys=True))
        return 0
    except Exception as exc:
        if execution is not None and rank in (0, 1) and local_rank in (0, 1) and device_ordinal is not None:
            try:
                if evidence_path is None:
                    evidence_dir = _inside(root, str(config["evidence_dir"]))
                    evidence_path = evidence_dir / f"rank-{rank:05d}.json"
                _write_json(
                    evidence_path,
                    _rank_evidence(
                        execution=execution,
                        rank=rank,
                        local_rank=local_rank,
                        device_ordinal=device_ordinal,
                        state="failed",
                        completed_steps=0,
                        train_loss=None,
                        eval_loss=None,
                        peak_vram_bytes=None,
                        canonical_output_digest=None,
                        failure_type=type(exc).__name__,
                        recovery=recovery if "recovery" in locals() else None,
                        checkpoint_manifest=(
                            checkpoint_manifest if "checkpoint_manifest" in locals() else None
                        ),
                    ),
                )
            except Exception:
                pass
        label = "V2.4.4 distributed recovery worker" if "is_recovery" in locals() and is_recovery else "V2.4.3 distributed worker"
        print(f"{label} failed: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
