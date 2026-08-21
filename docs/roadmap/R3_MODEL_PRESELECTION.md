# R3 — Local Model Preselection

## Status

**COMPLETE / CLOSED.** The preselection produced the final R3 candidates, the official hardware-local acceptance passed, and PR #8 has been merged into `main`.

## Authoritative benchmark policy

- preselection: at least 4 repetitions per model;
- official `r3-accept`: 5 repetitions per finalist;
- `temperature=0`, deterministic seeds starting at 101;
- FAST/BASELINE: `num_predict=256`, `think=false`;
- CORE/CODER/final: `num_predict=1024`, capability-aware thinking; GPT-OSS uses `medium`;
- unload between repetitions;
- unscored preload before scored tasks, dedicated 240 s preload timeout;
- task timeout 120 s;
- cold-load/preload reported separately from correctness;
- strict validators for `KODEPOIA_OK`, `CharacterBody3D`, typed GDScript, Git `worktree`, structured JSON and real Ollama tool calls.

## FAST decision

Evidence: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

- `granite4.1:3b`: 28/32, 0.875 x4, 129.512 tok/s.
- `qwen3.5:4b`: 28/32, 0.875 x4, 80.690 tok/s.

**Winner: `granite4.1:3b`.** Both small models failed Git worktree, so complex repository work is explicitly out of FAST scope.

## CORE decision

Evidence: `.kodepoia/benchmarks/r3-preselect-core-v2.json`.

- `qwen3.5:9b`: 25/40, 0.625 x5, 15 bounded-thinking budget exhaustions.
- `gpt-oss:20b`: 40/40, 1.0 x5, all eight categories 5/5.

**Winner: `gpt-oss:20b`.** Qwen 9B remains a possible multimodal/non-thinking fallback.

## CODER decision

Evidence: `.kodepoia/benchmarks/r3-preselect-coder-v2.json`.

- `gpt-oss:20b`: 40/40, 15.611 tok/s.
- `north-mini-code-1.0:Q4_K_M`: 40/40, 18.330 tok/s, ~10.03 GB resident VRAM.
- `ornith:9b`: 40/40, 64.430 tok/s, 36.418 s preload, ~6.31 GB resident VRAM.
- `laguna-xs-2.1:Q4_K_M`: 25/40; structured output, native tools and worktree 0/5 under the tested Ollama chat integration.

**Winner: `ornith:9b`.** North remains an optional future `KodeDeepCoder` candidate for genuinely long repository-scale scenarios.

Earlier CODER v1 also established that `qwen2.5-coder:7b-instruct` is a useful compact code helper but failed native tool calling and worktree, while Devstral 24B was impractical on the target hardware.

## Final official acceptance

Evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

- `granite4.1:3b` — 35/40, 0.875 x5, 131.366 tok/s; accepted KodeFast with repository-routing restriction.
- `gpt-oss:20b` — 40/40, 1.0 x5, all categories 5/5; accepted KodeCore.
- `ornith:9b` — 40/40, 1.0 x5, all categories 5/5, 64.512 tok/s; accepted KodeCoder.

All final candidates had zero runtime errors, preload failures/timeouts and budget exhaustions.

## Accepted defaults

- `KodeFast` → `granite4.1:3b`
- `KodeCore` → `gpt-oss:20b`
- `KodeCoder` → `ornith:9b`

These are hardware-specific defaults, not permanent architectural dependencies. Kodepoia remains model-agnostic and may rerun this benchmark policy when better local candidates appear.

PR #8 was merged into `main` as `8e16e6a7d9f6c38d26a663ba9bdafd4950dba7c4`. R3 is closed; R4 is **AUTHORIZED / NOT STARTED**.
