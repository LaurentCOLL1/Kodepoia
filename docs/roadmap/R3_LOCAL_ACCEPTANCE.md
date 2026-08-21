# R3 — Local hardware acceptance

R3 cannot be marked `COMPLETE` from GitHub Actions alone because model quality, throughput and VRAM usage depend on the target workstation and locally installed Ollama models.

## Finalists selected from local preselection

Measured role candidates on the target workstation:

- KodeFast: `granite4.1:3b`
- KodeCore: `gpt-oss:20b`
- KodeCoder: `ornith:9b`

`north-mini-code-1.0:Q4_K_M` remains a future optional `KodeDeepCoder` candidate but is not required for the accepted R3 default stack.

## Official acceptance command

```powershell
.\scripts\r3_accept_local.ps1 -Model "granite4.1:3b","gpt-oss:20b","ornith:9b"
```

Output:

```text
.kodepoia/benchmarks/r3-local-acceptance.json
```

## Acceptance result — PASSED on 21 August 2026

The target workstation generated and structurally validated the official report.

Environment/metadata:
- Windows 11;
- Python 3.12.4;
- Ollama 0.32.14;
- 5 repetitions per finalist;
- `temperature=0`;
- `num_predict=1024`;
- `acceptance_profile=full-capability-thinking-aware`;
- `phase=R3-local-acceptance`;
- `acceptance_completed=true`;
- `candidate_count=3`;
- `ollama_url=http://127.0.0.1:11434`;
- `loopback_verified=true`.

### `granite4.1:3b` — accepted KodeFast

- 35/40, score 0.875 x5, stddev 0.0;
- 131.366 tok/s;
- 24.089 s average scored repeat;
- 16.294 s average preload/cold-load;
- exact instruction, Python, Godot, typed GDScript, debugging, structured JSON and native tool calling: 5/5 each;
- software-engineering/worktree: 0/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.

Engineering decision: accept for FAST/lightweight routing. Do not route non-trivial Git/repository-management decisions to Granite; route them to KodeCore/KodeCoder.

### `gpt-oss:20b` — accepted KodeCore

- 40/40, score 1.0 x5, stddev 0.0;
- 15.909 tok/s;
- 152.993 s average scored repeat;
- 90.435 s average preload/cold-load;
- all eight categories 5/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- thinking `medium`.

Engineering decision: accept for CORE/reasoning/general engineering. Keep-alive/KodeVRAM should minimize reload churn because cold-load is expensive.

### `ornith:9b` — accepted KodeCoder

- 40/40, score 1.0 x5, stddev 0.0;
- 64.512 tok/s;
- 53.149 s average scored repeat;
- 36.116 s average preload/cold-load;
- all eight categories 5/5, including structured JSON, native tool calling and Git worktree;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- about 6.31 GB model and 6.31 GB resident VRAM reported by Ollama;
- thinking enabled.

Engineering decision: accept for CODER because it combines perfect repeatable capability evidence with substantially better latency and VRAM fit than the heavier coding finalists.

## Accepted routing defaults

- `KodeFast` → `granite4.1:3b`
- `KodeCore` → `gpt-oss:20b`
- `KodeCoder` → `ornith:9b`

These defaults are hardware-specific accepted choices, not architectural lock-in. Future models may replace them after the same benchmark/acceptance process.

## Completion status

The hardware-local acceptance requirements are satisfied. R3 can be marked `COMPLETE` on the hardening branch.

Remaining repository integration steps before R4:
1. final acceptance-documentation CI must be green;
2. PR #8 must be merged;
3. `main` must be verified after merge;
4. continuity must reflect the merged state;
5. only then may R4 begin.
