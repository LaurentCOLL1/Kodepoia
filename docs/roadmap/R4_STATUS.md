# R4 — KodeCode — Status

**Phase:** R4  
**Status:** IN PROGRESS — FINAL ACCEPTANCE PENDING  
**Started:** 2026-08-21

## R4.1 — ACCEPTED AND MERGED
PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

## R4.2 — ACCEPTED AND MERGED
PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

## R4.3 — ACCEPTED AND MERGED
PR #15, merge `1074533e9930549b71af281003b74c6ed049ba9b`.

## R4.4 — ACCEPTED AND MERGED
PR #17, merge `0b16277c00782382780c2b5f2b1aa7a616b4f9da`.

Final accepted R4.4 branch head `084ad9d83515067a63e2d02c0e3689ce368f74bc`:
- R0 Repository Guard `32514727455` — SUCCESS;
- Python Core `32514727480` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32514727690` — SUCCESS Windows.

## R4.5 — Code intelligence graphs — ACCEPTED AND MERGED

PR #18 — `R4.5 code intelligence graphs` — MERGED.  
Merge commit: `344a29022c6e96f447944d3e064ebeb1933a4600`.

Final accepted branch head `af75e5277b86974e02c5c37c3e78e99f445b4aac`:
- R0 Repository Guard `32519472687` — SUCCESS;
- Python Core `32519472699` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32519472724` — SUCCESS Windows.

Accepted implementation:
- Tree-sitter-backed multi-file symbol graph;
- call graph with source symbol/file provenance;
- dependency/import graph for Python/JavaScript/TypeScript/TSX;
- deterministic stable IDs for files, symbols and edges;
- conservative call resolution; ambiguous target names remain unresolved;
- SHA-256 per-file incremental refresh and unchanged-file skip;
- stable symbol IDs across body-only edits;
- bounded workspace-confined `GraphToolAPI`;
- regression hardening in `WorkspaceBoundary`: escaped missing paths are denied before strict filesystem resolution;
- tests for stable IDs, provenance, skip/refresh, dependencies, resolved/ambiguous calls, bounds and path escape.

## R4.6 — Governed orchestration + final acceptance

**Status: IMPLEMENTED ON `agent/r4-6-orchestration` / FINAL CI ACCEPTANCE PENDING.**

Implementation:
- [x] `KodeCodeExecutor` composes base KodeCode + graph structured catalogs.
- [x] every exposed R4 tool requires an explicit `ToolPolicy`; unclassified tools fail executor construction.
- [x] policies classify tools as READ / WRITE / EXECUTE and map them to Guardian `ActionType`.
- [x] Guardian + `PermissionSet` authorization occurs before tool execution.
- [x] path-bearing file tools authorize against workspace-resolved absolute targets.
- [x] protected file writes (`kodecode_patch_replace_once`) require SafeChange snapshot before execution.
- [x] process-bearing Git/LSP/DAP operations require PROCESS_EXECUTE and still launch only through their existing sandbox/allowlist boundaries.
- [x] audit events record permission-denied / denied / confirmation-required / authorized / failed / completed outcomes without logging raw argument values.
- [x] Orchestrator exposes the composed tool catalog to tool-capable Brain calls when an executor is configured.
- [x] Orchestrator exposes explicit `execute_tool()` and `execute_tool_calls()`; no hidden autonomous tool loop was introduced.
- [x] Ollama-style nested tool calls and JSON-string/object arguments are supported.
- [x] repository-scale acceptance builds 30 source files and validates read/search/parse/graphs, incremental graph refresh, stable IDs, protected patch snapshot and audit-chain verification.
- [x] denial tests cover missing FILE_WRITE and missing PROCESS_EXECUTE permissions.
- [x] orchestrator acceptance verifies that a fake tool-calling Brain receives the full catalog and that its tool call is executed through the governed executor.
- [ ] exact-head R0 Repository Guard success.
- [ ] exact-head Python Core success on Ubuntu + Windows.
- [ ] exact-head KodeStudio UI Smoke success on Windows.

## Completion rule

R4 may be marked **COMPLETE** only after the exact R4.6 PR head passes all three workflows above, the PR is mergeable and merged, then post-merge status/continuity is normalized on `main` with final evidence. R5 must not begin before that normalization is merged.
