# R15.9 — QLoRA/SFT training design

**Status:** IN_PROGRESS  
**Branch base:** normalized R15.8 `main` `4c1c726301b5a5f798944632336e130ccfb0cbbe`  
**Manual state:** CONDITIONAL / NOT TRIGGERED for bounded fixture acceptance

## Goal

R15.9 adds a reproducible, fail-closed adapter-training boundary without turning PyTorch/Transformers/PEFT/TRL/bitsandbytes into core dependencies and without requiring a large model or GPU for repository acceptance.

The authoritative unit is a typed `TrainingPlan`. It binds exact repository source SHA, base model identity/revision/digest, tokenizer identity/digest, immutable dataset manifest and split digests, dataset format, engine/backend/dtype/quantization, LoRA/SFT configuration, seeds and budgets. Its canonical digest is carried by every checkpoint and run report.

## Engines

### Repository-owned fixture engine

The fixture engine is CPU/non-quantized and intentionally tiny. It reads only the declared training JSONL for adapter state construction, writes deterministic LoRA-shaped tensors to a valid minimal Safetensors file, emits bounded train/eval metrics, and persists checkpoint directories with `kodepoia_checkpoint.json` plus a separately hashed state file. Validation JSONL is read only after training-state construction for evaluation; changing validation content must not change the fixture adapter or training loss.

This engine proves orchestration, evidence, lineage and recovery in CI without downloading weights or importing ML packages.

### Optional TRL/PEFT engine

The real path is loaded only in the isolated training worker. It requires a successful R15.8 capability report matching requested backend/dtype/4-bit requirements before launch. Model and tokenizer loads use `local_files_only=True`; R15.9 does not silently download model weights.

For 4-bit QLoRA, the worker uses `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")`, preprocesses the model with `prepare_model_for_kbit_training()`, and applies PEFT `LoraConfig`. QLoRA-style `target_modules="all-linear"` is accepted when selected by the plan, but architecture-specific lists remain supported.

TRL `SFTTrainer` receives a structured `SFTConfig`; conversational `assistant_only_loss` and prompt-completion `completion_only_loss` are validated against dataset format before launch. `resume_from_checkpoint` is passed only after repository-side lineage validation.

## Current upstream compatibility evidence — 2026-08-30

- PEFT’s current quantization guide calls `prepare_model_for_kbit_training()` before training a quantized model with adapters and documents `target_modules="all-linear"` for QLoRA-style coverage.
- Transformers/bitsandbytes documentation recommends NF4 for training 4-bit base models and exposes it through `BitsAndBytesConfig`.
- TRL documents conversational `assistant_only_loss`, prompt-completion `completion_only_loss`, adapter training with PEFT and `resume_from_checkpoint` restoring model/optimizer/scheduler state.
- PyTorch explicitly warns that identical seeds do not guarantee identical results across releases/platforms/devices. R15.9 therefore records seeds plus exact software/hardware evidence and promises bounded same-environment reproducibility, not universal bit identity.

Official references:

- https://huggingface.co/docs/peft/developer_guides/quantization
- https://huggingface.co/docs/peft/main/package_reference/lora
- https://huggingface.co/docs/transformers/quantization/bitsandbytes
- https://huggingface.co/docs/trl/sft_trainer
- https://docs.pytorch.org/docs/stable/notes/randomness.html

## Dataset firewall

`train_path` and optional `validation_path` must be distinct repository-relative paths. Their bytes are re-hashed immediately before launch and must equal the immutable split digests in the plan. The worker receives no benchmark holdout path. Validation content is evaluation-only and cannot be substituted as the training split.

The plan accepts text, prompt-completion or conversational JSONL. Loss-mode combinations that do not match the declared format fail before any worker starts.

## Checkpoint and resume lineage

Checkpoint directories contain a repository-owned metadata sidecar with plan/base/tokenizer/dataset/train-split identities, step and state digest. Resume is rejected before subprocess launch when metadata is absent, corrupt, state bytes do not match their digest, or any lineage identity differs from the current plan.

A resumed TRL run receives the validated checkpoint directory. A resumed fixture run resumes from the recorded step and deterministically reproduces the accepted final adapter for the same plan.

## Budgets, cancellation and evidence

Host disk/RAM availability is measured before launch. Unknown or insufficient configured resources are terminal `BUDGET_BLOCKED`. A real accelerator plan is additionally gated by the R15.8 VRAM capability report. Training executes only through `ProcessSandbox` using fixed Python/module/config-file argv; dataset/model text is never command text.

Timeout and KillSwitch/cancel paths are terminal and never promoted to success. Worker stderr/stdout failures are bounded and redacted using the R15.8 redactor. Adapter bytes and checkpoint state are re-hashed by the parent process before a successful report is accepted.

## Acceptance strategy

Core CI installs `.[dev]` only and must prove:

- deterministic TrainingPlan digest and validation;
- tiny fixture run creates a structurally valid Safetensors adapter and checkpoints;
- compatible resume succeeds; mismatched/corrupt resume fails before worker execution;
- validation content does not affect trained adapter bytes;
- train split digest mismatch fails closed;
- unknown/insufficient host budgets fail before worker;
- timeout/cancel are terminal and argv does not expose model/tokenizer/dataset identifiers;
- real engine cannot start without R15.8 capability authorization;
- core imports do not load heavy ML packages;
- schema, Ruff and compile checks pass on Ubuntu + Windows.

Large real-model training remains conditional and is not required for R15.9 core acceptance.
