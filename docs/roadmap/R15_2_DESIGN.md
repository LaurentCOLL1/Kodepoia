# R15.2 — Governed validated-experience capture design

**Phase:** R15.2  
**Status:** END-SYNC COMPLETE / EXACT END-HEAD RE-GATES PENDING
**Clean START-head:** `135fd085002bf8074d87308beca35ab33c35ed47`  
**Immutable technical source:** `48b519c09fa50f5407cc4a55a0b76baf6f8e8ffd`  
**Normalized R15.1 base:** `f6681cdc072fdbd9eb8ebcf2c109859df31fb30f`  
**Manual intervention:** NONE

## Purpose

R15.2 introduces a governed capture boundary for validated terminal experiences. It does not create a training dataset, does not promote records to training eligibility, and does not infer quality from process success alone. Its only responsibility is to preserve explicitly validated outcomes as auditable raw/quarantined evidence under project/workspace scope so later R15 subdivisions can curate them without bypassing R15.1 authorization contracts.

## Frozen safety invariants

1. Capture is disabled by default.
2. A project must be explicitly opted in by repository/application policy.
3. The source type must be explicitly allowed by policy.
4. The terminal outcome must be explicitly validated; absence of an error, exit code 0, or lack of user complaint is not validation.
5. `UNKNOWN` outcomes are never captured.
6. `FAILED` and `REJECTED` outcomes require explicit diagnostic-capture policy and remain `QUARANTINED`.
7. `ACCEPTED` and `CORRECTED` captures enter only `OBSERVED`; capture never grants training eligibility.
8. Every newly captured `ExperienceRecord` retains the R15.1 fail-closed defaults: all `TrainingAuthorization` axes remain `UNKNOWN` and sanitation remains `NOT_RUN`.
9. Sanitization/redaction is not performed by R15.2 and can never compensate for denied/unknown source, consent, provenance, license or privacy authorization.
10. Raw content never appears in audit/status/summary surfaces. Storage keys and managed raw paths are also excluded from those surfaces.
11. All durable writes are confined through the accepted R8 `VaultBoundary` and require R1 Guardian `FILE_WRITE` authorization.
12. No process, shell or network execution surface is introduced.

## Capture policy

`CapturePolicy` is immutable and has conservative defaults:

- `enabled = False`;
- no opted-in projects;
- no allowed source types;
- explicit allowed media types (`text/plain`, `application/json` by default);
- per-record byte limit;
- per-project record-count limit;
- per-project aggregate byte limit;
- negative-outcome capture disabled unless explicitly enabled for diagnostics.

The normalized policy is SHA-256 digested and recorded with each capture envelope and safe audit event. A policy digest is evidence of the policy inputs used for capture, not an authorization token and not a legal conclusion.

## Validated terminal outcome contract

`ValidatedOutcome` records stable identifiers for:

- replay/event identity;
- workspace and project;
- source type and source identity;
- task and domain labels;
- action/result/validation references;
- validator identity;
- explicit validation boolean;
- outcome label (`accepted`, `rejected`, `corrected`, `failed`, `unknown`);
- origin digest;
- optional license expression as evidence only;
- optional correction provenance.

The contract intentionally carries references and digests rather than arbitrary executable commands or external paths.

## Correction provenance

A `CORRECTED` outcome must carry `CorrectionProvenance` linking:

- the original experience ID;
- original workspace and project;
- original content digest;
- evaluator identity.

The correction must remain in the same workspace/project scope. Cross-scope correction linkage is rejected before storage. R15.2 does not decide whether the correction is training-eligible; it only preserves the explicit relationship for later curation.

## Replay-safe identity and idempotence

Replay identity is derived from `workspace_id + project_id + event_id`. The collector also computes a request digest over stable outcome metadata, correction provenance, payload digest and media type.

- exact replay of the same scoped event and request returns `IDEMPOTENT` and does not add a second audit entry;
- reuse of the event ID with changed content or metadata raises `CaptureConflict` and fails closed;
- event IDs are never global across projects/workspaces.

## Raw Vault layout and physical project isolation

R15.2 composes the accepted R8 `VaultBoundary`. It does not expose arbitrary filesystem access and does not weaken `WorkspaceBoundary` semantics.

Raw objects are content-addressed **inside a workspace/project-specific scope**:

`experience/raw/scopes/<scope-hash>/objects/sha256/<prefix>/<sha256>`

Capture manifests are stored under:

`experience/raw/scopes/<scope-hash>/records/<event-hash>.json`

Temporary writes use a `.staging` directory inside the same scope.

The scope hash is derived from workspace + project identity. Consequently, identical bytes in two projects are physically isolated instead of being globally deduplicated. This deliberately favors deletion/privacy isolation over cross-project raw-data deduplication. Later curated/exportable artifacts may use other accepted Vault reuse rules only after explicit governance.

## Integrity and crash behavior

Raw content is staged, SHA-256/length verified, atomically promoted with `os.replace`, then reverified. Existing content-addressed objects are accepted only after exact digest/length verification.

Capture manifests contain:

- schema/version;
- scoped event key;
- replay request digest;
- nested R15.1 record digest;
- policy digest;
- validator/validation/action/result references;
- correction provenance when applicable;
- nested `ExperienceRecord`.

On read/inspect, envelope shape, event key, nested record digest, scoped storage prefix and raw object SHA-256/length are revalidated. Corruption is surfaced as `CaptureStorageError`; path existence never manufactures validity.

R15.2 does not introduce SQLite and therefore does not claim database transactional guarantees. The accepted implementation uses atomic file promotion plus digest verification for this raw capture layer.

## Audit model

Successful capture appends only safe structured metadata to the accepted tamper-evident `AuditLog`:

- disposition;
- experience/event/workspace/project identifiers;
- outcome/state;
- content SHA-256 and byte length;
- media type;
- validator/validation references;
- correction-of ID when present;
- policy digest.

Raw payload, storage key and managed raw path are never copied into the event. Quota-block audit events likewise record only bounded identifiers/reason/policy digest.

If a manifest was committed but audit append fails, the manifest is removed and the operation raises. A content-addressed raw object may remain orphaned; it is not referenced as a completed capture and can be reclaimed by later governed maintenance. This is preferable to reporting a completed capture without the required audit event.

## Quotas and denial behavior

R15.2 enforces three independent limits before committing a new record:

- per-record bytes;
- records per project;
- aggregate captured bytes per project.

Limit violations return `QUOTA_BLOCKED`; no record manifest is created. Record-count/aggregate quota violations generate a safe audit event. The per-record oversized case is rejected before raw bytes are written.

## Training boundary

R15.2 is deliberately **capture-only**. It cannot move a record from `OBSERVED`/`QUARANTINED` into `ELIGIBLE`, `CURATED` or any training state. It never changes R15.1 source/consent/provenance/license/privacy decisions and never runs sanitization. R15.3+ must consume these records through the R15.1 state machine and policy axes rather than interpreting their mere presence in the raw Vault as permission.

## Public API

The stable R15.2 surface exported from `kodepoia.experience` is:

- `ExperienceCollector`;
- `CapturePolicy`;
- `ValidatedOutcome`;
- `CorrectionProvenance`;
- `CaptureDisposition`;
- `CaptureResult` / `CaptureSummary`;
- `CaptureError`, `CaptureConflict`, `CaptureStorageError`;
- capture schema name/version constants.

No raw filesystem helper is exposed to model-facing callers.

## Schema

`schemas/experience-capture-v1.schema.json` uses JSON Schema Draft 2020-12 and validates the capture envelope. Tests additionally validate the nested record against the accepted `experience-record-v1` schema, preventing the capture envelope from weakening R15.1 record contracts.

## External reference notes (non-normative)

Current official JSON Schema documentation identifies Draft 2020-12 as the current specification, matching the accepted R15 schema dialect. OWASP application-logging guidance recommends removing/masking/sanitizing or otherwise protecting secrets, tokens and sensitive data and notes that file paths may also require special handling. R15.2's safe audit/status surfaces are intentionally stricter: raw payloads, storage keys and raw Vault paths are excluded entirely.

These references inform compatibility/security practice only; they do not override the frozen Kodepoia governance model.

## Technical acceptance evidence

Immutable technical source `48b519c09fa50f5407cc4a55a0b76baf6f8e8ffd` passed:

- R15.2 Validated Experience Capture Acceptance #4 / `33272926744`: SUCCESS Ubuntu + Windows, exact checkout, 33 focused/regression tests per OS, Ruff PASS, compile PASS;
- R15.1 Experience Contracts Acceptance #19 / `33272926691`: SUCCESS;
- R0 Repository Guard #2069 / `33272926687`: SUCCESS;
- Python Core #2044 / `33272926696`: SUCCESS 5/5;
- KodeStudio UI Smoke #2009 / `33272926737`: SUCCESS.

A previous clean-push focused campaign also passed R15.2 #3 / `33272857930` and R15.1 regression #10 / `33272857993` on the same source content lineage. The PR exact-head campaign above is authoritative for technical-source acceptance.

## Manual intervention

**NONE.** No live external provider, GPU, credential, model weight, legal review or user-device execution is required by R15.2 acceptance.

## Rollback

R15.2 introduces only additive capture code/schema/tests/workflow and raw Vault layout. Rollback removes the collector/public exports/schema/workflow and stops capture. Existing raw records remain governed Vault data and must be deleted only through an explicit later deletion/retention operation; rollback must not silently erase captured evidence.
