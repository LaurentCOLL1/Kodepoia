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
- Validated hardening commit: `e2cc5cb624e14c459b92fd9128343c8e2b4a1d1f`.
- `R0 Repository Guard` run `32456258458`: SUCCESS on Windows and Ubuntu.
- `Python Core` run `32456258437`: SUCCESS on Windows and Ubuntu; Windows KodeStudio smoke job SUCCESS.
- `KodeStudio UI Smoke` run `32456258443`: SUCCESS on Windows.

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
- [x] `kodepoia r3-accept` local-only acceptance command requiring two or three distinct installed candidates.
- [x] Mocked Ollama API tests so CI validates protocols without requiring downloaded models.
- [x] R3 hardening CI on Windows and Ubuntu.

## Remaining hardware-local acceptance

GitHub Actions cannot benchmark the actual Ollama models installed on the target workstation. R3 therefore remains intentionally incomplete until two or three real candidates are compared on that PC.

### Prepared Windows runner

From the Kodepoia repository root:

```powershell
.\scripts\r3_accept_local.ps1 -ListOnly
```

Then run two or three installed candidates:

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

The report must then be reviewed for:
- pass/total score;
- structured-output success;
- tool-call success;
- Godot/GDScript correctness;
- general software-engineering/debugging correctness;
- elapsed time and tokens/s;
- VRAM/model metadata when Ollama exposes them;
- model-load or runtime errors.

Concrete FAST/CORE/CODER assignments remain intentionally unfrozen until these measured local results are reviewed.

## Completion rule

R3 becomes `COMPLETE` only after the target workstation has generated and reviewed `.kodepoia/benchmarks/r3-local-acceptance.json`. PR #8 remains open until that hardware-local evidence exists. R4 must not begin before R3 is accepted.
