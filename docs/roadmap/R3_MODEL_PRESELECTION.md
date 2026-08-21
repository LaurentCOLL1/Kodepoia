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

**Provisional KodeFast winner: `granite4.1:3b`.**

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

**Provisional KodeCore winner: `gpt-oss:20b`.**

`qwen3.5:9b` remains available as a smaller multimodal/non-thinking fallback candidate.

## CODER v1 — DIAGNOSTIC COMPLETE

Evidence: `.kodepoia/benchmarks/r3-preselect-coder.json`.

- `qwen2.5-coder:7b-instruct`: 30/40, 82.296 tok/s, but native tool calling 0/5 and worktree 0/5 (`Git Subtree`). Retain only as possible compact code helper.
- `devstral-small-2:24b`: raw 30/40, about 3.968 tok/s, unstable loading and worktree 0/5. Removed from default-coder contest on this workstation.
- `north-mini-code-1.0:Q4_K_M`: raw 35/40; its only five misses were first-task 120 s cold-load timeouts. Python/Godot/GDScript/debug/JSON/native-tools/worktree were 5/5. This exposed the cold-load scoring bias and triggered the unscored preload hardening.

## Cold-load hardening — VALIDATED

The harness now preloads each model with a non-scored empty Ollama chat request before scored tasks. Preload uses a dedicated 240 s timeout. Cold-load remains a practicality metric but is no longer misclassified as a knowledge failure.

Validated functional/documentary head before CODER v2: `e07278744870f979ff9a128ee0b93de44717cdcc`.

## CODER v2 — COMPLETE / PROVISIONAL WINNER SELECTED

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
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.
- About 10.03 GB reported resident in VRAM while running.

The corrected preload proves that North's old 35/40 score was a harness artifact: it now passes exact instruction 5/5.

### `ornith:9b`
- 40/40, score **1.000** x5, score stddev 0.0.
- **64.430 tok/s**.
- **53.863 s average scored repeat**.
- **36.418 s average cold-load/preload**.
- All eight categories 5/5, including structured output, true tool calling and Git worktree.
- 0 errors, 0 preload failures/timeouts, 0 budget exhaustions.
- Ollama reports about **6.31 GB model size and 6.31 GB resident VRAM**, so it fits fully in the target 12 GB VRAM.

### `laguna-xs-2.1:Q4_K_M`
- 25/40, score **0.625** x5, score stddev 0.0.
- 19.950 tok/s.
- 263.606 s average scored repeat.
- 116.359 s average cold-load/preload.
- Passes exact/Python/Godot/GDScript/debug 5/5.
- **Structured output 0/5, native tool calling 0/5, software-engineering/worktree 0/5.**
- Failures are deterministic empty final responses under the current Ollama `/api/chat` + format/tools integration, with no preload timeout and no generation-budget exhaustion.

Because Ollama upstream advertises Laguna XS 2.1 as tools/thinking capable, this is treated as an **operational incompatibility with Kodepoia's current Ollama chat/tool path on the target setup**, not proof that the underlying model is intrinsically incapable. It is removed from R3 final selection.

## CODER decision

**Provisional KodeCoder winner: `ornith:9b`.**

Rationale: it ties GPT-OSS and North at perfect, perfectly repeatable correctness, but is approximately 3.5x faster than North and 4.1x faster than GPT-OSS in generation throughput, has by far the shortest scored-repeat time, the lowest cold-load among the three perfect models, and fits fully in 12 GB VRAM.

`north-mini-code-1.0:Q4_K_M` remains a strong future `KodeDeepCoder` / long-horizon repository candidate because it is explicitly trained for agentic software engineering and also achieved 40/40 once cold-load was separated. It is not selected as the default daily coder because its hardware cost is much higher without measurable quality gain in this R3 suite.

`gpt-oss:20b` remains KodeCore and is also a valid coding fallback/reviewer.

## R3 final hardware acceptance candidates

The natural three role finalists are now:

- KodeFast candidate: `granite4.1:3b`
- KodeCore candidate: `gpt-oss:20b`
- KodeCoder candidate: `ornith:9b`

Run official `r3-accept` only with these three unless new evidence appears. Default acceptance uses five repeats and the full-capability thinking-aware profile.

R3 remains `PENDING ACCEPTANCE` until `.kodepoia/benchmarks/r3-local-acceptance.json` is generated, structurally validated, technically reviewed, roles are recorded, final CI is green, and PR #8 is safe to merge.
