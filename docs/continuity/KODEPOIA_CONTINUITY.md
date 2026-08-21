# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 21 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. R1/R2/R3 COMPLETE. **R4 KodeCode IN PROGRESS**. R4.1/R4.2/R4.3 sont ACCEPTED AND MERGED. **R4.4 DAP est IMPLEMENTED / PENDING CI ACCEPTANCE** sur `agent/r4-4-dap`. R4.5/R4.6 non commencés.

## Source de vérité et contraintes

- Dépôt `LaurentCOLL1/Kodepoia`, visibilité **PUBLIC volontairement**.
- `main` avant R4.4 : `cdec758a2dfd024c978c1c1a932a61af0213c7fa`.
- Branche active : `agent/r4-4-dap`.
- Modèles : KodeFast=`granite4.1:3b`, KodeCore=`gpt-oss:20b`, KodeCoder=`ornith:9b`.
- Git/repository/software-engineering non trivial ne doit pas être routé vers Granite.

## R4.1/R4.2/R4.3

R4.1 PR #11 merged. R4.2 PR #13 merged. R4.3 PR #15 merged (`1074533e9930549b71af281003b74c6ed049ba9b`). LSP dispose du framing partagé, processus stdio persistants sandboxés, lifecycle/navigation/diagnostics et Tool API structurée.

## R4.4 — IMPLEMENTED / PENDING CI ACCEPTANCE

Implemented:
- DAP request/response/event session over shared R4.3 framing;
- initialize capability negotiation;
- launch/attach only from pre-registered `DebugConfigurationSpec` selected by `config_id`;
- breakpoints + configurationDone;
- threads → stackTrace → scopes → variables;
- event capture + disconnect;
- explicit adapter registry and `ProcessSandbox.spawn_piped()` launch;
- adapter→client execution requests (`runInTerminal`) rejected in baseline;
- breakpoint paths workspace-confined;
- structured DAP tools expose no argv or arbitrary launch arguments;
- deterministic tests for lifecycle, waterfall, security and API schemas.

Do not mark R4.4 ACCEPTED before Repository Guard, Python Core Ubuntu+Windows and UI Smoke succeed on the exact final head.

## Next sequence

1. R4.4 CI/merge.
2. R4.5 symbol/call/dependency graphs + stable provenance + incremental refresh.
3. R4.6 orchestrator Tool API execution + Guardian/Permissions/SafeChange + repository-scale final acceptance.
4. Mark R4 COMPLETE only after final R4.6 acceptance and CI.

## Permanent rules

Update continuity in same cycle for phase/PR/acceptance changes. Never mark COMPLETE from partial CI. Preserve Guardian/Sandbox/Secrets/Health/Budget. No direct system access outside Tool API. Public repository visibility is intentional.
