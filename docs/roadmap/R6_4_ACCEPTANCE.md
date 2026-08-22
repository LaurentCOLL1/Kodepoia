# R6.4 — KodeVisualQA foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** REQUIRED — SATISFIED  
**Accepted implementation head:** `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`  
**Implementation PR:** #39  
**Implementation merge:** `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`

R6.4 is accepted. The implementation head remained unchanged between final hosted CI and the required hardware-local Windows/Godot acceptance.

## Implementation acceptance matrix

| Gate | Required | Result |
| --- | --- | --- |
| Deterministic fixture comparison Windows + Ubuntu | yes | PASS |
| Exact match = PASS | yes | PASS |
| Encoding-only pixel identity remains PASS | yes | PASS |
| Inclusive WARN/FAIL threshold boundaries | yes | PASS |
| Above blocking threshold = FAIL | yes | PASS |
| Resolution/mode/format incompatibility explicit | yes | PASS |
| Missing baseline/current cannot PASS | yes | PASS |
| Baseline mutation detected | yes | PASS |
| Policy/masks hash-bound | yes | PASS |
| Report derived/policy/evidence tampering rejected | yes | PASS |
| Workspace `../` and symlink escape rejected | yes | PASS |
| R6.3 stable test hook | yes | PASS |
| `visual-report-v1` JSON Schema validation | yes | PASS |
| New Godot PNG tool structured and explicitly governed | yes | PASS |
| Existing R5 AVI behavior/regressions remain green | yes | PASS |
| R0 Repository Guard final head | yes | PASS — `32564304755` / #666 |
| Python Core Windows + Ubuntu final head | yes | PASS — `32564304757` / #640 |
| KodeStudio UI Smoke final head | yes | PASS — `32564304798` / #607 |
| Real Godot 4.7.x rendered PNG evidence on accepted workstation | yes | PASS |
| Non-empty renderer/method/video-adapter evidence | yes | PASS |
| Baseline/current/diff/report chain + R6.3 hook PASS | yes | PASS |
| AuditLog hash chain valid | yes | PASS |

## Final-head hosted evidence

All authoritative hosted workflows completed successfully on the exact implementation head `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`:

- R0 Repository Guard run `32564304755` / #666 — SUCCESS Windows + Ubuntu;
- Python Core run `32564304757` / #640 — SUCCESS Windows + Ubuntu, Windows PowerShell acceptance-runner syntax validation, full pytest suite and integrated KodeStudio smoke;
- KodeStudio UI Smoke run `32564304798` / #607 — SUCCESS Windows.

## Required hardware-local acceptance — PASS

The user executed `scripts/r6_4_accept_local.ps1` on the exact final implementation head and returned the complete terminal JSON. The authoritative result was:

- `metadata.acceptance_completed = true`;
- platform `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- Godot `4.7.2.stable.steam.ed1daf0bf`, compatible 4.7.x;
- executable `godot.windows.opt.tools.64.exe`;
- rendering method `gl_compatibility`;
- rendering driver `opengl3`;
- video adapter `AMD Radeon RX 6750 XT`;
- baseline capture return code 0, no timeout/cancellation;
- current capture return code 0, no timeout/cancellation;
- baseline SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- current SHA-256 `98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a`;
- changed ratio `0.0`;
- perceptual distance ratio `0.0`;
- policy SHA-256 `a2dbb4532c50e522639a1b1a264420d2f491d17e7b2350d500ddf415bd70014e`;
- report evidence SHA-256 `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- VisualQA status `pass`;
- R6.3 hook ID `visual:godot-real-render` status `pass`;
- AuditLog chain valid;
- summary `8 PASS / 0 FAIL / 8`.

The real-render evidence is authoritative because method, driver and video adapter were non-empty and identified the accepted Radeon workstation; no dummy/headless evidence was accepted.

## Accepted evidence paths from local run

- baseline artifact: `.kodepoia/visual_tests/baselines/godot-real-render/98dca538d872e8f883b4de4e9b92b741091365f15d193bac1127801277ca567a.png`;
- diff artifact: `.kodepoia/r6-4-acceptance/project/.kodepoia/visual_tests/diffs/godot-real-render-20260822T094123834561Z.png`;
- visual report: `.kodepoia/r6-4-acceptance/project/.kodepoia/visual_tests/runs/godot-real-render/latest.json`;
- local acceptance summary: `.kodepoia/visual_tests/r6-4-local-acceptance.json`.

These paths are local evidence locations, not repository-tracked artifacts.

## Accepted implementation properties

R6.4 establishes:

- deterministic engine-neutral VisualQA evidence;
- immutable content-addressed baseline approval and provenance;
- exact file identity, pixel statistics and deterministic dHash perceptual distance;
- explicit PASS/WARN/FAIL/UNKNOWN semantics;
- policy-declared masks included in canonical policy evidence;
- PNG diff generation;
- report round-trip and derived/policy/evidence tamper rejection;
- `.kodepoia/visual_tests/{baselines,runs,diffs}` confinement through `WorkspaceBoundary`;
- stable R6.3 `visual:<case-id>` integration;
- separate governed real-render PNG sequence capture while preserving the accepted R5 AVI contract;
- rejection of arbitrary executable/argv/command/cwd/host/output-path model inputs for the new Godot capture tool.

## Rollback / regression protection

R6.4 remains additive. If a later demonstrated regression requires rollback, revert the R6.4 implementation merge without mutating accepted R6.1–R6.3 evidence. Later changes must not:

- auto-update a baseline after failure;
- weaken missing-evidence semantics into PASS;
- remove policy/mask hashing;
- accept altered baseline/report evidence;
- substitute headless/dummy rendering for a required real-render gate;
- change the accepted R5 AVI behavior while modifying PNG VisualQA capture;
- allow user/model-supplied arbitrary process arguments or host paths.

## Completion record

- final implementation head: `72f8a13f68eb8c2e11069fe8e489858cbf2edd41`;
- PR #39;
- R0 `32564304755` / #666 — SUCCESS;
- Python Core `32564304757` / #640 — SUCCESS;
- KodeStudio UI Smoke `32564304798` / #607 — SUCCESS;
- required local hardware acceptance: PASS, `8/8`, `failed=0`, `acceptance_completed=true`;
- local evidence SHA-256: `4c0375391d8f0e1b54c8c949b264ec70d6c9a18f10798a52a72d79ac18daab56`;
- implementation merge: `27c634cc60e1c00e5d0c7ed8731668cf07ae008f`.

**R6.4 = COMPLETE. R6 remains IN PROGRESS. R6.5 is NEXT / NOT STARTED.**
