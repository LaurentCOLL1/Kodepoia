# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS et R6.1 — KodeHealth foundation est COMPLETE.** R6.1 a été acceptée sur le head `802de4ba3110ace657c4e16306a0ca29850ce2bd` après CI finale verte, puis PR #30 a été fusionnée dans `main` en `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`. La source de vérité fusionnée reste `main`. Ne pas rouvrir R5 ou R6.1 sans régression démontrée ou changement d'architecture nécessitant un ADR. Lire architecture, ADR, roadmap, `R5_STATUS.md`, `R6_STATUS.md`, `R6_1_ACCEPTANCE.md`, puis ce fichier avant de reprendre.

## Source de vérité et état des phases

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : PUBLIC volontairement.
- Architecture : v1.0 gelée.
- Source de vérité fusionnée : `main`.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local model acceptance passed.
- R4 : COMPLETE — governed KodeCode acceptance passed.
- R5 : COMPLETE — KodeGodot 4.7.x hardware-local acceptance passed and PR #28 merged.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merged as `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R7–R16 : PENDING according to the frozen roadmap.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not be routed to Granite.

## Permanent architecture/security boundary

Kodepoia must continue using the governed layers established in R1–R4:

- `WorkspaceBoundary` for path confinement;
- `ProcessSandbox` plus the global KillSwitch for process execution;
- structured Tool APIs rather than arbitrary model-supplied commands;
- Guardian and `PermissionSet` authorization;
- SafeChange snapshots before sensitive mutations;
- AuditLog hash-chain logging;
- Secrets/Health/Budget boundaries from the frozen architecture.

No later phase may bypass these controls merely because an external engine/tool has its own API or CLI.

## R5 — KodeGodot 4.7.x — COMPLETE

Accepted and merged subdivisions:

- R5.1 Engine/project foundation — PR #22.
- R5.2 Scene/resource intelligence — PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`.
- R5.3 GDScript + Godot LSP/DAP — PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`.
- R5.4 2D/3D intelligence + safe edits — PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`.
- R5.5 automation/import/export/capture/benchmark — PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.
- R5.6 governed orchestration + real Godot acceptance — PR #28, merge `ecb0455d179c8c0b2de0a5d1d8a496a0f8f980e8`.

### Target workstation accepted for R5

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- ports LSP `6005`, DAP `6006`, debug `6007`;
- renderer/device observed during Movie Maker acceptance: AMD Radeon RX 6750 XT.

### Final hardware-local evidence

Generated `2026-08-22T06:49:29.198572+00:00`:

```text
probe_only=false
acceptance_completed=true
passed=19
failed=0
total=19
```

All real gates passed: Godot version, project/scene/GDScript inspection, GDScript `--check-only`, import, smoke, benchmark, Movie Maker capture, governed scene edit with SafeChange snapshot, LSP startup/symbols/diagnostics, DAP initialize/launch/threads, Windows release export and AuditLog verification.

Concrete evidence:

- benchmark ~101.0 effective FPS on the disposable 120-frame fixture;
- AVI `.kodepoia/captures/r5-acceptance.avi` = **64,612 bytes**;
- `snapshot_created=true` for governed scene edit;
- LSP and DAP initialized on loopback;
- DAP project launch PASS;
- DAP thread ID 1 name `Main`;
- release EXE `.kodepoia/exports/r5-acceptance.exe` = **109,127,680 bytes**;
- audit chain `valid=true`.

### Important R5 defects that must not regress

1. Foreground `ProcessSandbox.run()` must drain stdout/stderr while waiting via `communicate(timeout=...)`; polling for exit before reading PIPEs can deadlock verbose processes.
2. Long-lived socket services must use the sandboxed background-process path when stdio is not their protocol; do not leave unread stdout/stderr PIPEs.
3. Godot Movie Maker capture must not combine normal capture with headless/dummy rendering when real rendered frames are required.
4. TCP connect timeouts must not remain as protocol-read timeouts after the LSP/DAP socket is established.
5. DAP launch must support deferred response sequencing: send launch, complete initialization/configuration including `configurationDone`, then consume the launch response; do not assume launch always responds before `configurationDone`.
6. Godot services remain loopback-only; model input must not expose arbitrary host, argv, command, program or cwd fields.

### Final supporting CI before PR #28 merge

PR #28 head `8e9f01d785a691ce03d3b589367b724b073c8cec`:

- R0 Repository Guard `32557370901` — SUCCESS;
- Python Core `32557370829` — SUCCESS Windows + Ubuntu and PowerShell validation;
- KodeStudio UI Smoke `32557370915` — SUCCESS Windows.

## R6 — Quality / Health / Budget / CI — IN PROGRESS

### R6.1 — KodeHealth foundation — COMPLETE

Accepted implementation head: `802de4ba3110ace657c4e16306a0ca29850ce2bd`.  
Merged PR: **#30**.  
Merge commit: `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.

Delivered and accepted:

- `src/kodepoia/quality/health.py` with the 14 frozen-architecture health dimensions;
- explicit `unknown/pass/warn/fail` states, deterministic score and coverage calculation, and blocking failures;
- exhaustive report validation and JSON round-trip;
- serialized `blockers` and `unknown_dimensions` consistency checks;
- `HealthStore` writing only to `.kodepoia/health/`, with atomic `latest.json` and timestamped snapshots;
- reuse of `WorkspaceBoundary`, including rejection of `.kodepoia` symlink escape;
- `schemas/health-report-v1.schema.json`;
- focused R6.1 tests and documented rollback.

Final acceptance evidence:

- isolated R6.1 tests after hardening: **9 passed**;
- R0 Repository Guard `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu, including PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows;
- PR #30 merged only after those final-head gates passed.

**R6.1 is COMPLETE. R6 remains IN PROGRESS.**

## Next phase action

Continue R6 only from the normalized current `main`, on a dedicated branch. The remaining frozen R6 scope includes Budget, Tests, Regression, VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity baseline, Privacy baseline, License/BOM, and major-patch validation/rollback. Do not skip directly to R7.

## User operational preference — permanent

Whenever the user must perform a manual operation, explain the reason, prerequisites, exact commands/actions, expected output, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat information already known.

## Permanent process rules

Update this continuity file in the same work cycle whenever phase status, PR state, hardware acceptance, prerequisites or important recovered defects change. Never declare a phase COMPLETE from partial CI. Use exact acceptance evidence where required, but do not write self-invalidating instructions that tell a future session to reset to an old branch head. Preserve the frozen architecture unless an ADR explicitly authorizes a change.
