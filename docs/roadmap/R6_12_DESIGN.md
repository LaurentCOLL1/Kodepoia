# R6.12 — Major-patch validation + rollback gate and R6 integration acceptance — Design

**Status:** IN PROGRESS  
**Starting normalized main:** `264f129d3e32e38c8867871fc4dcf9a03ef2b5b9`  
**Manual intervention:** CONDITIONAL — NOT TRIGGERED

## Objective

Make the frozen R6 rule “every major patch has validation and rollback” enforceable with structured evidence, then produce a machine-validated integrated R6 acceptance report covering R6.1–R6.12.

R6.12 is a quality/governance layer. It must not introduce an unrestricted execution path, second backup engine, model-controlled command/argv/cwd/host field or destructive rehearsal on a real project.

## Classification contract

`KodePatchGate.classify()` derives `minor` or `major` from structured `PatchChange` records. Major triggers are deterministic and explainable:

- protected architecture domains: core, governance, security, schema, public API, build;
- HIGH or CRITICAL risk;
- destructive delete/rename outside documentation/tests;
- ten or more changed paths;
- changes spanning at least two named target platforms.

The model does not supply the final classification label independently of these inputs.

## Validation matrix

Each changed domain maps to required existing R6 gates. Examples:

- UI → tests, regression, visual, accessibility, localization, health;
- dependencies → tests, CI/build, security, license/BOM, health;
- privacy → tests, privacy, security, health;
- performance → tests, regression, budget, health.

Major classification always adds rollback, regression and technical-debt validation.

Required evidence uses explicit `pass/warn/fail/skip/cancelled/missing/not_applicable`. Missing, fail, skip, cancelled or N/A on a required gate fails closed. WARN remains WARN and may never become PASS. Measured required evidence must be bound to the exact patch `head_sha` and carry an evidence SHA-256.

## Rollback strategy

A major patch requires an explicit `RollbackStrategy` with stable ID, method, description and project-relative restore scope. The foundation supports SafeChange, BackupManager, RecoveryJournal and composite strategies. Major acceptance requires a controlled rollback rehearsal to PASS.

The rehearsal implementation intentionally reuses accepted primitives:

- `SafeChangeManager` for a project-confined pre-mutation snapshot;
- `BackupManager` for a verified full fixture archive and restore;
- `RecoveryJournal` for an atomic mutation checkpoint that must be cleared after successful recovery;
- `AuditLog` for a tamper-evident event chain;
- `WorkspaceBoundary` for project-relative target confinement.

No parallel restore implementation is introduced.

## Fixture-only rehearsal guard

`rehearse_fixture_rollback()` is permitted only on an explicitly marked temporary fixture containing `.kodepoia-r6-rollback-fixture`.

Additional restrictions:

- mutation target must be an existing file inside the fixture;
- parent traversal, absolute paths and Windows drive-style paths are rejected;
- support/backup/audit state must be outside and not an ancestor/descendant of the fixture project;
- the complete file set and SHA-256 hashes are captured before mutation and must match after restore;
- the backup must verify before and after restore;
- recovery checkpoint must be cleared;
- AuditLog chain must verify.

A corrupted archive is rejected by the existing `BackupManager`; a restore rehearsal is never run against the real repository or a user project.

## Patch gate report

`PatchGateReport` v1 binds:

- patch ID;
- base/head Git SHAs;
- sorted changes;
- derived classification and triggers;
- deterministic required gates;
- underlying evidence source/digest/status/head binding;
- rollback strategy and rehearsal evidence;
- derived status/blockers;
- canonical SHA-256 anti-tamper digest.

Persistence is confined to `.kodepoia/patch_gates/` through `WorkspaceBoundary`, using latest + timestamped snapshots.

## Integrated R6 report

`R6IntegrationReport` v1 enumerates R6.1–R6.12 structured evidence. A PASS subdivision must carry an accepted Git head and evidence SHA-256. R6.12's accepted head must equal the integration report `source_sha`. Missing subdivision evidence, non-PASS status, pending required manual gate, stale R6.12 source head or tampered derived fields/hash must prevent integrated PASS.

This report is an evidence aggregator, not a substitute for the underlying subdivision reports or CI records.

## R6 adapters

- patch gate → Health `tests` dimension without hiding FAIL/WARN/UNKNOWN;
- patch gate → stable R6.3 cases `patch-gate:<gate>`;
- required cancelled/missing/fail evidence maps to failing test evidence;
- WARN maps to SKIP rather than fake PASS.

## External reference context

SLSA v1.2 remains the current approved SLSA specification and defines provenance as verifiable information linking artifacts back to source/build context. R6.12 uses that only as provenance-design context; it does not claim any SLSA level. Existing R6.8 build provenance remains authoritative for package artifacts.

CycloneDX 1.7 remains stable BOM interoperability context. R6.12 does not change the frozen R6 SPDX/BOM decisions made in R6.11.

## Manual intervention

**CONDITIONAL — NOT TRIGGERED.**

The rollback rehearsal is designed for hosted CI using a disposable fixture, so no local destructive action is needed. Manual user action becomes necessary only if an acceptance-critical selected gate genuinely requires hardware/capability unavailable to hosted CI, or an existing Guardian policy explicitly requires human approval for a real sensitive operation. If triggered, exact final-head instructions must be documented before execution.

## Anti-regression

- never classify from model prose alone;
- never accept required missing/skipped/cancelled/N/A evidence;
- never accept measured evidence without exact-head binding and digest;
- never allow a major patch to PASS without rollback strategy + passing rehearsal;
- never rehearse rollback on a real project/repository;
- never add arbitrary model-controlled execution/network fields;
- never treat self-generated summary data as a substitute for underlying evidence;
- never mark R6 COMPLETE before exact-final-head CI, implementation merge and final normalization.
