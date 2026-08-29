# R15.1 Design — Experience contracts, eligibility state machine + training-data trust boundary

## Purpose

R15.1 creates the canonical contract boundary that prevents ordinary logs, conversations, project files, model outputs or tool results from silently becoming training data. It defines identities, state, references and fail-closed policy facts only. Collection is R15.2; sanitization/license policy is R15.3; deduplication/benchmark isolation is R15.4; dataset construction is R15.5.

## Core invariant

**Sanitization cannot launder an unauthorized source into training eligibility.**

A source that is denied, unknown or review-only for any required authorization dimension remains non-training-eligible even if secret/privacy redaction reports `PASSED`. Redaction is permitted only as a transformation of content that is otherwise independently authorized. It never converts forbidden/private/out-of-scope/unlicensed data into allowed training data.

The five independent authorization dimensions are:

- `source_scope`;
- `consent`;
- `provenance`;
- `license`;
- `privacy`.

Each defaults to `UNKNOWN`; all five must be explicitly `ALLOW` before the record can cross from `OBSERVED` to `ELIGIBLE`. A benchmark-protected record is vetoed independently of these five facts.

## Canonical state model

Happy-path promotion is deliberately staged:

`OBSERVED -> ELIGIBLE -> SANITIZED -> CURATED -> DATASET_INCLUDED`

Policy/terminal states are `REJECTED`, `QUARANTINED`, `REVOKED` and `EXPIRED`.

Allowed transitions are:

| From | Allowed targets |
| --- | --- |
| `OBSERVED` | `ELIGIBLE`, `REJECTED`, `QUARANTINED`, `EXPIRED` |
| `ELIGIBLE` | `SANITIZED`, `REJECTED`, `QUARANTINED`, `REVOKED`, `EXPIRED` |
| `SANITIZED` | `CURATED`, `REJECTED`, `QUARANTINED`, `REVOKED`, `EXPIRED` |
| `CURATED` | `DATASET_INCLUDED`, `REJECTED`, `QUARANTINED`, `REVOKED`, `EXPIRED` |
| `DATASET_INCLUDED` | `REVOKED`, `EXPIRED` |
| terminal alternatives | no outgoing transition in R15.1 |

Skipping eligibility/sanitization/curation is rejected. Promotion to `SANITIZED`, `CURATED` or `DATASET_INCLUDED` requires `SanitizationStatus.PASSED` with a sanitizer digest. R15.1 records this evidence but does not implement the sanitizer itself.

## Immutable identities and content references

`ExperienceId` is immutable and deterministically derived from workspace identity, source identity and origin digest. Content remains outside audit/status records and is addressed through `ContentRef` containing:

- workspace identity;
- governed relative storage key;
- SHA-256 digest;
- byte length;
- media type.

Absolute paths, drive-qualified paths, empty/dot segments and traversal (`..`) are rejected. A content reference from another workspace is rejected. R15.1 does not implement a new vault; it exposes `ExperienceContentStore` as a protocol so R15.2+ can bind the accepted governed storage authority.

## Provenance and transformation lineage

`ProvenanceDescriptor` records stable source type/source ID, origin digest, project scope and an optional license expression. R15.1 deliberately does not infer legal permission from that expression: the authoritative license decision remains an independent `PolicyDecision`, and actual SPDX-aware parsing/policy belongs to R15.3.

`TransformationRef` binds transformation ID, input digest, output digest and policy digest. Later sanitizer/dedup/dataset stages can therefore add derived transformations without overwriting source identity.

## Serialization and redaction boundary

`ExperienceRecord.canonical_json()` uses deterministic UTF-8 JSON with sorted keys and compact separators; `contract_digest()` is SHA-256 over those canonical bytes.

`audit_summary()` contains safe metadata, digests, policy blockers, sanitization categories/counts and benchmark protection state. It does not contain raw payload bytes and deliberately omits the governed `storage_key`.

The repository schema is `schemas/experience-record-v1.schema.json`, dialect JSON Schema 2020-12, schema name `kodepoia.experience.record`, version `1`. Schema validation is part of the focused acceptance tests.

## Protocol boundaries

R15.1 introduces interfaces, not duplicate persistence systems:

- `ExperienceRegistry.get/save` — record registry contract;
- `ExperienceContentStore.exists/verify_digest` — governed content-store contract.

R15.2 will implement capture/storage integration against accepted R1/R6/R8 authorities. R15.1 therefore has no automatic recording, no filesystem crawler, no chat harvesting and no training process.

## Audit and permission integration

State transitions require an explicit actor and policy reason and return structured transition metadata suitable for the existing append-only audit authority. R15.1 does not create a second AuditLog or Guardian. Later orchestration must pass these transition events to the accepted R1 audit/permission boundaries.

## Benchmark firewall seed

`benchmark_protected` is a hard trust-boundary veto. Such a record cannot become `ELIGIBLE` or `DATASET_INCLUDED`, regardless of all other authorization values. R15.4 will replace the simple flag decision input with the protected-signature/near-duplicate contamination authority.

## Security properties

R15.1 guarantees at contract level:

1. training eligibility is disabled/fail-closed by default;
2. sanitizer success cannot override source/consent/provenance/license/privacy denial or uncertainty;
3. benchmark-protected content cannot become training data;
4. cross-workspace content references are rejected;
5. storage traversal/absolute-path escapes are rejected;
6. content is digest-bound and not embedded into audit summaries;
7. IDs and records are immutable dataclasses;
8. canonical serialization is deterministic;
9. unsupported schema name/version is rejected;
10. terminal state resurrection and promotion skipping are rejected.

## Explicit non-claims

R15.1 does not claim that:

- a supplied license expression is valid or training-compatible;
- content has actually been sanitized;
- consent has been collected;
- a source has been legally reviewed;
- benchmark near-duplicate scanning exists;
- a dataset exists;
- any model has been trained.

Those authorities are intentionally deferred to later frozen subdivisions.
