# R12.13 — Acceptance

## Scope

Framework-neutral accessibility, localization, theming, keyboard/focus and DPI/scaling QA contracts mapped to every frozen R12 desktop adapter. R12.13 integrates with the existing R6 quality/governance model; it does not create a second accessibility authority and it does not manufacture interactive screen-reader PASS from structural metadata.

Manual intervention: **CONDITIONAL / NOT TRIGGERED**.

The trigger is restricted to a required interactive accessibility/DPI/runtime semantic that hosted CI cannot verify, for example an actual assistive-technology announcement discrepancy that cannot be reduced to structural automation metadata. No such discrepancy or required unproven runtime claim was discovered on the accepted candidate. Structural metadata, localization, contrast, keyboard order, focus restoration intent and deterministic layout probes were machine-verified.

## Required acceptance

- `DesktopAccessibilityProfile` identity is canonical and digest-stable and covers WPF, WinUI 3, Avalonia, Qt 6 and Tauri v2;
- framework bindings explicitly map accessible name/description/role, focus, localization, theme and DPI concepts without serializing framework-native objects into shared contracts;
- every enabled interactive canonical element exposes an accessible-name resource key, keyboard focusability and a deterministic tab position;
- duplicate tab positions, missing accessible metadata and invalid focus restoration fail closed;
- translatable strings use localization keys; hard-coded translatable UI text fails the configured gate;
- locale fallback is explicit and deterministic;
- pseudo-localization is deterministic, expands strings and preserves named placeholders;
- RTL catalog intent is explicit and fails if the fixture does not declare RTL-safe layout support;
- light, dark and high-contrast profiles are explicit; high-contrast requires system-resource semantics;
- text contrast is evaluated deterministically against 4.5:1 normal-text / 3:1 large-text thresholds;
- required Windows QA scale profiles span 100–400%; missing scale probes, clipping, overlap or hidden focused controls fail closed;
- canonical fixture passes with zero errors and negative fixtures prove the configured failures;
- focused R12.13 tests plus exact-head R0 Repository Guard, full Python Core and KodeStudio UI Smoke succeed; existing desktop adapter workflows remain regression evidence.

## Web-researched implementation basis

Microsoft's Windows accessibility guidance centers on programmatic access (names/roles/values), keyboard navigation, and color/contrast. Windows guidance also requires visible/logical focus behavior, high-contrast support and scale-safe UI. Current Windows guidance uses minimum text contrast of 4.5:1 for normal text and 3:1 for large text and provides language/scale/contrast resource qualifiers.

Qt 6 documents device-independent pixels/device pixel ratios for high-DPI support and separates internationalization/resource concerns. R12.13 records framework mapping identities but does not claim an interactive assistive-technology result that was not executed.

Official references:

- https://learn.microsoft.com/windows/apps/develop/accessibility
- https://learn.microsoft.com/windows/apps/develop/input/focus-navigation
- https://learn.microsoft.com/windows/apps/design/accessibility/accessible-text-requirements
- https://learn.microsoft.com/windows/apps/windows-app-sdk/mrtcore/tailor-resources-lang-scale-contrast
- https://doc.qt.io/qt-6/highdpi.html
- https://doc.qt.io/qt-6/internationalization.html

## Accepted evidence

Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
Branch: `r12/13-accessibility-localization-qa`.
PR: #211.
Accepted implementation candidate: `646b4ad079113e27bb8d091c4153b125b6673f8c`.
Manual state: **CONDITIONAL / NOT TRIGGERED**.

Exact-head candidate gates:

- R0 Repository Guard #1562 / run `32827475621` — SUCCESS;
- Python Core #1536 / run `32827475643` — SUCCESS, including `python-core-ubuntu-latest` and `python-core-windows-latest` Test steps;
- KodeStudio UI Smoke #1503 / run `32827475650` — SUCCESS;
- R12 WPF Acceptance #57 / run `32827475625` — SUCCESS;
- R12 WinUI3 Acceptance #47 / run `32827475686` — SUCCESS;
- R12 Avalonia Acceptance #43 / run `32827475711` — SUCCESS;
- R12 Qt6 Acceptance #38 / run `32827475698` — SUCCESS;
- R12 Tauri2 Acceptance #29 / run `32827475658` — SUCCESS.

The focused suite `tests/test_desktop_r12_13.py` is exercised by full Python Core on Linux and Windows. It proves canonical PASS plus negative failure cases for missing accessible names/resources, hard-coded translatable strings, duplicate/missing keyboard tab stops, invalid focus restoration, RTL declaration mismatch, low contrast, missing system high-contrast semantics, missing scale probes, clipping, overlap and hidden focus. No acceptance requirement depends on an unexecuted interactive screen-reader claim.

## Merge / normalization rule

These evidence-recording documentation bytes changed after the accepted implementation candidate. The resulting final documentation HEAD must pass the same fresh exact-head standard gates and desktop adapter regressions before PR #211 may merge with `expected_head_sha`. After merge, perform exactly one continuity-only `r12/13-postmerge-continuity-normalization` PR, gate its exact HEAD and merge it. R12.14 remains forbidden until that normalization merges.
