# R3 — KodeBrain + Ollama + KodeMemory + KodeContext — Status

**Phase:** R3  
**Status:** IMPLEMENTED — cross-platform CI plus local-Ollama acceptance required  
**Date:** 2026-08-21

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
- [x] Model-role example configuration with 12 GB sequential-heavy-model policy.
- [x] Mocked API tests ensure CI does not require an Ollama daemon or downloaded model.

## Hardware-local acceptance

GitHub Actions cannot benchmark the models installed on the user's Windows/Radeon workstation. Therefore R3 code can be merged after CI, but the **model selection is intentionally not frozen** until the following is run locally with at least two (preferably three) installed Ollama candidates:

```powershell
kodepoia ollama-status
kodepoia bench-models --model <candidate1> --model <candidate2> --model <candidate3>
```

This is consistent with the frozen decision that KodeBrain remains model-agnostic and KodeBench selects concrete models from measured results rather than assumptions.
