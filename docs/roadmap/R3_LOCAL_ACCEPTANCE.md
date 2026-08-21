# R3 — Local hardware acceptance

## Status

**PASSED / CLOSED** on 21 August 2026 and merged to `main` through PR #8.

Official evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

## Accepted defaults

- KodeFast: `granite4.1:3b`
- KodeCore: `gpt-oss:20b`
- KodeCoder: `ornith:9b`

`north-mini-code-1.0:Q4_K_M` remains a future optional `KodeDeepCoder` candidate and is not part of the accepted R3 default trio.

## Acceptance environment

- Windows 11 target workstation;
- Python 3.12.4;
- Ollama 0.32.14;
- local endpoint `http://127.0.0.1:11434`;
- loopback verified;
- 5 repetitions per finalist;
- `temperature=0`;
- `num_predict=1024`;
- `full-capability-thinking-aware` profile;
- `acceptance_completed=true`;
- `candidate_count=3`.

## Results

### `granite4.1:3b` — KodeFast
- 35/40, 0.875 x5, stddev 0.0;
- 131.366 tok/s;
- 16.294 s average preload/cold-load;
- exact/Python/Godot/GDScript/debug/JSON/native-tools: 5/5;
- software-engineering/worktree: 0/5;
- 0 errors, preload failures/timeouts or budget exhaustions.

Routing rule: non-trivial Git/repository decisions must route to CORE/CODER.

### `gpt-oss:20b` — KodeCore
- 40/40, 1.0 x5, stddev 0.0;
- 15.909 tok/s;
- 90.435 s average preload/cold-load;
- all eight categories 5/5;
- 0 errors, preload failures/timeouts or budget exhaustions;
- thinking `medium`.

### `ornith:9b` — KodeCoder
- 40/40, 1.0 x5, stddev 0.0;
- 64.512 tok/s;
- 36.116 s average preload/cold-load;
- all eight categories 5/5;
- 0 errors, preload failures/timeouts or budget exhaustions;
- ~6.31 GB resident VRAM;
- thinking enabled.

## Repository closure

Final hardening CI was green, PR #8 was merged as commit `8e16e6a7d9f6c38d26a663ba9bdafd4950dba7c4`, and R3 is COMPLETE on `main`.

This procedure is retained as the repeatable acceptance method for future model replacements. Future candidate changes should re-run the same evidence process rather than silently changing defaults.

R4 is **AUTHORIZED / NOT STARTED** and must begin from the latest `main` on a new branch.
