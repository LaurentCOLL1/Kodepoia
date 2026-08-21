# R3 — Local Model Preselection

This preselection step runs before official `r3-accept`. It compares models by intended Kodepoia role so latency-oriented FAST candidates are not scored with the same thinking policy as CORE/CODER candidates.

## Repetition and scoring policy

Official preselection uses at least **4 repetitions per model**. `bench-models --repeats N` supports 1–8 repetitions for diagnostics. Official `r3-accept` uses **5 repetitions per finalist** by default and rejects fewer than 4.

Generation controls are deterministic: `temperature=0` and seed series starting at 101.

Generation budget is role-aware:
- BASELINE / FAST: `num_predict=256`;
- CORE / CODER: `num_predict=1024` because thinking tokens are emitted before final content and share the generation budget;
- official R3 acceptance uses the full-capability thinking-aware profile and the 1024-token budget.

### Cold-load separation hardening

The CODER v1 run exposed a second measurement bias: the benchmark unloaded a model after each repetition, then used the **first scored task itself** to reload it. On heavy models, a >120 s cold-load therefore became a false task failure even when every subsequent warm task passed.

This is now corrected before final acceptance:
- each repetition begins with an **unscored Ollama preload request**;
- the preload has a dedicated 240 s timeout;
- only after preload does Kodepoia execute scored tasks;
- model load remains part of the end-to-end performance measurement;
- report summary separately records `avg_cold_load_s`, `avg_preload_elapsed_s`, `preload_failures` and `preload_timeouts`;
- a preload problem is therefore a **hardware/practicality signal**, not automatically a knowledge/capability failure.

Ollama documents empty `/api/chat` or `/api/generate` requests as the supported way to preload a model, and `keep_alive` as the mechanism for retaining/unloading it.

The report schema v2 also records aggregate score, repeat scores, score standard deviation, minimum repeat score, average repeat elapsed time, timing deviation, average tokens/s, tokens/s deviation, per-task pass rates, errors, budget-exhaustion count and thinking mode. Ollama `done_reason` is preserved in metrics.

Scoring is strict:
- exact-instruction requires exactly `KODEPOIA_OK`;
- Godot requires `CharacterBody3D` and rejects legacy/wrong `KinematicBody3D` / `KinematicCharacter3D` answers;
- typed GDScript requires `var count: int = 0` syntax;
- Git worktree requires a real `worktree` answer;
- structured JSON and tool calls use structural validation.

## Candidate set — 21 August 2026

### FAST
- `granite4.1:3b`
- `qwen3.5:4b`

FAST forces `think=false` to measure low-latency everyday behavior.

### CORE
- `qwen3.5:9b`
- `gpt-oss:20b`
- `qwen3.6:27b`

CORE inspects local Ollama `/api/show` capabilities. Thinking-capable models use thinking automatically; GPT-OSS uses `think="medium"`.

### CODER v1
- `qwen2.5-coder:7b-instruct`
- `devstral-small-2:24b`
- `north-mini-code-1.0:Q4_K_M`

CODER enables supported thinking automatically. Models that do not advertise the capability are called without a `think` field.

## FAST v2 result — completed on target workstation

Evidence file: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

Both candidates produced identical correctness and perfect repeatability across four controlled runs:
- `granite4.1:3b`: 28/32, score 0.875 x4, score stddev 0.0;
- `qwen3.5:4b`: 28/32, score 0.875 x4, score stddev 0.0.

Both passed 4/4 on exact instruction, Python reasoning, Godot `CharacterBody3D`, typed GDScript, debugging, structured JSON and real tool calling. Both failed 4/4 on Git worktree.

Efficiency strongly favors Granite:
- Granite: 129.512 tok/s, 22.212 s average repeat, 0.179 s timing stddev, 15.484 s average cold load;
- Qwen 4B: 80.690 tok/s, 24.068 s average repeat, 8.244 s timing stddev, 13.797 s average cold load.

**FAST preselection decision: `granite4.1:3b` is the provisional KodeFast winner.**

`qwen3.5:4b` remains a compact fallback/secondary model and keeps its multimodal value.

## CORE v1 diagnostic — completed

Evidence file: `.kodepoia/benchmarks/r3-preselect-core.json`.

The target workstation ran five repetitions with the old `num_predict=256`. The report exposed thinking-budget exhaustion for Qwen 9B and triggered the 1024-token hardening plus `done_reason` / `generation_budget_exhausted` instrumentation.

`qwen3.6:27b` was independently impractical as a daily CORE on this hardware at about 3.131 tok/s, 673.694 s average repeat and nine 120-second timeouts.

## CORE v2 result — completed on target workstation

Evidence file: `.kodepoia/benchmarks/r3-preselect-core-v2.json`.

The workstation ran five repetitions per candidate with `num_predict=1024`, `temperature=0`, deterministic seeds and capability-aware thinking.

### `qwen3.5:9b`
- 25/40, score **0.625** x5, score stddev 0.0;
- 54.609 tok/s;
- exact instruction, Godot, typed GDScript, debugging and tool calling: 5/5 each;
- Python reasoning, structured output and software engineering: 0/5 each;
- 15 deterministic `generation_budget_exhausted` cases with `done_reason="length"`, `eval_count=1024`, thinking non-empty and final content empty.

The model remains useful as a smaller multimodal/vision or non-thinking fallback candidate, but not as the default reasoning CORE under the bounded-latency policy.

### `gpt-oss:20b`
- 40/40, score **1.000** x5, score stddev 0.0;
- 15.399 tok/s;
- all eight categories 5/5;
- 0 errors and 0 budget exhaustions;
- cold-load about 90.985 s;
- thinking `medium`.

**CORE preselection decision: `gpt-oss:20b` is the provisional KodeCore winner.**

KodeVRAM / keep-alive policy should avoid unnecessary unload/reload churn during active CORE work.

## CODER v1 result — diagnostic completed on target workstation

Evidence file: `.kodepoia/benchmarks/r3-preselect-coder.json`.

The workstation ran **5 repetitions** for all three candidates with `benchmark_role=coder`, `temperature=0` and `num_predict=1024`.

### `qwen2.5-coder:7b-instruct`
- 30/40, score 0.750 x5, score stddev 0.0;
- 82.296 tok/s;
- 49.528 s average repeat in the v1 harness;
- exact/Python/Godot/GDScript/debugging/structured-output: 5/5 each;
- **tool calling: 0/5** — it prints a JSON-shaped tool request in normal content instead of returning a real Ollama `tool_calls` object;
- **software engineering: 0/5** — it answers `Git Subtree` instead of `git worktree`;
- no transport errors and no budget exhaustion.

Interpretation: excellent compact/warm code helper, but not reliable enough as Kodepoia's default **agentic** coder because native tool calling and repository workflow knowledge are essential.

### `devstral-small-2:24b`
- raw 30/40, apparent score 0.750;
- repeat scores 0.25 / 0.875 / 0.875 / 0.875 / 0.875;
- 3.968 tok/s;
- 291.038 s average repeat;
- raw average cold load 96.426 s;
- true tool calling and structured output work;
- **software engineering / worktree: 0/5**, repeatedly answering sparse checkout;
- first repetition suffers five consecutive 120 s timeouts before later tasks begin succeeding.

Interpretation: its dedicated software-engineering positioning is not enough to overcome ~4 tok/s, unstable initial loading and 0/5 on the repository-workflow test on this target PC. It is removed from the default KodeCoder contest.

### `north-mini-code-1.0:Q4_K_M`
- raw 35/40, apparent score 0.875 x5, score stddev 0.0;
- 12.838 tok/s;
- about 10.03 GB reported resident in VRAM while running;
- Python/Godot/GDScript/debugging/structured-output/**real tool calling**/**software engineering worktree**: **5/5 each**;
- raw exact-instruction: 0/5, but **all five are 120 s transport timeouts on the first task immediately after unload**, not wrong responses;
- after each timeout, the following seven tasks run successfully with the model already loaded.

This is the strongest substantive CODER evidence in v1, but the old harness contaminated its capability score with cold-load latency. North therefore becomes the **provisional deep/agentic coding leader**, not yet the final KodeCoder winner.

North Mini Code's upstream Ollama description is consistent with the measured behavior: it is a 30B-total / 3B-active MoE built for agentic software engineering, native tool use and interleaved thinking, and is intended to run with thinking enabled.

## CODER v2 — required after cold-load hardening

Do not rerun all three models. Devstral and Qwen2.5-Coder already supplied enough evidence to rule them out as the default agentic coder for different reasons.

The final CODER head-to-head is:
- `gpt-oss:20b` — already perfect on CORE including tool calling + worktree, and a strong warm fallback candidate;
- `north-mini-code-1.0:Q4_K_M` — best substantive CODER v1 result, specialized for agentic coding, but with a very expensive cold load.

After the cold-load-preload hardening CI is green, run:

```powershell
python -m kodepoia.cli bench-models `
  --role coder `
  --repeats 5 `
  --model "gpt-oss:20b" `
  --model "north-mini-code-1.0:Q4_K_M" `
  --output ".kodepoia/benchmarks/r3-preselect-coder-v2.json"
```

The report must show preload metrics separately from scored task correctness. No official `r3-accept` before CODER v2 is reviewed.

## Selection rule

Do not select winners from aggregate pass count alone.

FAST: prioritize repeatable correctness, structured/tool reliability, minimum repeat score, then tokens/s, cold-load time and memory cost.

CORE: prioritize valid repeatable correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost. A result caused by output-budget exhaustion is a runtime-fit diagnostic, not proof that the model is intrinsically incapable.

CODER: prioritize repeatable software-engineering/Godot/GDScript/debugging/native-tool reliability. Cold-load is a separate practicality constraint and must not masquerade as a wrong answer. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After CODER v2 is reviewed, select up to three finalists and run official `r3-accept` with the default five repetitions. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.
