# R4 — KodeCode — Status

**Phase:** R4  
**Status:** COMPLETE  
**Started:** 2026-08-21  
**Completed:** 2026-08-21

## Completion decision

R4 is **COMPLETE**. Every frozen R4 requirement is implemented, tested, accepted and merged. R5 — KodeGodot 4.7.x — is **AUTHORIZED / NOT STARTED**.

## R4.1 — Safe workspace + files/search/patch + Git worktrees — ACCEPTED AND MERGED

PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

Delivered: workspace confinement, safe file list/read/search, exact atomic patching with stale-content protection, ProcessSandbox-backed Git worktrees, explicit structured Tool API, symlink/path/injection hardening and Windows+Ubuntu tests.

## R4.2 — Tree-sitter parser layer — ACCEPTED AND MERGED

PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

Delivered: provider-based Tree-sitter registry, ABI validation, Python/JavaScript/TypeScript/TSX grammars, optional GDScript provider, tolerant parsing, incremental `Tree.edit()` + `Parser.parse(old_tree=...)` + changed ranges, bounded parser tools and cross-platform tests.

## R4.3 — LSP protected client layer — ACCEPTED AND MERGED

PR #15, merge `1074533e9930549b71af281003b74c6ed049ba9b`.

Delivered: bounded Content-Length JSON framing, timeout channel, persistent sandboxed stdio process sessions, explicit server registry, initialize/initialized/shutdown/exit lifecycle, symbols/definitions/references/diagnostics and structured LSP tools.

Accepted final head `36c53f3d5af53ec63977dd71260055df0b1c3181`:
- R0 Repository Guard `32513904670` — SUCCESS;
- Python Core `32513904676` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32513904762` — SUCCESS Windows.

## R4.4 — DAP protected client layer — ACCEPTED AND MERGED

PR #17, merge `0b16277c00782382780c2b5f2b1aa7a616b4f9da`.

Delivered: DAP request/response/event session over shared framing, initialize, pre-registered launch/attach configurations, breakpoints/configurationDone, threads/stack/scopes/variables, event capture/disconnect, protected adapter launch and baseline refusal of adapter-originated execution requests such as `runInTerminal`.

Accepted final head `084ad9d83515067a63e2d02c0e3689ce368f74bc`:
- R0 Repository Guard `32514727455` — SUCCESS;
- Python Core `32514727480` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32514727690` — SUCCESS Windows.

## R4.5 — Code intelligence graphs — ACCEPTED AND MERGED

PR #18, merge `344a29022c6e96f447944d3e064ebeb1933a4600`.

Delivered: Tree-sitter-backed multi-file symbol/call/dependency graphs, deterministic stable IDs, source provenance, conservative call resolution, SHA-256 incremental refresh, unchanged-file skip, stable symbol IDs across body-only edits and bounded `GraphToolAPI`. Acceptance also hardened `WorkspaceBoundary` so escaped missing paths are denied before strict filesystem resolution.

Accepted final head `af75e5277b86974e02c5c37c3e78e99f445b4aac`:
- R0 Repository Guard `32519472687` — SUCCESS;
- Python Core `32519472699` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32519472724` — SUCCESS Windows.

## R4.6 — Governed orchestration + final acceptance — ACCEPTED AND MERGED

PR #19 — `R4.6 governed KodeCode orchestration and final acceptance` — MERGED.  
Merge commit: `80931d3f4302456783a884f117976ad0f4fed340`.

Accepted implementation:
- `KodeCodeExecutor` composes base KodeCode and graph structured catalogs;
- every exposed tool has an explicit `ToolPolicy`, with construction failure for unclassified tools;
- READ / WRITE / EXECUTE policies map to Guardian action types;
- Guardian + `PermissionSet` authorization occurs before every execution;
- path-bearing tools authorize against workspace-resolved paths;
- `kodecode_patch_replace_once` takes a `SafeChangeManager` snapshot before mutation;
- process-bearing Git/LSP/DAP operations require PROCESS_EXECUTE and retain their ProcessSandbox/allowlist boundaries;
- audit records permission-denied / denied / confirmation-required / authorized / failed / completed outcomes without raw argument values;
- Orchestrator supplies the composed structured catalog to tool-capable Brain calls when configured;
- explicit `execute_tool()` and `execute_tool_calls()` support Ollama-style function calls without introducing a hidden autonomous execution loop;
- repository-scale acceptance creates 30 source files and validates read/search/parse/graphs, call/dependency linking, unchanged-file skip, protected patch snapshot, changed-file graph refresh, stable symbol IDs and audit verification;
- denial tests cover missing FILE_WRITE and PROCESS_EXECUTE permissions.

Final accepted R4.6 PR head `ba23422981d0bc5dce35b4f6714705a82bea64b6`:
- R0 Repository Guard `32520187214` — **SUCCESS**;
- Python Core `32520187196` — **SUCCESS** Ubuntu + Windows;
- KodeStudio UI Smoke `32520187172` — **SUCCESS** Windows.

## Frozen-scope acceptance matrix

- Files/search/patch — PASS (R4.1)
- Git worktrees — PASS (R4.1)
- Tree-sitter parsers — PASS (R4.2)
- LSP — PASS (R4.3)
- DAP — PASS (R4.4)
- Symbol/call/dependency graphs — PASS (R4.5)
- Structured tools only / no direct model system access — PASS (R4.1–R4.6)
- Guardian/permissions/SafeChange governed orchestration — PASS (R4.6)
- Repository-scale acceptance — PASS (R4.6)
- Windows + Ubuntu CI acceptance — PASS

## Next phase

**R5 — KodeGodot 4.7.x: AUTHORIZED / NOT STARTED.**

Do not reopen R4 or change the frozen v1.0 architecture without new evidence or an ADR. R4 is now a completed dependency for R5.
