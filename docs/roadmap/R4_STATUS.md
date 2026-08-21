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

## R4.4 — DAP

**Status: IMPLEMENTED ON `agent/r4-4-dap` / CI ACCEPTANCE PENDING.**

Implementation:
- [x] DAP request/response/event session over R4.3 shared Content-Length framing.
- [x] initialize capability negotiation.
- [x] pre-registered `launch`/`attach` configurations selected only by `config_id`.
- [x] setBreakpoints + configurationDone.
- [x] threads → stackTrace → scopes → variables baseline.
- [x] event capture and disconnect.
- [x] explicit debug-adapter registry and protected adapter launch via `ProcessSandbox.spawn_piped()`.
- [x] adapter→client execution requests such as `runInTerminal` rejected in baseline.
- [x] workspace-confined breakpoint source paths.
- [x] structured DAP tools; no arbitrary argv or launch arguments in model schemas.
- [x] tests for lifecycle, stack/variables waterfall, path confinement, registry/config validation and Tool API secrecy.
- [ ] exact-head Repository Guard / Python Core Windows+Ubuntu / UI Smoke evidence.

## Remaining R4 work

### R4.5 — Code intelligence graphs — NEXT AFTER R4.4 ACCEPTANCE
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

R4 remains **IN PROGRESS**, not COMPLETE. R4.1/R4.2/R4.3 are accepted and merged. R4.4 is implemented but remains pending CI acceptance.
