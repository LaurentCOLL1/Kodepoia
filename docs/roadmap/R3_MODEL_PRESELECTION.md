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
- structured JSON and tool calls use structural validation.

The four manual FAST runs performed before this hardening were diagnostic only and are not final selection evidence.

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

Both candidates produced identical correctness and perfect repeatability across the four controlled runs:
- `granite4.1:3b`: 28/32, score 0.875, repeat scores 0.875 / 0.875 / 0.875 / 0.875, score stddev 0.0;
- `qwen3.5:4b`: 28/32, score 0.875, repeat scores 0.875 / 0.875 / 0.875 / 0.875, score stddev 0.0.

Both passed 4/4 on exact instruction, Python reasoning, Godot `CharacterBody3D`, typed GDScript, debugging, structured JSON and real tool calling. Both failed 4/4 on the Git worktree question: Granite answered `branching`; Qwen answered `Submodules`.

Efficiency strongly favors Granite on this machine:
- Granite: 129.512 tok/s average, 4.055 stddev; 22.212 s average repeat time, 0.179 s stddev; 15.484 s average cold load.
- Qwen 4B: 80.690 tok/s average, 7.493 stddev; 24.068 s average repeat time, 8.244 s stddev; 13.797 s average cold load.

Qwen's average cold-load number is influenced by a very slow first repeat (~28.3 s load) followed by roughly 8.5–9.9 s loads, while Granite stayed around 15.35–15.86 s on all four repeats. Granite therefore has much more predictable end-to-end timing and about 60% higher generation throughput.

**FAST preselection decision: `granite4.1:3b` is the provisional KodeFast winner.**

Rationale: identical correctness, identical repeatability, same structured/tool reliability, materially higher throughput and much lower run-time variance. The Git/worktree miss remains a routing constraint: repository-mechanics questions should go to CORE/CODER rather than be trusted to FAST.

`qwen3.5:4b` remains a useful fallback/secondary compact model and is not removed from the registry. It also has multimodal capability in Ollama, whereas Granite 4.1 3B is text-only; vision routing will be evaluated separately and does not overturn the text FAST decision.

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

## FAST preselection command — already completed

```powershell
python -m kodepoia.cli bench-models `
  --role fast `
  --repeats 4 `
  --model "granite4.1:3b" `
  --model "qwen3.5:4b" `
  --output ".kodepoia/benchmarks/r3-preselect-fast-v2.json"
```

## Next step — CORE preselection

```powershell
python -m kodepoia.cli bench-models `
  --role core `
  --repeats 4 `
  --model "qwen3.5:9b" `
  --model "gpt-oss:20b" `
  --model "qwen3.6:27b" `
  --output ".kodepoia/benchmarks/r3-preselect-core.json"
```

## CODER preselection — do not run until CORE report is reviewed

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

CORE: prioritize repeatable correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost.

CODER: prioritize repeatable software-engineering/Godot/GDScript/debugging/tool reliability. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After the three reports are reviewed, select up to three finalists and run official `r3-accept` with the default 5 repetitions. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.
