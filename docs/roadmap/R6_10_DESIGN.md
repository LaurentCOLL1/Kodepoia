# R6.10 — KodePrivacy baseline — Design

**Status:** IN PROGRESS  
**Starting normalized main:** `4df229e431d2d54e4268607f38bac4045ac590d1`  
**Manual intervention:** NONE

## Objective

Create a structured, local-first privacy evidence layer that inventories data categories and lifecycle metadata, records unresolved privacy questions without inventing legal conclusions, prepares platform-store declarations, feeds Health/Tests, and persists only redacted metadata inside the project boundary.

## Reference interpretation

R6.10 uses external references as data-model context only:

- EU/GDPR principles motivate explicit purpose, minimisation, retention, deletion/security/accountability metadata;
- Google Play Data safety motivates collected/shared/optional/purpose preparation fields;
- Apple App Privacy / privacy manifests motivate collected data type, purpose, linked-to-user and tracking preparation fields.

Kodepoia does **not** infer a lawful basis, consent requirement, legal compliance, store approval or certification. `UNSPECIFIED` remains explicit when the project owner has not supplied a basis.

## Core model

### PrivacyDataItem

Stable inventory entry with:

- stable ID/category;
- disposition `collected`, `none`, or `not_applicable`;
- target platform scope;
- evidence source;
- for collected data: source, purpose, storage, recipients, retention, deletion and sensitivity;
- basis state `unspecified`, `declared`, or `not_applicable`;
- optional declared legal/consent-basis placeholders with provenance;
- rationale for `none/not_applicable`;
- redacted metadata details.

Collected items fail construction if purpose/storage/retention/deletion evidence is missing. `none/not_applicable` entries require rationale and cannot carry collection lifecycle fields.

### PrivacyIssue

Typed applicability/status/severity evidence. N/A is not PASS; measured PASS/WARN/FAIL requires provenance; only FAIL can block.

### StorePrivacyDeclaration

Preparation-only store evidence:

- Apple: collected, linked-to-user, tracking, purposes;
- Google Play: collected, shared, optional collection, purposes;
- generic fallback for other stores;
- explicit `yes/no/unknown/not_applicable` values;
- readiness is derived and anti-tamper checked;
- declaration collection state must agree with the inventory;
- store/platform mismatches fail closed.

No store submission is performed.

### PrivacyReport

Canonical v1 report with:

- target platforms;
- inventory, issues and store declarations;
- deterministic UNKNOWN/PASS/WARN/FAIL aggregation;
- counts and blockers derived from evidence;
- canonical SHA-256 anti-tamper binding;
- JSON round-trip validation;
- Health `privacy` adapter;
- stable R6.3 cases;
- persistence in `.kodepoia/diagnostics/privacy/` through `WorkspaceBoundary`.

## Status semantics

- FAIL: any failed/blocking privacy issue;
- UNKNOWN: no inventory evidence;
- WARN: collected data has unspecified basis or unknown sensitivity, any issue is WARN/UNKNOWN, or a supplied store declaration remains incomplete;
- PASS: inventory is structurally complete and no warning/failure condition remains.

A PASS means the structured evidence is internally complete under this contract; it is **not** a legal-compliance determination.

## Evidence privacy

Persistent evidence is metadata only. The serializer:

- reuses R6.8 secret redaction;
- redacts obvious raw/sample/personal-value fields;
- redacts email-address and IPv4-shaped values in free-form details;
- never requires raw personal-data samples to prove a category exists.

## Architecture boundaries

R6.10 adds no scanner, shell, network collector, remote analytics service or store-submission path. Existing `WorkspaceBoundary`, Guardian, Sandbox, KillSwitch, SafeChange and secret boundaries remain unchanged.

## Accepted deliverables target

- `src/kodepoia/quality/privacy.py`;
- `schemas/privacy-report-v1.schema.json`;
- `tests/test_r6_10_privacy.py`;
- quality exports;
- `docs/roadmap/R6_10_DESIGN.md`;
- `docs/roadmap/R6_10_ACCEPTANCE.md`;
- status/continuity updates;
- exact-final-head R0, Python Core and KodeStudio UI Smoke;
- implementation merge + post-merge normalization.
