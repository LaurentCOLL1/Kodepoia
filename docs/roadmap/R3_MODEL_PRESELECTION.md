# R3 — Local Model Preselection

This preselection step runs before official `r3-accept`. It compares models by intended Kodepoia role so latency-oriented FAST candidates are not scored with the same thinking policy as CORE/CODER candidates.

## Repetition and scoring policy

Official preselection uses **4 repetitions per model**. `bench-models --repeats N` supports 1–8 repetitions for diagnostics, but the R3 preselection evidence must use at least 4. Official `r3-accept` uses **5 repetitions per finalist** by default and rejects fewer than 4.

Each repetition reloads the model so Kodepoia measures both repeatability and the real cold-load cost relevant to sequential VRAM routing. Generation controls are fixed by the harness for fair comparison: `temperature=0`, deterministic seed series starting at 101, and `num_predict=256`.

The report schema v2 records aggregate score, repeat scores, score standard deviation, minimum repeat score, average repeat elapsed time, timing deviation, average tokens/s, tokens/s deviation, average cold-load time, per-task pass rates, errors, and thinking mode.

Scoring is strict rather than substring-only:
- exact-instruction requires exactly `KODEPOIA_OK`;
- Godot requires `CharacterBody3D` and rejects legacy/wrong `KinematicBody3D` / `KinematicCharacter3D` answers;
- typed GDScript requires `var count: int = 0` syntax;
- Git worktree requires a real `worktree` answer;
- structured JSON and tool calls continue to use structural validation.

The four manual FAST runs performed before this hardening were useful diagnostics but are **not final selection evidence** because they revealed score instability and false-positive validators. Their observed summaries were:
- Granite: scores 0.75 / 0.875 / 0.875 / 0.75; average 0.8125; ~122.4 tokens/s average.
- Qwen 3.5 4B: scores 0.75 / 0.75 / 0.875 / 0.75; average 0.78125; ~72.4 tokens/s average.

Those runs showed Granite consistently faster, but the stricter repeated harness must be rerun before selecting FAST.

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

## Prerequisites

From the repository root on the target workstation:

```powershell
git switch agent/r1-r3-acceptance-hardening
git pull
.\.venv\Scripts\Activate.ps1
python --version
ollama --version
ollama list
```

Python must be 3.12+. Ollama must be local.

## Run FAST preselection

```powershell
python -m kodepoia.cli bench-models `
  --role fast `
  --repeats 4 `
  --model "granite4.1:3b" `
  --model "qwen3.5:4b" `
  --output ".kodepoia/benchmarks/r3-preselect-fast.json"
```

## Run CORE preselection

```powershell
python -m kodepoia.cli bench-models `
  --role core `
  --repeats 4 `
  --model "qwen3.5:9b" `
  --model "gpt-oss:20b" `
  --model "qwen3.6:27b" `
  --output ".kodepoia/benchmarks/r3-preselect-core.json"
```

## Run CODER preselection

```powershell
python -m kodepoia.cli bench-models `
  --role coder `
  --repeats 4 `
  --model "qwen2.5-coder:7b-instruct" `
  --model "devstral-small-2:24b" `
  --model "north-mini-code-1.0:Q4_K_M" `
  --output ".kodepoia/benchmarks/r3-preselect-coder.json"
```

## Outputs

- `.kodepoia/benchmarks/r3-preselect-fast.json`
- `.kodepoia/benchmarks/r3-preselect-core.json`
- `.kodepoia/benchmarks/r3-preselect-coder.json`

## Selection rule

Do not select winners from aggregate pass count alone.

FAST: prioritize repeatable correctness, structured/tool reliability, minimum repeat score, then tokens/s, cold-load time and memory cost.

CORE: prioritize repeatable correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost.

CODER: prioritize repeatable software-engineering/Godot/GDScript/debugging/tool reliability. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After the three reports are reviewed, select up to three finalists and run official `r3-accept` with the default 5 repetitions. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.
