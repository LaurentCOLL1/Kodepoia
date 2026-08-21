# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3 COMPLETE. **R4 KodeCode IN PROGRESS**. R4.1/R4.2 ACCEPTED AND MERGED. **R4.3 LSP ACCEPTED ON BRANCH / MERGE PENDING** sur `agent/r4-3-lsp`, PR #15. R4.4/R4.5/R4.6 non commencés. Lire architecture, ADR, roadmap, `R4_STATUS.md`, puis ce fichier.

## Source de vérité et contraintes

- Dépôt : `LaurentCOLL1/Kodepoia`, visibilité **PUBLIC volontairement**.
- `main` avant R4.3 : `1ec80dcef878a1bac4affb062834c9cc8e75ad7b`.
- Branche active : `agent/r4-3-lsp` ; PR #15 ouverte.
- R1/R2/R3 COMPLETE ; R4 IN PROGRESS.
- Modèles acceptés : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4.1 — ACCEPTED AND MERGED
PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.
WorkspaceBoundary, safe files/search/patch, Git worktrees via ProcessSandbox, structured Tool API.

## R4.2 — ACCEPTED AND MERGED
PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.
Tree-sitter 0.26.x, Python/JavaScript/TypeScript/TSX, provider registry, ABI checks, tolerant + incremental parsing, optional GDScript provider.

## R4.3 — ACCEPTED ON BRANCH / MERGE PENDING

Implemented:
- shared Content-Length UTF-8 JSON framing with limits;
- timeout-capable threaded framed channel;
- `ProcessSandbox.spawn_piped()` + `ManagedProcess` persistent processes under allowlist/root/global kill switch;
- explicit `LanguageServerSpec`/registry, no model-supplied argv;
- LSP initialize/initialized/shutdown/exit;
- document symbols, definition, references, publishDiagnostics;
- baseline server→client request replies;
- workspace-confined didOpen/file URIs;
- structured LSP tools;
- deterministic protocol/lifecycle tests and real bidirectional sandboxed stdio process test.

Acceptance head `618842926b5c81552eb1cb5345422d77f9f5eeb1`:
- R0 Repository Guard `32513727806` — SUCCESS;
- Python Core `32513727725` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32513727609` — SUCCESS Windows.

PR #15 must be merged before R4.3 becomes source of truth on `main`.

## Next sequence

1. merge PR #15 after final exact-head checks;
2. R4.4 DAP;
3. R4.5 symbol/call/dependency graphs;
4. R4.6 orchestrator wiring + Guardian/Permissions/SafeChange + repository-scale acceptance;
5. mark R4 COMPLETE only when R4.6 acceptance and final CI are green.

## Permanent rules

Update continuity in the same cycle for phase/PR/acceptance/prerequisite changes. Never mark COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional.
