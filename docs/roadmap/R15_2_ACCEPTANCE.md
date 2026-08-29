# R15.2 — Governed validated-experience capture acceptance

**Phase:** R15.2  
**Acceptance state:** TECHNICAL SOURCE ACCEPTED / END-HEAD RE-GATES PENDING  
**Clean START-head:** `135fd085002bf8074d87308beca35ab33c35ed47`  
**Immutable technical source:** `48b519c09fa50f5407cc4a55a0b76baf6f8e8ffd`  
**Normalized R15.1 base:** `f6681cdc072fdbd9eb8ebcf2c109859df31fb30f`  
**Manual intervention:** NONE

## Acceptance rule

R15.2 is accepted technically only on one immutable source SHA. Documentation/continuity END-sync changes are not allowed to retroactively redefine that source. Because END-sync changes repository bytes, a later exact END-head must receive fresh R15.2 focused, R0 Repository Guard, full Python Core and KodeStudio UI Smoke evidence before merge.

Evidence from rejected/intermediate candidates is never combined with accepted evidence.

## Accepted technical source

`48b519c09fa50f5407cc4a55a0b76baf6f8e8ffd`

The source is derived from clean START-head `135fd085002bf8074d87308beca35ab33c35ed47`. Relative to normalized R15.1 `main`, the technical source changes exactly seven net paths:

- `.github/workflows/r15-2-experience-capture.yml`;
- `docs/continuity/KODEPOIA_CONTINUITY.md` — START-sync only;
- `docs/roadmap/R15_PLAN.md` — START-sync only;
- `schemas/experience-capture-v1.schema.json`;
- `src/kodepoia/experience/__init__.py`;
- `src/kodepoia/experience/collector.py`;
- `tests/test_experience_collector.py`.

No temporary CI helper or wake-marker survives in the technical source.

## Authoritative technical gates

All following runs checked out exact source `48b519c09fa50f5407cc4a55a0b76baf6f8e8ffd`:

| Gate | Run | Result |
| --- | --- | --- |
| R15.2 Validated Experience Capture Acceptance #4 | `33272926744` | SUCCESS Ubuntu + Windows |
| R15.1 Experience Contracts Acceptance #19 | `33272926691` | SUCCESS Ubuntu + Windows |
| R0 Repository Guard #2069 | `33272926687` | SUCCESS |
| Python Core #2044 | `33272926696` | SUCCESS 5/5 |
| KodeStudio UI Smoke #2009 | `33272926737` | SUCCESS |

The focused R15.2 job executed **33 tests per OS** across the accepted R15.1 contract regression suite plus the R15.2 collector suite, followed by Ruff and compile, all successful.

## Focused acceptance matrix

| Requirement | Evidence | Result |
| --- | --- | --- |
| Capture disabled by default | `test_capture_is_disabled_by_default_without_raw_or_audit_write` | PASS |
| Explicit project opt-in | `test_project_and_source_require_repository_policy_opt_in` | PASS |
| Explicit source-type policy | same test | PASS |
| Explicit validated terminal outcome | `test_unvalidated_or_unknown_outcomes_are_not_captured` | PASS |
| `UNKNOWN` outcome blocked | same test | PASS |
| Accepted capture does not become training-eligible | `test_accepted_capture_is_observed_and_training_disabled` | PASS |
| Sanitization does not run implicitly | same test (`not_run`) | PASS |
| Duplicate delivery is idempotent | `test_identical_event_replay_is_idempotent_without_audit_inflation` | PASS |
| Event replay conflict fails closed | `test_replayed_event_with_changed_payload_fails_closed` | PASS |
| Negative outcomes require explicit diagnostic policy | `test_negative_outcomes_need_explicit_diagnostic_policy_and_stay_quarantined` | PASS |
| Negative captures remain quarantined | same test | PASS |
| Correction provenance explicit | `test_correction_provenance_is_explicit_and_scope_confined` | PASS |
| Cross-project correction link rejected | same test | PASS |
| Per-record quota | `test_payload_record_count_and_project_byte_quotas_fail_closed` | PASS |
| Per-project record-count quota | same test | PASS |
| Per-project aggregate-byte quota | same test | PASS |
| Same payload physically isolated across projects | `test_same_payload_is_physically_isolated_between_projects` | PASS |
| Audit/status/summary do not echo raw synthetic secret | `test_audit_and_status_never_echo_raw_secret_or_storage_key` | PASS |
| Audit/status/summary do not expose `storage_key` or raw path | same test | PASS |
| Guardian write permission required | `test_guardian_permission_is_required_for_raw_write` | PASS |
| Raw object tamper detected | `test_tampered_raw_object_is_rejected_on_inspection` | PASS |
| Manifest/record digest tamper detected | `test_tampered_manifest_digest_is_rejected` | PASS |
| Capture envelope validates as JSON Schema 2020-12 | `test_capture_schema_and_nested_experience_schema_validate` | PASS |
| Nested R15.1 record schema remains valid | same test | PASS |
| R15.1 regression preserved | `tests/test_experience_contracts.py` inside focused workflow | PASS |

## Security/governance acceptance

### Default denial

`CapturePolicy()` has `enabled=False`, no opted-in project and no allowed source type. Disabled capture returns without creating raw bytes, record manifests or audit entries.

### Training eligibility remains disabled

Newly captured records enter only `OBSERVED` (accepted/corrected) or `QUARANTINED` (explicitly captured failed/rejected). `TrainingAuthorization` remains all `UNKNOWN`; sanitation remains `NOT_RUN`. R15.2 therefore cannot manufacture `ELIGIBLE` state.

### No outcome inference

The capture API requires the caller to provide `validated=True`, a validation reference and validator identity. R15.2 does not inspect exit code, process completion, exception absence or user silence and therefore cannot treat them as evidence of acceptance.

### Project/workspace isolation

Replay identity includes workspace + project + event. Raw objects are stored beneath a scope hash derived from workspace + project. Identical bytes captured for two projects therefore occupy distinct scoped object paths.

### Integrity

Content is SHA-256/length checked before and after atomic promotion. Read/inspect verifies the envelope shape, scoped event key, nested record digest, storage-scope prefix and raw-object digest/length. Corrupt state raises instead of being treated as ready.

### Guardian and audit

Durable raw/staging/manifest/audit writes require Guardian `FILE_WRITE`. Audit events use the accepted append-only tamper-evident `AuditLog` and contain bounded metadata only. Tests prove that a synthetic secret from the raw payload, the `storage_key` field name and the managed `experience/raw/` path do not appear in audit/status/summary output.

## Rejected/non-authoritative candidates

- Early candidate before Ruff fix: R15.1 regression tests passed but Ruff reported two `UP012` findings. It is rejected as a source of final evidence.
- Marker-present candidate `dd2b4e47…`: focused R15.2 succeeded, but the temporary CI wake file existed. It is rejected as authority.
- Clean-push campaigns R15.2 #3 / `33272857930` and R15.1 #10 / `33272857993` were useful pre-PR confirmation, but the PR exact-head campaign on `48b519c0…` is authoritative.

No rejected candidate's evidence is needed to make the accepted technical source pass.

## External-reference verification

Official JSON Schema documentation identifies Draft 2020-12 as the current specification. The R15.2 capture schema uses that dialect.

OWASP logging guidance says secrets/tokens/sensitive data should generally not be recorded directly and notes that file paths may need special treatment. R15.2 implements a stricter capture-audit boundary by excluding raw payloads, storage keys and raw Vault paths from audit/status/summary surfaces.

These external references are non-normative; Kodepoia's frozen R1/R6/R8/R15 governance remains authoritative.

## Manual intervention

**NONE.**

No live model, GPU, external provider, production credential, external dataset, legal decision or device-only acceptance is required for R15.2.

## END-head rule

This document is part of END-sync and therefore changes bytes after the immutable technical source. R15.2 must not be merged on technical-source evidence alone. After END-sync is complete, the clean END-head must receive fresh:

1. R15.2 Validated Experience Capture Acceptance on Ubuntu + Windows;
2. R0 Repository Guard;
3. full Python Core;
4. KodeStudio UI Smoke.

Only after those gates are successful may the R15.2 PR be merged with exact expected head SHA. A single post-merge continuity-only normalization must then receive fresh R0/Python/UI and merge before R15.3 START-sync.
