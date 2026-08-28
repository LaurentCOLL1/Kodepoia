# Kodepoia — R14 detailed phase plan

**Phase:** R14  
**Roadmap title:** Backend / Platform Services / LiveOps  
**Status:** IN PROGRESS
**Phase planning started:** 2026-08-28  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`  
**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED and R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f`. R14.1 accepted immutable technical source `84972d283f6f530ae46ebf6c0452188927b178ff` passed R0 Repository Guard #1752 / `33140670364`, Python Core #1726 / `33140670445`, and KodeStudio UI Smoke #1693 / `33140670391`, all SUCCESS; Ubuntu full suite recorded 1445 passed / 13 skipped and Windows Core also passed. R14.1 is COMPLETE at technical/evidence level; final END-synchronized documentation head must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before PR #257 may merge. R14.2–R14.17 remain PLANNED.

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
| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | PLANNED | NONE | R14.1 + R2/R13 profile patterns |
| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | PLANNED | NONE | R14.1–R14.2 + R8/R12 patterns |
| R14.4 | Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary | PLANNED | CONDITIONAL | R14.1–R14.3 + R1/R6/R7 |
| R14.5 | PostgreSQL authoritative persistence, migrations, transactions + concurrency | PLANNED | NONE | R14.1–R14.3 + R8/R12 |
| R14.6 | Authoritative server command/state model + real-time transport/trust boundary | PLANNED | NONE | R14.4–R14.5 |
| R14.7 | Matchmaking, lobby, reservations, presence + reconnect | PLANNED | NONE | R14.6 |
| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | PLANNED | NONE | R14.5–R14.6 |
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

- Accepted immutable technical head: `84972d283f6f530ae46ebf6c0452188927b178ff`.
- Technical exact-head gates: R0 Repository Guard #1752 / `33140670364` SUCCESS; Python Core #1726 / `33140670445` SUCCESS; KodeStudio UI Smoke #1693 / `33140670391` SUCCESS.
- Ubuntu full Python suite: 1445 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS.
- Manual intervention: NONE.
- Final END-synchronized documentation/evidence re-gates and implementation PR #257 merge remain pending.
- Current subdivision status: `COMPLETE` at technical/evidence level, not `COMPLETE + NORMALIZED` until post-merge continuity normalization.

---

# R14.2 — Project DNA/KodeProduct backend profiles + Wizard conditional service intent

## Objective and rationale

Make backend capability opt-in and product-driven so offline/single-player/local-only projects do not acquire hidden services.

## In scope

Backend intent/profile fields; conditional Wizard questions; generated requirements/acceptance criteria; platform/client compatibility; service dependency graph; default `disabled` state.

## Out of scope

Provisioning, deployment and service implementation.

## Dependencies and prerequisites

R14.1 COMPLETE; R2 DNA/Product/Wizard and R13 mobile profile patterns.

## Detailed implementation plan

Extend schemas with service intent for auth, authoritative state, multiplayer, saves, progression, billing, config/flags, content and events. Derive only necessary questions and dependencies; validate contradictions such as billing without catalog/entitlement boundary or matchmaking without authoritative session service. No credentials/provider account IDs belong in DNA.

## Deliverables

Schema/model/Wizard changes, fixtures for offline vs online products, generated product requirements and regression tests.

## Acceptance gates / Definition of Done

Offline fixture creates zero backend runtime intent; service-enabled fixtures produce deterministic profiles; schema migration/round-trip tests; R0/Python/UI; exact-head PR + normalization.

## Validation and evidence

Profile digests, conditional-question snapshots, negative fixtures and CI identities.

## Rollback / recovery

Backward-compatible optional fields; old DNA loads with backend disabled.

## Risks and regression traps

Silent service opt-in, secrets in project metadata, mobile/desktop target leakage, unstable default provider choice.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.3 — Deterministic local backend scaffold/runtime + environments/config/secrets/health

## Objective and rationale

Provide a reproducible local backend development surface before any external provider is required.

## In scope

Deterministic backend scaffold, repository-owned local server runner, typed config, environment overlays, KodeSecrets references, loopback-first bind policy, health/readiness endpoints, graceful shutdown, logs/redaction and reproducible fixture service.

## Out of scope

Public deployment, auth semantics, production TLS termination and managed hosting.

## Dependencies and prerequisites

R14.1–R14.2; R8 lineage; R12 scaffold/runtime patterns.

## Detailed implementation plan

Generate a local service workspace from canonical templates. Runtime defaults to loopback, ephemeral/test-safe ports, network off except explicit local service communications, structured config and secret handles. Add startup capability probe, health/readiness/liveness state and bounded teardown. No arbitrary package scripts.

## Deliverables

Scaffold templates, manifest/schema, runtime adapter, health model, fixtures, tests and DESIGN/ACCEPTANCE docs.

## Acceptance gates / Definition of Done

Generate twice = identical tree; start/health/stop bounded; secret redaction; port conflict behavior; Windows/Ubuntu; R0/Python/UI; exact-head merge + normalization.

## Validation and evidence

Generated tree hashes, runtime identity/version, bound interface/port evidence, process cleanup and logs.

## Rollback / recovery

Owned local process/state only; terminate via ProcessSandbox/KillSwitch and remove generated workspace/cache.

## Risks and regression traps

Binding `0.0.0.0` by default, zombie processes, port hijack, config drift, logs leaking secrets.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.4 — Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary

## Objective and rationale

Establish secure identity/authentication/session semantics before authoritative multiplayer or billing depends on them.

## In scope

Account/auth realm identities; local deterministic identity provider fixture; session lifecycle; access/refresh token abstraction; token validation policy; revocation/rotation; passkey/WebAuthn capability model; OIDC discovery/provider adapter boundary; CSRF/state/PKCE/nonce/redirect validation where applicable; rate/lockout/session security evidence.

## Out of scope

Mandatory social-login vendor, production IdP tenant provisioning and generalized enterprise federation.

## Dependencies and prerequisites

R14.1–R14.3; R1 secrets/security; current standards evidence.

## Detailed implementation plan

Implement typed auth provider contracts and a deterministic local provider. Never accept algorithm/issuer/audience/redirect from untrusted raw project text without policy validation. Separate browser/public-client/native/server-confidential semantics. Passkey credential records store only public credential material and metadata; private keys remain authenticator-owned. OIDC external provider is explicit/allowlisted and capability-probed.

## Deliverables

Auth models/services, local provider, OIDC/passkey adapters/contracts, schemas, attack fixtures and tests.

## Acceptance gates / Definition of Done

Replay/expiry/issuer/audience/algorithm-mismatch/redirect/PKCE/state/nonce tests; session rotation/revocation; passkey contract tests; no secret leakage; R0/Python/UI; external IdP proof not required for core.

## Validation and evidence

Standards provenance/effective date, redacted auth traces, negative vector results and exact-head CI.

## Rollback / recovery

Local auth state disposable; schema migrations reversible; revoke generated local sessions/credentials.

## Risks and regression traps

Token confusion, open redirect, weak algorithm acceptance, long-lived bearer leakage, account enumeration, clock skew assumptions.

## Manual intervention

**CONDITIONAL.** Core acceptance uses local deterministic providers. Manual/provider-side work is required only if a claim explicitly requires a real domain/TLS/IdP/passkey relying-party configuration. Never send client secrets, private keys or passwords back in evidence.

## Completion record

To be appended when accepted.

---

# R14.5 — PostgreSQL authoritative persistence, migrations, transactions + concurrency

## Objective and rationale

Create the durable transactional authority required by saves, progression, billing, config and event checkpoints.

## In scope

PostgreSQL capability adapter; connection/pool policy; typed repositories/unit-of-work; migration identities/checksums; transactional semantics; optimistic/pessimistic concurrency policy; isolation/deadlock handling; backup/restore fixtures; SQLite remains inappropriate as production authority when multi-writer server semantics require PostgreSQL.

## Out of scope

Managed cloud database provisioning and product-specific tables beyond validation fixtures.

## Dependencies and prerequisites

R14.1–R14.3; stable PostgreSQL 18.x CI capability; R8 lineage/backup patterns.

## Detailed implementation plan

Use repository-owned migrations with forward/rollback metadata and schema digest. Apply only after drift/preflight checks and SafeChange snapshot. Add transaction/idempotency primitives and deterministic integration fixtures. Production connection strings remain secret references, never model-visible literals.

## Deliverables

DB adapter, migration engine/contracts, schemas, test migrations, concurrency fixtures, backup/restore acceptance tooling and docs.

## Acceptance gates / Definition of Done

Fresh PostgreSQL stable CI: create/migrate/rollback/reapply, concurrent update conflict, deadlock bounded retry, transaction atomicity, backup/restore hash equivalence; R0/Python/UI; no beta DB production claim.

## Validation and evidence

PostgreSQL version/capability snapshot, schema/migration hashes, transaction/concurrency results, restore digest and run IDs.

## Rollback / recovery

Migration rollback or snapshot restore; failed migration must never be marked applied; restore tested before destructive path promotion.

## Risks and regression traps

Schema drift, non-idempotent retries, migration partial apply, connection exhaustion, deadlock loops, secret DSN exposure.

## Manual intervention

**NONE** for core; hosted/local CI database is authoritative for R14.5 capability.

## Completion record

To be appended when accepted.

---

# R14.6 — Authoritative server command/state model + real-time transport/trust boundary

## Objective and rationale

Ensure clients cannot directly dictate trusted state and establish deterministic command/revision semantics used by multiplayer and progression services.

## In scope

Authority domains; typed commands; validation/authorization; state revisions; idempotency keys; sequence/version checks; request/response and real-time transport abstraction; reconnect-safe protocol; bounded timeouts/backpressure; server clock/lease policy.

## Out of scope

Matchmaking policy, cloud saves and concrete product gameplay rules.

## Dependencies and prerequisites

R14.4–R14.5.

## Detailed implementation plan

Clients submit commands/intents. Server validates actor/session/authorization/current revision, performs transaction, emits authoritative outcome/events. Add provider-neutral HTTP/request + real-time channel contracts with typed messages and no raw model-selected protocol commands. Define duplicate, stale, out-of-order and disconnect handling.

## Deliverables

Authority/command/state modules, transport contracts, fixtures, concurrency/adversarial tests, docs.

## Acceptance gates / Definition of Done

Forgery/stale revision/duplicate/out-of-order/reconnect/backpressure tests; transaction/event consistency; R0/Python/UI; deterministic local multi-client fixture.

## Validation and evidence

Command/revision traces, rejected attack fixtures, latency/budget results and exact-head CI.

## Rollback / recovery

No irreversible external state; transactional fixture reset and event replay checkpoint rollback.

## Risks and regression traps

Client authority leakage, race conditions, duplicate commands, clock dependence, unbounded queues.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.7 — Matchmaking, lobby, reservations, presence + reconnect

## Objective and rationale

Add the frozen multiplayer service capability on top of authoritative sessions rather than embedding trust in clients.

## In scope

Lobby lifecycle, membership/roles, matchmaking tickets/criteria, queueing, reservation/expiry, match identity, presence, reconnect tokens/leases, cancellation, deterministic local matcher and fairness/budget hooks.

## Out of scope

Global-scale commercial matchmaking provider and game-specific MMR algorithm tuning.

## Dependencies and prerequisites

R14.6 COMPLETE.

## Detailed implementation plan

Persist tickets/lobbies/reservations with explicit revisions and expiry. Matching is deterministic for fixtures and policy-driven. Reconnect uses short-lived server-side reservation/session semantics; client cannot forge membership. Add queue/race/duplicate/cancel tests.

## Deliverables

Matchmaking/lobby service, schemas, local simulator, tests and docs.

## Acceptance gates / Definition of Done

Concurrent join/leave/cancel, duplicate ticket, reservation expiry, reconnect and stale presence tests; latency budgets; R0/Python/UI; exact-head merge + normalization.

## Validation and evidence

Queue timings, lifecycle traces, persisted revision hashes and CI identities.

## Rollback / recovery

Cancel/expire owned tickets/reservations; fixture DB reset; no live player pool claim.

## Risks and regression traps

Double assignment, ghost lobby members, unbounded queue, unfair nondeterministic tests, reconnect privilege escalation.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R14.8 — Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery

## Objective and rationale

Provide server-authoritative cross-device save synchronization without overwriting newer state or corrupting lineage.

## In scope

Save slots, immutable save revisions, metadata/hash, compare-and-swap, client base revision, conflict detection, deterministic resolution policies, quotas, compression/encryption boundary, retention, rollback/recovery and R11/R13 save compatibility bridge.

## Out of scope

Provider-specific consumer cloud drive integration and arbitrary binary merge algorithms.

## Dependencies and prerequisites

R14.5–R14.6; existing SaveBridge/provenance.

## Detailed implementation plan

Upload creates a new revision only after hash/size/schema/authorization checks. Sync uses base revision and explicit conflict object; never last-write-wins silently unless product policy explicitly selects it. Preserve lineage and rollback points; large blobs use governed object/content boundary rather than unbounded DB rows where appropriate.

## Deliverables

Cloud-save service/models/schema, conflict resolver, migration/compatibility fixtures, tests and docs.

## Acceptance gates / Definition of Done

Offline divergent edits, duplicate upload, stale base, rollback, corrupt payload, quota and migration tests; deterministic conflict resolution; R0/Python/UI.

## Validation and evidence

Save/revision hashes, conflict traces, restore results and budgets.

## Rollback / recovery

Select prior immutable revision; no destructive overwrite of last known-good state.

## Risks and regression traps

Silent data loss, cross-user access, unbounded save growth, schema mismatch, content hash confusion.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

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
