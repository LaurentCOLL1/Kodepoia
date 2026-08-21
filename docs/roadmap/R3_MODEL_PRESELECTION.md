# R3 — Local Model Preselection

This preselection step runs before official `r3-accept`. It compares models by intended Kodepoia role so latency-oriented FAST candidates are not scored with the same thinking policy as CORE/CODER candidates.

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

CODER also enables supported thinking automatically. North Mini Code is expected to benefit from thinking; models that do not advertise the capability are called without a `think` field.

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
  --model "granite4.1:3b" `
  --model "qwen3.5:4b" `
  --output ".kodepoia/benchmarks/r3-preselect-fast.json"
```

## Run CORE preselection

```powershell
python -m kodepoia.cli bench-models `
  --role core `
  --model "qwen3.5:9b" `
  --model "gpt-oss:20b" `
  --model "qwen3.6:27b" `
  --output ".kodepoia/benchmarks/r3-preselect-core.json"
```

## Run CODER preselection

```powershell
python -m kodepoia.cli bench-models `
  --role coder `
  --model "qwen2.5-coder:7b-instruct" `
  --model "devstral-small-2:24b" `
  --model "north-mini-code-1.0:Q4_K_M" `
  --output ".kodepoia/benchmarks/r3-preselect-coder.json"
```

## Outputs

- `.kodepoia/benchmarks/r3-preselect-fast.json`
- `.kodepoia/benchmarks/r3-preselect-core.json`
- `.kodepoia/benchmarks/r3-preselect-coder.json`

Each report records pass score, elapsed time, average tokens/s when Ollama provides metrics, thinking mode, runtime model information and task-level results.

## Selection rule

Do not select winners from pass count alone.

FAST: prioritize first-pass correctness, structured/tool reliability and tokens/s/latency.

CORE: prioritize correctness, reasoning/general engineering quality, tool/structured reliability, then latency and memory cost.

CODER: prioritize software-engineering/Godot/GDScript/debugging/tool reliability. Slower models may win if materially more capable, but models that are impractical on the target workstation should not become the default daily coder.

After the three reports are reviewed, select up to three finalists and run official `r3-accept`. R3 remains `PENDING ACCEPTANCE` until the official hardware-local report is reviewed.