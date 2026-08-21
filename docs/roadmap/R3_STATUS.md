# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** IMPLEMENTATION COMPLETE — HARDWARE-LOCAL ACCEPTANCE PENDING  
**Updated:** 2026-08-21

## Validation evidence

Original implementation:
- PR #5 — `R3: implement KodeBrain, Memory, Context and ModelRouter`.
- Merge commit: `b5e61dea1d50ccfc8ffff6f1e525f95a39b8096f`.

Acceptance hardening:
- PR #8 — `R1-R3 Acceptance Hardening`.
- Hardening is validated iteratively on Windows/Ubuntu with Repository Guard, Python Core and KodeStudio UI smoke.

## Implemented

- [x] Model-agnostic Brain protocol.
- [x] Local Ollama adapter using `/api/version`, `/api/tags`, `/api/chat` and `/api/embed`.
- [x] Non-streaming and streaming chat.
- [x] Tool-call payload/result support.
- [x] JSON-schema / structured-output support.
- [x] Thinking and keep-alive parameters.
- [x] Image payload support for multimodal messages.
- [x] Explicit model unload support.
- [x] Explicit unscored Ollama preload support before benchmark tasks.
- [x] KodeModelRegistry with FAST / CORE / CODER / EMBED / VISION roles.
- [x] Capability-aware KodeModelRouter.
- [x] Persistent SQLite KodeMemory + semantic retrieval wired into the Orchestrator.
- [x] KodeContext token budget and streaming Orchestrator path.
- [x] `kodepoia ollama-status` local diagnostic.
- [x] Role-aware repeated benchmark and JSON report.
- [x] FAST 256 tokens/no thinking; CORE/CODER 1024 tokens/capability-aware thinking.
- [x] Ollama `done_reason` retention and explicit `generation_budget_exhausted` detection.
- [x] Cold-load separation: preload is measured separately from scored task correctness.
- [x] Preload diagnostics: `avg_cold_load_s`, `avg_preload_elapsed_s`, `preload_failures`, `preload_timeouts`.
- [x] `kodepoia r3-accept` local-only acceptance requiring two or three installed candidates and full-capability thinking-aware evaluation.
- [x] Mocked Ollama API/benchmark tests.

## Local preselection evidence

### FAST — completed

Evidence: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

- `granite4.1:3b`: 28/32, score 0.875 x4, 129.512 tok/s.
- `qwen3.5:4b`: 28/32, score 0.875 x4, 80.690 tok/s.

**Provisional KodeFast winner: `granite4.1:3b`.**

### CORE — completed

CORE v2 evidence: `.kodepoia/benchmarks/r3-preselect-core-v2.json`, target workstation, five repeats, `num_predict=1024`.

`qwen3.5:9b`:
- 25/40, score 0.625 x5;
- 54.609 tok/s;
- 15 deterministic `generation_budget_exhausted` cases.

`gpt-oss:20b`:
- 40/40, score 1.0 x5;
- 15.399 tok/s;
- all eight categories 5/5;
- 0 errors, 0 budget exhaustions;
- cold-load about 90.985 s.

**Provisional KodeCore winner: `gpt-oss:20b`.**

### CODER v1 — diagnostic completed

Evidence: `.kodepoia/benchmarks/r3-preselect-coder.json`, five repeats, `num_predict=1024`.

`qwen2.5-coder:7b-instruct`:
- 30/40, 0.750 x5, 82.296 tok/s;
- core coding/Godot/GDScript/debug/JSON tasks pass 5/5;
- native tool calling 0/5;
- software-engineering worktree 0/5 (`Git Subtree`).

`devstral-small-2:24b`:
- raw 30/40;
- 3.968 tok/s;
- first repetition contains five consecutive 120 s timeouts;
- software-engineering worktree 0/5 (`sparse checkout`).

`north-mini-code-1.0:Q4_K_M`:
- raw 35/40, apparent 0.875 x5, 12.838 tok/s;
- Python/Godot/GDScript/debug/structured/native-tools/worktree all 5/5;
- raw exact-instruction 0/5 consists entirely of 120 s timeouts on the **first task after unload**, followed by successful warm tasks;
- about 10.03 GB resident VRAM observed while running.

CODER v1 therefore exposed a **cold-load scoring bias**. North is the substantive coding leader but cannot be declared final from the raw 0.875 score.

### Cold-load benchmark hardening — implementation complete, CI validation required

The benchmark now preloads each model using an unscored empty Ollama chat request before any scored task. Preload uses a dedicated 240 s timeout. Its cost remains in end-to-end timing and cold-load metrics, but does not automatically become a knowledge failure. Tests explicitly verify that preload failure and task correctness are separate dimensions.

## Next hardware step — CODER v2 after CI green

Do not rerun Devstral/Qwen2.5-Coder as default contenders. Compare the two realistic agentic finalists under the corrected cold-load policy:

```powershell
python -m kodepoia.cli bench-models --role coder --repeats 5 --model "gpt-oss:20b" --model "north-mini-code-1.0:Q4_K_M" --output ".kodepoia/benchmarks/r3-preselect-coder-v2.json"
```

Do not run official `r3-accept` until CODER v2 is reviewed.

## Remaining hardware-local acceptance

R3 remains intentionally incomplete until:
1. cold-load hardening CI is green;
2. CODER v2 is reviewed;
3. 2–3 final candidates are selected;
4. official target-PC `r3-accept` is generated and reviewed.

Prepared runner:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
```

Then, after finalist selection only:

```powershell
.\scripts\r3_accept_local.ps1 -Model modelA,modelB
# or
.\scripts\r3_accept_local.ps1 -Model modelA,modelB,modelC
```

Final evidence: `.kodepoia/benchmarks/r3-local-acceptance.json`.

## Completion rule

R3 becomes `COMPLETE` only after the target workstation's official local acceptance report is structurally valid, technically reviewed, selected roles are recorded, final CI is green, and PR #8 is safe to merge. R4 must not begin before R3 is accepted.
