# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** IMPLEMENTATION COMPLETE — HARDWARE-LOCAL ACCEPTANCE PENDING  
**Updated:** 2026-08-21

## Validation evidence

Original implementation:
- PR #5 — `R3: implement KodeBrain, Memory, Context and ModelRouter`.
- Merge commit: `b5e61dea1d50ccfc8ffff6f1e525f95a39b8096f`.

Acceptance hardening:
- PR #8 — `R1-R3 Acceptance Hardening`.
- Cold-load separation hardening validated before CODER v2.
- R0 Repository Guard, Python Core Ubuntu/Windows and KodeStudio UI Smoke were green on the validated hardening head.

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

## Local preselection evidence

### FAST — completed

Evidence: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

- `granite4.1:3b`: 28/32, 0.875 x4, 129.512 tok/s.
- `qwen3.5:4b`: 28/32, 0.875 x4, 80.690 tok/s.

**Provisional KodeFast winner: `granite4.1:3b`.**

### CORE — completed

Evidence: `.kodepoia/benchmarks/r3-preselect-core-v2.json`.

- `qwen3.5:9b`: 25/40, 0.625 x5, 54.609 tok/s, 15 bounded-thinking generation-budget exhaustions.
- `gpt-oss:20b`: 40/40, 1.0 x5, 15.399 tok/s, all eight categories 5/5, 0 errors/budget exhaustions, cold-load ~90.985 s.

**Provisional KodeCore winner: `gpt-oss:20b`.**

### CODER v1 — diagnostic completed

Evidence: `.kodepoia/benchmarks/r3-preselect-coder.json`.

- Qwen2.5-Coder: fast but native tools 0/5 and worktree 0/5.
- Devstral 24B: ~3.968 tok/s and worktree 0/5; impractical default on target hardware.
- North Mini Code: substantive leader, but old raw score was contaminated by first-task cold-load timeouts.

This triggered the preload/cold-load hardening.

### CODER v2 — completed / decision made

Evidence: `.kodepoia/benchmarks/r3-preselect-coder-v2.json`.

Target workstation: Windows 11, Python 3.12.4, Ollama 0.32.14, five repeats, `benchmark_role=coder`, `temperature=0`, `num_predict=1024`.

`gpt-oss:20b`:
- 40/40, 1.0 x5;
- 15.611 tok/s;
- 162.613 s average scored repeat;
- 98.403 s average preload;
- all eight categories 5/5;
- 0 errors/preload failures/timeouts/budget exhaustions.

`north-mini-code-1.0:Q4_K_M`:
- 40/40, 1.0 x5;
- 18.330 tok/s;
- 201.761 s average scored repeat;
- 114.093 s average preload;
- all eight categories 5/5;
- 0 errors/preload failures/timeouts/budget exhaustions;
- ~10.03 GB resident VRAM.

`ornith:9b`:
- **40/40, 1.0 x5**;
- **64.430 tok/s**;
- **53.863 s average scored repeat**;
- **36.418 s average preload**;
- all eight categories 5/5, including structured output, true tool calling and worktree;
- 0 errors/preload failures/timeouts/budget exhaustions;
- ~6.31 GB model and ~6.31 GB resident VRAM.

`laguna-xs-2.1:Q4_K_M`:
- 25/40, 0.625 x5;
- 19.950 tok/s;
- structured output 0/5, native tools 0/5, worktree 0/5 under current Ollama chat integration;
- removed from R3 final selection.

**Provisional KodeCoder winner: `ornith:9b`.**

North remains a future `KodeDeepCoder`/long-horizon repository candidate; GPT-OSS remains a valid coding fallback/reviewer.

## Final R3 acceptance candidates

The measured role finalists are now:

- `granite4.1:3b` — KodeFast
- `gpt-oss:20b` — KodeCore
- `ornith:9b` — KodeCoder

## Remaining hardware-local acceptance

R3 remains intentionally incomplete until:
1. the official target-PC acceptance is run with the three finalists above;
2. `.kodepoia/benchmarks/r3-local-acceptance.json` is structurally validated and technically reviewed;
3. selected roles are recorded as accepted;
4. final CI is green;
5. PR #8 is safe to merge.

Prepared command from repository root after pulling the latest hardening branch:

```powershell
.\scripts\r3_accept_local.ps1 -Model "granite4.1:3b","gpt-oss:20b","ornith:9b"
```

Default acceptance performs five repetitions with the full-capability thinking-aware profile and `num_predict=1024`.

## Completion rule

R3 becomes `COMPLETE` only after the final local acceptance report is reviewed and acceptable, final documentation/CI are green, and PR #8 is safe to merge. R4 must not begin before R3 is accepted.
