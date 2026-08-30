# R15.4 — Acceptance record

**Acceptance state:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING  
**Technical source:** `b82c7595f69f94e173a6e7893073585c9f8c1aae`  
**Manual:** NONE

## Exact technical evidence

- R15.4 Dedup Contamination Acceptance #7 / `33284070954`: SUCCESS Ubuntu + Windows; 68 cumulative experience tests per OS, Ruff and compile.
- R0 Repository Guard #2092 / `33284070915`: SUCCESS Ubuntu + Windows.
- Python Core #2067 / `33284070930`: SUCCESS 5/5.
- KodeStudio UI Smoke #2032 / `33284070882`: SUCCESS.

## Adversarial coverage

Acceptance proves platform-stable comparison normalization; deterministic policy digests; invalid-policy rejection; row-order-independent exact clustering; inclusive near-threshold behavior and below-threshold separation; transitive cluster grouping; deterministic representatives; duplicate-ID and cross-policy rejection; exact holdout quarantine of the entire duplicate group; near-holdout fail-closed quarantine with review flag; safe below-threshold behavior; zero raw protected/candidate content in safe reports/manifests; idempotent holdout registration with conflicting identity rejection; registry policy binding; JSON-schema validation; group-ID policy sensitivity; and consistent-policy enforcement during contamination scans.

The technical source is frozen. This END state must receive fresh exact-head R15.4/R0/Python/UI gates before merge; technical-source evidence is not reused as END-head evidence.
