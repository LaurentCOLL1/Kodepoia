# R3 — Local hardware acceptance

R3 cannot be marked `COMPLETE` from GitHub Actions alone because model quality, throughput and VRAM usage depend on the target workstation and locally installed Ollama models.

## Preconditions

- Windows target workstation.
- Python 3.12+ available as `python`.
- Ollama running locally on loopback only (`127.0.0.1`, `localhost` or `::1`).
- Kodepoia checked out on `agent/r1-r3-acceptance-hardening` or a later branch containing the same acceptance code.
- FAST/CORE/CODER preselection reviewed.
- Cold-load separation hardening validated by CI.

## Finalists selected from local preselection

Measured role candidates on the target workstation:

- KodeFast: `granite4.1:3b`
- KodeCore: `gpt-oss:20b`
- KodeCoder: `ornith:9b`

`north-mini-code-1.0:Q4_K_M` remains a future optional `KodeDeepCoder` candidate but is not needed for R3 final acceptance because Ornith tied its 40/40 correctness while being much faster and lighter on the target hardware.

## 1. Inspect the local environment

From the repository root:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
```

The script verifies Python, calls Kodepoia `ollama-status`, and prints locally installed/running Ollama models.

## 2. Run the official R3 hardware-local acceptance

Use exactly the three selected role finalists unless new evidence is produced:

```powershell
.\scripts\r3_accept_local.ps1 -Model "granite4.1:3b","gpt-oss:20b","ornith:9b"
```

The wrapper invokes `python -m kodepoia.cli r3-accept` and writes:

```text
.kodepoia/benchmarks/r3-local-acceptance.json
```

Default final acceptance uses five repetitions per finalist, full-capability thinking-aware evaluation and `num_predict=1024`. GPT-OSS uses its supported reasoning level.

Each repetition performs an **unscored preload before scored tasks**. Preload uses a dedicated longer timeout. Its cost remains hardware-fit evidence but does not turn slow loading into a false task failure. The report separates correctness from `avg_cold_load_s`, `avg_preload_elapsed_s`, `preload_failures` and `preload_timeouts`.

## 3. Structural evidence automatically checked

The PowerShell wrapper refuses to report success unless the JSON contains:

- `metadata.phase == "R3-local-acceptance"`;
- `metadata.acceptance_completed == true`;
- `metadata.loopback_verified == true`;
- `candidate_count == 3`;
- all three requested candidates in the benchmark summary.

## 4. Engineering review still required

Before changing R3 to `COMPLETE`, review at minimum:

- pass/total and repeatability for all three finalists;
- minimum repeat score;
- structured-output success;
- real tool-call success;
- Godot/GDScript correctness;
- software-engineering/debugging correctness;
- tokens/s;
- scored task time;
- separate preload/cold-load behavior;
- VRAM/model metadata;
- `done_reason`;
- generation-budget exhaustion;
- task errors/timeouts;
- `preload_failures` / `preload_timeouts`.

The purpose is not merely to produce a JSON file. The report must prove that the selected routing candidates are usable on the real target workstation.

## 5. Completion rule

R3 may be marked `COMPLETE` only when all of the following are true:

1. R1/R2 hardening CI is green.
2. FAST/CORE/CODER preselection is reviewed and the three finalists above are recorded.
3. `.kodepoia/benchmarks/r3-local-acceptance.json` exists and passes structural validation.
4. The final benchmark results are reviewed for correctness, repeatability and practical hardware fit.
5. The selected roles are recorded as accepted in status/continuity documentation.
6. Final CI is green.
7. PR #8 is safe to merge.

Do not merge PR #8 and do not begin R4 before these conditions are satisfied.
