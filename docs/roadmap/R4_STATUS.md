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

## R4.1 — Safe workspace + files/search/patch + Git worktrees

Implementation status:
- [x] `WorkspaceBoundary` rejects absolute paths and workspace escapes after resolution.
- [x] File listing and UTF-8 reads are workspace-scoped and size-bounded.
- [x] Deterministic text/regex search with generated/cache exclusions.
- [x] Exact single-occurrence patch with optional SHA-256 stale-content precondition.
- [x] Patch writes use same-directory atomic replacement.
- [x] Git worktree operations go through `ProcessSandbox`; no shell execution is exposed.
- [x] Managed worktrees are confined under `.kodepoia/worktrees/`.
- [x] Git refs/names reject option-injection shapes.
- [x] Git worktree listing uses the stable porcelain format.
- [x] `KodeCodeToolAPI` exposes only explicit structured operations and schemas.
- [x] Unit tests cover boundary escape, search, patch guards and worktree dispatch/parser.
- [ ] CI evidence on the R4 branch.

## Remaining R4 work

### R4.2 — Tree-sitter parser layer
- [ ] Add official Python Tree-sitter runtime dependency behind an optional/code extra.
- [ ] Language registry and parser capability discovery.
- [ ] Incremental parse/update support.
- [ ] Syntax-error-tolerant extraction.
- [ ] Parser tests and version/ABI checks.

### R4.3 — LSP
- [ ] JSON-RPC transport abstraction.
- [ ] Server lifecycle/capabilities.
- [ ] document symbols / definitions / references / diagnostics baseline.
- [ ] Protected process launch through tool/sandbox boundary.

### R4.4 — DAP
- [ ] DAP framing and session abstraction.
- [ ] launch/attach capability representation.
- [ ] breakpoints, stack, scopes/variables baseline.
- [ ] Protected adapter launch through tool/sandbox boundary.

### R4.5 — Code intelligence graphs
- [ ] Symbol graph.
- [ ] Call graph.
- [ ] Dependency/import graph.
- [ ] Stable IDs/provenance and incremental refresh.

### R4.6 — Orchestration + acceptance
- [ ] Wire KodeCode structured catalog into agent/orchestrator tool execution.
- [ ] Enforce Guardian/permissions/SafeChange policy for mutating tools.
- [ ] Repository-scale acceptance scenarios.
- [ ] Windows + Ubuntu CI acceptance evidence.

## Current acceptance decision

R4 is **IN PROGRESS**, not COMPLETE. R4.1 is implemented on `agent/r4-kodecode`; it becomes accepted only after its CI is green. Tree-sitter/LSP/DAP/graphs remain pending and must not be represented as implemented yet.

## Reference research used for implementation

- Tree-sitter remains the intended incremental parser foundation; official Python bindings are available and document incremental parsing/tree updates.
- LSP 3.18 is the current published Language Server Protocol specification.
- Git documents `git worktree list --porcelain` as a stable machine-readable format.
