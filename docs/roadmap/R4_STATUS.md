# R4 — KodeCode — Status

**Phase:** R4  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

## R4.1 — ACCEPTED AND MERGED
PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

## R4.2 — ACCEPTED AND MERGED
PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

## R4.3 — ACCEPTED AND MERGED
PR #15, merge `1074533e9930549b71af281003b74c6ed049ba9b`.

## R4.4 — DAP — ACCEPTED AND MERGED

PR #17 — `R4.4 protected DAP client layer` — MERGED.  
Merge commit: `0b16277c00782382780c2b5f2b1aa7a616b4f9da`.

Final accepted branch head `084ad9d83515067a63e2d02c0e3689ce368f74bc`:
- R0 Repository Guard `32514727455` — SUCCESS;
- Python Core `32514727480` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32514727690` — SUCCESS Windows.

Implemented: DAP request/response/event session over shared framing, initialize, pre-registered launch/attach configs, breakpoints/configurationDone, threads/stack/scopes/variables, event capture/disconnect, protected adapter launch through ProcessSandbox, default refusal of adapter-originated execution requests such as runInTerminal, workspace-confined source paths and structured DAP tools without arbitrary argv/config arguments.

## R4.5 — Code intelligence graphs

**Status: IMPLEMENTED ON `agent/r4-5-code-graphs` / CI ACCEPTANCE PENDING.**

Implementation:
- [x] Tree-sitter-backed multi-file symbol graph.
- [x] call graph with source symbol/file provenance.
- [x] dependency/import graph for Python/JavaScript/TypeScript/TSX.
- [x] deterministic stable IDs for files, symbols and edges.
- [x] source provenance through path/start byte/end byte metadata.
- [x] conservative call target resolution: only unique symbol-name targets auto-link; ambiguous calls stay unresolved.
- [x] SHA-256 per-file incremental refresh; unchanged files are skipped.
- [x] stable symbol IDs across body-only changes.
- [x] bounded `GraphToolAPI` for refresh/symbol/call/dependency queries.
- [x] workspace confinement and result/file count limits.
- [x] tests for stable IDs, provenance, skip/refresh behavior, dependencies, resolved and ambiguous calls, bounds and path escape.
- [ ] exact-head Repository Guard / Python Core Windows+Ubuntu / UI Smoke evidence.

## R4.6 — Orchestration + final acceptance — PENDING

- [ ] compose KodeCode + Graph structured catalogs for orchestrator use.
- [ ] explicit per-tool policy classification.
- [ ] Guardian/PermissionSet authorization before execution.
- [ ] SafeChange snapshot before protected mutations.
- [ ] audit records for allowed/denied/completed tool operations.
- [ ] repository-scale acceptance scenarios.
- [ ] final Windows + Ubuntu exact-head CI evidence.

## Current decision

R4 remains **IN PROGRESS**, not COMPLETE. R4.1 through R4.4 are accepted and merged. R4.5 is implemented and pending exact-head CI acceptance. R4.6 must still pass final orchestration/acceptance before R4 can become COMPLETE.
