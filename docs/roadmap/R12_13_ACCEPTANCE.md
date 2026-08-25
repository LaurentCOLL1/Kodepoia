# R12.13 — Acceptance

## Scope

Framework-neutral accessibility, localization, theming, keyboard/focus and DPI/scaling QA contracts mapped to every frozen R12 desktop adapter. R12.13 integrates with the existing R6 quality/governance model; it does not create a second accessibility authority and it does not manufacture interactive screen-reader PASS from structural metadata.

Manual intervention: **CONDITIONAL**.

Manual evidence is triggered only if acceptance discovers a required interactive accessibility/DPI/runtime semantic that hosted CI cannot verify, for example an actual Narrator/focus announcement discrepancy that cannot be reduced to structural automation metadata. Structural metadata, localization, contrast, keyboard order, focus restoration intent and deterministic layout probes are machine-verifiable and do not by themselves require user intervention.

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

Microsoft's current Windows accessibility guidance centers on three pillars: programmatic access (names/roles/values), keyboard navigation, and color/contrast. Microsoft also requires visible keyboard focus, logical tab order, high-contrast support and DPI-safe layout. Current Windows guidance uses minimum text contrast of 4.5:1 for normal text and 3:1 for large text. Windows resource guidance uses language/scale/contrast qualifiers and recommends scale-aware assets.

Qt 6 documents device-independent pixels and device pixel ratios for high-DPI support, and its internationalization model separates application internationalization from locale-specific resources. R12.13 records framework mapping identities but does not claim an interactive assistive-technology result that was not executed.

Official references:

- https://learn.microsoft.com/windows/apps/develop/accessibility
- https://learn.microsoft.com/windows/apps/develop/input/focus-navigation
- https://learn.microsoft.com/windows/apps/design/accessibility/accessible-text-requirements
- https://learn.microsoft.com/windows/apps/windows-app-sdk/mrtcore/tailor-resources-lang-scale-contrast
- https://doc.qt.io/qt-6/highdpi.html
- https://doc.qt.io/qt-6/internationalization.html

## Evidence state

Base normalized `main`: `34c21c8ba6f12f6cd746dd9aea8c9b3cd7e32c41`.
Branch: `r12/13-accessibility-localization-qa`.
Manual state: **CONDITIONAL / NOT TRIGGERED unless an interactive runtime discrepancy is discovered**.

Exact implementation SHA and workflow run IDs are **PENDING** until the branch is frozen and independently gated.

## Merge / normalization rule

Freeze one immutable implementation head and require exact-head standard gates plus desktop adapter regressions. If a required interactive accessibility/DPI semantic cannot be demonstrated and becomes part of the acceptance claim, stop and trigger bounded manual evidence before any R12.14 work. Otherwise record manual state **NOT TRIGGERED**, re-gate any evidence-recording documentation bytes, merge with `expected_head_sha`, then perform exactly one continuity-only post-merge normalization. R12.14 remains forbidden until that normalization merges.
