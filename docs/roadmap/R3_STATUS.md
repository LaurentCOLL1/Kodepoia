# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** COMPLETE — HARDWARE-LOCAL ACCEPTANCE PASSED — MERGED TO MAIN  
**Updated:** 2026-08-21

## Repository state

- PR #8 — `R1-R3 Acceptance Hardening`: **MERGED**.
- Merge commit: `8e16e6a7d9f6c38d26a663ba9bdafd4950dba7c4`.
- Final hardening CI head: `e3f62b4d74f36e05f3041d56853ad50b7378c73c`.
- Final CI: R0 Repository Guard, Python Core (Ubuntu/Windows + PowerShell syntax) and KodeStudio UI Smoke all **SUCCESS**.
- `main` contains the accepted R3 implementation/status.

## Implemented and accepted

- [x] Model-agnostic Brain protocol.
- [x] Local Ollama non-streaming + streaming chat.
- [x] Tools, structured output, thinking, images, keep-alive, unload and preload.
- [x] KodeModelRegistry FAST / CORE / CODER / EMBED / VISION.
- [x] Capability-aware KodeModelRouter.
- [x] Persistent SQLite KodeMemory + embeddings + semantic retrieval wired into Orchestrator.
- [x] KodeContext token budget and streamed orchestration.
- [x] Repeated role-aware local benchmark with deterministic controls.
- [x] Strict exact/Godot/GDScript/Git/JSON/real-tool validators.
- [x] `done_reason` and generation-budget diagnostics.
- [x] Cold-load separated from scored correctness using unscored preload.
- [x] Local-only `r3-accept` and Windows runner.
- [x] Final hardware-local acceptance on target PC.

## Official R3 hardware-local acceptance

Evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

Environment:
- Windows 11;
- Python 3.12.4;
- Ollama 0.32.14;
- `http://127.0.0.1:11434`, loopback verified;
- 5 repetitions per finalist;
- `temperature=0`;
- `num_predict=1024`;
- profile `full-capability-thinking-aware`;
- `acceptance_completed=true`;
- `candidate_count=3`.

### Accepted KodeFast — `granite4.1:3b`
- 35/40, 0.875 x5, stddev 0.0;
- 131.366 tok/s;
- 16.294 s preload/cold-load;
- exact/Python/Godot/GDScript/debug/JSON/native-tools: 5/5;
- software-engineering/worktree: 0/5;
- 0 errors, preload failures/timeouts or budget exhaustions.

Routing constraint: non-trivial Git/repository-management work must go to CORE/CODER, not Granite.

### Accepted KodeCore — `gpt-oss:20b`
- 40/40, 1.0 x5, stddev 0.0;
- 15.909 tok/s;
- 90.435 s preload/cold-load;
- all eight categories 5/5;
- 0 errors, preload failures/timeouts or budget exhaustions;
- thinking `medium`.

### Accepted KodeCoder — `ornith:9b`
- 40/40, 1.0 x5, stddev 0.0;
- 64.512 tok/s;
- 36.116 s preload/cold-load;
- all eight categories 5/5;
- 0 errors, preload failures/timeouts or budget exhaustions;
- about 6.31 GB resident VRAM;
- thinking enabled.

## Accepted defaults

- `KodeFast` → `granite4.1:3b`
- `KodeCore` → `gpt-oss:20b`
- `KodeCoder` → `ornith:9b`

`north-mini-code-1.0:Q4_K_M` remains an optional future `KodeDeepCoder` candidate for repository-scale/long-horizon evaluation.

These are hardware-specific defaults, not architectural lock-in. Kodepoia remains model-agnostic.

## Next phase

R3 is closed. **R4 — KodeCode is AUTHORIZED / NOT STARTED.** Start R4 only from the latest `main` on a new dedicated branch, preserving the frozen v1.0 architecture.
