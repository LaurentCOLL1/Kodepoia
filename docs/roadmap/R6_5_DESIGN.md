# R6.5 — KodeAccessibility foundation — Design

**Phase:** R6.5  
**Parent:** `docs/roadmap/R6_PLAN.md`  
**Status:** IN PROGRESS  
**Manual intervention:** REQUIRED  
**Architecture:** v1.0 frozen

## Objective

R6.5 establishes deterministic accessibility evidence for Kodepoia-supported UI surfaces and a governed manual acceptance path for properties that hosted CI cannot authoritatively observe. The foundation is deliberately split into two layers:

1. **automated structural evidence** — stable control IDs, explicit accessible names/descriptions, Qt accessibility interfaces/roles/states, keyboard tab-focus eligibility, report/schema integrity, explicit contrast/target-size checks where source values exist, persistence and R6.3 regression hooks;
2. **real interactive evidence** — keyboard-only operation, visible/unobscured focus and Windows Narrator announcements in an actual desktop session.

The phase does not claim universal accessibility certification. It creates auditable evidence for the current KodeStudio and Project Wizard surfaces.

## External reference baseline

R6.5 uses external standards as applicable engineering references, not as a blanket certification claim:

- **W3C WCAG 2.2** — source criteria for keyboard accessibility, focus visibility, focus not obscured and target size;
- **W3C WCAG2ICT 2.2** — W3C guidance for applying WCAG 2.x criteria to non-Web software and documents; this is the preferred interpretation guide for KodeStudio as desktop software;
- **Qt 6 accessibility APIs** — QWidget accessibility metadata and `QAccessibleInterface` are the implementation mechanism used by assistive technologies;
- **Microsoft Windows Narrator documentation** — authoritative keyboard commands and real screen-reader behavior for the required Windows manual gate.

Reference URLs:

- https://www.w3.org/TR/WCAG22/
- https://www.w3.org/TR/wcag2ict-22/
- https://doc.qt.io/qt-6/accessible.html
- https://doc.qt.io/qt-6/qwidget.html#accessibleName-prop
- https://support.microsoft.com/en-us/accessibility/windows/narrator/appendix-b-narrator-keyboard-commands-and-touch-gestures

WCAG2ICT is especially relevant because it explicitly addresses non-Web software. R6.5 therefore does **not** label KodeStudio a WCAG-conformant Web page.

## Scope

### In scope

- stable accessibility rule IDs and target IDs;
- `unknown/pass/warn/fail/not_applicable` result states;
- `info/minor/major/critical` severity;
- explicit applicability reason for every `not_applicable` result;
- blocking failures only for actual `FAIL` evidence;
- deterministic aggregate report state and counts;
- canonical evidence SHA-256 and derived-field tamper rejection;
- JSON Schema v1;
- project-confined persistence under `.kodepoia/diagnostics/accessibility/`;
- R6.3 stable test IDs;
- explicit contrast-ratio checks when foreground/background sRGB values are supplied;
- direct-rectangle target-size checks when explicit dimensions are supplied;
- KodeStudio and Project Wizard control registration;
- Qt `accessibleName` / `accessibleDescription` metadata;
- Qt `QAccessibleInterface` name/role/state inspection;
- keyboard tab-focus eligibility for visible, enabled registered controls;
- explicit `not_applicable` for hidden/disabled adaptive controls instead of false PASS;
- deterministic tests for the initial Project Wizard adaptive state;
- real Windows keyboard-only/focus/Narrator acceptance with stable checklist IDs;
- source-head binding of manual evidence.

### Out of scope

- claiming full legal or standards compliance;
- universal WCAG certification of KodeStudio;
- TalkBack, VoiceOver, Orca, NVDA or JAWS certification in R6.5;
- Android/iOS/macOS device accessibility certification;
- automated aesthetic judgement of focus visibility;
- automating or spoofing Narrator output;
- OCR-based screen-reader validation;
- changing Guardian, Sandbox, KillSwitch or process-governance architecture;
- activating the emergency KillSwitch during accessibility acceptance;
- accessibility design for future generated products not yet implemented.

## Evidence model

`src/kodepoia/quality/accessibility.py` defines:

- `AccessibilitySeverity`;
- `AccessibilityStatus`;
- `AccessibilityReportStatus`;
- `AccessibilityResult`;
- `AccessibilityReport`;
- `KodeAccessibility`;
- `AccessibilityStore`.

A result is keyed by `(rule_id, target_id)`. Duplicate pairs are rejected. IDs use a constrained stable format so R6.3 can compare them across runs.

### Status semantics

- `PASS`: applicable criterion has positive evidence;
- `WARN`: applicable evidence is below a preferred threshold but not configured as blocking;
- `FAIL`: applicable criterion failed;
- `UNKNOWN`: applicable evidence cannot be established;
- `NOT_APPLICABLE`: criterion does not apply in the audited state and must include an explicit reason.

`NOT_APPLICABLE` is never silently treated as PASS. `UNKNOWN` prevents an aggregate PASS.

### Aggregate semantics

- no applicable results -> report `UNKNOWN`;
- any FAIL -> report `FAIL`;
- otherwise WARN or UNKNOWN result -> report `WARN`;
- otherwise -> report `PASS`.

The report serializes derived counts and blockers and computes `evidence_sha256` from canonical underlying evidence. Deserialization recomputes counts, blockers and hash and rejects mismatches.

## Persistence and boundary

`AccessibilityStore` resolves project paths through the existing `WorkspaceBoundary` and requires initialized `.kodepoia` metadata.

Authoritative persistent root:

`.kodepoia/diagnostics/accessibility/`

Each surface gets an atomic `*-latest.json` plus timestamped snapshots. Symlink escape is rejected by the existing `WorkspaceViolation` behavior; R6.5 does not replace or weaken it.

The manual acceptance manifest, responses and final summary are also restricted to this accessibility evidence directory.

## R6.3 integration

Applicable accessibility results map to stable test IDs:

`accessibility:<rule-id>:<target-id>`

Mapping:

- accessibility PASS -> R6.3 PASS;
- WARN -> SKIP/WARN semantics;
- FAIL -> FAIL;
- UNKNOWN -> ERROR;
- NOT_APPLICABLE -> omitted from the applicable test-case stream.

Every emitted test case carries the accessibility report evidence hash.

## Explicit numeric checks

### Contrast

`KodeAccessibility.contrast_ratio()` implements the standard relative-luminance contrast calculation for explicitly supplied sRGB colors. `check_contrast()` records the source values and configured minimum.

R6.5 does not pretend to infer final rendered contrast from arbitrary stylesheets, themes, alpha blending or OS composition when the needed source values are absent.

### Target size

`check_target_size()` evaluates an explicit rectangle against configured minimum width/height. The default `24x24` threshold reflects the WCAG 2.2 Target Size (Minimum) direct-size branch, but the implementation labels the evidence `direct_rectangle_only` because WCAG also defines spacing/equivalent/inline/user-agent/essential exceptions.

Therefore a small direct rectangle is not automatically a universal conformance failure unless the caller has established that the direct-size test is the applicable policy.

## Qt/KodeStudio integration

`src/kodepoia/kodestudio/accessibility.py` provides a deterministic registration/audit contract.

### Registration

`mark_accessible()` assigns:

- stable `objectName`;
- explicit `accessibleName`;
- optional `accessibleDescription`;
- registration properties used by the audit.

Descriptions are mandatory for controls where a name alone is insufficient to communicate risk or purpose, such as the emergency-stop button or complex tables.

### Audited surfaces

The current R6.5 foundation covers:

- KodeStudio main navigation;
- New project action;
- Security KillSwitch actions without triggering them;
- Project Wizard tab structure;
- General project fields;
- adaptive input fields;
- target-platform selectors;
- per-platform performance budget fields;
- local tool decisions;
- approval policies;
- capability decisions;
- lineage fields;
- product document fields;
- requirements table and dynamic requirement-priority controls;
- Create/Cancel actions.

### Automated Qt rules

For registered controls, the audit checks:

- `qt.control.present`;
- `qt.name.explicit`;
- `qt.description.required`;
- `qt.keyboard.tab_focus`;
- `qt.accessible.interface`;
- `qt.accessible.role`;
- `qt.accessible.state`.

The audit also finds named application-owned interactive controls that were not registered, so adding a new KodeStudio control cannot silently escape the accessibility contract.

Qt-owned implementation children are not application controls. Known `QTabBar` scroll buttons (`ScrollLeftButton`, `ScrollRightButton`) are explicitly excluded after CI demonstrated that Qt creates them internally.

## Adaptive-state rule

A visible enabled registered control must be tab-focusable for automated PASS.

A hidden or disabled adaptive control is marked `NOT_APPLICABLE` for `qt.keyboard.tab_focus`, with a reason. This avoids the false assertion that an invisible mobile/XR field is keyboard-operable in the current Windows-only initial state.

The registration/name/role/interface contract still applies so the control remains ready when its state becomes applicable.

## Manual Windows acceptance

Hosted CI cannot prove that:

- the user can visually perceive the real platform focus indicator;
- focus is not actually obscured or clipped in a human-observable session;
- Narrator speaks the expected names, roles, states and contextual descriptions;
- table navigation is understandable through the real screen reader.

`scripts/r6_5_accept_local.ps1` therefore launches KodeStudio in a real Windows session and walks the user through **13 stable blocking checks** across keyboard, focus and Narrator categories.

The script does not simulate Narrator. It records only what the user actually observes.

Narrator controls used by the checklist:

- `Win+Ctrl+Enter`: start/stop Narrator;
- `Narrator+Alt+X`: Speech Recap/live transcription, useful for reviewing actual spoken strings.

The Security checklist explicitly instructs the user to focus the emergency-stop control **without activating it**.

## Manual evidence binding

Preparation records:

- exact source Git head;
- Python/platform;
- automated KodeStudio report status/counts/hash/path;
- automated Project Wizard report status/counts/hash/path;
- the exact checklist IDs/instructions;
- Narrator shortcuts.

Finalization requires:

- same source head;
- exact checklist-ID set — no missing or extra answers;
- each answer `pass` or `fail`;
- unchanged automated report hashes;
- both automated reports PASS with zero blocking failures;
- all 13 manual checks PASS.

Only then can `metadata.acceptance_completed` be true.

Expected successful total: **15 PASS / 0 FAIL / 15** — two automated surfaces plus thirteen manual checks.

## CI contract

The hosted final head must pass:

- R0 Repository Guard — Windows + Ubuntu;
- Python Core — Windows + Ubuntu;
- PowerShell syntax validation including R6.4 and R6.5 acceptance scripts;
- complete pytest suite;
- integrated KodeStudio Windows smoke including R6.5 UI accessibility tests;
- separate KodeStudio UI Smoke Windows including R6.5 UI accessibility tests.

The manual gate is run only after those checks are green on the exact final implementation head.

## Rollback

R6.5 is additive to the quality layer and adds accessibility metadata to existing KodeStudio controls. Rollback of the implementation PR must remove the R6.5 modules/schema/tests/runner and metadata changes together while leaving R6.1–R6.4 accepted evidence intact.

Rollback must not delete the user's local `.kodepoia/diagnostics/accessibility/` evidence unless explicitly requested.

## Risks and mitigations

- **False PASS from hidden controls:** hidden/disabled focus rule is explicit N/A with reason.
- **False FAIL from Qt internals:** only identified Qt-owned implementation controls are excluded, not arbitrary names.
- **Missing future controls:** named application-owned controls not registered are blocking failures.
- **Screen-reader behavior differs from Qt metadata:** real Narrator gate remains mandatory.
- **Focus appearance cannot be inferred from object state:** human focus-visible/not-obscured checks remain mandatory.
- **Evidence edited after preparation:** report hashes and exact source head are revalidated during finalization.
- **User answers changed to manufacture PASS:** failure notes/evidence must be preserved; do not edit responses after observing failure.
- **Emergency action accidentally activated:** checklist explicitly forbids activation of the KillSwitch while testing its accessible metadata.

## Completion rule

R6.5 can be marked COMPLETE only when:

1. implementation and regression tests are green on the exact final head;
2. hosted R0/Python Core/KodeStudio UI workflows are all SUCCESS on that head;
3. the user runs the required keyboard/focus/Narrator acceptance on that same head;
4. automated reports PASS with zero blocking failures;
5. all 13 manual checks PASS;
6. final local summary reports `acceptance_completed=true` and `failed=0`;
7. evidence is reviewed before merge;
8. implementation PR merges;
9. plan/status/acceptance/continuity are normalized post-merge;
10. only then may R6.6 begin.
