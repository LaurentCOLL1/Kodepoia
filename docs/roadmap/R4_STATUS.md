# R4 — KodeCode — Status

**Phase:** R4  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

## R4.1 — ACCEPTED AND MERGED
PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

## R4.2 — ACCEPTED AND MERGED
PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

## R4.3 — LSP

**Status: ACCEPTED ON `agent/r4-3-lsp` / MERGE PENDING.**

Implemented and accepted:
- [x] Content-Length framed UTF-8 JSON transport with header/body limits.
- [x] Timeout-capable threaded message channel.
- [x] `ProcessSandbox.spawn_piped()` + `ManagedProcess` for persistent stdio processes under allowlist/cwd confinement/global kill switch.
- [x] Explicit `LanguageServerSpec`/registry; no arbitrary argv exposed through model tools.
- [x] LSP lifecycle `initialize` → `initialized` → requests → `shutdown` → `exit`.
- [x] document symbols, definitions, references and `publishDiagnostics` capture.
- [x] baseline server→client requests for workspace configuration and dynamic registration.
- [x] workspace-confined `didOpen` and `file://` URIs.
- [x] structured LSP capabilities/start/stop/symbols/definition/references/diagnostics tools.
- [x] deterministic protocol/lifecycle tests and real sandboxed persistent stdio process test.

Acceptance head: `618842926b5c81552eb1cb5345422d77f9f5eeb1`.
- R0 Repository Guard `32513727806` — **SUCCESS** Ubuntu + Windows.
- Python Core `32513727725` — **SUCCESS** Ubuntu + Windows.
- KodeStudio UI Smoke `32513727609` — **SUCCESS** Windows.

Security policy:
- only pre-registered language servers can start;
- no arbitrary argv through Tool API;
- no network LSP transport in R4.3;
- persistent processes inherit KodeSandbox/global kill switch;
- protocol sizes and waits are bounded.

## Remaining R4 work

### R4.4 — DAP — NEXT AFTER R4.3 MERGE
- [ ] DAP request/response/event session abstraction over shared framing.
- [ ] initialize + launch/attach capability representation.
- [ ] breakpoints, threads, stack, scopes and variables baseline.
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

R4 remains **IN PROGRESS**, not COMPLETE. R4.1/R4.2 are merged. R4.3 has passed implementation and CI acceptance but is not part of `main` until PR #15 merges.
