# R3 — Local Model Preselection

This preselection step runs before official `r3-accept`. It compares models by intended Kodepoia role so latency-oriented FAST candidates are not scored with the same thinking policy as CORE/CODER candidates.

## Authoritative benchmark policy

- Preselection: at least 4 repetitions per model; 5 are preferred for final head-to-heads.
- Official `r3-accept`: 5 repetitions per finalist by default.
- `temperature=0`, deterministic seeds starting at 101.
- FAST/BASELINE: `num_predict=256`, `think=false`.
- CORE/CODER: `num_predict=1024`, capability-aware thinking; GPT-OSS uses `think="medium"`.
- Each repeat unloads the model, then performs an **unscored preload** before scored tasks.
- Task timeout: 120 s. Dedicated preload timeout: 240 s.
- Cold-load is recorded separately through `avg_cold_load_s`, `avg_preload_elapsed_s`, `preload_failures`, `preload_timeouts`.
- `done_reason` and generation-budget exhaustion are preserved.
- Strict validators require exact `KODEPOIA_OK`, Godot 4 `CharacterBody3D`, typed GDScript `var count: int = 0`, Git `worktree`, structurally valid JSON and true Ollama tool calls.

## FAST v2 — COMPLETE

Evidence: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

- `granite4.1:3b`: 28/32, score 0.875 x4, 129.512 tok/s.
- `qwen3.5:4b`: 28/32, score 0.875 x4, 80.690 tok/s.
- Both pass exact/Python/Godot/GDScript/debug/JSON/tools 4/4 and fail Git worktree 4/4.

**KodeFast winner: `granite4.1:3b`.**

`qwen3.5:4b` remains a compact multimodal fallback candidate.

## CORE v2 — COMPLETE

Evidence: `.kodepoia/benchmarks/r3-preselect-core-v2.json`.

### `qwen3.5:9b`
- 25/40, score 0.625 x5.
- 54.609 tok/s.
- 15 deterministic `generation_budget_exhausted` failures under the bounded 1024-token thinking policy.

### `gpt-oss:20b`
- 40/40, score 1.000 x5.
- 15.399 tok/s.
- All eight categories 5/5.
- 0 errors, 0 budget exhaustions.
- Cold-load about 90.985 s.

**KodeCore winner: `gpt-oss:20b`.**

`qwen3.5:9b` remains available as a smaller multimodal/non-thinking fallback candidate.

## CODER v1 — DIAGNOSTIC COMPLETE

Evidence: `.kodepoia/benchmarks/r3-preselect-coder.json`.

- `qwen2.5-coder:7b-instruct`: 30/40, 82.296 tok/s, but native tool calling 0/5 and worktree 0/5 (`Git Subtree`). Retain only as possible compact code helper.
- `devstral-small-2:24b`: raw 30/40, about 3.968 tok/s, unstable loading and worktree 0/5. Removed from default-coder contest on this workstation.
- `north-mini-code-1.0:Q4_K_M`: raw 35/40; its only five misses were first-task 120 s cold-load timeouts. Python/Godot/GDScript/debug/JSON/native-tools/worktree were 5/5. This exposed the cold-load scoring bias and triggered the unscored preload hardening.

## Cold-load hardening — VALIDATED

The harness now preloads each model with a non-scored empty Ollama chat request before scored tasks. Preload uses a dedicated 240 s timeout. Cold-load remains a practicality metric but is no longer misclassified as a knowledge failure.

## CODER v2 — COMPLETE

Evidence: `.kodepoia/benchmarks/r3-preselect-coder-v2.json`.

Target workstation: Windows 11, Python 3.12.4, Ollama 0.32.14. Five repetitions per candidate, `benchmark_role=coder`, `temperature=0`, `num_predict=1024`.

### `gpt-oss:20b`
- 40/40, score **1.000** x5, score stddev 0.0.
- 15.611 tok/s.
- 162.613 s average scored repeat.
- 98.403 s average cold-load/preload.
- All eight categories 5/5.
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.

### `north-mini-code-1.0:Q4_K_M`
- 40/40, score **1.000** x5, score stddev 0.0.
- 18.330 tok/s.
- 201.761 s average scored repeat.
- 114.093 s average cold-load/preload.
- All eight categories 5/5, including true tool calling and Git worktree.
- About 10.03 GB reported resident in VRAM.

### `ornith:9b`
- 40/40, score **1.000** x5, score stddev 0.0.
- **64.430 tok/s**.
- **53.863 s average scored repeat**.
- **36.418 s average cold-load/preload**.
- All eight categories 5/5, including structured output, true tool calling and Git worktree.
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.
- Ollama reports about **6.31 GB model size and 6.31 GB resident VRAM**.

### `laguna-xs-2.1:Q4_K_M`
- 25/40, score **0.625** x5, score stddev 0.0.
- 19.950 tok/s.
- Structured output 0/5, native tool calling 0/5, software-engineering/worktree 0/5 under the current Ollama chat integration.
- Removed from R3 final selection.

**KodeCoder winner: `ornith:9b`.**

`north-mini-code-1.0:Q4_K_M` remains a strong future `KodeDeepCoder` / long-horizon repository candidate. `gpt-oss:20b` remains a valid coding fallback/reviewer.

## Official R3 hardware acceptance — COMPLETE / PASSED

Evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

Finalists:
- KodeFast: `granite4.1:3b`
- KodeCore: `gpt-oss:20b`
- KodeCoder: `ornith:9b`

Acceptance environment and controls:
- Windows 11 target workstation;
- Python 3.12.4;
- Ollama 0.32.14;
- loopback URL `http://127.0.0.1:11434` verified;
- `acceptance_completed=true`;
- 5 repeats;
- `temperature=0`;
- `num_predict=1024`;
- profile `full-capability-thinking-aware`.

Final results:

### `granite4.1:3b`
- 35/40, **0.875 x5**, stddev 0.0;
- 131.366 tok/s;
- 16.294 s cold-load/preload;
- seven categories 5/5 including JSON and real tool calling;
- software-engineering/worktree 0/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.

Accepted for FAST because the role is lightweight/routing-oriented. Repository-management/Git decisions must be routed away from Granite to CORE/CODER.

### `gpt-oss:20b`
- **40/40, 1.000 x5**, stddev 0.0;
- 15.909 tok/s;
- 90.435 s cold-load/preload;
- all eight categories 5/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- thinking `medium`.

### `ornith:9b`
- **40/40, 1.000 x5**, stddev 0.0;
- **64.512 tok/s**;
- **36.116 s cold-load/preload**;
- all eight categories 5/5;
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions;
- ~6.31 GB resident VRAM; thinking enabled.

## Final accepted defaults for the target workstation

- `KodeFast` → `granite4.1:3b`
- `KodeCore` → `gpt-oss:20b`
- `KodeCoder` → `ornith:9b`

These are measured local defaults, not architectural lock-in. Kodepoia remains model-agnostic and may re-benchmark replacements later.

R3 hardware-local acceptance is complete. Final CI and PR #8 merge are the remaining repository-integration steps before R4.
