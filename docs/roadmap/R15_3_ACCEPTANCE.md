# R15.3 — Acceptance record

**Acceptance state:** TECHNICAL SOURCE ACCEPTED / EXACT END-HEAD RE-GATES PENDING
**Technical source:** `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`
**Manual:** NONE

## Exact technical evidence

- R15.3 Experience Governance Acceptance #6 / `33281437119`: SUCCESS on Ubuntu + Windows; 49 R15.1–R15.3 tests per OS, Ruff and compile.
- R0 Repository Guard #2081 / `33281437161`: SUCCESS.
- Python Core #2056 / `33281437215`: SUCCESS 5/5.
- KodeStudio UI Smoke #2021 / `33281437163`: SUCCESS.

## Adversarial coverage

Acceptance proves deterministic secret/email/path redaction; zero detected values/storage paths in safe reports; deterministic policy/output digests; consent non-laundering; missing/unknown/denied/compound/license-ref behavior; case-insensitive SPDX operators; source deny precedence; benchmark protection; configured privacy denials; governance-policy conflict rejection; revocation cascade; observed-source quarantine; and source-scoped revocation isolation.

The technical source is frozen. This document plus the END state must receive fresh exact-head R15.3/R0/Python/UI gates before merge; technical-source evidence is not reused as END-head evidence.
