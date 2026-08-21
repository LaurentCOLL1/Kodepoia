# R4 — KodeCode — Status

**Phase:** R4  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

## R4.1 — ACCEPTED AND MERGED
PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

## R4.2 — ACCEPTED AND MERGED
PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

## R4.3 — LSP — ACCEPTED AND MERGED

PR #15 — `R4.3 LSP protected client layer` — MERGED.  
Merge commit: `1074533e9930549b71af281003b74c6ed049ba9b`.

Accepted implementation:
- Content-Length framed UTF-8 JSON with bounds and timeout-capable channel;
- persistent `ProcessSandbox.spawn_piped()`/`ManagedProcess` under allowlist, cwd confinement and global kill switch;
- explicit language-server registry, no arbitrary model-supplied argv;
- initialize/initialized/shutdown/exit lifecycle;
- document symbols, definitions, references, publishDiagnostics;
- baseline server→client requests;
- workspace-confined didOpen/file URIs;
- structured LSP Tool API.

Final branch-head evidence `36c53f3d5af53ec63977dd71260055df0b1c3181`:
- R0 Repository Guard `32513904670` — SUCCESS;
- Python Core `32513904676` — SUCCESS Ubuntu + Windows;
- KodeStudio UI Smoke `32513904762` — SUCCESS Windows.

## Remaining R4 work

### R4.4 — DAP — NEXT / NOT STARTED
- [ ] DAP request/response/event abstraction over shared framing.
- [ ] initialize + launch/attach capability representation.
- [ ] breakpoints, threads, stack, scopes, variables baseline.
- [ ] protected adapter launch through KodeSandbox.

### R4.5 — Code intelligence graphs — PENDING
- [ ] symbol graph.
- [ ] call graph.
- [ ] dependency/import graph.
- [ ] stable IDs/provenance and incremental refresh.

### R4.6 — Orchestration + acceptance — PENDING
- [ ] wire KodeCode catalog into orchestrator tool execution.
- [ ] enforce Guardian/permissions/SafeChange for mutations.
- [ ] repository-scale acceptance scenarios.
- [ ] Windows + Ubuntu final R4 acceptance.

## Current decision

R4 remains **IN PROGRESS**, not COMPLETE. R4.1, R4.2 and R4.3 are accepted and merged on `main`. R4.4 DAP is the next authorized sub-phase and is not started yet.
