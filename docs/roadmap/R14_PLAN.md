# Kodepoia — R14 detailed phase plan

**Phase:** R14  
**Roadmap title:** Backend / Platform Services / LiveOps  
**Status:** IN PROGRESS
**Phase planning started:** 2026-08-28  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`  
**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.7 are COMPLETE + NORMALIZED. R14.7 implementation/evidence PR #269 merged as `763ce96c4f82da2eaec167b56ffb62d9e548b300`; its single continuity-only normalization PR #270 merged as normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after R0 #1810, Python Core #1784 and UI #1751, all SUCCESS. R14.8 technical source `8132c4029983f693a32e0d26903d05e347313bf6` is accepted after R0 #1822, Python Core #1796, UI #1763 and R14 Cloud Save Acceptance #6, all SUCCESS. R14.8 is COMPLETE at END-sync; final exact-head re-gates, protected merge and the single continuity-only normalization remain required. R14.9–R14.17 remain PLANNED. R14.8 manual state is NONE.

## Purpose and authority

R14 implements the frozen-roadmap capability **“Conditionnel. Auth, DB, authoritative server, matchmaking/lobby, cloud saves, achievements/entitlements/billing, remote config/feature flags/content delivery/events.”** It extends the accepted R1–R13 local-first, governed development platform without replacing their security, provenance, release, client or product architecture.

“Conditionnel” means backend/platform/live-service capabilities are generated and activated only when Project DNA / KodeProduct intent requires them. It does **not** mean a paid cloud account, public Internet deployment, production database, real billing account or physical device is a global prerequisite for core acceptance. Provider-specific live claims remain explicit capability states and may be `UNAVAILABLE` or `CONDITIONAL` without invalidating provider-neutral local/core behavior.

This file is the exhaustive execution and recovery authority for R14. The subdivision list R14.1–R14.17 is frozen when the planning PR and its single planning continuity normalization are accepted. No subdivision may be silently added, removed, merged, split or renumbered. Scope/status/manual-state changes must update this plan and continuity in the same work cycle; architecture changes require an ADR when they cross the frozen v1.0 boundary.

## Permanent subdivision status synchronization rule

For every R14 subdivision:

1. **Start, before implementation:** prior normalized subdivisions are `COMPLETE`, the active subdivision becomes `IN_PROGRESS`, later subdivisions remain `PLANNED`; phase status/checkpoint and continuity are synchronized in the same work cycle.
2. **End, before final documentation/evidence re-gates:** the accepted active subdivision becomes `COMPLETE`; later subdivisions stay `PLANNED`; continuity is synchronized in the same work cycle.
3. A triggered manual gate uses truthful `BLOCKED` / `MANUAL_REQUIRED`, never synthetic `COMPLETE`.
4. Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
5. A stale subdivision index, stale phase status or reuse of evidence from a different head is an acceptance blocker.

## Phase objective

Deliver a deterministic, auditable, provider-neutral backend/platform-services/LiveOps capability that lets Kodepoia:

- represent backend intent in Project DNA/KodeProduct without silently adding services to projects that do not need them;
- scaffold a local deterministic backend with explicit environments, typed configuration and secrets boundaries;
- provide modern auth/identity/session contracts, including passwordless/passkey-capable and OIDC-compatible boundaries, without coupling core architecture to one vendor;
- use a transactional authoritative database with migrations, schema lineage, backup/restore and concurrency safety;
- model an authoritative server where clients submit intent and never directly own trusted game/application state;
- provide matchmaking, lobbies, reservations, presence and reconnect semantics;
- provide cloud-save synchronization with immutable revisions, conflict resolution, idempotency and rollback/recovery;
- provide achievements, stats and leaderboards as authoritative progression services;
- provide entitlements/billing/catalog and provider notification adapters with server-side verification semantics, without storing production credentials in repo/evidence/model-visible data;
- provide remote configuration, feature flags, targeting and safe rollout/rollback;
- provide versioned content delivery with signed/hashed manifests, immutable content identity, cache/provenance and rollback;
- provide an event pipeline with typed envelopes, deduplication, replay/checkpoints, retention and privacy/redaction controls;
- provide LiveOps campaigns/seasons/schedules/rotations with preview, approval, activation, expiry and rollback;
- provide health/readiness, rate limits, resilience, observability, backup/restore/DR and load/budget evidence;
- expose the above through structured CLI and KodeStudio workflows;
- close the phase with adversarial integrated exact-head acceptance that proves cross-service consistency without circular evidence.

## Explicitly out of scope

R14 does **not** implement R15 experience collection / benchmark-driven fine-tuning, QLoRA, GGUF/Ollama specialization or before/after model training evaluation. R14 also does **not** replace R16 final red-team/beta/v1.0 hardening.

Also outside R14 unless separately accepted by ADR:

- provider lock-in as the canonical architecture;
- mandatory Kubernetes, service mesh or managed cloud platform for core acceptance;
- arbitrary shell/deployment scripts generated by model/project text;
- direct production deployment from unreviewed model output;
- storing passwords, refresh/access tokens, private keys, database passwords, billing secrets or provider credentials in Project DNA, generated source, Git, logs, evidence or raw model-visible argv;
- treating client-side purchase receipts or client state as authoritative entitlement truth;
- silent production database destructive migration;
- silent remote flag activation, content publication, event replay, entitlement mutation or public LiveOps activation;
- advertising/marketing attribution pipelines, social-network services or generic analytics warehouses beyond the event/observability boundaries required by the frozen roadmap;
- blockchain/crypto assets, user-generated marketplace economy or payment processing outside app/platform billing contracts;
- global account federation beyond provider-neutral OIDC/passkey capability unless a later accepted scope decision requires it.

## Current external compatibility baseline — 2026-08-28

External standards and provider behavior are **versioned/effective-date evidence**, never permanent architecture constants. R14 capability-probes supported runtime/provider versions and preserves source/effective-date provenance.

### Authentication / identity

- OAuth 2.0 Security Best Current Practice is RFC 9700 (2025). R14 treats deprecated/insecure OAuth behaviors as non-authoritative and validates redirect, token and client security against current BCP evidence.
- JWT handling follows RFC 8725 security guidance: explicit algorithm policy, issuer/audience validation, typed/segregated token use and cryptographic agility; algorithm selection is never taken from untrusted project/model text.
- NIST SP 800-63B-4 (final 2025) is an informative authenticator/session assurance baseline, not a universal application policy mandate.
- WebAuthn Level 3 became a W3C Recommendation on 2026-08-25. R14 models passkey/public-key credential capability without making a browser vendor or external identity provider mandatory.
- OpenID Connect Core remains the provider-neutral identity interoperability baseline where federated login is requested.

Official references:

- https://www.rfc-editor.org/rfc/rfc9700
- https://www.rfc-editor.org/rfc/rfc8725
- https://pages.nist.gov/800-63-4/sp800-63b.html
- https://www.w3.org/TR/webauthn-3/
- https://openid.net/specs/openid-connect-core-1_0.html

### Database baseline

- PostgreSQL 18 is the current stable major family; PostgreSQL 18.6 was released 2026-08-13 and is supported through 2030-11-14. PostgreSQL 19 Beta 3 is testing-only and must not be promoted as production authority.
- R14 CI may use a supported stable PostgreSQL 18.x service/container/runtime as current compatibility evidence, while runtime architecture remains version-capability based rather than patch-pinned forever.
- Database migrations are repository-owned typed artifacts with checksums/lineage; no model-supplied raw migration command may execute directly.

Official references:

- https://www.postgresql.org/support/versioning/
- https://www.postgresql.org/docs/release/18.6/

### Billing / entitlement provider baseline

- Google Play billing guidance requires backend lifecycle management for authoritative entitlement consistency. Real-time developer notifications indicate that state changed; the backend must query authoritative purchase state and deduplicate/replay safely.
- Apple entitlement state is derived from validated transaction/subscription state. App Store Server Notifications use an HTTPS server endpoint; current implementations use the current notification API generation and can be exercised in sandbox/test mode.
- Real store accounts, production credentials and real-money transactions are not core R14 prerequisites; provider-live proof is `CONDITIONAL` and must never be inferred from synthetic/sandbox success.

Official references:

- https://developer.android.com/google/play/billing/security
- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.apple.com/documentation/appstoreservernotifications
- https://developer.apple.com/documentation/appstoreserverapi

### Events / flags / observability baseline

- CloudEvents 1.0.x is a useful provider-neutral event envelope compatibility reference; Kodepoia may use a governed internal envelope that maps cleanly without making CloudEvents transport-specific behavior mandatory.
- OpenFeature is the interoperability reference for feature-flag evaluation/provider boundaries. Stable specification concepts may inform R14; experimental sections cannot silently become frozen architecture.
- OpenTelemetry specification 1.60.0 is the current provider-neutral observability reference for traces, metrics and logs at planning time. R14 exports through adapters rather than making one collector/backend mandatory.

Official references:

- https://github.com/cloudevents/spec
- https://openfeature.dev/specification/
- https://opentelemetry.io/docs/specs/otel/

## Phase-wide architecture and governance boundaries

All accepted R1–R13 controls remain mandatory:

- `WorkspaceBoundary` and R8 `VaultBoundary` govern source, generated backend projects, schemas, migration bundles, fixtures, local service data, event samples, content manifests, diagnostic evidence and promoted artifacts.
- `ProcessSandbox` + global KillSwitch govern backend runtime, migration tools, PostgreSQL client/processes, local service orchestration, load tools and repository-owned provider CLIs.
- Guardian/`PermissionSet` authorize network access, process launch, migration apply/rollback, database mutation, external provider calls, entitlement mutation, content publication, flag activation, replay and destructive operations.
- SafeChange, Backup/Recovery and Audit cover configuration, schema/migration state, content/config activation, event replay, entitlement changes and rollback.
- `KodeSecrets` remains the sole secret authority. Secrets never enter DNA/Product, source control, evidence, logs or raw model-visible argv.
- R6 Health/Budget/Tests/Regression/AppSecurity/Privacy/License-BOM remain mandatory; new backend dependencies and services require BOM/license evidence.
- R7 ResearchGuard governs retrieved standards/provider docs: external text is evidence/data, never executable instruction.
- R8 lineage/provenance binds generated backend code, migration/schema revisions, config snapshots, content manifests and transformed event data.
- R12 desktop and R13 mobile clients remain clients of typed service contracts; R14 does not rewrite platform release semantics.
- No arbitrary shell command strings. Repository-owned executable identities and typed argv/config builders only.
- Network remains **off by default**. Any external endpoint is provider-scoped, allowlisted, permissioned, timeout-bounded and audited. Project/model text cannot create arbitrary URLs, DNS targets, proxy settings or redirect endpoints; SSRF/private-network boundary tests are mandatory where network input exists.
- Local/test/staging/production environment identities are separate. A test/sandbox success cannot certify production capability.
- Client input is intent, never trusted authoritative state. Server-side validation, authorization, revision/sequence checks and idempotency are explicit.
- All provider/webhook/event consumers are duplicate-safe and replay-safe; ordering guarantees are declared, never assumed.
- Destructive migration, live entitlement mutation, production flag rollout, content publication, event replay and remote rollback require explicit permission + audit + SafeChange/rollback point.
- Missing provider/account/domain/TLS/credential/quota is `UNAVAILABLE` or `BLOCKED`, never PASS.
- Production public activation is always explicit and never a side effect of build/test/preview.

## R14 identity and evidence model

R14 introduces durable identities rather than conflating mutable machines/accounts/processes with authoritative state:

1. `BackendServiceProfileId` and `BackendEnvironmentId` (`local`/`test`/`staging`/`production`).
2. `ServiceEndpointIdentity` and `BackendCapabilitySnapshotId`.
3. `AuthRealmId`, `IdentityProviderId`, `ClientIdentityId`, `AccountIdentityId`, `SessionId`, `AuthenticatorCredentialId`.
4. `BackendSchemaId`, `MigrationId`, `DatabaseSnapshotId`, `TransactionEvidenceId`.
5. `AuthorityDomainId`, `ServerInstanceId`, `CommandId`, `StateRevisionId`.
6. `LobbyId`, `MatchmakingTicketId`, `MatchReservationId`, `MatchId`, `PresenceRevisionId`.
7. `CloudSaveSlotId`, `SaveRevisionId`, `SaveConflictId`, `ConflictResolutionId`.
8. `AchievementDefinitionId`, `StatDefinitionId`, `LeaderboardDefinitionId`, `ProgressionRevisionId`.
9. `ProductCatalogId`, `StoreProductIdentity`, `PurchaseIdentity`, `EntitlementId`, `BillingProviderEventId`.
10. `ConfigSnapshotId`, `FeatureFlagId`, `EvaluationRevisionId`, `RolloutId`.
11. `ContentManifestId`, `ContentBundleId`, `DeliveryChannelId`, `ContentPromotionId`.
12. `EventEnvelopeId`, `EventStreamId`, `ConsumerCheckpointId`, `ReplayId`.
13. `LiveOpsCampaignId`, `SeasonId`, `ScheduleId`, `ActivationId`.
14. `ServiceHealthSnapshotId`, `BackupId`, `RestoreTestId`, `LoadProfileId`.
15. `R14IntegratedEvidenceDigest` — anti-circular phase evidence identity.

## Service and LiveOps budget model

R14 extends R6 Budget with bounded metrics and no synthetic PASS:

- request throughput, error rate and p50/p95/p99 latency;
- active/concurrent sessions and connection counts;
- DB query wall time, affected rows, lock/deadlock count, pool utilization and migration duration;
- matchmaking queue time, ticket count, reservation expiry and reconnect latency;
- cloud-save payload bytes, sync latency, conflict count and retained revision bytes;
- billing notification lag, duplicate count, verification latency and entitlement convergence;
- feature-flag evaluation latency/cache size and rollout population bounds;
- content manifest/bundle bytes, cache hit/miss, download wall time and rollback storage;
- event throughput, queue/backlog depth, dedupe/replay count, retention bytes and consumer lag;
- traces/metrics/log bytes and redaction failures;
- backup duration/bytes and tested RPO/RTO values;
- service process CPU/memory/network/open-file/process counts;
- optional provider quota/cost evidence when an external provider is actually used.

Budget overrun is explicit `BUDGET_EXCEEDED`, not PASS.

## Global prerequisites

Before R14.1 implementation:

- R1–R13 are `COMPLETE + NORMALIZED` on `main`.
- R13 canonical integrated report remains `status=pass`, `blockers=[]`, semantic digest `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`.
- R14 planning PR is merged and exactly one continuity-only planning normalization is merged after fresh exact-head R0 + full Python Core + KodeStudio UI Smoke.
- Python remains 3.12.x unless an accepted later decision changes it.
- Hosted CI may provision public test dependencies/services such as a supported PostgreSQL instance; Kodepoia runtime may not silently install or deploy services.
- Production domains, TLS certificates, IdP tenants, managed databases, app-store billing accounts, CDN accounts, production signing secrets and paid cloud access are **not** global prerequisites.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | COMPLETE | NONE | R13 COMPLETE + normalized R14 planning |
| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | COMPLETE | NONE | R14.1 + R2/R13 profile patterns |
| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | COMPLETE | NONE | R14.1–R14.2 + R8/R12 patterns |
| R14.4 | Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary | COMPLETE | CONDITIONAL / NOT TRIGGERED | R14.1–R14.3 + R1/R6/R7 |
| R14.5 | PostgreSQL authoritative persistence, migrations, transactions + concurrency | COMPLETE | NONE | R14.1–R14.3 + R8/R12 |
| R14.6 | Authoritative server command/state model + real-time transport/trust boundary | COMPLETE | NONE | R14.4–R14.5 |
| R14.7 | Matchmaking, lobby, reservations, presence + reconnect | COMPLETE | NONE | R14.6 |
| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | COMPLETE | NONE | R14.5–R14.6 |
| R14.9 | Achievements, stats, leaderboards + authoritative progression | PLANNED | NONE | R14.5–R14.6 |
| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | PLANNED | CONDITIONAL | R14.4–R14.6 + R13 store contracts |
| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | PLANNED | NONE | R14.5–R14.6 |
| R14.12 | Content delivery: immutable manifests/bundles, channels, cache + rollback | PLANNED | CONDITIONAL | R14.5/R14.11 + R8/R13 release provenance |
| R14.13 | Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge | PLANNED | NONE | R14.5–R14.6 + R6 |
| R14.14 | LiveOps campaigns, seasons, schedules, rotations, activation + rollback | PLANNED | NONE | R14.10–R14.13 |
| R14.15 | Service operations/resilience: health, limits, retries, backup/restore, DR + load budgets | PLANNED | CONDITIONAL | R14.3–R14.14 + R6 |
| R14.16 | CLI + KodeStudio Backend/LiveOps UX, local stack control + dry-run/provider status | PLANNED | NONE | R14.1–R14.15 |
| R14.17 | Adversarial integrated backend/platform-services/LiveOps acceptance | PLANNED | CONDITIONAL | R14.1–R14.16 |

---

# R14.1 — Backend contracts, identities, capability model + secure network/runtime boundaries

## Objective and rationale

Create the provider-neutral contracts that prevent later services from inventing ad-hoc identities, environment semantics, URL handling, credentials or network/process execution. This subdivision is the trust boundary for all R14 work.

## In scope

Typed service/environment/capability identities; endpoint/transport descriptors; local/test/staging/prod separation; provider capability snapshots; network allowlist policy; timeout/retry budgets; structured error/status vocabulary; permission/audit hooks; base schemas and tests.

## Out of scope

Concrete auth, DB schema, server gameplay logic, provider billing, flags, content or events.

## Dependencies and prerequisites

Normalized R13 main and normalized R14 planning; existing Workspace/Vault/Guardian/ProcessSandbox/KodeSecrets/Audit/Health/Budget contracts.

## Detailed implementation plan

Add `src/kodepoia/backend/` foundations with immutable IDs, environment enum, capability snapshots, logical endpoint definitions and typed request/provider boundaries. Reject user/model-supplied executable paths, raw URLs outside allowlisted provider definitions, private/link-local metadata endpoints and implicit production promotion. Preserve safe redacted serialization and canonical hashing for evidence.

## Deliverables

Backend package foundation, JSON schemas, focused tests, DESIGN/ACCEPTANCE docs and any required R0 allowlist/manifest updates.

## Acceptance gates / Definition of Done

Focused contract/serialization/adversarial SSRF/redaction tests; full Python Core; R0; UI smoke; Ubuntu/Windows where applicable; exact-head evidence; PR merge; one continuity-only post-merge normalization.

## Validation and evidence

Exact source SHA, test counts, schema round-trip hashes, rejected unsafe endpoint fixtures, run IDs and final diff.

## Rollback / recovery

Remove new backend package/schema/docs and restore manifest references; no persistent external state exists.

## Risks and regression traps

SSRF, environment confusion, accidental production default, secrets in repr/logs, mutable identity hashing, model-controlled URLs.

## Manual intervention

**NONE.**

## Completion record

- Dedicated branch: `r14/08-cloud-saves`.
- Exact branch point: normalized `main` `24e40db2781db8e42591c6ffa8fbdb8f0bf84108` after the single accepted R14.7 continuity normalization.
- START state: R14.1–R14.7 COMPLETE + NORMALIZED; R14.8 IN_PROGRESS; R14.9–R14.17 PLANNED.
- Frozen R14.8 scope: server-authoritative save slots, immutable append-only revisions, payload/schema/content digests, explicit client base revision / compare-and-swap semantics, duplicate-safe idempotency, first-class conflict objects, deterministic resolution, quotas/retention bounds, integrity validation and append-only rollback/recovery. No silent last-write-wins, no provider lock-in and no production cloud account requirement.
- Immutable technical source: `8132c4029983f693a32e0d26903d05e347313bf6`.
- Exact-source gates: R0 Repository Guard #1822 / `33206330276`, Python Core #1796 / `33206330171`, KodeStudio UI Smoke #1763 / `33206330345`, R14 Cloud Save Acceptance #6 / `33206330291` — all SUCCESS.
- Python Core Ubuntu: **1564 passed / 13 skipped / 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS; internal KodeStudio smoke SUCCESS.
- Focused R14.8/R14.7/R14.6/R14.5 regression: **70 passed Ubuntu + 70 passed Windows**.
- Fourteen dedicated checks PASS on both OS: immutable revision, idempotent replay, idempotency rebind rejection, explicit conflict, conflict replay, deterministic resolution, double-resolution rejection, explicit migration, silent schema-change rejection, append-only rollback, object authorization, function authorization, integrity guard and bounded quota.
- Cross-platform semantic evidence: state `984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345`; trace `f071636d1c5c99614b91817d328bab43ec406daaf315621affecd45af42df5e8`; slot `24c423bfc661d2f8d207364c9d7058cb45413b7e15347beb78b50ca10c7345d1`; current revision `4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e`; resolved conflict `be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca`.
- Evidence state: `revision_count=5`, `retained_bytes=145`; budgets `max_payload_bytes=1024`, `max_revisions_per_slot=12`, `max_retained_bytes_per_slot=8192`, `max_open_conflicts_per_slot=3`.
- Artifacts: Ubuntu `9699802370` / `sha256:bfd9d7cadb002a822f5c0f399f32dc7410b62318a1dee7a0c3d480bd1c8398d8`; Windows `9699818533` / `sha256:748f1b5572d679e619d82aeda314a1fa1f4c688d7edfe6f84e41fe54424c5a0d`.
- Evidence schema: `schemas/r14/backend-cloud-save-evidence.schema.json`; `provider_live_claim=false`; `secrets_exposed=false`.
- External evidence baseline: RFC 9110 conditional-request semantics are informative lost-update/CAS evidence; Google Play Games Saved Games explicitly exposes conflict states/resolution policies; OWASP API1:2023 remains the object-authorization baseline. None is a provider dependency.
- Manual intervention: NONE.
- END state: R14.8 COMPLETE; R14.9–R14.17 remain PLANNED. R14.9 is not authorized until this END-sync head passes fresh exact-head R0 + full Python Core + KodeStudio UI Smoke + R14 Cloud Save Acceptance, PR #271 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

# R14.9 — Achievements, stats, leaderboards + authoritative progression

## Objective and rationale

Implement achievements and adjacent authoritative progression/stat ranking semantics needed to make achievements meaningful and cheat-resistant.

## In scope

Achievement definitions/versioning, stat definitions, progression events, unlock idempotency, leaderboard definitions/periods/ties/ranking snapshots, server-side validation and privacy/display controls.

## Out of scope

Platform-store achievement publication adapters unless later needed as a client/provider mapping; anti-cheat ML.

## Dependencies and prerequisites

R14.5–R14.6.

## Detailed implementation plan

Progression changes only from authoritative validated events/commands. Definitions are immutable/versioned; unlocks are idempotent. Leaderboard scores declare ordering/tie/reset policy; direct client score writes are forbidden. Expose provider-neutral client queries.

## Deliverables

Progression service/schema, definition format, fixtures, tests and docs.

## Acceptance gates / Definition of Done

Forged score rejection, duplicate unlock, period rollover, tie ordering, privacy filter and concurrency tests; R0/Python/UI.

## Validation and evidence

Definition/revision hashes, ranking snapshots, rejection evidence and CI.

## Rollback / recovery

Restore progression snapshot/recompute from authoritative event source where available; definition rollback by version, not mutation.

## Risks and regression traps

Client cheating, non-deterministic ranking, duplicate unlock, retroactive definition mutation.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.10 — Entitlements, billing/catalog + server-side provider verification/notifications

## Objective and rationale

Make purchase state and entitlements authoritative on the backend, preserving R13 store boundaries while preventing client receipts or notification arrival alone from granting access.

## In scope

Catalog/product mapping, purchase identity, entitlement state machine, Google Play/Apple provider adapter contracts, server-side verification, webhook/RTDN/App Store notification intake, signature/provider validation, dedupe, replay, reconciliation, refunds/revocation/expiry/grace states and sandbox fixtures.

## Out of scope

Acting as a payment processor, storing card data, automatic production store configuration and mandatory real-money transactions.

## Dependencies and prerequisites

R14.4–R14.6; R13 store/release identity contracts.

## Detailed implementation plan

Normalize provider events into immutable provider-event records, dedupe by provider/message identity, then query/verify authoritative provider state when required. Entitlement transitions occur transactionally and idempotently. Separate sandbox/test/production environments. Raw credentials and sensitive payload fields are redacted from model-visible evidence.

## Deliverables

Catalog/entitlement models, provider adapters, notification receiver, reconciliation worker, schemas, sandbox/synthetic fixtures, tests and docs.

## Acceptance gates / Definition of Done

Duplicate/out-of-order notification, pending→purchased, refund/revoke/expiry, invalid signature/token, reconciliation and entitlement convergence tests; R0/Python/UI; no live provider state claimed from sandbox.

## Validation and evidence

Provider docs/effective dates, normalized event digests, transition traces, sandbox status and exact-head CI.

## Rollback / recovery

Entitlement mutations are append/audit-driven; reconciliation can restore provider-authoritative state; no deletion of financial audit evidence within retention policy.

## Risks and regression traps

Granting on unverified client receipt, replay/double grant, cross-environment event confusion, leaking purchase tokens, provider API lag.

## Manual intervention

**CONDITIONAL.** Core acceptance uses synthetic/sandbox contracts. Real Apple/Google production account, product and transaction verification is required only for a provider-live claim; user must never send secrets/private keys/tokens.

## Completion record

To be appended when accepted.

---

# R14.11 — Remote config, feature flags, targeting + safe rollout/rollback

## Objective and rationale

Allow server-controlled behavior/configuration changes without unsafe hidden code execution or irreversible broad activation.

## In scope

Config snapshots, typed values/schema, feature flag definitions, evaluation context, deterministic targeting, percentage rollout, prerequisites, expiry, kill switch, preview/dry-run, activation approvals, audit and rollback. OpenFeature-compatible conceptual adapter boundary where stable.

## Out of scope

Remote arbitrary code, script execution and ad/marketing segmentation.

## Dependencies and prerequisites

R14.5–R14.6.

## Detailed implementation plan

Every config/flag definition is immutable/versioned. Evaluation uses canonical context fields and stable hashing for percentage rollout. Production activation requires permission/audit/SafeChange; unsupported/unknown flag types fail closed. Client receives resolved/authorized values, not secret rule internals when inappropriate.

## Deliverables

Config/flag service/schema, evaluator, rollout planner, preview/rollback tooling, tests and docs.

## Acceptance gates / Definition of Done

Stable percentage assignment, prerequisite cycles, expiry, schema mismatch, kill-switch, rollback and environment-isolation tests; R0/Python/UI.

## Validation and evidence

Snapshot/evaluation hashes, rollout distribution fixtures, audit/rollback evidence.

## Rollback / recovery

Reactivate prior immutable snapshot; no in-place mutation required.

## Risks and regression traps

Nondeterministic targeting, PII in context, production/test confusion, remote-code smuggling, irreversible rollout.

## Manual intervention

**NONE** for provider-neutral core.

## Completion record

To be appended when accepted.

---

# R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback

## Objective and rationale

Provide governed live content distribution distinct from executable self-update, preserving R8 asset lineage and R13 release constraints.

## In scope

Content manifests/bundle identity/hash/signature-state metadata, channels/variants, dependency graph, immutable object store abstraction, local HTTP fixture, cache/ETag/range capability, staged promotion, revocation/rollback and client compatibility constraints.

## Out of scope

Self-modifying executable binaries, bypassing app-store update rules and mandatory commercial CDN.

## Dependencies and prerequisites

R14.5/R14.11 + R8/R13 provenance/release semantics.

## Detailed implementation plan

Manifest references immutable content hashes and declared compatible client/schema versions. Promote channel pointers only after integrity/dependency/budget checks. Client download uses allowlisted endpoints, size/hash verification and atomic cache promotion. Rollback switches channel to a prior manifest.

## Deliverables

Content models/store interface, local provider, manifest schema, cache/downloader, promotion/rollback tooling, tests and docs.

## Acceptance gates / Definition of Done

Tampered/truncated/wrong-version/dependency-cycle/cache-corruption/rollback tests; bandwidth/storage budgets; R0/Python/UI; real CDN not needed for core.

## Validation and evidence

Manifest/bundle hashes, cache/promotion traces, local provider version and CI.

## Rollback / recovery

Prior immutable manifest/channel pointer; corrupt cache purged/rebuilt safely.

## Risks and regression traps

Executable smuggling, hash bypass, CDN URL injection/SSRF, stale cache, client incompatibility.

## Manual intervention

**CONDITIONAL.** External CDN/provider proof requires a real account/domain only if explicitly claimed; local deterministic delivery is core authority.

## Completion record

To be appended when accepted.

---

# R14.13 — Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge

## Objective and rationale

Create the frozen event pipeline used by LiveOps and service observability without turning logs/events into ungoverned data exfiltration.

## In scope

Typed event envelope, source/type/time/subject/trace identity, schema registry/version, append/publish/consume abstraction, local broker/store fixture, dedupe, checkpoint, replay, dead-letter/error state, retention, privacy classification/redaction and OpenTelemetry export bridge.

## Out of scope

Generic data warehouse/BI platform and mandatory Kafka/cloud event bus.

## Dependencies and prerequisites

R14.5–R14.6 + R6 privacy/observability.

## Detailed implementation plan

Use immutable event IDs and schema/version. Consumers checkpoint transactionally or with explicit at-least-once semantics; duplicate-safe handlers required. Replay requires permission, bounded range, dry-run and audit. Sensitive payload fields are classified/redacted before export. OTel adapters export traces/metrics/log correlation without provider lock-in.

## Deliverables

Event model/schema, local store/broker adapter, consumer/checkpoint/replay engine, OTel bridge, tests/docs.

## Acceptance gates / Definition of Done

Duplicate/out-of-order/restart/checkpoint/replay/dead-letter/retention/redaction tests; event throughput budgets; R0/Python/UI.

## Validation and evidence

Envelope/schema hashes, replay ranges/checkpoints, redaction reports, throughput/lag values and CI.

## Rollback / recovery

Consumer checkpoint restore; replay from immutable retained events within policy; no silent destructive truncation.

## Risks and regression traps

PII leakage, replay side effects, duplicate mutation, schema drift, unbounded retention/backlog.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.14 — LiveOps campaigns, seasons, schedules, rotations, activation + rollback

## Objective and rationale

Compose entitlements/config/content/events into safe, explicit LiveOps operations rather than ad-hoc remote mutations.

## In scope

Campaign/season/schedule identities; time windows/timezones; audiences using governed flag targeting; content/config references; reward/entitlement references without raw grant bypass; preview/simulation; approval; staged activation; pause/expiry; rollback and audit.

## Out of scope

Marketing automation, push-notification provider integration unless later scoped, and arbitrary scheduled scripts.

## Dependencies and prerequisites

R14.10–R14.13.

## Detailed implementation plan

Campaign definitions reference immutable snapshots/manifests/catalog entries. Scheduler uses explicit UTC instants plus display timezone and idempotent activation IDs. Preview computes affected population/resources without mutation. Activation validates all dependencies and SafeChange rollback point. Emergency kill/pause is explicit.

## Deliverables

LiveOps models/scheduler/orchestrator, preview/activation/rollback services, fixtures, tests/docs.

## Acceptance gates / Definition of Done

DST/timezone, duplicate scheduler tick, dependency missing, partial activation prevention, pause/expiry/rollback and audience stability tests; R0/Python/UI.

## Validation and evidence

Campaign definition hash, preview vs activation diff, scheduler/activation traces and CI.

## Rollback / recovery

Restore prior config/content/channel snapshot and campaign state; append compensating audit records rather than deleting history.

## Risks and regression traps

Timezone errors, double activation, mass entitlement mistake, stale dependencies, irreversible broad rollout.

## Manual intervention

**NONE** for local/core LiveOps authority.

## Completion record

To be appended when accepted.

---

# R14.15 — Service operations/resilience: health, limits, retries, backup/restore, DR + load budgets

## Objective and rationale

Prove services fail predictably and recover before exposing them through final UX or integrated acceptance.

## In scope

Health/readiness/dependency graph; timeouts/retries/backoff/jitter; circuit breaker/bulkhead/rate limits; connection/queue budgets; graceful degradation; backup scheduling; restore test; RPO/RTO evidence; failure injection; load profiles; OTel-derived service health; bounded log/event retention.

## Out of scope

R16 full red-team/beta hardening and mandatory multi-region production deployment.

## Dependencies and prerequisites

R14.3–R14.14 + R6 quality/budget/security.

## Detailed implementation plan

Define service SLO-like test budgets as project/profile evidence, not universal promises. Add deterministic failure injection for DB/provider/event/content dependencies. Backup artifacts are encrypted/governed where configured and restore is tested in isolated environment. Rate/retry policy prevents retry storms and cascading failures.

## Deliverables

Resilience primitives, health aggregator, backup/restore/DR runner, load/failure fixtures, reports and docs.

## Acceptance gates / Definition of Done

Dependency outage, timeout/retry/circuit/rate-limit, graceful shutdown, backup+restore hash, bounded RPO/RTO test and load-budget tests; R0/Python/UI. No Internet-scale claim from local CI.

## Validation and evidence

Load profile, latency/error/memory/CPU/DB metrics, backup/restore digests, failure-injection timeline and CI.

## Rollback / recovery

Restore last accepted config/schema/data snapshot and disable new service path/flag; KillSwitch remains global escape hatch.

## Risks and regression traps

Retry storms, false health, backup not restorable, load test causing external cost, unbounded telemetry.

## Manual intervention

**CONDITIONAL.** Core uses bounded local/hosted CI. External provider quota/cost/load proof is manual/provider-dependent only when explicitly claimed; never run destructive/high-cost load against production by default.

## Completion record

To be appended when accepted.

---

# R14.16 — CLI + KodeStudio Backend/LiveOps UX, local stack control + dry-run/provider status

## Objective and rationale

Expose R14 safely through structured user workflows while preventing UI/CLI shortcuts from bypassing permissions, previews or environment boundaries.

## In scope

CLI commands and KodeStudio panels for backend profile, local start/stop/status, DB migration preview/apply, auth/provider capability, lobby/save/progression inspection, entitlement reconciliation preview, flags/config/content/campaign preview and rollout/rollback, events/replay preview, health/load/backup reports. Destructive/live actions require explicit confirmation/permission where policy requires it.

## Out of scope

Raw shell console, secret editor that reveals values and automatic production deployment/publish.

## Dependencies and prerequisites

R14.1–R14.15.

## Detailed implementation plan

All surfaces call structured domain APIs. Environment and authority scope are always visible; secret references are redacted. Default mode for migrations/replay/rollout/content/campaign is inspect/preview/dry-run. Add accessibility/localization and stable machine-readable CLI JSON output.

## Deliverables

CLI/KodeStudio handlers/views/models, localization strings, tests, UX docs and smoke fixtures.

## Acceptance gates / Definition of Done

CLI JSON contract tests, UI smoke, accessibility/localization regression, forbidden raw endpoint/secret/command input tests, R0/Python/UI; cross-platform where UI supports it.

## Validation and evidence

CLI snapshots, UI smoke run, redaction/permission evidence and exact-head CI.

## Rollback / recovery

Remove UI/CLI wiring while domain services remain intact; no state mutation outside explicit domain APIs.

## Risks and regression traps

Secret display, environment confusion, destructive default button, raw command escape, stale provider status.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.17 — Adversarial integrated backend/platform-services/LiveOps acceptance

## Objective and rationale

Close R14 with anti-circular evidence proving that accepted subdivisions interoperate on the same immutable technical source and that provider-local/sandbox evidence is not promoted to unsupported production claims.

## In scope

Integrated model/schema/verifier; fresh exact-head R0/Python/UI and R14 integrated workflow; canonical local auth + PostgreSQL + authoritative server + lobby + cloud-save + progression + entitlement sandbox + flags/config + content + events + LiveOps scenario; resilience/rollback checks; CI evidence manifest; canonical `R14_INTEGRATED_ACCEPTANCE.json`; DESIGN/ACCEPTANCE authority; adversarial tamper/circular-evidence tests.

## Out of scope

R15 fine-tuning and R16 final product red-team; requiring every optional commercial provider account for core PASS.

## Dependencies and prerequisites

R14.1–R14.16 COMPLETE + normalized. All prior acceptance artifacts immutable and available.

## Detailed implementation plan

Freeze an immutable technical source before decision evidence. Run required independent gates on that exact SHA. Build an anti-circular CI manifest containing run identities/artifact digests without letting the final report certify itself. End-sync plan/continuity/acceptance bytes, generate canonical integrated report bound to immutable source and prior subdivision artifacts, then run fresh final documentation/evidence exact-head gates before merge. After implementation/evidence merge, perform exactly one continuity-only R14 normalization.

Integrated scenario must prove at minimum:

1. create local/test account/session through governed auth;
2. persist authoritative state transactionally;
3. create lobby/match reservation and reconnect safely;
4. sync cloud-save revisions and exercise a conflict/rollback;
5. award progression only from authoritative event;
6. ingest duplicate/out-of-order billing sandbox/provider-event fixture without double entitlement;
7. evaluate stable feature rollout and switch to prior config;
8. publish immutable content manifest locally, verify hash/cache and rollback channel;
9. consume/dedupe/checkpoint/replay event safely;
10. preview then activate/pause/rollback a LiveOps campaign;
11. inject dependency failure and prove bounded health/retry/recovery;
12. verify secrets/PII redaction and unsupported provider-live states remain explicit.

## Deliverables

Integrated schemas/models/verifier/builders, CI workflow, focused adversarial tests, `R14_17_DESIGN.md`, `R14_17_ACCEPTANCE.md`, checked-in CI authority and canonical `R14_INTEGRATED_ACCEPTANCE.json` after independent gates.

## Acceptance gates / Definition of Done

All required standard gates and the R14 integrated multi-service workflow must be SUCCESS on the same immutable source; final docs/evidence head re-gated; report `status=pass`, `blockers=[]`; tamper/circular/mismatched-head/provider-overclaim tests fail closed; PR merged with expected-head SHA; one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

## Validation and evidence

Immutable source SHA; every run ID/conclusion; artifact/hash manifest; PostgreSQL/runtime identity; scenario state/event/config/content/save/progression/billing digests; manual state and unsupported provider-live boundaries.

## Rollback / recovery

Reject candidate without reuse of invalid decision evidence; retain prior normalized R14.16 main. Integration fixtures are isolated/local/test only. Post-merge normalization is continuity-only.

## Risks and regression traps

Circular evidence, mixed SHAs, sandbox→production claim escalation, stale provider state, hidden secrets, timing/flaky integration, accidental live endpoint use.

## Manual intervention

**CONDITIONAL.** The frozen core is designed to close with local/hosted/sandbox evidence. If a final accepted claim explicitly requires a real external IdP/store/CDN/managed provider or public domain/TLS state, stop before completion and provide exact user-side prerequisites/actions/evidence. No password, token, private key or secret is ever requested in chat evidence.

## Completion record

To be appended when accepted.

---

## Phase completion rule

R14 can be marked `COMPLETE` only when every subdivision R14.1–R14.17 is `COMPLETE` with its required exact-head acceptance evidence, or explicitly removed from scope by a recorded roadmap/architecture decision with ADR where required. No hidden or implied subdivision may support a phase completion claim.

After R14.17 implementation/evidence merge, exactly one continuity-only phase normalization must pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merge. Only then is R14 `COMPLETE + NORMALIZED` and R15 planning authorized.

## Ongoing maintenance rule

Update `R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects or phase ordering changes. Mutable standards/provider facts are updated as versioned evidence with source/effective date; they do not silently mutate the frozen architecture.
