# R15.16 — Hardware-local end-to-end qualification acceptance

Status: COMPLETE / END-sync closed; final exact-head re-gates pending.

R15.16 provides the repository-owned, non-mutating local doctor that distinguishes proven runtime capability from package names, device marketing names or hosted-CI assumptions. A real target-workstation training/conversion/promotion claim remains conditional and was not triggered by the accepted technical scope.

## Frozen qualification contract

- exact repository HEAD must equal the supplied 40-character source SHA before any qualification can pass;
- the service reuses R15.8 `TrainingRuntime` rather than duplicating backend logic: disk/RAM preflight, CPU/CUDA/ROCm operation probes, dtype operation, optional NF4 `Linear4bit` operation, optional local-only model load and VRAM admission remain bounded/fail-closed;
- Ollama inspection is a fixed, non-mutating `ollama --version` probe; Ollama availability does not imply training-backend availability;
- `training_required=true` requires an operationally READY backend and maps budget failure to `resource_budget_blocked` and all other non-ready runtime paths to `training_backend_unavailable`;
- when training is not required by the accepted project evidence, `no_train_required` is a valid PASS while unavailable optional runtime/Ollama capabilities remain explicit warnings;
- report output must stay inside the project root; reports contain bounded/redacted facts and a canonical SHA-256 digest and validate against `schemas/r15-16-local-qualification-v1.schema.json`;
- the core acceptance environment installs only `.[dev]`; no GPU driver, Torch, Transformers, PEFT, TRL, bitsandbytes, llama.cpp, cloud service or public model account is installed or required;
- manual state: `CONDITIONAL / NOT TRIGGERED`.

## Accepted technical-source evidence

Immutable technical source `d492bfe53dd805aadcfa14193a2cf4fba1711276` passed R15.16 Hardware Local Qualification Acceptance #2 / `33337106579` on both Ubuntu 24.04 and Windows 2025:

- exact-SHA checkout/provenance assertion: SUCCESS on both OS;
- core development dependency install only: SUCCESS;
- compile of the R15.16-owned surface: SUCCESS;
- 9 focused/schema tests: SUCCESS on both OS;
- real non-mutating CI doctor execution: SUCCESS;
- Draft 2020-12 report-schema and exact-source provenance validation: SUCCESS;
- Ruff over R15.16-owned Python: SUCCESS.

The first candidate `6f2c1aa61faa51536e99eaeab40a0f97d04bed3a` / R15.16 #1 `33337019018` is explicitly rejected and MUST NOT be reused as acceptance evidence. Its functional steps passed, but Ruff B008 failed on both OS because `QualificationPolicy()` was constructed in a function default. The accepted source fixes only that static defect by using a null default and constructing the immutable policy inside the method.

## Conditional real-hardware state

No accepted R15 gap decision or promotion claim currently requires a real target-workstation QLoRA/conversion/promotion result. Therefore the conditional manual gate is not triggered. This is not a claim that the target RX 6750 XT is training-capable or incapable under every future stack; the accepted contract requires the exact operation probe on the exact future environment if such a claim becomes necessary.

Current external compatibility documentation is dated/advisory only. A wheel/tool may list an AMD architecture while a particular Windows HIP/PyTorch stack or vendor support matrix does not support the exact device. R15.16 therefore treats actual backend/dtype/NF4/model operations and resource evidence as authoritative, never the wheel name or GPU family alone.

## Exact-head acceptance required before merge

This END synchronization changes documentary authority. The final R15.16 PR head must receive, on one unchanged SHA:

1. R15.16 Hardware Local Qualification Acceptance on Ubuntu and Windows;
2. R0 Repository Guard;
3. full Python Core (all jobs);
4. KodeStudio UI Smoke.

Only then may the implementation/evidence PR merge with exact `expected_head_sha`. Exactly one continuity-only post-merge normalization with fresh exact-head R0/Python/UI remains mandatory before R15.17 START-sync is authorized.
