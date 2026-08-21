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

**Status: ACCEPTED AND MERGED TO `main`.**

Integration evidence:
- PR #11 — `R4.1 KodeCode safe tool foundation` — MERGED.
- Merge commit: `91f3d77cc375021efcb24172b2859a27748843b8`.

Implementation and acceptance:
- [x] `WorkspaceBoundary` rejects absolute paths and workspace escapes after resolution.
- [x] File listing and UTF-8 reads are workspace-scoped and size-bounded.
- [x] Recursive listing/search skip symlinks resolving outside the workspace.
- [x] Deterministic text/regex search with generated/cache exclusions.
- [x] Exact single-occurrence patch with optional SHA-256 stale-content precondition.
- [x] Patch writes use same-directory atomic replacement, preserve exact UTF-8 bytes/newlines and file mode.
- [x] Git worktree operations go through `ProcessSandbox`; no shell execution is exposed.
- [x] Managed worktrees are confined under `.kodepoia/worktrees/`.
- [x] Git refs/names reject option-injection shapes.
- [x] Git worktree listing uses the stable porcelain format.
- [x] `KodeCodeToolAPI` exposes only explicit structured operations and function schemas.
- [x] Unit tests cover boundary escape, search, patch guards/newline preservation, structured API and worktree dispatch/parser.
- [x] R0 Repository Guard run `32508868032` — SUCCESS on final documentation head.
- [x] Python Core run `32508868396` — SUCCESS on Ubuntu and Windows.
- [x] KodeStudio UI Smoke run `32508868371` — SUCCESS on Windows.

## Remaining R4 work

### R4.2 — Tree-sitter parser layer — NEXT / NOT STARTED
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

R4 remains **IN PROGRESS**, not COMPLETE. R4.1 is accepted and merged on `main`. R4.2 Tree-sitter is the next authorized sub-phase. LSP/DAP/graphs/orchestration remain pending and must not be represented as implemented yet.

## Reference research used for implementation

- Tree-sitter remains the intended incremental parser foundation; official Python bindings are available and document incremental parsing/tree updates.
- LSP 3.18 is the current published Language Server Protocol specification.
- Git documents `git worktree list --porcelain` as a stable machine-readable format.
