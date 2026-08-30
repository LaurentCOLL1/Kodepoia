# R15.16 — Hardware-local end-to-end qualification + reproducibility/resource acceptance

Status: IN_PROGRESS — automated doctor/fixture acceptance first; real target-workstation gate remains CONDITIONAL / NOT TRIGGERED.

## Authority

R15.16 starts from normalized R15.15 `main` `01f91fd4b56ed2a02151b46d70502b734c771e7f` on branch `r15/16-hardware-local-qualification`.

Hosted CI is not authoritative evidence that a user's specific GPU, driver, ROCm/CUDA stack, local model store or Ollama installation can execute a real QLoRA/conversion/promotion path. CI validates the runner, schema, fail-closed decisions and truthful unavailable/no-train paths only.

## Implemented qualification contract

The repository-owned `scripts/r15_16_local_acceptance.py` runner:

1. requires an exact 40-character source SHA and rejects execution evidence from a different repository HEAD;
2. reuses the accepted R15.8 `TrainingRuntime` operation probe rather than inferring training capability from GPU names, VRAM size or package presence;
3. records only bounded OS/machine/Python facts, R15.8 capability evidence, and a bounded non-mutating `ollama --version` availability probe;
4. never installs drivers, ROCm/CUDA, Python ML packages, Ollama or model tooling;
5. never accepts arbitrary commands or environment variables from model/dataset text;
6. keeps the output inside the project root and emits a canonical SHA-256 over the report;
7. distinguishes `no_train_required`, `training_backend_ready`, `training_backend_unavailable`, `resource_budget_blocked`, `ollama_required_unavailable` and exact-source mismatch;
8. treats an unavailable training backend as a blocker only when a real training claim is explicitly required;
9. treats missing Ollama as a blocker only when an Ollama packaging/runtime claim is explicitly required;
10. preserves unsupported/unavailable probe results as evidence instead of converting them to synthetic PASS capability claims.

Schema authority: `schemas/r15-16-local-qualification-v1.schema.json`.

## Current external compatibility evidence

External compatibility is dated evidence, not a repository architecture constant.

- Current Hugging Face bitsandbytes installation documentation lists AMD ROCm support and Windows ROCm wheel targets, but still requires a compatible ROCm-enabled PyTorch stack and operation-level validation.
- AMD's current Windows HIP SDK compatibility tables remain GPU-specific and explicitly distinguish supported and unsupported Radeon devices.
- Therefore R15.16 accepts only the local operation probe as authority for a requested training backend. A package wheel target, GPU architecture name, or successful Ollama inference path alone cannot prove QLoRA support.

References:

- https://huggingface.co/docs/bitsandbytes/installation
- https://rocm.docs.amd.com/projects/install-on-windows/en/latest/reference/system-requirements.html
- https://rocm.docs.amd.com/projects/install-on-windows/en/latest/conceptual/component-support.html

## Core CI acceptance

The dedicated R15.16 workflow must pass on Ubuntu and Windows and must:

- checkout and assert the exact workflow source SHA;
- install only repository development dependencies, not heavy optional training stacks;
- compile the R15.16 doctor/runner;
- run focused doctor, source-mismatch, backend-unavailable, required-Ollama, path-boundary and schema tests;
- execute the real runner against the CI host with `--backend cpu` and neither training nor Ollama required;
- validate the generated report against the Draft 2020-12 schema;
- prove the generated report source SHA equals the exact checked-out source;
- pass Ruff on R15.16-owned Python files.

The CI host may truthfully report the training probe as unsupported because optional Torch is absent. That remains an accepted `no_train_required` CI path and is not a claim about the target workstation.

## Conditional target-workstation gate

The manual gate is triggered only if completion of R15.16 requires a real target-workstation training, conversion or Ollama promotion capability claim. If it triggers, stop before R15.17 and run the bounded command set on the exact accepted R15.16 head.

Baseline PowerShell doctor shape:

```powershell
$SourceSha = (git rev-parse HEAD).Trim()
python scripts/r15_16_local_acceptance.py `
  --source-sha $SourceSha `
  --backend rocm `
  --output docs/roadmap/R15_16_LOCAL_ACCEPTANCE.json
```

`--training-required`, `--ollama-required`, model identifiers and resource budgets are added only when the accepted R15.7/R15.9/R15.12/R15.13 evidence actually requires those claims. Do not install or change GPU drivers, BIOS settings, ROCm/CUDA, Ollama, model weights or system tuning merely to make this command pass.

If the report says `training_backend_unavailable`, that result is authoritative for the tested stack. An alternate OS/backend may be evaluated separately, but it must not overwrite or reinterpret the original report.

## Privacy and evidence

Return only the generated qualification JSON when a manual gate is triggered. Do not send passwords, tokens, private keys, unrelated environment variables, full user profile paths, unrelated model-store listings, serial numbers or machine identifiers. The runner intentionally omits hostname and username.

## Exact-head completion gates

Before R15.16 implementation may merge, its exact final documented head must pass:

1. R15.16 Hardware Local Qualification Acceptance on Ubuntu + Windows;
2. R0 Repository Guard;
3. full Python Core;
4. KodeStudio UI Smoke.

If the conditional target-workstation gate is not required by the frozen `QLoRA if useful` policy, the completion record must say `CONDITIONAL / NOT TRIGGERED` and may not claim real target-GPU training/conversion/promotion success. If it is triggered, no R15.17 work is authorized until the returned exact-head JSON is reviewed.

After implementation merge, exactly one continuity-only post-merge normalization with fresh exact-head R0/Python/UI remains mandatory before R15.17 START-sync.
