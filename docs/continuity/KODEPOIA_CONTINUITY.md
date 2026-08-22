# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 KodeHealth, R6.2 KodeBudget et R6.3 KodeTests + KodeRegression sont COMPLETE. Le plan exhaustif `docs/roadmap/R6_PLAN.md` est ACCEPTED et fige R6.1–R6.12. R6.4 — KodeVisualQA foundation est IN PROGRESS sur `feature/r6-4-visualqa`, PR #39, depuis le main normalisé `e96e7c3b168975869c911f880044b7ef8e322157`.** R6.4 implémente le comparateur visuel déterministe, baseline immuable/hashée, masques hashés, diff PNG, schéma/report anti-tamper, hook R6.3, et une capture PNG Godot Movie Maker structurée/gouvernée séparée du contrat AVI R5. La PR #39 NE DOIT PAS être fusionnée et R6.5 NE DOIT PAS commencer avant CI verte sur le head final ET acceptation hardware-local Windows/Godot réelle. Lire `R6_PLAN.md`, `R6_STATUS.md`, `R6_4_DESIGN.md`, `R6_4_ACCEPTANCE.md`, les acceptances R6.1–R6.3, l'architecture gelée et ce fichier avant reprise. Ne pas rouvrir R1–R6.3 sans régression démontrée/ADR, ne pas renuméroter R6 sans mise à jour gouvernée, et ne pas passer à R7 avant R6 COMPLETE.

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture : v1.0 gelée le 21 août 2026.
- Source de vérité fusionnée : normalized current `main`.
- Base exacte de démarrage R6.4 : `e96e7c3b168975869c911f880044b7ef8e322157`.
- Branche active R6.4 : `feature/r6-4-visualqa`.
- PR active R6.4 : #39 — DO NOT MERGE until final-head CI + REQUIRED local acceptance.
- R1 : COMPLETE.
- R2 : COMPLETE.
- R3 : COMPLETE — hardware-local model acceptance passed.
- R4 : COMPLETE — governed KodeCode acceptance passed.
- R5 : COMPLETE — KodeGodot 4.7.x hardware-local acceptance passed.
- R6 : IN PROGRESS.
- R6.1 : COMPLETE — PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.
- R6.2 : COMPLETE — PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`.
- R6.3 : COMPLETE — PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`.
- R6 detailed plan : ACCEPTED — PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`.
- R6 plan post-merge normalization : PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.
- R6.4 : IN PROGRESS — PR #39 — manual `REQUIRED`, currently pending final-head CI then hardware-local evidence.
- R6.5–R6.12 : PLANNED in `docs/roadmap/R6_PLAN.md`.
- R7–R16 : PENDING.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` remains a future KodeDeepCoder candidate.
- Nontrivial Git/repository/software-engineering must not route to Granite.

## Permanent architecture/security boundaries

All later work must preserve:

- `WorkspaceBoundary` path confinement and symlink-escape rejection;
- `ProcessSandbox` + global KillSwitch;
- Guardian + `PermissionSet`;
- structured Tool APIs, never arbitrary model-supplied commands;
- SafeChange snapshots before sensitive mutations;
- AuditLog hash-chain evidence;
- secrets redaction and exclusion from LLM context/persistent memory;
- Schema/DataGovernance discipline;
- structured Health/Budget/Test/Regression evidence;
- platform-aware behavior: non-target platforms must not impose requirements/dependencies/inputs/budgets/tests;
- architecture-foundation changes require ADR.

## R5 hardware-local accepted baseline

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- LSP 6005, DAP 6006, debug 6007;
- AMD Radeon RX 6750 XT observed during real Movie Maker acceptance;
- final hardware-local acceptance: 19 PASS / 0 FAIL / 19, `acceptance_completed=true`;
- benchmark ~101 effective FPS on disposable fixture;
- AVI capture 64,612 bytes;
- governed scene edit with SafeChange snapshot;
- loopback LSP/DAP, DAP thread `Main`;
- Windows release export 109,127,680 bytes;
- valid AuditLog chain.

### R5 anti-regression rules

1. `ProcessSandbox.run()` drains stdout/stderr with `communicate(timeout=...)`; never poll exit before draining PIPEs.
2. Long-lived socket services use the sandboxed background path when stdio is not protocol; no unread PIPEs.
3. Real Godot Movie Maker capture must not be substituted with headless/dummy rendering.
4. TCP connect timeout must not remain protocol-read timeout after connection.
5. DAP launch supports deferred response sequencing through `configurationDone`.
6. Godot services remain loopback-only; model input must not expose arbitrary host/argv/command/program/cwd.

## R6 detailed plan — ACCEPTED

`docs/roadmap/R6_PLAN.md` is the authoritative exhaustive R6 plan. It was reconstructed retroactively by explicit user request because R6.1–R6.3 predated the permanent phase-plan rule.

Planning acceptance evidence:

- accepted planning head `8fbad7c13dd65f9dcd49a03b33a3174fcf28d18a`;
- R0 Repository Guard run `32563057993` / #639 — SUCCESS Windows + Ubuntu;
- Python Core run `32563057956` / #613 — SUCCESS Windows + Ubuntu, PowerShell validation + integrated KodeStudio smoke;
- KodeStudio UI Smoke run `32563057903` / #580 — SUCCESS Windows;
- PR #37 merge `0a91064608507966a47921df8fb36e5f25477141`;
- post-plan normalization PR #38 merge `e96e7c3b168975869c911f880044b7ef8e322157`.

The plan freezes this structure:

1. R6.1 — KodeHealth foundation — COMPLETE — manual `NONE`.
2. R6.2 — KodeBudget foundation — COMPLETE — manual `NONE`.
3. R6.3 — KodeTests + KodeRegression foundation — COMPLETE — manual `NONE`.
4. R6.4 — KodeVisualQA foundation — IN PROGRESS — manual `REQUIRED`.
5. R6.5 — KodeAccessibility foundation — PLANNED — manual `REQUIRED`.
6. R6.6 — KodeLocalization + pseudo-localization — PLANNED — manual `NONE`.
7. R6.7 — KodeTechnicalDebt — PLANNED — manual `NONE`.
8. R6.8 — KodeCI + KodeBuild — PLANNED — manual `CONDITIONAL`.
9. R6.9 — KodeAppSecurity baseline — PLANNED — manual `NONE`.
10. R6.10 — KodePrivacy baseline — PLANNED — manual `NONE`.
11. R6.11 — KodeLicense + KodeBOM — PLANNED — manual `CONDITIONAL`.
12. R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — PLANNED — manual `CONDITIONAL`.

Do not silently add/remove/merge/split/renumber any R6.N. Update plan + continuity in the same work cycle; architecture changes need ADR.

## Accepted R6.1 evidence

- head `802de4ba3110ace657c4e16306a0ca29850ce2bd`;
- PR #30 merge `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`;
- 9 focused tests PASS;
- R0 `32561211168`, Python Core `32561211156`, UI Smoke `32561211167` — SUCCESS.

## Accepted R6.2 evidence

- head `8ac3772e98c70260c320519a214bb25b6cedbb38`;
- PR #32 merge `65510a9b116d9c48b185a0edb51d99e5b951200a`;
- derivation/evaluation/persistence smoke PASS;
- R0 `32561719921`/#603, Python Core `32561719925`/#577, UI Smoke `32561720008`/#544 — SUCCESS.

## Accepted R6.3 evidence

- head `7150237c263dd3ac96af4662d74909e05f3cf991`;
- PR #34 merge `6657b258f2396b3d6a3850153b1ffaae1951104d`;
- baseline/current comparison + persistence smoke PASS;
- R0 `32562032986`/#622, Python Core `32562032998`/#596, UI Smoke `32562032982`/#563 — SUCCESS.

## R6.4 — KodeVisualQA — IN PROGRESS

Implementation branch/PR:

- base normalized `main`: `e96e7c3b168975869c911f880044b7ef8e322157`;
- branch: `feature/r6-4-visualqa`;
- PR: #39;
- authoritative final implementation head: **NOT YET FROZEN** until all final-head documentation/code updates and CI are complete;
- manual acceptance: **REQUIRED and PENDING**.

Current implementation scope:

- `src/kodepoia/quality/visual.py`: deterministic engine-neutral VisualQA evidence model/evaluator;
- immutable content-addressed baseline approval, approval provenance and artifact mutation checks;
- current image metadata, exact-file identity, changed pixel ratio, normalized mean error, max delta and deterministic dHash perceptual distance;
- rectangular masks declared in policy and included in canonical policy SHA-256;
- explicit `UNKNOWN` for missing evidence and `FAIL` for incompatible format/mode/resolution;
- diff PNG artifacts + validated `visual-report-v1` + report evidence SHA-256;
- R6.3 adapter with stable `visual:<case-id>` test IDs;
- `WorkspaceBoundary` persistence under `.kodepoia/visual_tests/{baselines,runs,diffs}` and path/symlink escape fixtures;
- Pillow constrained to `>=12.3,<12.4`;
- separate structured KodeGodot tool `kodegodot_capture_png_sequence`, fixed output under `.kodepoia/visual_tests/runs`, explicit Executor policy, no arbitrary executable/argv/command/cwd/host/output path;
- accepted R5 `kodegodot_capture_movie` AVI behavior remains unchanged;
- hardware-local acceptance module `kodepoia.quality.visual_acceptance` + `scripts/r6_4_accept_local.ps1`;
- real-render fixture requires non-empty Godot rendering method, rendering driver and video adapter and rejects `dummy/headless` evidence;
- acceptance chain requires VisualQA PASS, stable R6.3 hook PASS and AuditLog hash-chain PASS;
- `docs/roadmap/R6_4_DESIGN.md` and `R6_4_ACCEPTANCE.md` describe implementation, rollback, exact manual contract and failure recovery.

R6.4 completion constraints:

1. all implementation/fixture tests green on final-head Windows + Ubuntu CI;
2. R0/Python Core/KodeStudio UI Smoke green on that exact final head;
3. user checks out that exact final head and runs the required real Windows/Godot acceptance;
4. local JSON has `acceptance_completed=true`, non-empty real-render evidence, VisualQA PASS, R6.3 hook PASS, AuditLog PASS and `summary.failed=0`;
5. evidence is reviewed before merge;
6. only then may PR #39 merge and post-merge plan/status/continuity normalization mark R6.4 COMPLETE;
7. R6.5 must not start earlier.

## Manual-intervention forecast — remaining R6

The user must receive exact commands/actions, expected output, recovery, evidence and do-not-do-yet instructions when each gate is reached.

- **R6.4 REQUIRED:** real Windows/Godot rendered visual-regression acceptance on the accepted workstation. Never substitute headless/dummy capture. This gate is currently pending final-head CI.
- **R6.5 REQUIRED:** real interactive Windows keyboard-only + Narrator accessibility checklist.
- **R6.8 CONDITIONAL:** local Windows build evidence only if hosted CI cannot authoritatively meet the build/reproducibility DoD.
- **R6.11 CONDITIONAL:** provenance/license evidence only if an acceptance-critical component remains unresolved after trusted metadata/source inspection.
- **R6.12 CONDITIONAL:** local integration/user approval only if final selected gates require hardware-local execution or explicit approval.
- R6.6, R6.7, R6.9 and R6.10 currently require no user-side acceptance execution.

The exact planned procedures are in `R6_PLAN.md`. Before requesting manual execution, replace user-facing placeholders with the exact final implementation head and verify the implementation-specific script/commands exist.

## Current external baselines used by the R6 plan

- accessibility: W3C WCAG 2.2 current Recommendation baseline, only where applicable;
- application security: OWASP ASVS 5.0.0 current stable baseline, only for applicable surfaces;
- BOM: SPDX 3.0 current stable baseline; SPDX 3.1 RC1 is not an authoritative stable R6 baseline.

## Permanent phase-start planning rule

Adopted via PR #36 merge `56f12eb3eba1adc40a1cf4c58970ed40156360b9`. For every newly started major phase from R7 onward:

1. create `docs/roadmap/RX_PLAN.md` from `PHASE_PLAN_TEMPLATE.md` before `RX.1`;
2. enumerate every planned `RX.N` with detailed objective/scope/dependencies/implementation/deliverables/acceptance/evidence/rollback/risks;
3. classify each `NONE`, `REQUIRED` or `CONDITIONAL` for manual intervention;
4. for REQUIRED/CONDITIONAL, pre-document reason, prerequisites, exact commands/actions, expected output, recovery, evidence, do-not-do-yet and privacy/security requirements;
5. planning PR final-head checks must pass and plan must merge before implementation starts;
6. keep plan + continuity synchronized on scope/status/prerequisites/manual gates/important defects;
7. scope renumber/add/remove/merge/split requires explicit rationale and ADR if architecture changes;
8. major phase COMPLETE only when every planned subdivision is COMPLETE or explicitly removed by governed decision.

## Next action

Continue only **R6.4 PR #39** until its exact final head is CI-green. Then give the user the exact final SHA and commands from `R6_4_ACCEPTANCE.md` for the REQUIRED Windows/Godot hardware-local acceptance. Do not merge PR #39 before that local evidence is reviewed. Do not start R6.5 and do not start R7.

## Permanent process rules

- Update the active phase plan, status and continuity in the same work cycle whenever subdivision/phase status, PR state, hardware acceptance, prerequisites, manual requirements or important defects change.
- Never mark phase/subdivision COMPLETE from partial CI or unsupported claims.
- Use exact accepted head/PR/run/merge evidence.
- Preserve frozen architecture unless ADR authorizes a foundation change.
- No manual acceptance by inference from silence, partial logs/screenshots or wrong-environment evidence.
- Never ask for passwords, tokens, private keys or unrelated personal data; require redaction where logs can contain secrets.
