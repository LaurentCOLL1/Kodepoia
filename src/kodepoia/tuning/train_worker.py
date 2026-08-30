from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any


def _inside(root: Path, value: str) -> Path:
    path = (root / value).resolve(strict=False)
    if path != root and root not in path.parents:
        raise ValueError("worker path escapes training root")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _write_safetensors(path: Path, tensors: dict[str, tuple[tuple[int, ...], tuple[float, ...]]]) -> None:
    """Write a tiny deterministic F32 Safetensors file without importing ML packages."""
    header: dict[str, object] = {"__metadata__": {"format": "kodepoia-r15.9-fixture"}}
    data_parts: list[bytes] = []
    offset = 0
    for name in sorted(tensors):
        shape, values = tensors[name]
        count = math.prod(shape)
        if count != len(values):
            raise ValueError("fixture tensor shape/value mismatch")
        raw = struct.pack(f"<{count}f", *values)
        header[name] = {
            "data_offsets": [offset, offset + len(raw)],
            "dtype": "F32",
            "shape": list(shape),
        }
        data_parts.append(raw)
        offset += len(raw)
    encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    padding = (-len(encoded)) % 8
    encoded += b" " * padding
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + b"".join(data_parts))


def _fixture_weights(plan_digest: str, seed: int, step: int) -> tuple[float, ...]:
    digest = hashlib.sha256(f"{plan_digest}:{seed}:{step}".encode()).digest()
    return tuple(((digest[index] / 255.0) - 0.5) / max(step, 1) for index in range(8))


def _fixture_losses(step: int) -> tuple[float, float]:
    train_loss = 1.0 / (step + 1.0)
    eval_loss = 1.0 / (step + 0.75)
    return train_loss, eval_loss


def _checkpoint(
    root: Path,
    run_dir: Path,
    plan_digest: str,
    seed: int,
    step: int,
) -> dict[str, object]:
    checkpoint_id = f"checkpoint-{step:08d}"
    tensor_path = run_dir / "checkpoints" / checkpoint_id / "adapter_model.safetensors"
    weights = _fixture_weights(plan_digest, seed, step)
    _write_safetensors(
        tensor_path,
        {
            "fixture.lora_A.weight": ((2, 2), weights[:4]),
            "fixture.lora_B.weight": ((2, 2), weights[4:]),
        },
    )
    train_loss, eval_loss = _fixture_losses(step)
    record = {
        "artifact_digest": _sha256(tensor_path),
        "artifact_path": str(tensor_path.relative_to(root)),
        "checkpoint_id": checkpoint_id,
        "eval_loss": eval_loss,
        "plan_digest": plan_digest,
        "step": step,
        "train_loss": train_loss,
    }
    metadata_path = run_dir / "checkpoints" / checkpoint_id / "checkpoint.json"
    metadata_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    record["metadata_path"] = str(metadata_path.relative_to(root))
    return record


def _run_fixture(config: dict[str, Any], root: Path, run_dir: Path) -> dict[str, object]:
    plan_digest = str(config["plan_digest"])
    sft = dict(config["sft"])
    seeds = dict(config["seeds"])
    dataset = dict(config["dataset"])
    max_steps = int(sft["max_steps"])
    checkpoint_steps = int(sft["checkpoint_steps"])
    seed = int(seeds["seed"])

    start_step = 0
    resume = config.get("resume_checkpoint")
    if resume:
        resume_path = _inside(root, str(resume))
        record = json.loads(resume_path.read_text(encoding="utf-8"))
        if record.get("plan_digest") != plan_digest:
            raise ValueError("resume checkpoint lineage mismatch in worker")
        start_step = int(record["step"])

    checkpoints: list[dict[str, object]] = []
    for step in range(start_step + 1, max_steps + 1):
        if step % checkpoint_steps == 0 or step == max_steps:
            record = _checkpoint(root, run_dir, plan_digest, seed, step)
            checkpoints.append({key: value for key, value in record.items() if key != "metadata_path"})

    final_weights = _fixture_weights(plan_digest, seed, max_steps)
    adapter_path = run_dir / "adapter" / "adapter_model.safetensors"
    _write_safetensors(
        adapter_path,
        {
            "fixture.lora_A.weight": ((2, 2), final_weights[:4]),
            "fixture.lora_B.weight": ((2, 2), final_weights[4:]),
        },
    )
    train_loss, eval_loss = _fixture_losses(max_steps)
    return {
        "adapter_digest": _sha256(adapter_path),
        "adapter_path": str(adapter_path.relative_to(root)),
        "checkpoints": checkpoints,
        "completed_steps": max_steps,
        "eval_loss": eval_loss,
        "framework_versions": {"python": sys.version.split()[0]},
        "optimized_splits": ["train"],
        "plan_digest": plan_digest,
        "train_loss": train_loss,
        "train_rows": int(dataset["train_rows"]),
        "validation_rows": int(dataset["validation_rows"]),
    }


def _load_json_dataset(path: Path) -> Any:
    from datasets import load_dataset

    return load_dataset("json", data_files=str(path), split="train")


def _run_real(config: dict[str, Any], root: Path, run_dir: Path) -> dict[str, object]:
    """Execute optional SFT/QLoRA. Heavy packages are imported only in this worker."""
    import torch
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    mode = str(config["mode"])
    model_cfg = dict(config["model"])
    dataset_cfg = dict(config["dataset_paths"])
    lora_cfg = dict(config["lora"])
    sft_cfg = dict(config["sft"])
    seeds = dict(config["seeds"])

    train_path = _inside(root, str(dataset_cfg["train_path"]))
    validation_path = _inside(root, str(dataset_cfg["validation_path"]))
    if _sha256(train_path) != dataset_cfg["train_export_digest"]:
        raise ValueError("train export digest mismatch")
    if _sha256(validation_path) != dataset_cfg["validation_export_digest"]:
        raise ValueError("validation export digest mismatch")

    tokenizer = AutoTokenizer.from_pretrained(
        model_cfg["tokenizer_ref"],
        revision=model_cfg["model_revision"],
        trust_remote_code=False,
    )
    quantization_config = None
    if mode == "qlora":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        )
    model = AutoModelForCausalLM.from_pretrained(
        model_cfg["model_ref"],
        revision=model_cfg["model_revision"],
        quantization_config=quantization_config,
        trust_remote_code=False,
    )
    if mode == "qlora":
        model = prepare_model_for_kbit_training(
            model,
            use_gradient_checkpointing=bool(sft_cfg["gradient_checkpointing"]),
        )

    targets = lora_cfg["target_modules"]
    target_modules: str | list[str]
    target_modules = "all-linear" if targets == ["all-linear"] else list(targets)
    peft_config = LoraConfig(
        r=int(lora_cfg["rank"]),
        lora_alpha=int(lora_cfg["alpha"]),
        lora_dropout=float(lora_cfg["dropout"]),
        target_modules=target_modules,
        task_type="CAUSAL_LM",
    )
    train_dataset = _load_json_dataset(train_path)
    eval_dataset = _load_json_dataset(validation_path)
    output_dir = run_dir / "trainer"
    args = SFTConfig(
        output_dir=str(output_dir),
        max_steps=int(sft_cfg["max_steps"]),
        per_device_train_batch_size=int(sft_cfg["train_batch_size"]),
        per_device_eval_batch_size=int(sft_cfg["eval_batch_size"]),
        gradient_accumulation_steps=int(sft_cfg["gradient_accumulation_steps"]),
        max_length=int(sft_cfg["context_length"]),
        learning_rate=float(sft_cfg["learning_rate"]),
        save_strategy="steps",
        save_steps=int(sft_cfg["checkpoint_steps"]),
        eval_strategy="steps",
        eval_steps=int(sft_cfg["eval_steps"]),
        gradient_checkpointing=bool(sft_cfg["gradient_checkpointing"]),
        completion_only_loss=bool(sft_cfg["completion_only_loss"]),
        assistant_only_loss=bool(sft_cfg["assistant_only_loss"]),
        full_determinism=bool(sft_cfg["full_determinism"]),
        seed=int(seeds["seed"]),
        data_seed=int(seeds["data_seed"]),
        optim=str(sft_cfg["optimizer"]),
        lr_scheduler_type=str(sft_cfg["scheduler"]),
        report_to="none",
        push_to_hub=False,
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    resume = config.get("resume_checkpoint")
    result = trainer.train(
        resume_from_checkpoint=(
            None
            if not resume
            else str(
                _inside(root, str(resume)).parent
                if str(resume).endswith(".json")
                else _inside(root, str(resume))
            )
        )
    )
    metrics = dict(result.metrics)
    eval_metrics = trainer.evaluate()
    adapter_dir = run_dir / "adapter"
    trainer.save_model(str(adapter_dir))
    adapter_path = adapter_dir / "adapter_model.safetensors"
    if not adapter_path.is_file():
        raise ValueError("PEFT trainer did not produce adapter_model.safetensors")

    checkpoints: list[dict[str, object]] = []
    for path in sorted(output_dir.glob("checkpoint-*")):
        try:
            step = int(path.name.rsplit("-", 1)[1])
        except (IndexError, ValueError):
            continue
        adapter = path / "adapter_model.safetensors"
        if not adapter.is_file():
            continue
        record = {
            "artifact_digest": _sha256(adapter),
            "artifact_path": str(adapter.relative_to(root)),
            "checkpoint_id": path.name,
            "eval_loss": float(eval_metrics.get("eval_loss", 0.0)),
            "plan_digest": config["plan_digest"],
            "step": step,
            "train_loss": float(metrics.get("train_loss", 0.0)),
        }
        metadata_path = path / "checkpoint.json"
        metadata_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        checkpoints.append(record)

    return {
        "adapter_digest": _sha256(adapter_path),
        "adapter_path": str(adapter_path.relative_to(root)),
        "checkpoints": checkpoints,
        "completed_steps": int(trainer.state.global_step),
        "eval_loss": float(eval_metrics.get("eval_loss", 0.0)),
        "framework_versions": {
            name: _package_version(name)
            for name in (
                "accelerate",
                "bitsandbytes",
                "datasets",
                "peft",
                "safetensors",
                "torch",
                "transformers",
                "trl",
            )
        },
        "optimized_splits": ["train"],
        "plan_digest": config["plan_digest"],
        "train_loss": float(metrics.get("train_loss", 0.0)),
        "train_rows": int(dataset_cfg["train_rows"]),
        "validation_rows": int(dataset_cfg["validation_rows"]),
    }


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m kodepoia.tuning.train_worker <config.json>")
    root = Path.cwd().resolve(strict=False)
    config_path = _inside(root, sys.argv[1])
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("schema") != "kodepoia.r15.9.training-run" or config.get("schema_version") != 1:
            raise ValueError("unsupported R15.9 training worker schema")
        run_dir = _inside(root, str(config["run_dir"]))
        run_dir.mkdir(parents=True, exist_ok=True)
        if config.get("mode") == "fixture_sft":
            output = _run_fixture(config, root, run_dir)
        else:
            output = _run_real(config, root, run_dir)
        print(json.dumps(output, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return 0
    except Exception as exc:  # worker boundary intentionally converts failures to one redacted parent path
        print(f"R15.9 training worker failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
