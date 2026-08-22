# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1/R2/R3/R4/R5 sont COMPLETE. R6 est IN PROGRESS. R6.1 — KodeHealth, R6.2 — KodeBudget et R6.3 — KodeTests + KodeRegression sont COMPLETE.** R6.3 a été acceptée sur le head `7150237c263dd3ac96af4662d74909e05f3cf991` après CI finale verte, puis PR #34 a été fusionnée dans `main` en `6657b258f2396b3d6a3850153b1ffaae1951104d`. Après normalisation, reprendre uniquement le reste de R6 depuis le `main` courant. Ne pas rouvrir une phase complète sans régression démontrée ou changement d'architecture nécessitant un ADR, et ne pas passer à R7 avant achèvement de R6.

## Source de vérité et état des phases

- Dépôt : `LaurentCOLL1/Kodepoia`.
- Visibilité GitHub : PUBLIC volontairement.
- Architecture : v1.0 gelée.
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

Target workstation accepted for R5:

- Python `3.12.4`;
- Windows 11 build `26220`;
- Godot `4.7.2.stable.steam.ed1daf0bf`;
- executable `D:\SteamLibrary\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe`;
- LSP 6005 / DAP 6006 / debug 6007;
- AMD Radeon RX 6750 XT observed for Movie Maker acceptance.

Final hardware-local evidence: `probe_only=false`, `acceptance_completed=true`, **19/19 PASS**. Concrete accepted artifacts included ~101 FPS on the disposable benchmark fixture, AVI capture 64,612 bytes, governed scene-edit snapshot, loopback LSP/DAP, DAP thread `Main`, Windows release export 109,127,680 bytes and valid audit chain.

### Important R5 defects that must not regress

1. `ProcessSandbox.run()` must drain stdout/stderr through `communicate(timeout=...)`; do not poll process exit before draining PIPEs.
2. Long-lived socket services must use the sandboxed background-process path when stdio is not their protocol.
3. Movie Maker real capture must not combine normal capture with headless/dummy rendering.
4. TCP connection timeouts must not remain protocol-read timeouts after LSP/DAP connection establishment.
5. DAP launch must support deferred response sequencing through `configurationDone`.
6. Godot services remain loopback-only; model input must not expose arbitrary host, argv, command, program or cwd.

## R6 — Quality / Health / Budget / CI — IN PROGRESS

### R6.1 — KodeHealth foundation — COMPLETE

Accepted implementation head `802de4ba3110ace657c4e16306a0ca29850ce2bd`, merged by PR #30 as `55c7394d0afc6b4b24653bdbee9b0e234b0ffea1`.

Accepted scope:

- 14 frozen health dimensions;
- `unknown/pass/warn/fail`, score, coverage and blocking failures;
- exhaustive report validation and serialized derived-field consistency;
- atomic `.kodepoia/health/` persistence through `WorkspaceBoundary`;
- symlink escape rejection;
- health-report-v1 schema and focused tests.

Final evidence:

- isolated hardened R6.1 tests: **9 passed**;
- R0 `32561211168` — SUCCESS Windows + Ubuntu;
- Python Core `32561211156` — SUCCESS Windows + Ubuntu;
- KodeStudio UI Smoke `32561211167` — SUCCESS Windows.

### R6.2 — KodeBudget foundation — COMPLETE

Accepted implementation head `8ac3772e98c70260c320519a214bb25b6cedbb38`, merged by PR #32 as `65510a9b116d9c48b185a0edb51d99e5b951200a`.

Accepted scope:

- 16 architecture-aligned budget metrics covering FPS/frame time, CPU/GPU, RAM/VRAM, storage, draw calls, polygons, textures, audio memory/voices, build size, mobile battery/thermal and online network;
- per-platform `at_least` / `at_most` constraints;
- target versus hard-limit semantics;
- Project DNA derivation for FPS, frame time, RAM, VRAM and build size without inventing untargeted platform requirements;
- explicit configured-observation coverage, unknown values and unconfigured-observation rejection;
- blocking hard-limit failures;
- validated report round-trip with derived-field tamper checks;
- `.kodepoia/budgets/` persistence through `WorkspaceBoundary`;
- budget-report-v1 schema and focused tests.

Final evidence:

- isolated core derivation/evaluation/persistence smoke: PASS;
- R0 Repository Guard `32561719921` / #603 — SUCCESS Windows + Ubuntu;
- Python Core `32561719925` / #577 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32561720008` / #544 — SUCCESS Windows;
- PR #32 merged only after final-head gates were green.

### R6.3 — KodeTests + KodeRegression foundation — COMPLETE

Accepted implementation head `7150237c263dd3ac96af4662d74909e05f3cf991`, merged by PR #34 as `6657b258f2396b3d6a3850153b1ffaae1951104d`.

Accepted scope:

- stable unique test case IDs and `pass/fail/error/skip` observations;
- deterministic test-run `unknown/pass/warn/fail` aggregation;
- validated serialized counts and total duration;
- atomic `.kodepoia/tests/runs/` persistence through `WorkspaceBoundary`;
- baseline/current comparison by stable test ID and matching suite identity;
- `unchanged/regressed/fixed/added/removed` classifications;
- detection of PASS→FAIL/ERROR, PASS→SKIP, FAIL→ERROR, removed tests and new failing/error tests as regressions;
- FAIL/ERROR→SKIP remains a regression so skipping cannot hide a known failure;
- separately enumerable regressions, fixes, additions and removals;
- derived-field tamper detection;
- atomic `.kodepoia/tests/regression/` persistence through `WorkspaceBoundary`;
- test-run-report-v1 and regression-report-v1 schemas;
- no new arbitrary command-execution path.

Final evidence:

- isolated baseline/current comparison and persistence smoke: PASS;
- R0 Repository Guard `32562032986` / #622 — SUCCESS Windows + Ubuntu;
- Python Core `32562032998` / #596 — SUCCESS Windows + Ubuntu, PowerShell validation and integrated KodeStudio smoke;
- KodeStudio UI Smoke `32562032982` / #563 — SUCCESS Windows;
- PR #34 merged only after final-head gates were green.

## Next phase action

Stop after R6.3 unless the user explicitly asks to continue. The remaining R6 scope is VisualQA, Accessibility, Localization, TechnicalDebt, CI/Build, AppSecurity baseline, Privacy baseline, License/BOM and the requirement that every major patch has validation and rollback. Do not skip directly to R7.

## User operational preference — permanent

Whenever the user must perform a manual operation, explain the reason, prerequisites, exact commands/actions, expected output, error recovery, what to send back, and what must not be done yet. Do not ask the user to repeat information already known.

## Permanent process rules

Update this continuity file in the same work cycle whenever phase status, PR state, hardware acceptance, prerequisites or important recovered defects change. Never declare a phase COMPLETE from partial CI. Use exact acceptance evidence where required. Preserve the frozen architecture unless an ADR explicitly authorizes a change.
