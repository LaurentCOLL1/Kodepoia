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

This **must not be interpreted as a real 50% capability score**. Every failure in Python reasoning, Godot, structured output and software engineering has the same signature:
- empty final `response`;
- non-empty `thinking`;
- `eval_count=256` exactly;
- no Ollama transport error.

That is generation-budget exhaustion before final content. Qwen 9B therefore requires a fair rerun with the new 1024-token CORE budget.

### `gpt-oss:20b`

Raw report: 39/40, score 0.975, repeat scores 1.0 / 1.0 / 0.875 / 1.0 / 1.0, 15.676 tok/s, 180.232 s average repeat, 94.285 s average cold load.

It passed Python, Godot, typed GDScript, debugging, structured output, tool calling and Git worktree 5/5. Its only failure was an HTTP/Ollama timeout on the exact-instruction task in repeat 3, not a wrong answer.

**Provisional CORE leader: `gpt-oss:20b`.** It has the strongest valid correctness evidence so far, but its latency/cold-load cost is much higher than Qwen 9B, so the fair CORE v2 rerun remains necessary before choosing the default.

### `qwen3.6:27b`

Raw report: 10/40, score 0.25, 3.131 tok/s, 673.694 s average repeat, nine 120-second timeouts.

Its content score is also partially contaminated by the old 256-token thinking budget, but the hardware result is independently decisive: ~3 tok/s and repeated 120-second timeouts make this model impractical as the **default daily CORE** on the target workstation. It is therefore removed from the CORE v2 rerun. This does not claim the model is intrinsically weak; Ollama positions Qwen3.6 for agentic coding and thinking, but this local hardware cannot run the 27B variant at acceptable daily latency.

## CORE v2 — next hardware step

After pulling the latest branch, rerun only the two viable CORE candidates with the corrected 1024-token budget:

```powershell
python -m kodepoia.cli bench-models `
  --role core `
  --repeats 4 `
  --model "qwen3.5:9b" `
  --model "gpt-oss:20b" `
  --output ".kodepoia/benchmarks/r3-preselect-core-v2.json"
```

The CLI now selects `num_predict=1024` automatically for CORE. Do not pass a manual generation budget.

Do **not** run CODER until CORE v2 is reviewed.

## CODER preselection — pending CORE v2 review

```powershell
python -m kodepoia.cli bench-models `
  --role coder `
  --repeats 4 `
  --model "qwen2.5-coder:7b-instruct" `
  --model "devstral-small-2:24b" `
  --model "north-mini-code-1.0:Q4_K_M" `
  --output ".kodepoia/benchmarks/r3-preselect-coder.json"
```

## Selection rule

Do not select winners from aggregate pass count alone.

FAST: prioritize repeatable correctness, structured/tool reliability, minimum repeat score, then tokens/s, cold-load time and memory cost.

CORE: prioritize valid repeatable correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost. A result caused by output-budget exhaustion is a harness diagnostic, not evidence of model incapability.

CODER: prioritize repeatable software-engineering/Godot/GDScript/debugging/tool reliability. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After the three groups are reviewed, select up to three finalists and run official `r3-accept` with the default 5 repetitions. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.
