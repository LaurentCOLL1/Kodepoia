# R6.10 — KodePrivacy baseline — Design

**Status:** IN PROGRESS  
**Starting normalized main:** `4df229e431d2d54e4268607f38bac4045ac590d1`  
**Manual intervention:** NONE

## Objective

Create a structured, local-first privacy evidence layer that inventories data categories and lifecycle metadata, records unresolved privacy questions without inventing legal conclusions, prepares platform-store declarations, feeds Health/Tests, and persists only redacted metadata inside the project boundary.

## Reference interpretation

R6.10 uses external references as data-model context only:

- EU/GDPR principles motivate explicit purpose, minimisation, retention/deletion, security and accountability metadata;
- Google Play Data safety motivates collected/shared/optional/purpose preparation fields;
- Apple App Privacy/privacy manifests motivate collected data type, purpose, linked-to-user and tracking preparation fields.

Kodepoia does **not** infer a lawful basis, consent requirement, legal compliance, store approval or certification. `UNSPECIFIED` remains explicit when the project owner has not supplied a basis.

## Core model

### PrivacyDataItem

Stable inventory entry with stable ID/category, disposition `collected/none/not_applicable`, target-platform scope, provenance and redacted details. Collected data requires source, purpose, storage, retention and deletion; recipients and sensitivity are explicit. `none/not_applicable` require rationale and cannot carry collection lifecycle fields. Basis state is `unspecified/declared/not_applicable`; declared basis placeholders require provenance and are never inferred by Kodepoia.

### PrivacyIssue

Typed applicability/status/severity evidence. N/A is not PASS; measured PASS/WARN/FAIL requires provenance; only FAIL can block.

### StorePrivacyDeclaration

Preparation-only evidence:

- Apple: collected, linked-to-user, tracking, purposes;
- Google Play: collected, shared, optional collection, purposes;
- generic fallback for other stores;
- explicit `yes/no/unknown/not_applicable`;
- readiness is derived and anti-tamper checked;
- declaration collection state must agree with inventory;
- store/platform mismatches fail closed.

No store submission is performed.

### PrivacyReport

Canonical v1 report with target platforms, inventory, issues and store declarations. In addition, PASS requires an explicit `inventory_complete=true` claim bound to `inventory_review_source`; completeness is therefore evidence, not an assumption derived from a non-empty list.

The report provides deterministic UNKNOWN/PASS/WARN/FAIL aggregation, derived counts/blockers, canonical SHA-256 anti-tamper binding, JSON round-trip validation, Health `privacy`, stable R6.3 cases and `.kodepoia/diagnostics/privacy/` persistence through `WorkspaceBoundary`.

## N/A neutrality and status semantics

The design review after the first green diagnostic identified a false-green risk: a structurally valid N/A entry could otherwise contribute to a perfect score or an all-N/A inventory could appear PASS. The final contract prevents that:

- N/A inventory entries are excluded from numeric score;
- N/A issues are excluded from numeric score;
- N/A store declarations are excluded from numeric score and map to R6.3 SKIP even when structurally ready;
- an all-N/A report with no applicable evidence is UNKNOWN;
- incomplete inventory evidence is WARN, never PASS;
- incomplete-inventory score is reduced by a deterministic completeness factor;
- PASS requires inventory completeness provenance plus no remaining WARN/FAIL condition.

Other status rules:

- FAIL: any failed/blocking privacy issue;
- UNKNOWN: no inventory or no applicable measured evidence;
- WARN: inventory not proven complete, collected data has unspecified basis/unknown sensitivity, an applicable issue is WARN/UNKNOWN, or an applicable supplied store declaration is incomplete;
- PASS: applicable evidence exists, inventory completeness is proven, and no warning/failure condition remains.

A PASS means structured evidence is internally complete under this contract; it is **not** a legal-compliance determination.

## Evidence privacy

Persistent evidence is metadata only. The serializer reuses R6.8 secret redaction, redacts obvious raw/sample/personal-value fields plus email/IPv4-shaped values in free-form details, and never requires raw personal-data samples to prove a category exists.

## Architecture boundaries

R6.10 adds no scanner, shell, network collector, remote analytics/privacy service or store-submission path. Existing `WorkspaceBoundary`, Guardian, Sandbox, KillSwitch, SafeChange and secret boundaries remain unchanged.

## Development evidence so far

- first diagnostic head `935d6b4fc7a29ad832df501f605c3648cde05988` passed R0 #830, Python Core #804 and UI Smoke #771;
- design review then strengthened inventory-completeness provenance and N/A neutrality rather than accepting the first green result;
- hardened head `48daa4f82194e1875211f205b99ba19089f42d92` passed R0 #836, Python Core #810 with all five jobs and UI Smoke #777.

Neither review change adds process/network execution or relaxes privacy evidence rules.

## Deliverables

- `src/kodepoia/quality/privacy.py`;
- `schemas/privacy-report-v1.schema.json`;
- `tests/test_r6_10_privacy.py`;
- quality exports;
- `docs/roadmap/R6_10_DESIGN.md`;
- `docs/roadmap/R6_10_ACCEPTANCE.md`;
- status/continuity/plan updates;
- exact-final-head R0, Python Core and KodeStudio UI Smoke;
- implementation merge + post-merge normalization.
