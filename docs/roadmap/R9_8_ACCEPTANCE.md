# R9.8 Acceptance — VRAM telemetry, admission scheduler + Ollama coexistence

Status: **PENDING REQUIRED LOCAL GPU EVIDENCE**.

Authority: `docs/roadmap/R9_PLAN.md` R9.8. This document does not authorize R9.9 while the required local state is unresolved.

## Hosted acceptance

The exact R9.8 implementation candidate must pass, on the same commit:

- R0 Repository Guard — Ubuntu + Windows;
- full Python Core — all jobs, including Ubuntu/Windows tests and package builds;
- KodeStudio UI Smoke;
- deterministic R9.8 tests for telemetry, admission, total/reserve/headroom policy, cleanup/re-measure, explicit Ollama coexistence, OOM estimate monotonicity, Health/Budget bridge, audit and evidence tamper rejection.

The exact candidate SHA and CI run IDs are filled only after the implementation head is green.

## REQUIRED local acceptance

Reason: hosted runners cannot authoritatively prove real local GPU VRAM allocation/release or the user's installed ComfyUI backend behavior.

Prerequisites:

- checkout the exact candidate SHA that will be supplied after hosted CI passes;
- clean repository worktree/index;
- current project Python environment installed;
- an already-installed local ComfyUI reachable only on loopback;
- one already-installed compatible image model represented by an explicit R9.4 workflow definition in the workspace;
- enough free disk for one bounded generated output and local evidence;
- no secrets in workflow parameters or evidence.

Do **not** install/update GPU drivers, ComfyUI, custom nodes, models, runtimes, or Ollama models merely to satisfy this gate.

Command shape:

```powershell
python -m kodepoia.cli r9-local-vram-acceptance `
  --candidate-head <EXACT_R9_8_SHA> `
  --endpoint http://127.0.0.1:8188 `
  --workflow-root <WORKSPACE_RELATIVE_R9_4_CATALOG_DIR> `
  --workflow-file <EXPLICIT_WORKFLOW_JSON_BASENAME> `
  --estimate-mib <BOUNDED_ESTIMATE> `
  --output .kodepoia/evidence/r9-8-local-vram.json
```

Add only the flags actually required by that declared workflow:

- `--model REQUIREMENT=TOKEN` for explicit ambiguous model requirements;
- `--param NAME=JSON` for every declared scalar parameter;
- `--input NAME=JSON` for every declared scalar input;
- `--reserve-mib`, `--headroom-mib`, `--total-limit-mib`, `--device-index` for explicit policy choices;
- `--allow-ollama-unload MODEL` only for an already-running model the user explicitly authorizes Kodepoia to unload;
- `--restore-ollama` only when restoration of those exact unloaded models is desired.

Expected result:

- exit code 0;
- `R9_8_local_vram_acceptance = PASS`;
- candidate head exactly matches the checked-out Git HEAD;
- CURRENT ComfyUI capability evidence and real device/backend telemetry;
- final scheduler decision `admit`;
- one R9.5 bounded run reaches `succeeded`;
- output SHA-256 and exact positive byte length exist;
- start/minimum/end VRAM observation exists;
- terminal `/free` request is followed by a new `/system_stats` measurement;
- resource and lifecycle audit chains validate;
- Ollama state is explicit `tested`, `n/a`, or `unavailable` with reason.

If Ollama has no model already loaded, `n/a` is valid and no model is to be loaded/downloaded for the gate. If Ollama is unavailable, the evidence must say so; this does not create fabricated coexistence proof.

## Failure handling

On any non-zero exit, REJECT/DEFER/UNKNOWN final decision, failed generation, missing output, audit failure, head mismatch, dirty worktree, unavailable required model/workflow, or malformed evidence:

1. stop R9.8 acceptance;
2. preserve the JSON/evidence/logs that were produced;
3. do not weaken reserve/headroom, invent a model selection, install random components, expose ComfyUI remotely, or change drivers/runtimes as a workaround;
4. return the error plus any produced evidence for diagnosis.

## Evidence to return

Return:

- `.kodepoia/evidence/r9-8-local-vram.json`;
- the redacted console output from the acceptance command;
- if requested during review, `.kodepoia/evidence/r9-8/resource-audit.jsonl` and the run's lifecycle audit file.

Private absolute paths, usernames and secrets must be redacted from console material. The canonical JSON is designed to carry workspace-relative paths only.

## Gate state

Manual R9.8: **REQUIRED / NOT YET SATISFIED**.

R9.9 MUST NOT START until this document is updated with accepted exact-head hosted CI plus reviewed local GPU evidence, then the final documentation/continuity head passes all three hosted gates and R9.8 is merged + normalized according to the permanent phase rule.
