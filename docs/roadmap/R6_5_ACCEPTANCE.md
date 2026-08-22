# R6.5 — KodeAccessibility foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** REQUIRED — SATISFIED  
**Accepted implementation head:** `06fd66af4b3a85da24b98ea2a5fbb2685358c540`  
**Implementation PR:** #41  
**Implementation merge:** `db1a1ab78eb2ac7d90f75ab294074dec0238268c`

R6.5 is accepted. The exact implementation head passed all hosted gates and the required real interactive Windows keyboard/focus/Narrator gate before PR #41 was merged. No implementation commit was added after the local acceptance evidence was produced.

## Acceptance matrix

| Gate | Result |
| --- | --- |
| Stable rule/target IDs and duplicate rejection | PASS |
| PASS/WARN/FAIL/UNKNOWN/NOT_APPLICABLE semantics | PASS |
| `not_applicable` requires an explicit reason | PASS |
| Blocking state allowed only for FAIL | PASS |
| Aggregate status/counts/blockers deterministic | PASS |
| Report evidence SHA-256 and tamper rejection | PASS |
| `accessibility-report-v1` JSON Schema | PASS |
| Workspace and symlink escape protection | PASS |
| R6.3 stable accessibility test hooks | PASS |
| Explicit sRGB contrast helper | PASS |
| Explicit direct-rectangle target-size helper | PASS |
| KodeStudio explicit accessible metadata | PASS |
| Project Wizard explicit accessible metadata | PASS |
| Dynamic budget/requirement controls registered | PASS |
| QAccessible interface/name/role/state audit | PASS |
| Visible enabled registered controls are tab-focusable | PASS |
| Hidden/disabled adaptive controls are explicit N/A | PASS |
| Named application controls cannot silently bypass registration | PASS |
| Qt-owned tab-scroll internals excluded narrowly | PASS |
| R0 Repository Guard final head | PASS |
| Python Core Windows + Ubuntu final head | PASS |
| PowerShell acceptance-runner syntax final head | PASS |
| Integrated KodeStudio UI accessibility smoke | PASS |
| Separate KodeStudio UI Smoke final head | PASS |
| Real keyboard-only navigation on Windows | PASS |
| Real visible focus check | PASS |
| Real focus-not-obscured check | PASS |
| Real Windows Narrator names/roles/states | PASS |
| Narrator table/action checks | PASS |
| Manual evidence tied to exact final source head | PASS |
| Final local result `acceptance_completed=true` | PASS |

## Hosted final-head evidence

All hosted acceptance workflows completed successfully on the exact accepted implementation head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`:

- R0 Repository Guard `32567824374` / #710 — SUCCESS Windows + Ubuntu;
- Python Core `32567824373` / #684 — SUCCESS Windows + Ubuntu, compilation, PowerShell acceptance-runner syntax, full pytest and integrated KodeStudio accessibility UI smoke;
- KodeStudio UI Smoke `32567824370` / #651 — SUCCESS Windows.

## Required Windows interactive evidence — SATISFIED

The user executed `scripts/r6_5_accept_local.ps1` on the exact accepted head.

Environment:

- Windows `Windows-11-10.0.26220-SP0`;
- Python `3.12.4`;
- source head `06fd66af4b3a85da24b98ea2a5fbb2685358c540`.

Automated KodeStudio surface:

- status `pass`;
- applicable `343`;
- passed `343`;
- failed `0`;
- warnings `0`;
- unknown `0`;
- not applicable `98`;
- blocking failures `0`;
- evidence SHA-256 `9244424a8addb921822bae80de2d7c1a95733a10f04775dc7ec8b55194041920`;
- persisted path `.kodepoia/diagnostics/accessibility/kodestudio-main-latest.json`.

Automated Project Wizard surface:

- status `pass`;
- applicable `318`;
- passed `318`;
- failed `0`;
- warnings `0`;
- unknown `0`;
- not applicable `95`;
- blocking failures `0`;
- evidence SHA-256 `e824358a8068d871f59fdbcc55092b300b572d34548d76b0c379973002ea2d91`;
- persisted path `.kodepoia/diagnostics/accessibility/kodestudio-project-wizard-latest.json`.

Manual observations:

- keyboard checks: 5/5 PASS;
- focus checks: 2/2 PASS;
- Narrator checks: 6/6 PASS;
- manual total: 13/13 PASS;
- manual failed: 0;
- manual blocking failures: 0.

Integrated local result:

- automated passed: true;
- summary `15 PASS / 0 FAIL / 15`;
- `metadata.acceptance_completed=true`;
- output `.kodepoia/diagnostics/accessibility/r6-5-local-acceptance.json`.

The observed `QFontDatabase` missing-font-directory and Qt `propagateSizeHints()` console notices did not create accessibility warnings/failures in either structured report. They are not acceptance blockers for R6.5; future quality/technical-debt work may track them separately if they remain relevant.

## Reference boundary

R6.5 uses WCAG 2.2 criteria where applicable and W3C WCAG2ICT guidance to interpret those criteria for non-Web desktop software. WCAG2ICT is informative guidance, not a claim that KodeStudio has received external WCAG certification.

Qt accessibility metadata/QAccessible evidence is used for deterministic structural verification. The manual Windows gate exists because hosted/offscreen CI cannot authoritatively prove human-observable focus and Narrator behavior.

## Accepted implementation scope

R6.5 includes:

- structured accessibility result/report evidence with stable IDs, severity, applicability and blockers;
- canonical SHA-256 evidence and derived-field tamper validation;
- project-confined `AccessibilityStore` under `.kodepoia/diagnostics/accessibility/` through `WorkspaceBoundary`;
- stable R6.3 accessibility test hooks;
- deterministic explicit contrast and target-size helpers where source values exist;
- explicit Qt accessible names/descriptions for KodeStudio and Project Wizard controls;
- stable required-control manifests including dynamic budget and requirement controls;
- QAccessible interface/name/role/state inspection;
- tab-focus checks for visible enabled registered controls;
- explicit N/A for hidden/disabled adaptive controls;
- blocking discovery of named application-owned interactive controls that bypass accessibility registration;
- narrow exclusion of Qt-owned QTabBar `ScrollLeftButton` / `ScrollRightButton` implementation children;
- Windows UI CI coverage;
- source-head-bound 13-item keyboard/focus/Narrator acceptance contract;
- rejection of wrong-SHA, incomplete, failing, tampered or out-of-workspace manual acceptance evidence.

## Anti-regression rules

Later changes must not:

- convert missing accessibility evidence to PASS;
- treat `not_applicable` as PASS or omit its reason;
- weaken evidence hashing/tamper validation;
- allow application-owned controls to bypass the accessibility registry silently;
- broaden the Qt-internal control exemption beyond identified Qt-owned implementation children without evidence;
- treat offscreen QAccessible success as a substitute for a required real assistive-technology gate;
- accept incomplete/manual evidence from a different source SHA;
- manufacture a PASS by editing manual response/report files.

R6.5 must not be reopened without a demonstrated regression or architecture-changing ADR.

## Completion record

- accepted head: `06fd66af4b3a85da24b98ea2a5fbb2685358c540`;
- PR #41;
- merge: `db1a1ab78eb2ac7d90f75ab294074dec0238268c`;
- hosted CI: R0 #710, Python Core #684, UI Smoke #651 — all SUCCESS;
- automated surfaces: 2/2 PASS, zero blocking failures;
- manual checks: 13/13 PASS;
- integrated local result: `15 PASS / 0 FAIL / 15`, `acceptance_completed=true`;
- R6.5: COMPLETE;
- R6.6: NEXT / NOT STARTED pending post-merge normalization acceptance.
