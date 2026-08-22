# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 — KodeHealth, R6.2 — KodeBudget et R6.3 — KodeTests + KodeRegression sont COMPLETE.** Par demande explicite de l'utilisateur, R6 est maintenant ramenée sous la règle de planification détaillée avant R6.4 : lire `docs/roadmap/R6_PLAN.md`, `docs/roadmap/R6_STATUS.md`, les acceptances R6.1–R6.3, l'architecture gelée et ce fichier avant toute reprise. Le plan fige R6.1–R6.12. **Ne pas commencer R6.4 avant que la PR contenant `R6_PLAN.md` ait passé tous ses checks final-head et soit fusionnée/normalisée dans `main`.** Ne pas rouvrir R1–R6.3 sans régression démontrée ou ADR requis, et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état des phases

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité fusionnée : `main`.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local model acceptance passed.
- R4 : COMPLETE — governed KodeCode acceptance passed.
- R5 : COMPLETE — KodeGodot 4.7.x hardware-local acceptance passed.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6.4–R6.12 : PLANNED in `docs/roadmap/R6_PLAN.md`.
- R7–R16 : PENDING according to the frozen roadmap.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not be routed to Granite.

## Permanent architecture/security boundaries

Kodepoia must continue using the governed layers established in R1–R4:

- `WorkspaceBoundary` for path confinement;
- `ProcessSandbox` plus global KillSwitch for process execution;
- structured Tool APIs rather than arbitrary model-supplied commands;
- Guardian and `PermissionSet` authorization;
- SafeChange snapshots before sensitive mutations;
- AuditLog hash-chain logging;
- Secrets redaction and exclusion from model context / persistent memory;
- Schema/DataGovernance discipline;
- Health/Budget/Test/Regression evidence must remain structured and validated;
- no later phase may bypass these controls because an external engine/tool has its own API or CLI;
- platform-aware behavior: non-target platforms must not impose requirements, dependencies, inputs, budgets or tests.

## R5 — KodeGodot 4.7.x — COMPLETE

Accepted subdivisions:

- R5.1 Engine/project foundation — PR #22.
- R5.2 Scene/resource intelligence — PR #24, merge `7720bfc90951e2180b909004b7fa8320d93a6e27`.
- R5.3 GDScript + Godot LSP/DAP — PR #25, merge `d2641862b98a969b9adfc905f818e01b3d7e4730`.
- R5.4 2D/3D intelligence + safe edits — PR #26, merge `b81cf430249e341219dcb759cb49f67697c27782`.
- R5.5 automation/import/export/capture/benchmark — PR #27, merge `c4409c78eacfa1777d22d7e0995d4db7dbdaa5a2`.
- R5.6 governed orchestration + real Godot acceptance — PR #28, merge `ecb0455d179c8c0b2de0a5d1d8a496a0f8f980e8`.

Accepted workstation / real-engine evidence:

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- LSP 6005 / DAP 6006 / debug 6007;
- AMD Radeon RX 6750 XT observed during rendered Movie Maker acceptance;
- `probe_only=false`, `acceptance_completed=true`, 19 PASS / 0 FAIL / 19;
- ~101 effective FPS on disposable benchmark fixture;
- AVI capture 64,612 bytes;
- governed scene edit with SafeChange snapshot;
- loopback LSP/DAP and DAP thread `Main`;
- Windows release export 109,127,680 bytes;
- valid AuditLog chain.

### R5 anti-regression defects — permanent

1. `ProcessSandbox.run()` must drain stdout/stderr through `communicate(timeout=...)`; never poll exit before draining PIPEs.
2. Long-lived socket services must use the sandboxed background-process path when stdio is not their protocol.
3. Godot Movie Maker real capture must not combine rendered capture with headless/dummy rendering.
4. TCP connection timeout must not remain the protocol-read timeout after LSP/DAP connection establishment.
5. DAP launch must support deferred sequencing through `configurationDone` before consuming deferred launch response.
6. Godot services remain loopback-only; model input must not expose arbitrary host/argv/command/program/cwd fields.

## R6 — Quality / Health / Budget / CI — IN PROGRESS

### Authoritative detailed plan

`docs/roadmap/R6_PLAN.md` is the exhaustive R6 recovery/execution plan. It is a retroactive exception created by explicit user request because R6.1–R6.3 predated the permanent phase-plan rule. It records those completed subdivisions without reopening them and freezes the remaining structure before R6.4.

Complete R6 structure:

1. R6.1 — KodeHealth foundation — COMPLETE — manual `NONE`.
2. R6.2 — KodeBudget foundation — COMPLETE — manual `NONE`.
3. R6.3 — KodeTests + KodeRegression foundation — COMPLETE — manual `NONE`.
4. R6.4 — KodeVisualQA foundation — PLANNED — manual `REQUIRED`.
5. R6.5 — KodeAccessibility foundation — PLANNED — manual `REQUIRED`.
6. R6.6 — KodeLocalization + pseudo-localization foundation — PLANNED — manual `NONE`.
7. R6.7 — KodeTechnicalDebt foundation — PLANNED — manual `NONE`.
8. R6.8 — KodeCI + KodeBuild foundation — PLANNED — manual `CONDITIONAL`.
9. R6.9 — KodeAppSecurity baseline — PLANNED — manual `NONE`.
10. R6.10 — KodePrivacy baseline — PLANNED — manual `NONE`.
11. R6.11 — KodeLicense + KodeBOM foundation — PLANNED — manual `CONDITIONAL`.
12. R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — PLANNED — manual `CONDITIONAL`.

Do not add/remove/merge/split/renumber a subdivision silently. Update `R6_PLAN.md` and continuity in the same work cycle; architecture changes require ADR.

### R6.1 — KodeHealth foundation — COMPLETE

Accepted head `802de4ba3110ace657c4e16306a0ca29850ce2bd`, merged by PR #30 as `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.

Accepted scope: 14 frozen health dimensions; `unknown/pass/warn/fail`; score/coverage; blocking failures; exhaustive report validation; atomic `.kodepoia/health/` persistence through `WorkspaceBoundary`; symlink escape rejection; health-report-v1 schema.

Final evidence:

- isolated hardened R6.1 tests: 9 PASS;
- R0 `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows.

### R6.2 — KodeBudget foundation — COMPLETE

Accepted head `8ac3772e98c70260c320519a214bb25b6cedbb38`, merged by PR #32 as `65510a9b116d9c48b185a0edb51d99e5b951200a`.

Accepted scope: 16 architecture-aligned budget metrics; target/hard-limit semantics; Project DNA derivation for FPS/frame time/RAM/VRAM/build size; explicit unknown coverage; blocking failures; validated report round-trip; `.kodepoia/budgets/` through `WorkspaceBoundary`; budget-report-v1 schema.

Final evidence:

- isolated derivation/evaluation/persistence smoke: PASS;
- R0 `32561719921` / #603 — SUCCESS Windows + Ubuntu;
- Python Core `32561719925` / #577 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561720008` / #544 — SUCCESS Windows.

### R6.3 — KodeTests + KodeRegression foundation — COMPLETE

Accepted head `7150237c263dd3ac96af4662d74909e05f3cf991`, merged by PR #34 as `6657b258f2396b3d6a3850153b1ffaae1951104d`.

Accepted scope: stable test IDs; `pass/fail/error/skip`; deterministic run aggregation; validated counts/duration; `.kodepoia/tests/runs/`; baseline/current comparison; `unchanged/regressed/fixed/added/removed`; removed/skipped known tests cannot hide regressions; `.kodepoia/tests/regression/`; test-run-report-v1 and regression-report-v1 schemas; no new arbitrary command-execution path.

Final evidence:

- isolated baseline/current comparison and persistence smoke: PASS;
- R0 `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows.

## Manual-intervention forecast for remaining R6

The user must be warned before each required/conditional gate and receive exact copy-paste commands/actions, expected output, recovery and evidence instructions.

- **R6.4 REQUIRED:** real Windows/Godot rendered visual-regression run on the accepted workstation. Do not substitute headless/dummy capture.
- **R6.5 REQUIRED:** real interactive Windows keyboard-only + Narrator accessibility checklist.
- **R6.8 CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively satisfy build/reproducibility DoD.
- **R6.11 CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved after trusted metadata/source inspection.
- **R6.12 CONDITIONAL:** local integration/approval only if the final major-patch gate selects a hardware-local or user-approval-required path.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

The exact planned manual command contracts and failure-recovery procedures are in `R6_PLAN.md`. When a gate is reached, replace plan placeholders with the exact final accepted head and implementation-specific details before asking the user to execute anything.

## Current external reference baselines for R6 planning

These references guide applicable checks without replacing frozen architecture or imposing irrelevant platform requirements:

- accessibility: W3C WCAG 2.2 current Recommendation baseline;
- application security: OWASP ASVS 5.0.0 current stable baseline for applicable web/API/auth/security surfaces;
- BOM: SPDX 3.0 current stable baseline; SPDX 3.1 RC1 is not authoritative for R6 stable acceptance.

## Next phase action

Complete and merge/normalize the `R6_PLAN.md` planning PR first. **Only then start R6.4 from the normalized resulting `main`.** R6.4 must be implemented exactly against the plan unless a governed plan change is recorded first. Do not start R7.

## User operational preference — permanent

Whenever the user must perform a manual operation, explain the reason, prerequisites, exact commands/actions, expected output, error recovery, what to send back, what must not be done yet, and privacy/security redaction requirements. Never ask for passwords, tokens, private keys or unrelated personal data. Do not ask the user to repeat information already known.

## Permanent phase-start planning rule — mandatory

This rule was adopted through PR #36, merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9`, and applies to every newly started major phase from R7 onward. R6 is the explicit retroactive exception requested by the user.

1. Before implementing `RX.1`, create `docs/roadmap/RX_PLAN.md` from `PHASE_PLAN_TEMPLATE.md` on a planning branch from normalized `main`.
2. Enumerate all planned `RX.N` up front and detail objective, scope, dependencies, implementation, deliverables, acceptance, evidence, rollback, risks and manual gates.
3. Every subdivision is `NONE`, `REQUIRED` or `CONDITIONAL` for manual intervention.
4. For REQUIRED/CONDITIONAL, document reason, prerequisites, exact commands/actions, expected output, failure recovery, exact evidence, do-not-do-yet instructions and privacy/security requirements before the manual gate.
5. Planning PR final-head checks must pass and the plan must merge before `RX.1` begins.
6. Keep plan and continuity synchronized whenever scope/status/prerequisites/manual requirements/important defects change.
7. Added/removed/merged/split/renumbered subdivisions require explicit plan+continuity rationale; architecture change requires ADR.
8. Major phase COMPLETE only when every planned subdivision is COMPLETE or explicitly removed by recorded decision.

## Permanent process rules

- Update continuity and the active phase plan in the same work cycle whenever phase/subdivision status, PR state, hardware acceptance, prerequisites, manual-intervention requirements or important defects change.
- Never declare a phase/subdivision COMPLETE from partial CI.
- Use exact acceptance head/PR/run evidence.
- Preserve frozen architecture unless an ADR explicitly authorizes a foundation change.
- No manual acceptance by inference from silence, partial logs or wrong-environment evidence.
- Never start a new major phase implementation before its plan PR is merged to normalized `main`.
