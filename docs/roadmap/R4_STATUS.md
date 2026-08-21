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

## R4.2 — Tree-sitter parser layer

**Status: IMPLEMENTED ON `agent/r4-2-tree-sitter` / CI ACCEPTANCE PENDING.**

Implementation:
- [x] Optional `code` extra uses official `tree-sitter>=0.26,<0.27` Python runtime.
- [x] Packaged grammar providers: Python 0.25.x, JavaScript 0.25.x, TypeScript/TSX 0.23.2.x.
- [x] Provider-based `TreeSitterLanguageRegistry` with aliases and extension detection.
- [x] Capability discovery reports runtime version, supported ABI range, grammar ABI/semantic version and compatibility errors.
- [x] ABI compatibility is enforced before a grammar is used.
- [x] GDScript (`.gd`) is registered as an optional discoverable provider without an implicit source/Git dependency.
- [x] `TreeSitterParserService` performs tolerant parsing and named-node extraction even when syntax contains errors.
- [x] `IncrementalParseSession` uses `Tree.edit()` + `Parser.parse(old_tree=...)` and reports `changed_ranges`.
- [x] `ParserTool` confines file parsing to `WorkspaceBoundary` and applies a maximum source-size limit.
- [x] Structured tools `kodecode_parser_capabilities` and `kodecode_parser_parse` are exposed through `KodeCodeToolAPI`.
- [x] Tests parse Python, JavaScript, TypeScript and TSX with their real installed grammars.
- [x] Tests cover malformed-source tolerance, incremental edits, changed ranges, provider discovery and structured invocation.
- [ ] Final Repository Guard / Python Core Windows+Ubuntu / UI Smoke evidence on the R4.2 head.

### R4.2 dependency/ABI policy

- Current Python runtime family: Tree-sitter 0.26.x.
- Runtime supported grammar ABI range is discovered at runtime; for Tree-sitter 0.26.0 this is ABI 13..15.
- A grammar outside the runtime-supported ABI interval is reported incompatible and is not loaded.
- Language packages are lazy-loaded; base Kodepoia can run without the `code` extra.
- GDScript grammar support is intentionally provider-based until a reproducible Python wheel/distribution policy is accepted; no runtime Git download is introduced by R4.2.

## Remaining R4 work

### R4.3 — LSP — PENDING
- [ ] JSON-RPC transport abstraction.
- [ ] Server lifecycle/capabilities.
- [ ] document symbols / definitions / references / diagnostics baseline.
- [ ] Protected process launch through tool/sandbox boundary.

### R4.4 — DAP — PENDING
- [ ] DAP framing and session abstraction.
- [ ] launch/attach capability representation.
- [ ] breakpoints, stack, scopes/variables baseline.
- [ ] Protected adapter launch through tool/sandbox boundary.

### R4.5 — Code intelligence graphs — PENDING
- [ ] Symbol graph.
- [ ] Call graph.
- [ ] Dependency/import graph.
- [ ] Stable IDs/provenance and incremental refresh.

### R4.6 — Orchestration + acceptance — PENDING
- [ ] Wire KodeCode structured catalog into agent/orchestrator tool execution.
- [ ] Enforce Guardian/permissions/SafeChange policy for mutating tools.
- [ ] Repository-scale acceptance scenarios.
- [ ] Windows + Ubuntu CI acceptance evidence.

## Current acceptance decision

R4 remains **IN PROGRESS**, not COMPLETE. R4.1 is accepted and merged on `main`. R4.2 is implemented but must remain **PENDING ACCEPTANCE** until the exact R4.2 head has green Repository Guard, Python Core on Windows+Ubuntu and KodeStudio UI Smoke. LSP/DAP/graphs/orchestration are still pending.

## Reference research used for implementation

- py-tree-sitter 0.26.0 documents `LANGUAGE_VERSION=15`, `MIN_COMPATIBLE_LANGUAGE_VERSION=13`, `Language.abi_version`, `Parser.parse(..., old_tree=...)`, `Tree.edit()` and `Tree.changed_ranges()`.
- PyPI publishes precompiled Python wheels for `tree-sitter`, `tree-sitter-python`, `tree-sitter-javascript` and `tree-sitter-typescript` on supported major platforms.
- PrestonKnopp/tree-sitter-gdscript is an active MIT GDScript grammar listed in the Tree-sitter parser ecosystem, but R4.2 does not make its source repository a runtime dependency.
