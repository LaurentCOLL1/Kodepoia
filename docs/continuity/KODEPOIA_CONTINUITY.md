# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3 COMPLETE. **R4 KodeCode IN PROGRESS**. R4.1, R4.2 et **R4.3 LSP sont ACCEPTED AND MERGED**. La prochaine sous-phase est **R4.4 DAP — NEXT / NOT STARTED**. Lire architecture, ADR, roadmap, `R4_STATUS.md`, puis ce fichier.

## Source de vérité

- Dépôt `LaurentCOLL1/Kodepoia`, visibilité **PUBLIC volontairement**.
- Source active : `main`.
- R4.3 merge : `1074533e9930549b71af281003b74c6ed049ba9b`, PR #15 MERGED.
- R1/R2/R3 COMPLETE ; R4 IN PROGRESS.
- R4.1/R4.2/R4.3 ACCEPTED AND MERGED.
- R4.4 NEXT / NOT STARTED ; R4.5/R4.6 PENDING.
- Modèles : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.

## R4.1
PR #11 merged. WorkspaceBoundary, safe files/search/patch, Git worktrees via ProcessSandbox, structured Tool API.

## R4.2
PR #13 merged. Tree-sitter 0.26.x, Python/JavaScript/TypeScript/TSX, provider registry, ABI checks, tolerant + incremental parsing, optional GDScript provider.

## R4.3 — ACCEPTED AND MERGED

PR #15 merged, commit `1074533e9930549b71af281003b74c6ed049ba9b`.
Implemented: bounded Content-Length JSON framing, timeout channel, persistent sandboxed stdio process sessions, explicit language-server registry, LSP lifecycle, symbols/definitions/references/diagnostics, workspace-confined didOpen URIs, structured LSP tools.

Final CI head `36c53f3d5af53ec63977dd71260055df0b1c3181`:
- Repository Guard `32513904670` SUCCESS;
- Python Core `32513904676` SUCCESS Ubuntu+Windows;
- UI Smoke `32513904762` SUCCESS Windows.

## Next sequence

1. R4.4 DAP: framing/session reuse, initialize, launch/attach, breakpoints, threads, stack, scopes, variables, protected adapter launch.
2. R4.5 graphs: symbol/call/dependency graphs, stable IDs/provenance, incremental refresh.
3. R4.6: orchestrator Tool API wiring, Guardian/permissions/SafeChange for mutations, repository-scale acceptance, final R4 CI.
4. Mark R4 COMPLETE only after R4.6 acceptance.

## Permanent rules

Update continuity in the same cycle for phase/PR/acceptance/prerequisite changes. Never mark COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional. Git/repository/software-engineering non trivial must not be routed to Granite.
