# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3 COMPLETE. **R4 KodeCode IN PROGRESS**. R4.1/R4.2/R4.3/R4.4 sont ACCEPTED AND MERGED. **R4.5 graphs est IMPLEMENTED / PENDING CI ACCEPTANCE** sur `agent/r4-5-code-graphs`. R4.6 reste à faire. Ne marquer R4 COMPLETE qu'après orchestration protégée + acceptance repository-scale + CI finale.

## Source de vérité et contraintes

- Dépôt `LaurentCOLL1/Kodepoia`, visibilité **PUBLIC volontairement**.
- `main` après R4.4 : `0b16277c00782382780c2b5f2b1aa7a616b4f9da`.
- Branche active : `agent/r4-5-code-graphs`.
- R4.4 PR #17 MERGED.
- Modèles : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4.1 à R4.4

- R4.1 PR #11 merged : WorkspaceBoundary, safe files/search/patch, Git worktrees, structured Tool API.
- R4.2 PR #13 merged : Tree-sitter, provider registry, ABI checks, tolerant + incremental parsing.
- R4.3 PR #15 merged : LSP framing, persistent sandboxed stdio sessions, lifecycle/navigation/diagnostics.
- R4.4 PR #17 merged, commit `0b16277c00782382780c2b5f2b1aa7a616b4f9da` : DAP initialize, pre-registered launch/attach configs, breakpoints, threads/stack/scopes/variables, protected adapter launch and runInTerminal refusal.

R4.4 final CI head `084ad9d83515067a63e2d02c0e3689ce368f74bc`:
- Repository Guard `32514727455` SUCCESS;
- Python Core `32514727480` SUCCESS Ubuntu+Windows;
- UI Smoke `32514727690` SUCCESS Windows.

## R4.5 — IMPLEMENTED / PENDING CI ACCEPTANCE

Implemented:
- `CodeGraphIndex` Tree-sitter-backed multi-file index;
- deterministic file/symbol/call/dependency stable IDs;
- source provenance via path and byte ranges;
- Python/JavaScript/TypeScript/TSX definitions, calls and imports/dependencies;
- call resolution only when a target name is unique; ambiguous targets stay unresolved;
- SHA-256 per-file incremental refresh; unchanged files skipped;
- stable symbol IDs across body-only edits;
- bounded `GraphToolAPI`: refresh/symbols/calls/dependencies;
- tests for provenance, stable IDs, incremental skip/refresh, resolved/ambiguous calls, dependencies, bounds and workspace escape.

Do not mark R4.5 ACCEPTED before exact-head Repository Guard, Python Core Ubuntu+Windows and UI Smoke are green.

## R4.6 — NEXT AFTER R4.5 ACCEPTANCE

1. Compose base KodeCode and Graph catalogs for orchestrator execution.
2. Explicitly classify every tool as read/write/execute.
3. Authorize through KodeGuardian + PermissionSet.
4. Snapshot mutating file operations through SafeChange before execution.
5. Audit allow/deny/completion.
6. Add repository-scale acceptance scenarios covering read/search/parse/graph + protected mutation and denial paths.
7. Require final Windows+Ubuntu CI on exact head.
8. Only then mark R4 COMPLETE and merge to main.

## Permanent rules

Update continuity in same cycle for phase/PR/acceptance changes. Never mark COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional.
