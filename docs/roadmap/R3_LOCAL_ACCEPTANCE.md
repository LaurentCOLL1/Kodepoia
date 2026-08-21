# R3 — Local hardware acceptance

R3 cannot be marked `COMPLETE` from GitHub Actions alone because model quality, throughput and VRAM usage depend on the target workstation and the locally installed Ollama models.

## Preconditions

- Windows target workstation.
- Python 3.12+ available as `python`.
- Ollama running locally.
- Kodepoia repository checked out on the R1–R3 hardening branch or on a later branch containing the same acceptance code.
- Two or three distinct candidate Ollama models already installed locally.
- Ollama endpoint must be loopback only: `127.0.0.1`, `localhost` or `::1`.

## 1. Inspect the local environment

From the repository root:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
```

The script verifies Python, calls Kodepoia `ollama-status`, and prints the models exposed by the local Ollama daemon.

Equivalent direct command:

```powershell
$env:PYTHONPATH = "$PWD\src"
python -m kodepoia.cli ollama-status --url http://127.0.0.1:11434
```

## 2. Choose two or three candidates

Use models that represent the roles Kodepoia may route to (for example a fast/general model and a stronger coding/core model). The acceptance command itself does not hard-code concrete model names because the architecture is model-agnostic and the installed candidates may evolve.

The models must be distinct and already installed.

## 3. Run hardware-local acceptance

Two models:

```powershell
.\scripts\r3_accept_local.ps1 -Model modelA,modelB
```

Three models:

```powershell
.\scripts\r3_accept_local.ps1 -Model modelA,modelB,modelC
```

The wrapper invokes:

```powershell
python -m kodepoia.cli r3-accept --model <model1> --model <model2> [--model <model3>]
```

and writes:

```text
.kodepoia/benchmarks/r3-local-acceptance.json
```

## 4. Structural evidence automatically checked

The PowerShell wrapper refuses to report success unless the JSON contains:

- `metadata.phase == "R3-local-acceptance"`;
- `metadata.acceptance_completed == true`;
- `metadata.loopback_verified == true`;
- the expected `candidate_count`;
- a benchmark summary entry for every requested candidate.

## 5. Human/engineering review still required

Before changing R3 to `COMPLETE`, inspect the report and compare at minimum:

- total tasks passed / total tasks;
- structured-output success;
- tool-call success;
- Godot/GDScript correctness;
- software-engineering/debugging correctness;
- elapsed time;
- average tokens/s when Ollama exposes the metric;
- `size_vram`, parameter size and quantization when Ollama exposes them;
- errors or model-load failures.

The purpose is not merely to produce a JSON file. The report must show that at least two real local candidates were actually compared on the target workstation and that the chosen routing candidates are usable within the machine's performance constraints.

## 6. Completion rule

R3 may be marked `COMPLETE` only when all of the following are true:

1. R1/R2 hardening CI is green.
2. The local acceptance report exists and passes structural validation.
3. The benchmark results have been reviewed.
4. The selected model roles/candidates are recorded in the project continuity/status documentation.
5. The PR containing R1–R3 hardening is safe to merge.

R4 must not begin before these conditions are satisfied.
