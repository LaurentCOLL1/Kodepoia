# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3 COMPLETE. **R4 KodeCode est en FINAL ACCEPTANCE**. R4.1/R4.2/R4.3/R4.4/R4.5 sont ACCEPTED AND MERGED. **R4.6 governed orchestration est IMPLEMENTED / FINAL CI ACCEPTANCE PENDING** sur `agent/r4-6-orchestration`. Ne marquer R4 COMPLETE qu'après CI exacte, merge de la PR R4.6 et normalisation post-merge sur `main`.

## Source de vérité et contraintes

- Dépôt `LaurentCOLL1/Kodepoia`, visibilité **PUBLIC volontairement**.
- `main` après R4.5 : `344a29022c6e96f447944d3e064ebeb1933a4600`.
- Branche active : `agent/r4-6-orchestration`.
- R4.5 PR #18 MERGED.
- Modèles : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4.1 à R4.5 — ACCEPTED AND MERGED

- R4.1 PR #11: workspace/files/search/patch/Git worktrees + structured Tool API.
- R4.2 PR #13: Tree-sitter providers, ABI checks, tolerant/incremental parsing.
- R4.3 PR #15: LSP framing, persistent sandboxed stdio, lifecycle/navigation/diagnostics.
- R4.4 PR #17: DAP initialize, pre-registered launch/attach configs, breakpoints, stack/scopes/variables, runInTerminal refusal.
- R4.5 PR #18, merge `344a29022c6e96f447944d3e064ebeb1933a4600`: symbol/call/dependency graphs, stable IDs/provenance, SHA incremental refresh, bounded graph tools, WorkspaceBoundary escaped-missing-path hardening.

R4.5 final accepted head `af75e5277b86974e02c5c37c3e78e99f445b4aac`:
- Repository Guard `32519472687` SUCCESS;
- Python Core `32519472699` SUCCESS Ubuntu+Windows;
- UI Smoke `32519472724` SUCCESS Windows.

## R4.6 — IMPLEMENTED / FINAL CI ACCEPTANCE PENDING

Implemented:
- `KodeCodeExecutor` composes the base KodeCode catalog and `GraphToolAPI` catalog;
- every exposed tool must be explicitly classified by `ToolPolicy`; missing policy aborts executor construction;
- READ / WRITE / EXECUTE effects map to Guardian `ActionType`;
- Guardian + PermissionSet authorization before every tool execution;
- file path authorization uses workspace-resolved paths;
- `kodecode_patch_replace_once` snapshots the existing target through `SafeChangeManager` before mutation;
- Git/LSP/DAP execution operations require PROCESS_EXECUTE and retain their own ProcessSandbox/allowlist protection;
- audit chain records denied/authorized/failed/completed outcomes without raw argument values;
- Orchestrator passes the composed catalog to tool-capable Brain calls only when a KodeCode executor is configured;
- Orchestrator exposes explicit `execute_tool()` and `execute_tool_calls()`; no hidden autonomous execution loop;
- Ollama-style nested function tool calls and JSON-string/object arguments supported;
- repository-scale test creates 30 Python modules and validates read/search/parse/graphs, dependency/call linking, incremental skip, stable symbol IDs after patch, SafeChange snapshot and audit verification;
- denial tests cover missing FILE_WRITE and PROCESS_EXECUTE;
- fake tool-calling Brain acceptance verifies catalog delivery and governed tool-call execution.

## Final R4 completion rule

1. Open R4.6 PR from `agent/r4-6-orchestration` to `main`.
2. Exact PR head must pass Repository Guard, Python Core Ubuntu+Windows and KodeStudio UI Smoke.
3. Fix any discovered defect and repeat on the new exact head.
4. Only after all checks are SUCCESS, mark R4.6 accepted and merge.
5. Create post-merge continuity/status normalization on `main`, recording final run IDs and merge commit.
6. That normalization must itself pass required checks and merge.
7. Then and only then set **R4 = COMPLETE** and authorize R5. R5 must not start earlier.

## Permanent rules

Update continuity in the same cycle for phase/PR/acceptance changes. Never mark COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional.
