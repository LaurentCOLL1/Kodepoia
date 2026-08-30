from __future__ import annotations

import hashlib
import importlib.metadata
import json
import random
import struct
import sys
from pathlib import Path

from .training_contracts import (
    DatasetFormat,
    LoraPlan,
    SFTPlan,
    TrainingBudget,
    TrainingEngine,
    TrainingPlan,
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _plan_from_dict(value: object) -> TrainingPlan:
    if not isinstance(value, dict):
        raise ValueError("plan must be an object")
    raw = dict(value)
    lora = raw.pop("lora")
    sft = raw.pop("sft")
    budget = raw.pop("budget")
    if not isinstance(lora, dict) or not isinstance(sft, dict) or not isinstance(budget, dict):
        raise ValueError("nested training plan fields are invalid")
    targets = lora.get("target_modules", "all-linear")
    if isinstance(targets, list):
        targets = tuple(str(item) for item in targets)
    return TrainingPlan(
        **raw,
        lora=LoraPlan(
            rank=int(lora["rank"]),
            alpha=int(lora["alpha"]),
            dropout=float(lora["dropout"]),
            target_modules=targets,
            bias=str(lora["bias"]),
        ),
        sft=SFTPlan(**sft),
        budget=TrainingBudget(**budget),
    )


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row {line_number} is not an object")
        rows.append(value)
    if not rows:
        raise ValueError("training split is empty")
    return rows


def _validate_rows(rows: list[dict[str, object]], dataset_format: DatasetFormat) -> None:
    for row in rows:
        if dataset_format is DatasetFormat.TEXT:
            if not isinstance(row.get("text"), str) or not row["text"]:
                raise ValueError("text dataset row requires non-empty text")
        elif dataset_format is DatasetFormat.PROMPT_COMPLETION:
            if not isinstance(row.get("prompt"), str) or not isinstance(row.get("completion"), str):
                raise ValueError("prompt-completion row requires prompt and completion strings")
        else:
            messages = row.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError("conversational row requires messages")
            for message in messages:
                if not isinstance(message, dict) or not isinstance(message.get("role"), str) or not isinstance(message.get("content"), str):
                    raise ValueError("conversation messages require role/content strings")


def _write_safetensors(path: Path, *, plan_digest: str, seed_material: bytes) -> None:
    values = []
    digest = hashlib.sha256(seed_material).digest()
    for offset in range(0, 16, 4):
        integer = int.from_bytes(digest[offset : offset + 4], "little")
        values.append((integer / 2**32) * 2.0 - 1.0)
    payload = b"".join(struct.pack("<f", value) for value in values)
    header = {
        "__metadata__": {"format": "pt", "plan_digest": plan_digest, "fixture": "r15.9"},
        "lora_A.weight": {"dtype": "F32", "shape": [1, 2], "data_offsets": [0, 8]},
        "lora_B.weight": {"dtype": "F32", "shape": [2, 1], "data_offsets": [8, 16]},
    }
    encoded = json.dumps(header, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    padding = (-len(encoded)) % 8
    encoded += b" " * padding
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<Q", len(encoded)) + encoded + payload)


def _checkpoint_payload(plan: TrainingPlan, *, path: str, step: int, state_digest: str) -> dict[str, object]:
    return {
        "base_model_digest": plan.base_model_digest,
        "checkpoint_path": path,
        "dataset_manifest_digest": plan.dataset_manifest_digest,
        "plan_digest": plan.digest,
        "state_digest": state_digest,
        "step": step,
        "tokenizer_digest": plan.tokenizer_digest,
        "train_split_digest": plan.train_split_digest,
    }


def _save_checkpoint(root: Path, output_dir: Path, plan: TrainingPlan, step: int, material: bytes) -> dict[str, object]:
    relative = (output_dir / f"checkpoint-{step}.json").relative_to(root).as_posix()
    path = root / relative
    body = {
        "base_model_digest": plan.base_model_digest,
        "dataset_manifest_digest": plan.dataset_manifest_digest,
        "material_digest": hashlib.sha256(material).hexdigest(),
        "plan_digest": plan.digest,
        "step": step,
        "tokenizer_digest": plan.tokenizer_digest,
        "train_split_digest": plan.train_split_digest,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    state_digest = _sha256_file(path)
    payload = _checkpoint_payload(plan, path=relative, step=step, state_digest=state_digest)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    payload["state_digest"] = _sha256_file(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    payload["state_digest"] = _sha256_file(path)
    return payload


def _fixture_train(root: Path, plan: TrainingPlan, output_dir: Path, resume: str | None) -> dict[str, object]:
    train_path = root / plan.train_path
    rows = _read_jsonl(train_path)
    _validate_rows(rows, plan.dataset_format)
    validation_rows: list[dict[str, object]] = []
    if plan.validation_path is not None:
        validation_rows = _read_jsonl(root / plan.validation_path)
        _validate_rows(validation_rows, plan.dataset_format)

    start_step = 0
    if resume is not None:
        checkpoint = json.loads((root / resume).read_text(encoding="utf-8"))
        start_step = int(checkpoint["step"])
    random.seed(plan.seed)
    material = (
        plan.digest
        + plan.train_split_digest
        + str(plan.seed)
        + str(plan.data_seed)
        + json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    ).encode("utf-8")

    checkpoint_payload: dict[str, object] | None = None
    for step in range(start_step + 1, plan.sft.max_steps + 1):
        step_material = material + f":{step}".encode("ascii")
        if step % plan.sft.checkpoint_every_steps == 0 or step == plan.sft.max_steps:
            checkpoint_payload = _save_checkpoint(root, output_dir, plan, step, step_material)

    adapter = output_dir / "adapter_model.safetensors"
    _write_safetensors(adapter, plan_digest=plan.digest, seed_material=material)
    train_fraction = int(hashlib.sha256(material).hexdigest()[:8], 16) / 0xFFFFFFFF
    train_loss = 0.25 + train_fraction * 0.5
    eval_loss = None
    if validation_rows:
        validation_material = json.dumps(validation_rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        eval_fraction = int(hashlib.sha256(validation_material + plan.digest.encode("ascii")).hexdigest()[:8], 16) / 0xFFFFFFFF
        eval_loss = 0.25 + eval_fraction * 0.5
    return {
        "adapter_digest": _sha256_file(adapter),
        "adapter_path": adapter.relative_to(root).as_posix(),
        "checkpoint": checkpoint_payload,
        "eval_loss": eval_loss,
        "packages": {},
        "state": "succeeded",
        "steps_completed": plan.sft.max_steps,
        "train_loss": train_loss,
    }


def _trl_peft_train(root: Path, plan: TrainingPlan, output_dir: Path, resume: str | None) -> dict[str, object]:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    train_rows = _read_jsonl(root / plan.train_path)
    _validate_rows(train_rows, plan.dataset_format)
    eval_rows = None
    if plan.validation_path is not None:
        eval_rows = _read_jsonl(root / plan.validation_path)
        _validate_rows(eval_rows, plan.dataset_format)

    dtype = {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[plan.dtype.value]
    quantization_config = None
    if plan.quantization.value == "bnb_nf4":
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,
        )
    model = AutoModelForCausalLM.from_pretrained(
        plan.base_model_ref,
        revision=plan.base_revision,
        local_files_only=True,
        dtype=dtype,
        quantization_config=quantization_config,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        plan.tokenizer_ref,
        revision=plan.base_revision,
        local_files_only=True,
    )
    if quantization_config is not None:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=plan.sft.gradient_checkpointing)
    peft_config = LoraConfig(
        r=plan.lora.rank,
        lora_alpha=plan.lora.alpha,
        lora_dropout=plan.lora.dropout,
        target_modules=plan.lora.target_modules,
        bias=plan.lora.bias,
        task_type="CAUSAL_LM",
    )
    args = SFTConfig(
        output_dir=str(output_dir),
        max_steps=plan.sft.max_steps,
        per_device_train_batch_size=plan.sft.batch_size,
        gradient_accumulation_steps=plan.sft.gradient_accumulation_steps,
        learning_rate=plan.sft.learning_rate,
        max_length=plan.sft.context_length,
        seed=plan.seed,
        data_seed=plan.data_seed,
        packing=plan.sft.packing,
        assistant_only_loss=plan.sft.assistant_only_loss,
        completion_only_loss=plan.sft.completion_only_loss,
        gradient_checkpointing=plan.sft.gradient_checkpointing,
        save_steps=plan.sft.checkpoint_every_steps,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=Dataset.from_list(train_rows),
        eval_dataset=None if eval_rows is None else Dataset.from_list(eval_rows),
        processing_class=tokenizer,
        peft_config=peft_config,
    )
    result = trainer.train(resume_from_checkpoint=None if resume is None else str(root / resume))
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    adapter = output_dir / "adapter_model.safetensors"
    if not adapter.is_file():
        raise RuntimeError("TRL/PEFT did not produce adapter_model.safetensors")
    checkpoints = sorted(output_dir.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[-1]))
    checkpoint_payload = None
    if checkpoints:
        checkpoint_dir = checkpoints[-1]
        state_file = checkpoint_dir / "trainer_state.json"
        state_digest = _sha256_file(state_file) if state_file.is_file() else hashlib.sha256(checkpoint_dir.name.encode()).hexdigest()
        checkpoint_payload = _checkpoint_payload(
            plan,
            path=checkpoint_dir.relative_to(root).as_posix(),
            step=int(checkpoint_dir.name.split("-")[-1]),
            state_digest=state_digest,
        )
    metrics = dict(result.metrics)
    eval_loss = None
    if eval_rows is not None:
        eval_metrics = trainer.evaluate()
        if "eval_loss" in eval_metrics:
            eval_loss = float(eval_metrics["eval_loss"])
    packages = {
        name: importlib.metadata.version(name)
        for name in ("accelerate", "datasets", "peft", "safetensors", "torch", "transformers", "trl")
    }
    return {
        "adapter_digest": _sha256_file(adapter),
        "adapter_path": adapter.relative_to(root).as_posix(),
        "checkpoint": checkpoint_payload,
        "eval_loss": eval_loss,
        "packages": packages,
        "state": "succeeded",
        "steps_completed": int(metrics.get("epoch", 0) or plan.sft.max_steps),
        "train_loss": None if metrics.get("train_loss") is None else float(metrics["train_loss"]),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or Path(args[0]).name != args[0]:
        print("training worker requires one local config filename", file=sys.stderr)
        return 2
    root = Path.cwd().resolve(strict=False)
    config_path = root / args[0]
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or set(payload) != {"output_dir", "plan", "plan_digest", "resume_checkpoint"}:
            raise ValueError("worker payload fields are invalid")
        plan = _plan_from_dict(payload["plan"])
        if payload["plan_digest"] != plan.digest:
            raise ValueError("worker plan digest mismatch")
        output_dir = (root / str(payload["output_dir"])).resolve(strict=False)
        output_dir.relative_to(root)
        resume = None if payload["resume_checkpoint"] is None else str(payload["resume_checkpoint"])
        if plan.engine is TrainingEngine.FIXTURE:
            result = _fixture_train(root, plan, output_dir, resume)
        else:
            result = _trl_peft_train(root, plan, output_dir, resume)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return 0
    except Exception as exc:
        print(f"training_worker_failed:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
