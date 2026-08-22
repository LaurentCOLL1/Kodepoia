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
| exact base/head SHA binding | yes | IMPLEMENTED / HARDENING TESTED |
| measured required evidence requires exact head + digest | yes | TEST ADDED — DIAGNOSTIC PENDING |
| missing required evidence fails | yes | IMPLEMENTED |
| fail required evidence fails | yes | IMPLEMENTED |
| skipped required evidence fails | yes | IMPLEMENTED |
| cancelled required evidence fails | yes | IMPLEMENTED |
| required N/A cannot become PASS | yes | IMPLEMENTED |
| WARN remains WARN | yes | IMPLEMENTED |
| explicit rollback strategy for major patch | yes | IMPLEMENTED |
| rollback rehearsal mandatory for major PASS | yes | IMPLEMENTED |
| fixture-only rehearsal marker | yes | IMPLEMENTED |
| SafeChange reused | yes | IMPLEMENTED |
| BackupManager reused | yes | IMPLEMENTED |
| RecoveryJournal reused | yes | IMPLEMENTED |
| AuditLog reused and verified | yes | IMPLEMENTED |
| exact file-set/hash restoration checked | yes | IMPLEMENTED |
| corrupt backup rejected | yes | TEST ADDED |
| parent/absolute/drive path escape rejected | yes | TEST ADDED — DIAGNOSTIC PENDING |
| no real-repository destructive rehearsal | yes | IMPLEMENTED |
| patch report canonical SHA-256 | yes | IMPLEMENTED |
| patch report derived-field tamper rejection | yes | IMPLEMENTED |
| patch report JSON Schema | yes | IMPLEMENTED |
| patch report `.kodepoia/patch_gates/` confinement | yes | IMPLEMENTED |
| Health adapter | yes | IMPLEMENTED |
| stable R6.3 patch-gate cases | yes | IMPLEMENTED |
| R6.1–R6.12 integration report | yes | IMPLEMENTED / HARDENING TESTED |
| PASS subdivision requires accepted head | yes | TEST ADDED — DIAGNOSTIC PENDING |
| R6.12 accepted head equals integration source SHA | yes | TEST ADDED — DIAGNOSTIC PENDING |
| missing subdivision evidence blocks | yes | IMPLEMENTED |
| pending manual evidence blocks | yes | IMPLEMENTED |
| integration report anti-tamper | yes | IMPLEMENTED |
| integration report JSON Schema | yes | IMPLEMENTED |
| no arbitrary shell/argv/cwd/host/network field | yes | IMPLEMENTED |
| R0 exact final head Windows+Ubuntu | yes | PENDING FINAL HEAD |
| Python Core exact final head all five jobs | yes | PENDING FINAL HEAD |
| KodeStudio UI Smoke exact final head | yes | PENDING FINAL HEAD |
| integrated R6 fixture PASS | yes | PENDING FINAL HEAD |
| implementation PR merge | yes | PENDING |
| final R6 post-merge normalization | yes | PENDING |

## Required behavioral acceptance

The final suite must demonstrate at minimum:

1. documentation/test-only low-risk changes can remain MINOR;
2. protected-domain, high/critical-risk, destructive non-doc/test, >=10-change and multi-platform triggers can deterministically produce MAJOR;
3. domain changes select the expected existing R6 validation gates;
4. MAJOR always adds rollback, regression and technical-debt gates;
5. required fail/skip/cancelled/missing/N/A evidence prevents PASS;
6. WARN is preserved as WARN rather than becoming PASS;
7. required measured evidence is tied to the exact patch head SHA and an evidence SHA-256;
8. wrong-source SHA is rejected;
9. parent traversal, absolute and Windows drive-style patch paths are rejected;
10. MAJOR without rollback/rehearsal FAILs;
11. a marked temporary fixture is snapshotted, backed up, checkpointed, mutated, restored and hash-compared;
12. backup verifies both before and after restore;
13. RecoveryJournal checkpoint is cleared only after successful restore path;
14. AuditLog chain verifies after rehearsal;
15. rehearsal refuses an unmarked project and escaped/support-inside-project paths;
16. corrupted backup verify/restore fails closed;
17. patch report round-trip retains canonical evidence and tampered hash/status/classification is rejected;
18. PatchGateStore requires initialized `.kodepoia` and round-trips within WorkspaceBoundary;
19. R6.3 patch-gate cases preserve FAIL/SKIP/PASS semantics;
20. integrated R6 PASS requires all R6.1–R6.12 entries;
21. PASS subdivision evidence requires an accepted Git head;
22. R6.12 accepted head must match integration `source_sha`;
23. unsatisfied required manual evidence blocks integrated PASS;
24. integrated report round-trip and tamper rejection work;
25. both JSON Schemas accept canonical reports.

## Current diagnostic expectation

The first strict suite intentionally includes hardening tests that the initial code may not yet satisfy. In particular, optional `source_sha`/digest fields on measured evidence and optional accepted heads in integrated subdivision evidence are treated as potential false-green paths and must be closed before final acceptance.

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
- never trust the integrated summary without underlying subdivision evidence;
- never mark R6 COMPLETE from partial CI or before final normalization.

## Completion record

PENDING diagnostic hardening, exact-final-head CI, integrated R6 PASS, implementation merge and final R6 normalization.
