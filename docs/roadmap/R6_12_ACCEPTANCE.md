# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — Acceptance

**Status:** IN PROGRESS  
**Parent plan:** `docs/roadmap/R6_PLAN.md`  
**Starting normalized main:** `264f129d3e32e38c8867871fc4dcf9a03ef2b5b9`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

R6.12 is COMPLETE only after the exact final implementation head passes all required hosted gates, the implementation PR merges, the integrated R6 evidence passes, every triggered manual gate is satisfied, and final R6 normalization is CI-green and merged.

## Acceptance matrix

| Gate | Required | Current |
| --- | --- | --- |
| deterministic major/minor classification | yes | IMPLEMENTED |
| explainable deterministic triggers | yes | IMPLEMENTED |
| domain-driven validation matrix | yes | IMPLEMENTED |
| major adds rollback/regression/debt gates | yes | IMPLEMENTED |
| exact base/head SHA binding | yes | HARDENED + PASS DIAGNOSTIC |
| all measured evidence requires source SHA + digest | yes | HARDENED + PASS DIAGNOSTIC |
| missing required evidence fails | yes | IMPLEMENTED |
| fail required evidence fails | yes | IMPLEMENTED |
| skipped required evidence fails | yes | IMPLEMENTED |
| cancelled required evidence fails | yes | IMPLEMENTED |
| required N/A cannot become PASS | yes | IMPLEMENTED |
| WARN remains WARN | yes | IMPLEMENTED |
| explicit rollback strategy for major patch | yes | IMPLEMENTED |
| rollback verification flags required for major PASS | yes | IMPLEMENTED |
| rollback rehearsal mandatory for major PASS | yes | IMPLEMENTED |
| fixture-only rehearsal marker | yes | IMPLEMENTED |
| SafeChange reused | yes | IMPLEMENTED |
| BackupManager reused | yes | IMPLEMENTED |
| RecoveryJournal reused | yes | IMPLEMENTED |
| AuditLog reused and verified | yes | IMPLEMENTED |
| exact file-set/hash restoration checked | yes | PASS DIAGNOSTIC |
| corrupt backup rejected | yes | PASS DIAGNOSTIC |
| parent/absolute/Windows-drive path escape rejected | yes | HARDENED + PASS DIAGNOSTIC |
| no real-repository destructive rehearsal | yes | IMPLEMENTED |
| patch report canonical SHA-256 | yes | IMPLEMENTED |
| patch report derived-field tamper rejection | yes | PASS DIAGNOSTIC |
| patch report JSON Schema | yes | HARDENED + PASS DIAGNOSTIC |
| patch report `.kodepoia/patch_gates/` confinement | yes | PASS DIAGNOSTIC |
| Health adapter | yes | PASS DIAGNOSTIC |
| stable R6.3 patch-gate cases | yes | PASS DIAGNOSTIC |
| R6.1–R6.12 integration report | yes | IMPLEMENTED |
| PASS subdivision requires accepted head | yes | HARDENED + PASS DIAGNOSTIC |
| R6.12 accepted head equals integration source SHA | yes | HARDENED + PASS DIAGNOSTIC |
| missing subdivision evidence blocks | yes | PASS DIAGNOSTIC |
| pending manual evidence blocks | yes | PASS DIAGNOSTIC |
| integration report anti-tamper | yes | PASS DIAGNOSTIC |
| integration report JSON Schema | yes | PASS DIAGNOSTIC |
| checked-in final integration report bound to acceptance-doc hashes | yes | TEST IMPLEMENTED — RUNS IN NORMALIZATION |
| no arbitrary shell/argv/cwd/host/network field | yes | IMPLEMENTED |
| R0 exact final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core exact final head all five jobs | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke exact final head | yes | PENDING FINAL HEAD |
| integrated R6 final report PASS | yes | POST-MERGE NORMALIZATION |
| implementation PR merge | yes | PENDING |
| final R6 post-merge normalization | yes | PENDING |

## Required behavioral acceptance

The final suite demonstrates at minimum:

1. documentation/test-only low-risk changes can remain MINOR;
2. protected-domain, high/critical-risk, destructive non-doc/test, >=10-change and multi-platform triggers deterministically produce MAJOR where applicable;
3. domain changes select the expected existing R6 validation gates;
4. MAJOR always adds rollback, regression and technical-debt gates;
5. required fail/skip/cancelled/missing/N/A evidence prevents PASS;
6. WARN is preserved as WARN rather than becoming PASS;
7. every measured PASS/WARN/FAIL evidence item requires source SHA and evidence SHA-256;
8. report evidence source SHA must equal the exact patch head SHA;
9. parent traversal, POSIX absolute and Windows drive-style patch paths are rejected;
10. MAJOR without rollback/rehearsal FAILs;
11. disabling required rollback snapshot/audit/verification semantics prevents major PASS;
12. a marked temporary fixture is snapshotted, backed up, checkpointed, mutated, restored and hash-compared;
13. backup verifies both before and after restore;
14. RecoveryJournal checkpoint is cleared only after successful restore path;
15. AuditLog chain verifies after rehearsal;
16. rehearsal refuses an unmarked project and escaped/support-inside-project paths;
17. corrupted backup verify/restore fails closed;
18. patch report round-trip retains canonical evidence and tampered hash/status/classification is rejected;
19. PatchGateStore requires initialized `.kodepoia` and round-trips within WorkspaceBoundary;
20. R6.3 patch-gate cases preserve FAIL/SKIP/PASS semantics;
21. integrated R6 PASS requires all R6.1–R6.12 entries;
22. PASS subdivision evidence requires an accepted Git head;
23. R6.12 accepted head must match integration `source_sha`;
24. unsatisfied required manual evidence blocks integrated PASS;
25. integrated report round-trip and tamper rejection work;
26. both JSON Schemas accept canonical reports;
27. after implementation merge, `R6_INTEGRATED_ACCEPTANCE.json` must validate structurally and each subdivision evidence digest must equal SHA-256 of its exact `R6_X_ACCEPTANCE.md` source bytes.

## Development diagnostic / hardening

Initial strict diagnostic head `9078b58d27e45c48696f5341b3666962fabd3dca` ran Python Core #896 (`32580284932`). Ubuntu compilation and package-build succeeded, but pytest reported 4 R6.12 failures with 294 passing and 3 skipped.

Review classified them as:

- one test-fixture error: low-risk UI was correctly MINOR, so the test was changed to explicit HIGH risk before asserting major rollback;
- three real false-green paths:
  1. measured evidence could omit source SHA/digest;
  2. Windows drive-style `C:/...` path was accepted;
  3. PASS subdivision evidence could omit accepted head and stale R6.12 source binding was not rejected strongly enough.

The implementation and schemas were hardened rather than the acceptance contract weakened. The evidence rule was made stronger than the minimum test: **all** measured PASS/WARN/FAIL evidence requires both provenance fields, not just evidence selected as required by one report.

Hardened diagnostic head `3b16329958dbf1c7b7cf37d94e35108ccbf64e8d` passed:

- R0 Repository Guard #928 (`32580692422`) — SUCCESS;
- Python Core #902 (`32580692436`) — SUCCESS all five jobs, including package-build Ubuntu + Windows and Windows PowerShell validation;
- KodeStudio UI Smoke #869 (`32580692502`) — SUCCESS.

A final repository-integration validator was added after that successful diagnostic; therefore these runs are not reused as final-head evidence.

## Final integrated report strategy

The checked-in final report is intentionally created only **after the implementation PR merges**. This avoids a self-referential cycle where adding a report containing the accepted R6.12 head would itself change that head.

During final R6 normalization:

1. create `docs/roadmap/R6_INTEGRATED_ACCEPTANCE.json` with R6.1–R6.12 PASS evidence;
2. use the accepted implementation head as report `source_sha` and R6.12 `accepted_head`;
3. point each subdivision `source` to `docs/roadmap/R6_X_ACCEPTANCE.md`;
4. set each subdivision evidence SHA-256 to the actual bytes of that source document;
5. record all required manual gates as satisfied/not-triggered according to accepted evidence;
6. let `tests/test_r6_12_repository_integration.py` validate the report in the normalization CI.

Only a green normalization containing this validated report can mark R6 COMPLETE.

## External reference interpretation

SLSA v1.2 is current approved provenance context. R6.12 does not claim a SLSA level or replace R6.8 build evidence; it only follows the principle that evidence should be traceable to the source/revision it describes.

CycloneDX 1.7 remains current stable BOM interoperability context and is not changed by R6.12.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.**

No user action is currently required. The rollback rehearsal runs only on disposable hosted-CI fixtures. A manual gate is triggered only if a final selected acceptance gate genuinely requires unavailable local hardware/capability or explicit Guardian human approval. If triggered, this document must first record exact final head, reason, prerequisites, commands/actions, expected output, recovery, evidence to return and what not to do.

## Failure recovery / anti-regression

- never rehearse destructive restore on real repository/user project;
- never accept required missing/skipped/cancelled/N/A evidence;
- never accept measured evidence without exact-head/digest binding;
- never let a major patch PASS without rollback strategy + passing rehearsal;
- never create a second unrestricted backup/restore system;
- never loosen WorkspaceBoundary, SafeChange, BackupManager verification, RecoveryJournal or AuditLog integrity;
- never trust the integrated summary without underlying subdivision evidence and exact acceptance-document hashes;
- never mark R6 COMPLETE from partial CI or before final normalization.

## Completion record

PENDING exact-final-head CI, implementation merge, checked-in integrated R6 report validation and final R6 normalization.
