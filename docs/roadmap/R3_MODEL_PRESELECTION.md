# R3 — Local Model Preselection

This preselection step runs before official `r3-accept`. It compares models by intended Kodepoia role so latency-oriented FAST candidates are not scored with the same thinking policy as CORE/CODER candidates.

## Repetition and scoring policy

Official preselection uses **4 repetitions per model**. `bench-models --repeats N` supports 1–8 repetitions for diagnostics, but R3 preselection evidence must use at least 4. Official `r3-accept` uses **5 repetitions per finalist** by default and rejects fewer than 4.

Each repetition reloads the model so Kodepoia measures both repeatability and the real cold-load cost relevant to sequential VRAM routing. Generation controls are deterministic: `temperature=0` and seed series starting at 101.

Generation budget is role-aware after the CORE diagnostic of 21 August 2026:
- BASELINE / FAST: `num_predict=256`;
- CORE / CODER: `num_predict=1024` because thinking tokens are emitted before the final answer and share the generation budget;
- official R3 acceptance uses the full-capability thinking-aware profile and the 1024-token budget.

The report schema v2 records aggregate score, repeat scores, score standard deviation, minimum repeat score, average repeat elapsed time, timing deviation, average tokens/s, tokens/s deviation, average cold-load time, per-task pass rates, errors, budget-exhaustion count and thinking mode. Ollama `done_reason` is preserved in metrics.

Scoring is strict rather than substring-only:
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

CORE inspects local Ollama `/api/show` capabilities. Thinking-capable models use thinking automatically; GPT-OSS uses `think="medium"` per Ollama requirements.

### CODER
- `qwen2.5-coder:7b-instruct`
- `devstral-small-2:24b`
- `north-mini-code-1.0:Q4_K_M`

CODER also enables supported thinking automatically. Models that do not advertise the capability are called without a `think` field.

## FAST v2 result — completed on target workstation

Evidence file: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

Both candidates produced identical correctness and perfect repeatability across four controlled runs:
- `granite4.1:3b`: 28/32, score 0.875, score 0.875 x4, score stddev 0.0;
- `qwen3.5:4b`: 28/32, score 0.875, score 0.875 x4, score stddev 0.0.

Both passed 4/4 on exact instruction, Python reasoning, Godot `CharacterBody3D`, typed GDScript, debugging, structured JSON and real tool calling. Both failed 4/4 on Git worktree: Granite answered `branching`; Qwen answered `Submodules`.

Efficiency strongly favors Granite:
- Granite: 129.512 tok/s, 22.212 s average repeat, 0.179 s timing stddev, 15.484 s average cold load;
- Qwen 4B: 80.690 tok/s, 24.068 s average repeat, 8.244 s timing stddev, 13.797 s average cold load.

**FAST preselection decision: `granite4.1:3b` is the provisional KodeFast winner.**

`qwen3.5:4b` remains a compact fallback/secondary model and keeps its multimodal value.

## CORE v1 diagnostic — completed, not final selection evidence

Evidence file: `.kodepoia/benchmarks/r3-preselect-core.json`.

The workstation ran **5 repetitions** for each candidate. The report exposed an additional harness problem: CORE still used `num_predict=256`, although thinking-capable models emit reasoning before final content.

### `qwen3.5:9b`

Raw report: 20/40, apparent score 0.50, 55.121 tok/s, 70.479 s average repeat, 33.816 s average cold load.

This **must not be interpreted as a real 50% capability score**. Every failure had the same signature: empty final response, non-empty thinking, and `eval_count=256` exactly. The harness was fixed and CORE rerun with 1024 tokens.

### `gpt-oss:20b`

Raw report: 39/40, score 0.975, 15.676 tok/s, 180.232 s average repeat, 94.285 s average cold load. Its only miss was one 120-second transport/runtime timeout, not a wrong answer.

### `qwen3.6:27b`

Raw report: 10/40, 3.131 tok/s, 673.694 s average repeat, nine 120-second timeouts. The old content score was partially budget-biased, but the hardware result independently made this 27B variant impractical as the default daily CORE on the target workstation. It was removed from CORE v2.

## CORE v2 result — completed on target workstation

Evidence file: `.kodepoia/benchmarks/r3-preselect-core-v2.json`.

The workstation again ran **5 repetitions per candidate**, now with the corrected CORE policy `num_predict=1024`, `temperature=0`, deterministic seeds, capability-aware thinking, and explicit budget-exhaustion detection.

### `qwen3.5:9b`

- 25/40, score **0.625**;
- repeat scores: 0.625 x5; score stddev 0.0;
- 54.609 tok/s average;
- 110.930 s average repeat;
- 29.020 s average cold load (strong first-load outlier; later reloads around 9–10 s);
- exact instruction 5/5;
- Godot 5/5;
- typed GDScript 5/5;
- debugging 5/5;
- tool calling 5/5;
- Python reasoning 0/5;
- structured output 0/5;
- software engineering / Git worktree 0/5;
- **15 generation-budget exhaustions out of 40 tasks**.

All 15 failures are deterministic and have the same explicit signature: `done_reason="length"`, `eval_count=1024`, non-empty thinking, empty final response, and `generation_budget_exhausted=true`. Increasing the CORE budget from 256 to 1024 therefore did not make Qwen 9B reliable under Kodepoia's bounded-latency thinking profile.

Qwen 9B remains valuable as a smaller multimodal/vision-capable model and can be evaluated later for non-thinking or vision-specific routing, but it is **not selected as the default reasoning CORE** from this evidence.

### `gpt-oss:20b`

- 40/40, score **1.000**;
- repeat scores: 1.0 x5; score stddev 0.0;
- minimum repeat score 1.0;
- 15.399 tok/s average;
- 154.905 s average repeat;
- 90.985 s average cold load;
- all eight task categories 5/5;
- 0 errors;
- 0 budget exhaustions;
- `thinking_mode="medium"`.

The model file is about 14.1 GB while Ollama reports about 10.1 GB resident in VRAM on this workstation during the run. Cold-load is therefore the main operational weakness. Once loaded, however, the useful-task latency is competitive because the model does not spend the full 1024-token budget on failed reasoning loops.

**CORE preselection decision: `gpt-oss:20b` is the provisional KodeCore winner.**

Rationale: perfect and perfectly repeatable correctness across all Kodepoia CORE categories, reliable structured output and tool calling, no budget exhaustion, and practical warm-task behavior. KodeVRAM / keep-alive policy should mitigate the approximately 91-second cold-load cost by avoiding unnecessary unload/reload churn during active CORE work.

`qwen3.5:9b` is retained in the registry as a smaller multimodal candidate/fallback, not deleted.

## CODER preselection — next hardware step

Current candidates remain justified for complementary reasons:
- `qwen2.5-coder:7b-instruct`: compact 7.6B / Q4_K_M coding specialist, expected to fit comfortably in 12 GB VRAM;
- `devstral-small-2:24b`: dedicated agentic software-engineering model with tool/codebase focus, but its ~15 GB Q4_K_M footprint means hardware latency/offload must be measured;
- `north-mini-code-1.0:Q4_K_M`: 30B-total / 3B-active MoE coding model aimed at code generation, agentic software engineering and terminal tasks; local efficiency must be measured rather than inferred from total parameter count.

Run:

```powershell
python -m kodepoia.cli bench-models `
  --role coder `
  --repeats 4 `
  --model "qwen2.5-coder:7b-instruct" `
  --model "devstral-small-2:24b" `
  --model "north-mini-code-1.0:Q4_K_M" `
  --output ".kodepoia/benchmarks/r3-preselect-coder.json"
```

The CLI selects `num_predict=1024` automatically for CODER. Do not pass a manual generation budget.

Do **not** run official `r3-accept` until the CODER report has been reviewed and the final 2–3 model set has been chosen.

## Selection rule

Do not select winners from aggregate pass count alone.

FAST: prioritize repeatable correctness, structured/tool reliability, minimum repeat score, then tokens/s, cold-load time and memory cost.

CORE: prioritize valid repeatable correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost. A result caused by output-budget exhaustion is a runtime-fit diagnostic, not proof that the model is intrinsically incapable.

CODER: prioritize repeatable software-engineering/Godot/GDScript/debugging/tool reliability. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After CODER is reviewed, select up to three finalists and run official `r3-accept` with the default 5 repetitions. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.
