# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** COMPLETE — HARDWARE-LOCAL ACCEPTANCE PASSED  
**Updated:** 2026-08-21

## Validation evidence

Original implementation:
- PR #5 — `R3: implement KodeBrain, Memory, Context and ModelRouter`.
- Merge commit: `b5e61dea1d50ccfc8ffff6f1e525f95a39b8096f`.

Acceptance hardening:
- PR #8 — `R1-R3 Acceptance Hardening`.
- Role-aware repeated benchmark, strict validators, thinking-budget diagnostics and cold-load/preload separation are implemented and CI-covered.
- Final target-workstation evidence: `.kodepoia/benchmarks/r3-local-acceptance.json` generated on 2026-08-21.

## Implemented

- [x] Model-agnostic Brain protocol.
- [x] Local Ollama adapter with non-streaming + streaming chat.
- [x] Tools, structured output, thinking, images, keep-alive, unload and preload.
- [x] KodeModelRegistry with FAST / CORE / CODER / EMBED / VISION roles.
- [x] Capability-aware KodeModelRouter.
- [x] Persistent SQLite KodeMemory + semantic retrieval wired into Orchestrator.
- [x] KodeContext token budget and streamed orchestration.
- [x] Repeated role-aware local benchmark with deterministic seeds/temperature.
- [x] Strict validators for exact instruction, Godot 4, typed GDScript, Git worktree, structured JSON and true Ollama tool calls.
- [x] `done_reason` + generation-budget diagnostics.
- [x] Cold-load separated from scored correctness with unscored preload and dedicated timeout.
- [x] `kodepoia r3-accept` local-only acceptance path and Windows runner.

## Preselection decisions

- KodeFast candidate: `granite4.1:3b`.
- KodeCore candidate: `gpt-oss:20b`.
- KodeCoder candidate: `ornith:9b`.
- Future optional `KodeDeepCoder` candidate: `north-mini-code-1.0:Q4_K_M` for later repository-scale/long-horizon evaluation.

## Official R3 hardware-local acceptance — PASSED

Evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

Environment:
- Windows 11 target workstation;
- Python 3.12.4;
- Ollama 0.32.14;
- local loopback endpoint `http://127.0.0.1:11434` verified;
- 5 repetitions per finalist;
- `temperature=0`;
- `num_predict=1024`;
- acceptance profile `full-capability-thinking-aware`.

Structural acceptance metadata passed:
- `phase == R3-local-acceptance`;
- `acceptance_completed == true`;
- `candidate_count == 3`;
- `loopback_verified == true`;
- all selected finalists present in the benchmark summary.

### Accepted KodeFast — `granite4.1:3b`

- 35/40, score **0.875 x5**, score stddev 0.0;
- 131.366 tok/s;
- 24.089 s average scored repeat;
- 16.294 s average preload/cold-load;
- exact/Python/Godot/GDScript/debug/structured-output/native-tools: 5/5 each;
- software-engineering/worktree: 0/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.

Acceptance rationale: the role is intentionally FAST/routing/lightweight. It is not trusted for repository-workflow decisions such as Git worktree; those tasks must route to CORE/CODER. Its measured latency/throughput and seven reliable categories make it suitable for the intended role.

### Accepted KodeCore — `gpt-oss:20b`

- **40/40, score 1.000 x5**, score stddev 0.0;
- 15.909 tok/s;
- 152.993 s average scored repeat;
- 90.435 s average preload/cold-load;
- all eight categories 5/5 including structured output, real tool calling and software-engineering/worktree;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- thinking mode `medium`.

Acceptance rationale: perfect repeatable capability evidence for reasoning/general engineering. KodeVRAM/keep-alive should avoid unnecessary reload churn because cold-load is expensive.

### Accepted KodeCoder — `ornith:9b`

- **40/40, score 1.000 x5**, score stddev 0.0;
- **64.512 tok/s**;
- **53.149 s average scored repeat**;
- **36.116 s average preload/cold-load**;
- all eight categories 5/5 including structured output, real tool calling and software-engineering/worktree;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- Ollama reports about 6.31 GB model and 6.31 GB resident VRAM, so it fits fully in the target 12 GB VRAM;
- thinking enabled.

Acceptance rationale: perfect repeatable capability evidence with substantially better latency and memory fit than the heavier coding finalists.

## Accepted R3 model roles

- `KodeFast` → `granite4.1:3b`
- `KodeCore` → `gpt-oss:20b`
- `KodeCoder` → `ornith:9b`

Routing constraint: Git/repository-management and other non-trivial software-engineering decisions must not be delegated to Granite because the final acceptance reproduced its 0/5 worktree weakness. Route those tasks to Ornith or GPT-OSS.

The architecture remains model-agnostic: these are the accepted local defaults for the current target workstation, not permanent architectural dependencies.

## Completion rule result

All R3 functional and hardware-local acceptance criteria are satisfied. R3 is therefore **COMPLETE** on the hardening branch.

Final sequence before R4:
1. run final CI for the acceptance-documentation head;
2. merge PR #8 only if final CI is green;
3. verify `main` after merge;
4. only then begin R4.
