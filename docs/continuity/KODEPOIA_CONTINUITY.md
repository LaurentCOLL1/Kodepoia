# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3/R4 sont **COMPLETE**. **R4 — KodeCode a passé son acceptation finale et toutes les sous-phases R4.1 à R4.6 sont ACCEPTED AND MERGED.** La prochaine phase autorisée est **R5 — KodeGodot 4.7.x**, actuellement **AUTHORIZED / NOT STARTED**. Lire architecture, ADR, roadmap, `R4_STATUS.md`, puis ce fichier avant de reprendre. Ne pas rouvrir R4 sans nouvelle preuve ou ADR.

## Source de vérité et contraintes

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : **PUBLIC volontairement** ; ne pas traiter ce choix comme une anomalie.
- Source de vérité active après la clôture R4 : `main`.
- R4.6 PR #19 — **MERGED**.
- R4.6 merge commit : `80931d3f4302456783a884f117976ad0f4fed340`.
- Architecture : v1.0 gelée.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local acceptance passed.
- R4 : **COMPLETE — final governed orchestration acceptance passed**.
- R5 : **AUTHORIZED / NOT STARTED**.
- Modèles acceptés : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste candidat futur KodeDeepCoder.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4 — KodeCode — COMPLETE

### R4.1 — ACCEPTED AND MERGED

PR #11, merge `91f3d77cc375021efcb24172b2859a27748843b8`.

WorkspaceBoundary, safe file list/read/search, patch atomique avec stale protection, Git worktrees via ProcessSandbox, structured Tool API, protections symlink/path/injection.

### R4.2 — ACCEPTED AND MERGED

PR #13, merge `ae1cfaa914962dec75950ec11d609c6b6fb929fb`.

Tree-sitter provider registry, ABI checks, Python/JavaScript/TypeScript/TSX, optional GDScript provider, tolerant parsing, incremental parse (`Tree.edit` + `Parser.parse(old_tree=...)` + changed ranges), bounded parser tools.

### R4.3 — ACCEPTED AND MERGED

PR #15, merge `1074533e9930549b71af281003b74c6ed049ba9b`.

LSP: bounded Content-Length JSON framing, timeout channel, persistent sandboxed stdio processes, explicit server registry, initialize/initialized/shutdown/exit, symbols/definitions/references/diagnostics and structured LSP tools.

Final accepted head `36c53f3d5af53ec63977dd71260055df0b1c3181`:
- Repository Guard `32513904670` SUCCESS;
- Python Core `32513904676` SUCCESS Ubuntu+Windows;
- UI Smoke `32513904762` SUCCESS Windows.

### R4.4 — ACCEPTED AND MERGED

PR #17, merge `0b16277c00782382780c2b5f2b1aa7a616b4f9da`.

DAP: initialize, pre-registered launch/attach configs, breakpoints/configurationDone, threads/stack/scopes/variables, protected adapter launch, workspace-confined source paths and default refusal of adapter-originated execution such as `runInTerminal`.

Final accepted head `084ad9d83515067a63e2d02c0e3689ce368f74bc`:
- Repository Guard `32514727455` SUCCESS;
- Python Core `32514727480` SUCCESS Ubuntu+Windows;
- UI Smoke `32514727690` SUCCESS Windows.

### R4.5 — ACCEPTED AND MERGED

PR #18, merge `344a29022c6e96f447944d3e064ebeb1933a4600`.

Tree-sitter-backed symbol/call/dependency graphs, deterministic stable IDs/provenance, conservative call resolution, SHA incremental refresh, bounded graph tools. Acceptance found and fixed the `WorkspaceBoundary.resolve(must_exist=True)` escaped-missing-path ordering bug: confinement is now checked before strict filesystem resolution.

Final accepted head `af75e5277b86974e02c5c37c3e78e99f445b4aac`:
- Repository Guard `32519472687` SUCCESS;
- Python Core `32519472699` SUCCESS Ubuntu+Windows;
- UI Smoke `32519472724` SUCCESS Windows.

### R4.6 — ACCEPTED AND MERGED

PR #19, merge `80931d3f4302456783a884f117976ad0f4fed340`.

Implemented and accepted:
- `KodeCodeExecutor` composes base KodeCode + graph catalogs;
- every exposed tool must have explicit `ToolPolicy` classification;
- Guardian + PermissionSet authorization before execution;
- SafeChange snapshot before protected patch mutation;
- Git/LSP/DAP execution still requires PROCESS_EXECUTE and existing ProcessSandbox/allowlist boundaries;
- append-only tamper-evident AuditLog records governance outcomes without raw argument values;
- Orchestrator supplies tool catalog to tool-capable Brain calls when executor configured;
- explicit `execute_tool()` / `execute_tool_calls()` supports Ollama-style function calls without hidden autonomous execution loop;
- deterministic repository-scale acceptance creates 30 Python modules and validates read/search/parse/graphs, calls/dependencies, incremental skip, snapshot, stable IDs and audit chain;
- denial paths validate missing FILE_WRITE and PROCESS_EXECUTE permissions.

Final accepted R4.6 head `ba23422981d0bc5dce35b4f6714705a82bea64b6`:
- Repository Guard `32520187214` — **SUCCESS**;
- Python Core `32520187196` — **SUCCESS** Ubuntu+Windows;
- KodeStudio UI Smoke `32520187172` — **SUCCESS** Windows.

## R4 acceptance decision

Frozen R4 scope is fully covered:
- files/search/patch: PASS;
- Git worktrees: PASS;
- Tree-sitter: PASS;
- LSP: PASS;
- DAP: PASS;
- symbol/call/dependency graphs: PASS;
- structured tool boundary/no direct model system access: PASS;
- Guardian/Permissions/SafeChange orchestration: PASS;
- repository-scale acceptance: PASS;
- Windows+Ubuntu acceptance: PASS.

Therefore **R4 = COMPLETE**.

## Next sequence

1. Merge the R4 post-merge completion normalization PR into `main` after all required checks are green.
2. After that merge, `main` is the sole source of truth and **R5 KodeGodot 4.7.x is AUTHORIZED / NOT STARTED**.
3. Start R5 only on a new branch from that normalized `main`.

## Permanent rules

Update continuity in the same cycle for phase/PR/acceptance/prerequisite changes. Never declare COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Do not return to R4 except for a demonstrated regression or an ADR-worthy architecture change.
