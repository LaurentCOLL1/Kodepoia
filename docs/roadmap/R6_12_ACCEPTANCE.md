# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — Acceptance

**Status:** COMPLETE — effective with the final R6 normalization merge  
**Accepted implementation head:** `f57d1c43cfa12a8f9918b80065f4ffa3502046de`  
**Implementation PR:** #56  
**Implementation merge:** `e557979ef818d03bc7602a0b96644b0b5863a73e`  
**Starting normalized main:** `264f129d3e32e38c8867871fc4dcf9a03ef2b5b9`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

R6.12 makes the frozen rule “every major patch has validation and rollback” enforceable and supplies the machine-validated integration contract used to close R6.

## Final implementation evidence

Exact accepted head `f57d1c43cfa12a8f9918b80065f4ffa3502046de` passed all required hosted gates before merge:

- R0 Repository Guard #934 / run `32580881005` — SUCCESS Windows + Ubuntu;
- Python Core #908 / run `32580881007` — SUCCESS all five jobs: Ubuntu core, Windows core, Ubuntu package-build, Windows package-build and integrated Windows KodeStudio UI;
- KodeStudio UI Smoke #875 / run `32580881010` — SUCCESS Windows;
- PR #56 was merged with exact-head protection as `e557979ef818d03bc7602a0b96644b0b5863a73e`.

No R6.12 manual gate was triggered: rollback proof is disposable fixture-only and the required properties were provable on hosted CI.

## Accepted contract

1. major/minor classification is deterministic from structured path/domain/operation/risk/platform evidence, never free model opinion;
2. patch reports bind exact base/head Git SHAs;
3. changed domains/platforms deterministically select existing R6 gates;
4. major classification always adds rollback, regression and technical-debt validation;
5. required fail/missing/skip/cancelled/N/A evidence fails closed; WARN remains WARN;
6. every measured PASS/WARN/FAIL item requires both `source_sha` and evidence SHA-256, and report evidence must match the exact patch head;
7. major PASS requires an explicit rollback strategy with snapshot/audit/verification semantics enabled plus a PASS rehearsal;
8. fixture rehearsal requires `.kodepoia-r6-rollback-fixture`, rejects parent/POSIX absolute/Windows-drive escapes and support-tree overlap, and never operates on a real repository or user project;
9. rollback composes existing `SafeChangeManager`, `BackupManager`, `RecoveryJournal`, `AuditLog` and `WorkspaceBoundary`; no parallel restore engine exists;
10. rehearsal verifies full file-set/content SHA-256 restoration, backup integrity, recovery checkpoint clearing and AuditLog chain integrity;
11. patch and integrated reports are schema-bound, canonically SHA-256-bound and reject derived-field tampering;
12. PASS subdivision evidence requires a non-empty accepted head; R6.12 accepted head must equal integrated report `source_sha`;
13. Health and stable R6.3 adapters preserve FAIL/WARN/UNKNOWN/SKIP semantics without manufacturing PASS;
14. no arbitrary model-controlled shell/argv/cwd/host/network field is introduced.

## Diagnostic hardening record

Initial strict diagnostic head `9078b58d27e45c48696f5341b3666962fabd3dca` exposed four R6.12 test failures while 294 tests passed and 3 skipped. Review separated one incorrect fixture expectation from three real false-green paths:

- low-risk UI was correctly MINOR; the test was corrected to explicit HIGH risk before asserting major rollback;
- measured evidence could omit source SHA/digest;
- Windows drive-style paths such as `C:/...` were not rejected;
- PASS subdivision evidence could omit `accepted_head`, and stale R6.12 source binding needed stronger rejection.

The implementation and schemas were hardened rather than the tests weakened. Hardened diagnostic head `3b16329958dbf1c7b7cf37d94e35108ccbf64e8d` then passed R0 #928, Python Core #902 five jobs and UI Smoke #869. The later final head `f57d1c43cfa12a8f9918b80065f4ffa3502046de` passed the authoritative gates listed above.

## Integrated R6 acceptance

Final normalization checks in `docs/roadmap/R6_INTEGRATED_ACCEPTANCE.json` enumerate R6.1–R6.12 as PASS, bind each entry to its accepted implementation head, require all manual gates satisfied/not-triggered, and SHA-256-bind each entry to the exact bytes of its `docs/roadmap/R6_X_ACCEPTANCE.md` source.

`tests/test_r6_12_repository_integration.py` validates the checked-in report, its JSON Schema, all 12 subdivision IDs, source paths, source-document digests, accepted heads, manual satisfaction, overall PASS/no blockers and the invariant that R6.12 `accepted_head` equals report `source_sha`.

## External reference interpretation

SLSA v1.2 remains provenance-design context only; R6.12 claims no SLSA level. CycloneDX 1.7 remains optional BOM interoperability context and does not replace the frozen SPDX decisions accepted in R6.11.

## Anti-regression

- never classify from model prose alone;
- never accept required missing/skipped/cancelled/N/A evidence;
- never accept measured evidence without exact-head/digest provenance;
- never allow major PASS without rollback strategy + passing rehearsal;
- never rehearse destructive rollback on a real project/repository;
- never weaken WorkspaceBoundary, SafeChange, BackupManager verification, RecoveryJournal, AuditLog or Guardian boundaries;
- never accept an integrated report whose acceptance-document hashes, accepted heads or R6.12 source head do not match;
- never start R7 before final R6 normalization is CI-green and merged.

**R6.12 = COMPLETE.**
