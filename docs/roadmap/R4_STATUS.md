# R4 — KodeCode — Status

**Phase:** R4  
**Status:** IN PROGRESS  
**Started:** 2026-08-21

## Frozen scope

Per roadmap v1.0, R4 delivers:
- files/search/patch;
- Git worktrees;
- parsers/Tree-sitter;
- LSP/DAP;
- symbol/call/dependency graphs;
- structured tools;
- no direct access outside the tool API.

## R4.1 — ACCEPTED AND MERGED

PR #11 — `R4.1 KodeCode safe tool foundation` — MERGED.  
Merge commit: `91f3d77cc375021efcb24172b2859a27748843b8`.

## R4.2 — ACCEPTED AND MERGED

PR #13 — `R4.2 Tree-sitter parser layer` — MERGED.  
Merge commit: `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

## R4.3 — LSP

**Status: IMPLEMENTED ON `agent/r4-3-lsp` / CI ACCEPTANCE PENDING.**

Implementation:
- [x] Shared Content-Length framed UTF-8 JSON transport with header/body limits.
- [x] Timeout-capable threaded framed message channel.
- [x] `ProcessSandbox.spawn_piped()` persistent stdio process sessions, preserving executable allowlist, cwd confinement and global kill switch.
- [x] Explicit `LanguageServerSpec` and `LanguageServerRegistry`; no arbitrary argv exposed to agents.
- [x] LSP lifecycle: `initialize`, `initialized`, `shutdown`, `exit`.
- [x] document symbols, definitions, references and `publishDiagnostics` capture.
- [x] Baseline server->client request handling for workspace configuration and dynamic registration.
- [x] Workspace-confined `file://` URIs and `didOpen`.
- [x] Structured LSP capabilities/start/stop/symbols/definition/references/diagnostics tools.
- [x] Deterministic framing/lifecycle tests and a real persistent sandbox stdio test.
- [ ] Final Repository Guard / Python Core Windows+Ubuntu / UI Smoke evidence on the exact R4.3 head.

Security policy:
- no arbitrary language-server executable/argv from model tool arguments;
- only pre-registered servers may start;
- no network LSP transport in R4.3;
- persistent processes remain bound to KodeSandbox/global kill switch;
- message sizes and waits are bounded.

## Remaining R4 work

### R4.4 — DAP — NEXT AFTER R4.3 ACCEPTANCE
- [ ] DAP request/response/event session abstraction over shared framing.
- [ ] initialize + launch/attach capability representation.
- [ ] breakpoints, threads, stack, scopes and variables baseline.
- [ ] Protected adapter launch through KodeSandbox.

### R4.5 — Code intelligence graphs — PENDING
- [ ] Symbol graph.
- [ ] Call graph.
- [ ] Dependency/import graph.
- [ ] Stable IDs/provenance and incremental refresh.

### R4.6 — Orchestration + acceptance — PENDING
- [ ] Wire KodeCode structured catalog into orchestrator tool execution.
- [ ] Enforce Guardian/permissions/SafeChange policy for mutating tools.
- [ ] Repository-scale acceptance scenarios.
- [ ] Windows + Ubuntu CI acceptance evidence.

## Current acceptance decision

R4 remains **IN PROGRESS**, not COMPLETE. R4.1 and R4.2 are accepted and merged. R4.3 is implemented but remains pending acceptance until its exact final head has green Repository Guard, Python Core on Windows+Ubuntu and KodeStudio UI Smoke.
