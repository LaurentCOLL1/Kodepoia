# R6.6 — KodeLocalization + pseudo-localization foundation — Acceptance

**Status:** COMPLETE  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Manual intervention:** NONE — no user-side gate required  
**Accepted implementation head:** `6890b9d37722c74703e8b86f7de11dbfe66821ed`  
**Implementation PR:** #43  
**Implementation merge:** `f677cb34eade0549edc951fe11955de2bc0b270d`

R6.6 is accepted. The final implementation head passed the complete hosted acceptance matrix on Windows and Ubuntu, including the KodeStudio pseudo-localization UI smoke, before PR #43 was merged without changing the tested head.

## Accepted scope

R6.6 establishes:

- stable locale and message IDs independent of visible text;
- source/target catalog validation;
- duplicate-key rejection;
- mandatory `other` message form;
- exact source/target form parity;
- per-form Python-format placeholder parity;
- explicit target-only-key WARN evidence;
- explicit fallback semantics;
- deterministic `qps-ploc` pseudo-localization;
- preservation of `{placeholders}`, `<markup>` and `&entities;`;
- deterministic visible expansion for long-string testing;
- canonical localization report hashing and tamper rejection;
- project-confined `.kodepoia/diagnostics/localization/` persistence through `WorkspaceBoundary`;
- stable R6.3 `localization:<rule>:<target>` hooks;
- a KodeStudio source-message registry for the registered main surface;
- English as the unchanged production default;
- a Windows KodeStudio pseudo-locale smoke that verifies expanded navigation/button strings and adaptive navigation width;
- preservation of the accepted R6.5 accessibility smoke after visible strings were routed through stable IDs.

This foundation does not claim professional translation, cultural certification, universal script/font coverage or full migration of every future KodeStudio/Project Wizard string.

## Acceptance matrix — final result

| Gate | Result |
| --- | --- |
| Stable locale/message IDs | PASS |
| Duplicate message IDs rejected | PASS |
| `other` form mandatory | PASS |
| Missing source message = blocking FAIL | PASS |
| Source/target form parity | PASS |
| Placeholder parity per form | PASS |
| Target-only key = explicit WARN | PASS |
| Missing fallback = explicit WARN | PASS |
| Wrong fallback = blocking FAIL | PASS |
| Source fallback translation works | PASS |
| Pseudo locale preserves placeholders | PASS |
| Pseudo locale preserves markup/entities | PASS |
| Pseudo locale visibly expands text | PASS |
| Report status/count/blocker derivation | PASS |
| Canonical evidence SHA-256 | PASS |
| Tampered counts/hash rejected | PASS |
| Workspace/symlink escape rejection | PASS |
| R6.3 stable localization hooks | PASS |
| KodeStudio stable message registry | PASS |
| English remains production default | PASS |
| `qps-ploc` KodeStudio smoke | PASS |
| Long navigation strings avoid fixed-width truncation | PASS |
| `localization-report-v1` schema | PASS |
| R0 final head Windows + Ubuntu | PASS |
| Python Core final head Windows + Ubuntu | PASS |
| Integrated KodeStudio UI smoke | PASS |
| Separate KodeStudio UI Smoke Windows | PASS |
| Implementation PR merge | PASS |
| Manual gate | NOT REQUIRED |

## Final-head hosted evidence

All authoritative implementation checks ran on exact head:

`6890b9d37722c74703e8b86f7de11dbfe66821ed`

- **R0 Repository Guard** run `32570001461` / #733 — SUCCESS on Windows and Ubuntu.
- **Python Core** run `32570001514` / #707 — SUCCESS:
  - Ubuntu tests SUCCESS;
  - Windows tests SUCCESS;
  - PowerShell acceptance-runner syntax SUCCESS;
  - integrated KodeStudio UI smoke SUCCESS, including R6.5 accessibility and R6.6 pseudo-localization tests.
- **KodeStudio UI Smoke** run `32570001491` / #674 — SUCCESS on Windows.

No manual or hardware-local evidence was required by the accepted R6 plan for R6.6.

## Development finding and correction

The first draft head `7d117aee05006ae937f7ec0f3bc4ffdc04e371a1` reached compilation but Ubuntu pytest reported two round-trip assertions. The issue was not report corruption or a weakening of catalog rules: in-memory `LocalizationResult` instances could carry `details=None`, while the canonical serialized form uses `details={}`. The evidence hash already canonicalized both to the same persisted representation.

The tests were corrected to compare the canonical `to_dict()` evidence representation used for persistence and hashing. No localization validation rule, blocker rule, placeholder check, fallback rule or `WorkspaceBoundary` protection was relaxed. The corrected final head is the accepted head above.

## Rollback / anti-regression

R6.6 is additive. A rollback must remove the localization quality module/schema/tests, KodeStudio message registry, optional locale integration and R6.6 UI smoke together, while restoring the previously accepted English KodeStudio surface and preserving R6.1–R6.5 evidence.

Later work must not:

- make pseudo-localization the production default;
- convert missing translations/forms/placeholders into PASS;
- silently drop extra keys or fallback evidence;
- alter stable IDs merely because visible copy changes;
- corrupt/exempt placeholders to make pseudo-localization pass;
- weaken report hash/tamper validation;
- bypass `WorkspaceBoundary`;
- regress R6.5 accessibility while localizing visible text.

## Manual intervention

**NONE.** R6.6 acceptance was fully authoritative in hosted CI.

## Completion record

- accepted head: `6890b9d37722c74703e8b86f7de11dbfe66821ed`;
- PR #43;
- merge: `f677cb34eade0549edc951fe11955de2bc0b270d`;
- R0 #733: PASS;
- Python Core #707: PASS;
- UI Smoke #674: PASS;
- manual gate: NONE;
- R6.6: **COMPLETE**;
- R6.7: **NEXT / NOT STARTED** until post-merge normalization is itself CI-green and merged.
