# R6.6 — KodeLocalization + pseudo-localization foundation — Design

**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Architecture:** v1.0 frozen  
**Manual intervention:** NONE

## Goal

R6.6 creates a deterministic localization-quality contract before later roadmap phases multiply user-visible surfaces. It is a structural foundation, not professional translation or cultural certification.

## Design boundaries

The implementation preserves all permanent Kodepoia governance rules:

- no process execution is introduced;
- all persistent evidence is project-confined through `WorkspaceBoundary`;
- no remote localization service is required;
- pseudo-localization never becomes the production default;
- missing translations, forms or placeholders cannot be silently converted to PASS;
- source and target catalogs use stable message IDs independent from visible text;
- R6.3 receives stable `localization:<rule>:<target>` cases.

## Data model

### `LocalizedMessage`

A stable message ID plus named text forms. Every message includes `other`; optional forms such as `one` are validated by exact source/target form parity.

### `LocaleCatalog`

Contains:

- locale ID;
- tuple of unique `LocalizedMessage` records;
- optional explicit fallback locale.

Duplicate message IDs are rejected at construction.

### Validation rules

`KodeLocalization.validate_catalog()` emits stable rule IDs:

- `catalog.key.present` — required source ID exists in target;
- `catalog.forms.parity` — target form IDs match source form IDs;
- `catalog.placeholders.parity` — Python-format placeholder roots match per form;
- `catalog.key.extra` — target-only IDs are WARN, never silently ignored;
- `catalog.fallback.explicit` — explicit source-locale fallback is PASS, missing fallback is WARN, wrong fallback is blocking FAIL.

A missing source key, missing/extra form or placeholder mismatch is blocking.

## Pseudo-localization

`pseudo_localize_text()`:

1. protects Python `{placeholder}` tokens;
2. protects markup-like `<...>` tokens;
3. protects entity-like `&...;` tokens;
4. accents Latin vowels;
5. expands alphabetic segments deterministically;
6. wraps the complete string in visible `⟦...⟧` markers.

`pseudo_catalog()` applies this transformation form-by-form and explicitly falls back to the source locale.

The pseudo locale used by KodeStudio is `qps-ploc`.

## KodeStudio integration

`src/kodepoia/kodestudio/localization.py` defines a source English catalog with stable IDs for the KodeStudio main navigation, Projects actions, Security actions/state and status messages.

`build_window(..., locale="en")` consumes those IDs through `KodeStudioTranslator`. Existing callers remain compatible because English is the default.

For pseudo-localization smoke, the navigation minimum width is derived from `QListWidget.sizeHintForColumn(0) + 24`, with a minimum of 160px. This allows the test to detect long-string clipping regressions on the registered main surface without pretending to certify all future screens.

The Project Wizard remains outside the translatable-message migration in this foundation. R6.6 validates the mechanism and a registered KodeStudio surface; future UI work can migrate additional strings using the same stable-ID contract.

## Report and evidence

`LocalizationReport` records:

- schema version;
- timezone-aware generated timestamp;
- source locale;
- target locale;
- fallback locale;
- aggregate `pass/warn/fail/unknown`;
- stable result list;
- deterministic counts and blockers;
- canonical SHA-256 evidence hash.

Round-trip loading rejects:

- unsupported schema version;
- duplicate rule/target pairs;
- aggregate-status mismatch;
- serialized-count mismatch;
- serialized-blocker mismatch;
- evidence-hash tampering.

`LocalizationStore` persists under:

`.kodepoia/diagnostics/localization/`

with per-locale latest evidence plus timestamped snapshots using atomic temp+replace writes.

## Standards/reference context

Unicode CLDR is used only as current reference context for locale-data conventions. R6.6 does not vendor CLDR or claim complete locale formatting coverage. The foundation is intentionally focused on catalog/message integrity and pseudo-localization.

## Rollback

R6.6 is additive. A rollback may remove:

- the quality localization module/schema/tests;
- the KodeStudio translation registry;
- the optional locale parameter and pseudo-locale UI smoke;
- workflow entries specific to R6.6.

Rollback must restore the previously accepted English KodeStudio strings without touching R6.1–R6.5 evidence.
