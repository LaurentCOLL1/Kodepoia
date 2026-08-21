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
- CI hardening has been validated on Windows and Ubuntu during PR #8.
- KodeStudio UI smoke is validated on Windows.
- Repository Guard is validated on Windows and Ubuntu.

## Implemented

- [x] Model-agnostic Brain protocol.
- [x] Local Ollama adapter using `/api/version`, `/api/tags`, `/api/chat` and `/api/embed`.
- [x] Non-streaming chat.
- [x] Streaming `stream_chat`.
- [x] Tool-call payload/result support.
- [x] JSON-schema / structured-output support.
- [x] Thinking and keep-alive parameters.
- [x] Image payload support for multimodal messages.
- [x] Explicit model unload support.
- [x] KodeModelRegistry with FAST / CORE / CODER / EMBED / VISION roles.
- [x] Capability-aware KodeModelRouter driven by task profile and VRAM fit.
- [x] Persistent SQLite KodeMemory with WAL, scopes, importance, metadata and governance flags.
- [x] Embedding persistence and cosine semantic retrieval.
- [x] Semantic retrieval wired into the Orchestrator: query embedding → semantic search → ContextBuilder.
- [x] KodeContext token budget, mandatory-context handling and relevance priority.
- [x] Streaming Orchestrator path.
- [x] `kodepoia ollama-status` local diagnostic.
- [x] Expanded `kodepoia bench-models` benchmark and JSON output.
- [x] Role-aware benchmark policy: FAST 256 tokens/no thinking; CORE/CODER 1024 tokens/capability-aware thinking.
- [x] Ollama `done_reason` retention and explicit `generation_budget_exhausted` detection.
- [x] `kodepoia r3-accept` local-only acceptance command requiring two or three distinct installed candidates and full-capability thinking-aware evaluation.
- [x] Mocked Ollama API tests so CI validates protocols without requiring downloaded models.
- [x] R3 hardening CI on Windows and Ubuntu.

## Local preselection evidence

### FAST — completed

Evidence: `.kodepoia/benchmarks/r3-preselect-fast-v2.json`.

- `granite4.1:3b`: 28/32, score 0.875 x4, 129.512 tok/s.
- `qwen3.5:4b`: 28/32, score 0.875 x4, 80.690 tok/s.

**Provisional KodeFast winner: `granite4.1:3b`.**

### CORE — completed

CORE v1 evidence: `.kodepoia/benchmarks/r3-preselect-core.json` exposed a too-small 256-token thinking budget and triggered benchmark hardening.

CORE v2 evidence: `.kodepoia/benchmarks/r3-preselect-core-v2.json`, run on the target workstation with Windows 11, Python 3.12.4, Ollama 0.32.14, 5 repeats and `num_predict=1024`.

`qwen3.5:9b`:
- 25/40, score 0.625 x5;
- 54.609 tok/s;
- 15/40 tasks ended in explicit `generation_budget_exhausted` with `done_reason="length"` and `eval_count=1024`;
- passes exact/Godot/GDScript/debug/tools 5/5, but Python reasoning/structured output/software engineering 0/5 under the current bounded-thinking policy.

`gpt-oss:20b`:
- 40/40, score 1.0 x5;
- 15.399 tok/s;
- all eight categories 5/5;
- 0 errors and 0 budget exhaustions;
- cold-load approximately 90.985 s, which must be mitigated operationally with keep-alive/KodeVRAM policy.

**Provisional KodeCore winner: `gpt-oss:20b`.**

`qwen3.5:9b` remains available as a smaller multimodal/fallback candidate; it is not deleted or declared intrinsically weak.

### CODER — pending

Candidates:
- `qwen2.5-coder:7b-instruct`
- `devstral-small-2:24b`
- `north-mini-code-1.0:Q4_K_M`

Next evidence file: `.kodepoia/benchmarks/r3-preselect-coder.json`.

## Remaining hardware-local acceptance

R3 remains intentionally incomplete until CODER preselection is reviewed, 2–3 final candidates are selected, and the official target-PC acceptance report is generated and reviewed.

### Prepared Windows runner

From the Kodepoia repository root:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
```

Then run two or three installed finalists:

```powershell
.\scripts\r3_accept_local.ps1 -Model modelA,modelB
# or
.\scripts\r3_accept_local.ps1 -Model modelA,modelB,modelC
```

Detailed procedure: `docs/roadmap/R3_LOCAL_ACCEPTANCE.md`.

The wrapper verifies:
- Python 3.12+;
- loopback-only Ollama (`127.0.0.1`, `localhost` or `::1`);
- local `ollama-status` connectivity;
- exactly two or three distinct installed candidates;
- generation of `.kodepoia/benchmarks/r3-local-acceptance.json`;
- `phase == R3-local-acceptance`;
- `acceptance_completed == true`;
- `loopback_verified == true`;
- candidate count and per-model summary presence.

## Review required before completion

The final report must be reviewed for:
- pass/total score and repeatability;
- structured-output success;
- tool-call success;
- Godot/GDScript correctness;
- general software-engineering/debugging correctness;
- elapsed time and tokens/s;
- VRAM/model metadata when Ollama exposes them;
- model-load/runtime errors and generation-budget exhaustion.

## Completion rule

R3 becomes `COMPLETE` only after CODER preselection and the target workstation's `.kodepoia/benchmarks/r3-local-acceptance.json` have been reviewed and accepted. PR #8 remains open until that hardware-local evidence exists. R4 must not begin before R3 is accepted.
