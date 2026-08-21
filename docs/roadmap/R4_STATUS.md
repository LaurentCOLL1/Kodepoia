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
- R0 Repository Guard `32508868032` — SUCCESS.
- Python Core `32508868396` — SUCCESS Ubuntu + Windows.
- KodeStudio UI Smoke `32508868371` — SUCCESS Windows.

Implemented: workspace confinement, safe file read/list/search, exact atomic patching with stale-content protection, ProcessSandbox-backed Git worktrees, explicit structured Tool API, path/symlink/injection hardening and tests.

## R4.2 — Tree-sitter parser layer

**Status: ACCEPTED AND MERGED TO `main`.**

Integration evidence:
- PR #13 — `R4.2 Tree-sitter parser layer` — MERGED.
- Merge commit: `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.
- Final accepted branch head: `d76824deadc52724411f2ea9b6d5548be6c74432`.
- R0 Repository Guard `32511436827` — SUCCESS on final head.
- Python Core `32511437141` — SUCCESS Ubuntu + Windows on final head with `.[dev,code]`.
- KodeStudio UI Smoke `32511437097` — SUCCESS Windows on final head.

Implementation:
- [x] Optional `code` extra uses `tree-sitter>=0.26,<0.27`.
- [x] Packaged grammar providers: Python 0.25.x, JavaScript 0.25.x, TypeScript/TSX 0.23.2.x.
- [x] Provider-based `TreeSitterLanguageRegistry` with aliases, extension detection, dynamic registration and collision checks.
- [x] Capability discovery reports runtime version, supported ABI range, grammar ABI/semantic version, compatibility and errors.
- [x] ABI compatibility is enforced before a grammar is used.
- [x] GDScript (`.gd`) is registered as an optional discoverable provider without an implicit source/Git runtime dependency.
- [x] `TreeSitterParserService` performs tolerant parsing and named-node extraction on valid or malformed syntax.
- [x] `IncrementalParseSession` uses `Tree.edit()` + `Parser.parse(old_tree=...)` and exposes `changed_ranges`.
- [x] `ParserTool` confines file parsing to `WorkspaceBoundary`, with source-size and node-count limits.
- [x] Structured tools `kodecode_parser_capabilities` and `kodecode_parser_parse` are exposed through `KodeCodeToolAPI`.
- [x] Tests load and parse real Python, JavaScript, TypeScript and TSX grammars.
- [x] Tests cover ABI checks, malformed-source tolerance, incremental edits, changed ranges, GDScript discovery, provider extensibility and structured invocation.

### R4.2 dependency/ABI policy

- Current Python runtime family: Tree-sitter 0.26.x.
- Supported grammar ABI range is discovered at runtime; Tree-sitter 0.26.0 reports ABI 13..15.
- Grammars outside the supported runtime ABI interval are reported incompatible and refused.
- Grammar providers are lazy-loaded so base Kodepoia can still start without the `code` extra.
- GDScript stays provider-based until a reproducible Python distribution path is adopted; no silent runtime Internet/Git install is allowed.

## Remaining R4 work

### R4.3 — LSP — NEXT / NOT STARTED
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

R4 remains **IN PROGRESS**, not COMPLETE. R4.1 and R4.2 are accepted and merged on `main`. R4.3 LSP is the next authorized sub-phase and is **NOT STARTED**. DAP, graphs and final orchestration/acceptance remain pending.

## Reference research used for implementation

- py-tree-sitter 0.26.x documents runtime ABI compatibility metadata, `Parser.parse(..., old_tree=...)`, `Tree.edit()` and `Tree.changed_ranges()`.
- PyPI publishes binary wheels for the selected Python/JavaScript/TypeScript grammar packages on supported major platforms; Windows + Ubuntu were verified by CI.
- GDScript is recognized as a Tree-sitter provider target but is not made a hidden network/runtime dependency.
