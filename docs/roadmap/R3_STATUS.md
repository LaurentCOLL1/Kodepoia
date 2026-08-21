# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** IMPLEMENTATION COMPLETE — LOCAL MODEL BENCHMARK PENDING  
**Completed in CI:** 2026-08-21

## Validation evidence

- PR #5 — `R3: implement KodeBrain, Memory, Context and ModelRouter`.
- Merge commit: `b5e61dea1d50ccfc8ffff6f1e525f95a39b8096f`.
- GitHub Actions Python Core run `32436947731`: SUCCESS on Windows and Ubuntu.
- GitHub Actions R0 Repository Guard run `32436947869`: SUCCESS on Windows and Ubuntu.

## Implemented

- [x] Model-agnostic Brain protocol.
- [x] Local Ollama adapter using `/api/version`, `/api/tags`, `/api/chat` and `/api/embed`.
- [x] Tool-call, JSON-schema/structured-output, thinking and keep-alive parameters.
- [x] KodeModelRegistry with FAST / CORE / CODER / EMBED / VISION roles.
- [x] KodeModelRouter driven by task profile and VRAM fit.
- [x] Persistent SQLite KodeMemory with WAL, scopes, importance, metadata and governance flags.
- [x] Embedding persistence and cosine semantic retrieval.
- [x] KodeContext token budget, mandatory-context handling and relevance priority.
- [x] KodeOrchestrator chat path joining routing, context, memory, Ollama and audit.
- [x] `kodepoia ollama-status` local diagnostic.
- [x] `kodepoia bench-models` baseline comparison runner and JSON output.
- [x] Sequential-heavy-model routing policy example.
- [x] Mocked Ollama API tests so CI does not require an Ollama daemon or downloaded model.

## Remaining hardware-local acceptance

GitHub Actions cannot benchmark the actual Ollama models installed on the target workstation. Concrete model assignment therefore remains intentionally unfrozen until at least two, preferably three, candidates are benchmarked locally:

```powershell
kodepoia ollama-status
kodepoia bench-models --model <candidate1> --model <candidate2> --model <candidate3>
```

This does **not** invalidate the R3 implementation: the model-agnostic runtime, router, memory, context and benchmark harness are complete and cross-platform validated. It preserves the frozen rule that concrete models are selected from measured local results rather than assumptions.
