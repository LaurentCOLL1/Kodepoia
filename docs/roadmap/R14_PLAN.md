# Kodepoia — R14 detailed phase plan

**Phase:** R14  
**Roadmap title:** Backend / Platform Services / LiveOps  
**Status:** IN PROGRESS
**Phase planning started:** 2026-08-28  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `b5b75b826bedabf64957494f7e2228ec1c9ff2d3`  
**Execution checkpoint:** R1–R13 are COMPLETE + NORMALIZED; R14 planning is ACCEPTED + NORMALIZED. R14.1–R14.14 are COMPLETE + NORMALIZED on normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`. R14.15 is IN_PROGRESS on dedicated branch `r14/15-service-operations-resilience`, branched exactly from that normalized main; R14.16–R14.17 remain PLANNED. R14.15 manual state is CONDITIONAL / NOT TRIGGERED for core acceptance: bounded local/hosted CI is authoritative, while external provider quota/cost/load proof remains manual/provider-dependent only if explicitly claimed. R14.14 immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; final END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; implementation/evidence merge PR #283 `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; fresh normalization gates R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` all SUCCESS; normalization PR #284 expected-head merge produced normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.

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
| R14.9 | Achievements, stats, leaderboards + authoritative progression | COMPLETE | NONE | R14.5–R14.6 |
| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | COMPLETE | CONDITIONAL / NOT TRIGGERED | R14.4–R14.6 + R13 store contracts |
| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | COMPLETE | NONE | R14.5–R14.6 |
| R14.12 | Content delivery: immutable manifests/bundles, channels, cache + rollback | COMPLETE | CONDITIONAL / NOT TRIGGERED | R14.5/R14.11 + R8/R13 release provenance |
| R14.13 | Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge | COMPLETE | NONE | R14.5–R14.6 + R6 |
| R14.14 | LiveOps campaigns, seasons, schedules, rotations, activation + rollback | COMPLETE | NONE | R14.10–R14.13 |
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
- Final END-head `75e5d68752a56b8a21fa4842e803d86f772f7468` passed R0 #1757 / `33140864294`, Python Core #1731 / `33140864327`, and UI #1698 / `33140864338`; PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`.
- Single continuity-only normalization head `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759 / `33141096835`, Python Core #1733 / `33141096889`, and UI #1700 / `33141096815`; PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.2 is authorized and starts from that exact normalized main.

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

- Accepted immutable technical head: `4e04812380a495dd799e1d7b9e96741d8688de31`.
- Technical exact-head gates: R0 Repository Guard #1761 / `33143230642` SUCCESS; Python Core #1735 / `33143230580` SUCCESS; KodeStudio UI Smoke #1702 / `33143230613` SUCCESS.
- Ubuntu full Python suite: 1465 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.
- Focused prevalidation `33143176492`: 34 passed, 2 skipped; diagnostic only, not acceptance authority.
- Manual intervention: NONE.
- Final END-head `cc034784b6b3350f3e24ece55e5d2304fa60705c` passed R0 #1766 / `33143514421`, Python Core #1740 / `33143514423`, and UI #1707 / `33143514466`; PR #259 merged as `ad5de7c1697d061946bf75220420c75b73851531`.
- Single continuity-only normalization head `b3587acf2a9c37d2e407a62bc1e805863f553564` passed R0 #1768 / `33145379528`, Python Core #1742 / `33145379581`, and UI #1709 / `33145379554`; PR #260 merged as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.3 is authorized and starts from that exact normalized main.

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

- Accepted immutable technical head: `4de5036e7a37f949ec64ae68d9ee45e57ac99631`.
- Technical exact-head gates: R0 Repository Guard #1770 / `33146235062` SUCCESS; Python Core #1744 / `33146235104` SUCCESS; KodeStudio UI Smoke #1711 / `33146235181` SUCCESS.
- Ubuntu full Python suite: 1477 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.
- Focused implementation/compatibility prevalidation `33146069094`: 36 passed after compileall.
- Cross-platform focused runtime validation `33146135676`: Ubuntu SUCCESS and Windows SUCCESS. A duplicate cleanup invocation later failed only because another invocation had already removed the temporary workflow/trigger; the tested implementation tree remained unchanged and the cumulative implementation diff contains no temporary files.
- Manual intervention: NONE.
- Final END-head `8411ce92da962a37cb9a5936bdac740d9a132204` passed R0 #1775 / `33146496788`, Python Core #1749 / `33146496859`, and UI #1716 / `33146496739`; PR #261 merged as `d288772a90d5877cabe35adb6e71f0ede32f6b8d`.
- Single continuity-only normalization head `b8151f3729d2648d5f1e4d6ecd3bc9afb3c3c401` passed R0 #1777 / `33186628042`, Python Core #1751 / `33186628118`, and UI #1718 / `33186628151`; PR #262 merged as normalized `main` `f28e6762830ec9a2b22ddedc24bdc9a446e5f4b2`.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.4 is authorized and starts from that exact normalized main.

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

- Accepted immutable technical head: `3660f351649e85450324df25888d577afb02b19a`.
- Technical exact-head gates: R0 Repository Guard #1779 / `33187747722` SUCCESS; Python Core #1753 / `33187747723` SUCCESS; KodeStudio UI Smoke #1720 / `33187747872` SUCCESS.
- Ubuntu full Python suite: 1494 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.
- Cross-platform focused prevalidation `33187554520`: 29 R14.4/R14.3 tests passed on Ubuntu and Windows after compileall.
- Standards evidence: RFC 9700 OAuth 2.0 Security BCP; OpenID Connect Core validation semantics; W3C WebAuthn Level 3 Candidate Recommendation Snapshot dated 26 May 2026; OWASP session guidance.
- Manual intervention: CONDITIONAL / NOT TRIGGERED. Core acceptance used deterministic local providers only.
- Final END-head `05b16a796bb65d513de0b631eca432195ee01461` passed R0 #1783 / `33189022908`, Python Core #1757 / `33189022727`, and UI #1724 / `33189022765`; PR #263 merged as `cae2a1ddcaa79390ff923336ee331eba81937e84`.
- Single continuity-only normalization head `8601ac19b87635648aef1c5f5c37a6cb899c26be` passed R0 #1785 / `33189536524`, Python Core #1759 / `33189536553`, and UI #1726 / `33189536543`; PR #264 merged as normalized `main` `45dc68f1cd3bf05c62aede1b2519c6c513c67166`.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.5 is authorized and starts from that exact normalized main.

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

- Accepted immutable technical source: `3273ac50b43b64f6f365522f170765f44f45eedf`.
- Technical exact-head gates: R0 Repository Guard #1787 / `33190672723` SUCCESS; Python Core #1761 / `33190672676` SUCCESS; KodeStudio UI Smoke #1728 / `33190672761` SUCCESS; R14 PostgreSQL Acceptance #1 / `33190672769` SUCCESS.
- Ubuntu full Python suite: 1509 passed, 13 skipped, 46 warnings; Windows Core suite also SUCCESS; both package builds and Python internal UI smoke SUCCESS.
- PostgreSQL focused acceptance: 44 R14.5/R14.4/R14.3 tests passed against PostgreSQL 18.6 (`server_version_num=180006`, stable_supported=true).
- Real PostgreSQL acceptance checks all true: fresh apply, rollback/reapply, transaction atomicity, optimistic conflict, row lock, idempotency, bounded retry and backup/restore. A real PostgreSQL `40P01` deadlock was provoked and detected.
- Migration plan digest: `b96484ae6d56fe54b013b975572310d8daf44cf43116c5c43edc73845856b71b`; restore digest: `bcc5ae8b707231568263e0f52c8426dd956a67e4e131bcf97becb4b45ccb9f6e`; evidence reports `secrets_exposed=false`.
- Stable external baseline at acceptance: PostgreSQL 18.6 released 2026-08-13; PostgreSQL 19 Beta 3 remains pre-release/testing-only.
- Manual intervention: NONE.
- Final END-head `9606436453c6cc2bed90120bc3f9069311ef65e0` passed fresh R0 #1791 / `33191315047`, Python Core #1765 / `33191315090`, UI #1732 / `33191315092`, and PostgreSQL Acceptance #5 / `33191315129`, all SUCCESS; PR #265 merged with `expected_head_sha=9606436453c6cc2bed90120bc3f9069311ef65e0` as `39d8aa12e3d36a618376f7060d1088f9fe61ba32`.
- Single continuity-only normalization head `721c9949914a0952b2afe8543dd37da5f8146545` passed R0 #1793 / `33191649309`, Python Core #1767 / `33191649218`, and UI #1734 / `33191649134`, all SUCCESS; PR #266 merged as normalized `main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.6 was authorized and started from that exact normalized main.

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

- Accepted immutable technical source: `a1425b53e1228f9c88ba373cdfabf1459393a7cf`.
- Technical exact-head gates: R0 Repository Guard #1795 / `33193110717` SUCCESS; Python Core #1769 / `33193110651` SUCCESS; KodeStudio UI Smoke #1736 / `33193110643` SUCCESS; R14 Authority Acceptance #3 / `33193110695` SUCCESS.
- Authority acceptance succeeded on both Ubuntu and Windows. All ten frozen adversarial/semantic checks passed: forgery rejection, stale-revision rejection, mutation-free duplicate replay, out-of-order rejection, reconnect/resync behavior, bounded backpressure, transaction/event consistency, deterministic multi-client conflict handling, server-clock lease expiry and recursive reserved-field rejection.
- Cross-platform semantic results are identical: final state digest `59c1afb567245df4f3521052564d0bdfbaa4a5423eb7db7997c1e20160a988a3`; event digest `3adad95a513ee4812126d7d9695cc297d2f57287263a5686ee1ee5c08a15e4a1`; trace digest `839f65c4ffbe019c43f6aad988ee8258945c328f348135ffef9320955102f178`; `secrets_exposed=false`.
- Ubuntu artifact id `9694600447`, ZIP digest `sha256:ec252c2e055cdb8aa9f94b0f6273f87e6e2724b22f715b8a8e986047766b194a`; Windows artifact id `9694625857`, ZIP digest `sha256:5a2b0ad3d0841649ee3d20cc8057b3def7644f208d44e7a5bfc8154053409464`.
- Final END-head `cf5a14295fdc3ff92ca72384b061e3a2c844e725` changed only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_6_ACCEPTANCE.md`, and continuity relative to the immutable technical source and passed fresh R0 #1798 / `33195032726`, Python Core #1772 / `33195032703`, UI #1739 / `33195032677`, and R14 Authority Acceptance #6 / `33195032645`, all SUCCESS.
- PR #267 merged with `expected_head_sha=cf5a14295fdc3ff92ca72384b061e3a2c844e725` as implementation/evidence merge `6033e5610a811a690a2998eb07183f19183fa557`.
- Single continuity-only normalization head `9dafc361e909157dedf5cb89d7a39cdbb6ffff14` changed exactly `docs/continuity/KODEPOIA_CONTINUITY.md`, passed fresh R0 #1800 / `33195413481`, Python Core #1774 / `33195413472`, and UI #1741 / `33195413558`, all SUCCESS; normalization PR #268 merged with `expected_head_sha=9dafc361e909157dedf5cb89d7a39cdbb6ffff14` as normalized `main` `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`.
- Manual intervention: NONE.
- Current subdivision status: `COMPLETE + NORMALIZED`. R14.7 is authorized and starts from that exact normalized main.

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

- Dedicated branch: `r14/07-matchmaking-lobby-presence`.
- Exact branch point: normalized `main` `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`.
- Mandatory START-sync completed before implementation: plan head `8dc25375e40c045b8831278faa0f55ad74cf6df1`, continuity head `63c41c51ad6fb4adb981d284c3753ea5a26c9eb6`.
- Initial candidate `12071ee561717ac436f4ffa0457361685214c989` is REJECTED and is not decision evidence. Dedicated acceptance #2 detected that `update_presence(IN_MATCH)` did not sweep server-clock reservation expiry before authorization; the implementation, not the test, was corrected.
- Accepted immutable technical source: `d04c841fcef9eb9f963085da68e579dbb58186da`.
- Technical exact-source gates: R0 Repository Guard #1803 / `33203286519` SUCCESS; Python Core #1777 / `33203286537` SUCCESS; KodeStudio UI Smoke #1744 / `33203286514` SUCCESS; R14 Matchmaking Acceptance #4 / `33203286510` SUCCESS.
- Full Ubuntu Python suite: 1543 passed, 13 skipped, 46 warnings; Windows Core, both package builds and Python internal UI smoke also SUCCESS.
- Focused R14.7/R14.6/R14.5/R14.4 regression suite: 66 tests passed on Ubuntu and 66 on Windows.
- All fourteen frozen matchmaking checks are true on both OS: lobby lifecycle, object authorization, duplicate join, recursive reserved-field rejection, duplicate ticket, deterministic match, incompatible criteria isolation, no double assignment, cancel terminality, reservation expiry, stale presence rejection, reconnect binding, reconnect expiry and bounded capacity.
- Cross-platform semantic digests are identical: state `ae9ecc0893537e5c12cc8a78247197ed53d094b1a811c386c17161fac10c0c19`; lobby `27bcd90471e3775b859ce21e977c5ac534909a898deab0eb2c27cd44b86db0cf`; reservation `e8423de1a2d1a92873bbfa466111ab4a07168adeafca4bde4d62c64a70a9f690`; presence `5f2ca6c7402bba1a3b2d195d9f63d1c8b758c01d577d4581785559d92de24f0f`; trace `5f25c8f15da7e4f9dd45fbf072dd72101d3f32deef349c28069beeb83d954bd3`.
- Ubuntu artifact `9698619713`, ZIP digest `sha256:f8bd9f43b431bb9a5f9b194da245a57381b000795a5c8ccacb51a866c371b1df`; Windows artifact `9698629064`, ZIP digest `sha256:1e3b191e9d1de0844b49c62bcd36c79798a23315e93edf20393b862d1fb44c1c`.
- Evidence reports `provider_live_claim=false` and `secrets_exposed=false`. External provider documentation is comparison evidence only; no provider account or Internet-scale capacity claim is part of R14.7 core acceptance.
- Manual intervention: NONE.
- Current subdivision status: `COMPLETE` at technical/evidence level. R14.8 remains `PLANNED` until this END synchronization passes fresh exact-head R0 + full Python Core + KodeStudio UI Smoke + R14 Matchmaking Acceptance, PR #269 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.
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

- Dedicated branch: `r14/09-progression-leaderboards`; exact normalized branch point: R14.8 `main` `433c86cc5d43bfea41adb529451367e10c75a30b`.
- Mandatory START-sync completed before implementation; final clean START head `d221057a91b9c0389346e6eec71044ce57898db1` differed from normalized main by plan + continuity only.
- Candidate `dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f` is REJECTED and its evidence is non-authoritative; the test fixture, not the production authorization boundary, was corrected.
- Pre-acceptance audit detected and corrected recurring-leaderboard lifetime-state bleed; recurring periods now derive period-local score state.
- Accepted immutable technical source: `155119282af7f4bf71840fc45c2d3de8891f73cd`.
- Technical exact-source gates: R0 #1836 / `33210136515`, Python Core #1810 / `33210136766`, UI #1777 / `33210136531`, R14 Progression Acceptance #3 / `33210136498` — all SUCCESS.
- Full Ubuntu: **1590 passed / 13 skipped / 46 warnings**; focused R14.9→R14.5: **96 passed Ubuntu + 96 passed Windows**.
- Fifteen frozen progression checks PASS cross-platform, including authoritative-only score mutation, idempotency/event rebinding rejection, deterministic ordering/ties, server-clock period boundaries, privacy filtering, bounded capacity and recurring rollover without lifetime bleed.
- Cross-platform digests: definition `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`; state `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`; trace `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`; classic `49a5655892db2649f2f9a926aff2e2cda14f8b51ef3f9901acc4c227c96e306c`; lower `2869ce012f10c143be8128f356288c21bc028793d18fae5ea2cb79b6f2b18859`; recurring p0 `a3fd0f5b9a06a093b0961626950ef0ddf9c3acb0ebd9f69e67bf4bb0dd6b9380`; recurring p1 `4d22f10134f62e6449fce47bee6e13ef4ed9556d7922889c0749dc3000ffd2fd`.
- Canonical artifacts: Ubuntu `9701251718` / `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`; Windows `9701266161` / `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`.
- `provider_live_claim=false`; `secrets_exposed=false`; provider docs are compatibility evidence only. Manual intervention: NONE.
- END state: R14.9 COMPLETE; R14.10–R14.17 remain PLANNED. Fresh exact END-head R0/Python/UI/R14 Progression, expected-head PR #273 merge and one continuity-only normalization remain mandatory before R14.10.

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

**CONDITIONAL / NOT TRIGGERED.** Core acceptance uses synthetic/provider-contract fixtures with `provider_live_claim=false`. Real Apple/Google production account, product and transaction verification is required only for a later explicit provider-live claim; user must never send secrets/private keys/tokens.

## START authority

- Dedicated branch: `r14/10-entitlements-billing-catalog`.
- Exact branch point: normalized R14.9 `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- R14.9 closure authority: technical source `155119282af7f4bf71840fc45c2d3de8891f73cd`; accepted END-head `2619e190601089ca2d98b22ccb4c0d254f1f11f7`; exact END gates R0 #1843 / `33211148134`, Python Core #1817 / `33211148235`, UI #1784 / `33211148160`, R14 Progression #10 / `33211148184` all SUCCESS; PR #273 merged with expected-head as `5f55e8b1811c08e8eef310f18aa3801798153018`.
- Single R14.9 post-merge normalization head `814fccac4a68e6de19a98b6c0b622c4298ca1a99` changed only continuity, passed R0 #1845 / `33223835030`, Python Core #1819 / `33223835012`, UI #1786 / `33223835008`, and PR #274 merged with expected-head as normalized `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- START state: R14.1–R14.9 COMPLETE + NORMALIZED; R14.10 IN_PROGRESS; R14.11–R14.17 PLANNED.
- Core trust invariants: notification arrival/client receipt never grants entitlement by itself; provider identity/environment/message identity are explicit; provider events are immutable and deduplicated; authoritative provider state is verified/reconciled before entitlement transitions; transitions are transactional/idempotent; raw provider credentials/tokens are never model-visible evidence.
- Current official compatibility baseline: Google RTDN requires a subsequent Google Play Developer API query for complete purchase status and recommends deduplication by RTDN `messageId`; Google purchase verification belongs on the backend before granting entitlement. Apple App Store Server Notifications V2 uses App Store-signed JWS `signedPayload`, `notificationUUID` for duplicate suppression, and `signedDate` to prefer the most recent transaction-state snapshot. These are compatibility constraints, not provider-live proof.
- Manual state: CONDITIONAL / NOT TRIGGERED. `provider_live_claim=false`; no production account, product, purchase, credential, private key or token is required for core acceptance.

## Completion record

- Dedicated branch: `r14/10-entitlements-billing-catalog`; exact normalized branch point: R14.9 `main` `1dc3f8206eb454ecb6638fd75a5b65609c4e4ebf`.
- Rejected candidate `55fed19c2ccbb63c790aa427a9afd9366cfe9cef` is NON-AUTHORITATIVE and its evidence must never be reused. Its first dedicated acceptance run exposed that the shared canonical JSON helper incorrectly coerced ordered event arrays through `dict(payload)`.
- The canonicalizer was corrected without changing existing mapping serialization semantics: canonical JSON now accepts JSON-compatible payloads directly while preserving key sorting, compact separators, Unicode handling and NaN rejection. No authority boundary was weakened.
- Accepted immutable technical source: `8a102a19512b076a8edb5c561e86b1d0101bc391`.
- Dedicated exact-source R14 Entitlements Acceptance run `33233097442`: Ubuntu job `99049221513` SUCCESS; Windows job `99049221666` SUCCESS.
- Focused regression covers R14.4 auth/identity/sessions, R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.10 entitlements/billing, plus R13.7 Google Play readiness and R13.15 mobile store compliance.
- Nineteen frozen checks PASS cross-platform: client receipt rejection, invalid notification signature/token rejection, pending-no-grant, verified-provider grant, mutation-free duplicate replay, message/purchase account rebind rejection, out-of-order no-regression, reconciliation convergence/idempotency, server-clock expiry, environment isolation, Apple V2 contract, immutable catalog version, object/function authorization, bounded capacity and redacted evidence.
- Cross-platform evidence JSON is byte-for-byte equivalent. Digests: catalog `029829e18972971f3551f3a0a99e3e641e55ab7a2fb6cb374f6b4645b482389c`; state `3a526baa050763c8b5453c7970f750ce205ef57d864a612986b43488ab9f0154`; trace `1333f7f917742d6a0f93028466e0f1c8e771b9442dfe5403c22184764e1edbeb`; provider events `57962e7fddd666146ebb90aa4fed26eb20a287346995bb37f552179780ea447d`; Google entitlement `b0348458e900e79b8eed4237040a6cd33ca329f52920e613a6d8007ea0ae9a88`; Apple entitlement `69bae02f05593d6c73bc0928cb01b8de72cb6afdacbea47d6592a57f6e20d851`.
- Evidence counts/budgets: 5 provider events, 3 purchase records, 2 catalog definitions; `max_catalog_versions=32`, `max_provider_events=128`, `max_purchases=32`, `max_accounts=32`, `max_reconciliations=64`.
- Canonical artifacts: Ubuntu `9709088552` / `sha256:9f768b4423cd6b735dc5be51ce258596f78d7bd722106f889fbad30b69f188f3`; Windows `9709093199` / `sha256:6c8475949e29a7720aea89a583d6f45bdfd3335c04598893fe7d7afe0070c57c`.
- Evidence schema: `schemas/r14/backend-entitlement-evidence.schema.json`; evidence reports `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `secrets_exposed=false`.
- Current official compatibility evidence remains aligned: Google RTDN is a change signal requiring backend status lookup and recommends message-ID dedupe; Apple V2 uses App Store-signed JWS `signedPayload`, duplicate identity `notificationUUID` and signed snapshot time `signedDate`. These are compatibility constraints only, not live-provider proof.
- Manual intervention: CONDITIONAL / NOT TRIGGERED. No production provider account, product, credential, private key, purchase token or real-money transaction was requested or used.
- END state: R14.10 COMPLETE; R14.11–R14.17 remain PLANNED. R14.11 is not authorized until the exact R14.10 END-head passes fresh R0/Python/UI/R14 Entitlements gates, PR #275 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

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

## START authority

- Dedicated branch: `r14/11-remote-config-feature-flags`.
- Exact branch point: normalized R14.10 `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- R14.10 closure authority: immutable technical source `8a102a19512b076a8edb5c561e86b1d0101bc391`; final END-head `37c7418e31e1467032eac0646b731eab1087f4eb`; END gates R0 #1852 / `33233480750`, Python Core #1826 / `33233480761`, UI #1793 / `33233480825`, R14 Entitlements #12 / `33233480782` all SUCCESS; PR #275 merge `c0059f02c193c4972daaaad851ce0d5a8fdcd715`.
- Single R14.10 post-merge normalization head `d56246f65f834c87ef32a0ba645ca3a76ba898ab` changed only continuity, passed R0 #1854 / `33233746051`, Python Core #1828 / `33233746018`, UI #1795 / `33233746115`, and PR #276 merged with expected-head as normalized `main` `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- START state: R14.1–R14.10 COMPLETE + NORMALIZED; R14.11 IN_PROGRESS; R14.12–R14.17 PLANNED.
- Trust invariants: immutable/versioned definitions and snapshots; no remote arbitrary code/script execution; unsupported or unknown value/rule types fail closed; evaluation context is canonical, bounded and privacy-governed; fractional rollout uses stable deterministic hashing; prerequisite cycles fail closed; expiry/kill-switch override rollout safely; production activation requires explicit permission + audit + SafeChange; rollback reactivates a prior immutable snapshot rather than mutating history.
- OpenFeature compatibility is conceptual/provider-boundary only. Current stable concepts used as reference: typed flag evaluation, evaluation context with optional targeting key, fractional evaluation, deterministic provider-neutral resolution and privacy caution for context data. Experimental/provider-specific behavior is not architecture authority.
- Manual intervention: NONE for provider-neutral core.

## Completion record

- Dedicated branch: `r14/11-remote-config-feature-flags`; exact normalized branch point `a9db57de1c1cc550604edbe6fec095e0a8e13c40`.
- Rejected candidate `b43acf2a0f870587a85141cbdb91a3cf352bf2c7` is NON-AUTHORITATIVE and its evidence must never be reused. Its first R14 Remote Config Acceptance run `33234680565` exposed an invalid test/acceptance fixture assumption: object authorization IDs cannot use the permission wildcard `*`.
- The correction enumerated explicit authorized snapshot/flag/environment object IDs and did not weaken historical R14.6 authority semantics.
- Intermediate green source `2a97caac8e2ac19615f7ce2c64585ae8080bd2fe` proved the corrected core but was not frozen because public backend exports were still incomplete.
- Accepted immutable technical source: `a58a0cf48a5e2311b5f6e671655f107e92c4645e`, including public `kodepoia.backend` exports and their dedicated regression.
- Dedicated exact-source R14 Remote Config Acceptance run `33234881304`: Ubuntu job `99053992967` SUCCESS; Windows job `99053993105` SUCCESS.
- Focused regression spans R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.11 remote-config semantics and R14.11 public backend exports.
- Nineteen checks PASS cross-platform: typed schema, immutable snapshots, targeting precedence, stable fractional assignment, bounded rollout distribution, targeting-key fail-closed, prerequisite-cycle rejection, prerequisite enforcement, server-clock expiry, kill-switch override, preview/dry-run, production approval + SafeChange, rollback, environment isolation, object/function authorization, typed OpenFeature-style fallback, redacted evidence, bounded capacity and remote-code type rejection.
- Cross-platform decoded evidence is identical. Digests: snapshot `70397539d8e0fd41102387f32a29f947f29b629cbbfddbd9b20b660b40ca27c4`; state `5343df1b58f0f595133261cdff705d720dc2e2c561e6d01cd69263060680a0c9`; trace `4f45743cdc5af05bbdb795026d2e15a76c502c37d46c649a5ba08347efd00509`; audit `4ec2eb54f751b49c6f43388fc7fcc76f16b7cc9e76eeffe703a638c941b46aa7`; rollout assignment `24df98a3b2058d746bbbec24af41299acc9d84ea2b3d102cee4efbb56de69a98`; rollback preview `d34ad885b9bb733120616e14c96c3e82418d1e3bdbc05099538c9c00022a176a`.
- Fractional fixture: 2,000 subjects -> `off=980`, `on=1020`; same targeting key remains assigned despite unrelated context changes.
- Rollback fixture: `test-v2 → test-v1`, final active `test-v1`; immutable snapshots remain registered.
- Budgets: `max_snapshots=32`, `max_flags_per_snapshot=32`, `max_evaluations=5000`, `max_audit_records=128`.
- Artifacts: Ubuntu `9709604569` / `sha256:25026a76c041d780cb75aeb0cc6cf06143c4a6a5430dc1c1c3a3c82725c6ef63`; Windows `9709607701` / `sha256:1db48d5162f36132568ec8d223c036c7267831f471f068d4140e6ef9360eee24`.
- Evidence schema: `schemas/r14/backend-remote-config-evidence.schema.json`; state is `manual_state=none`, `provider_live_claim=false`, `secrets_exposed=false`, `pii_exposed=false`, `arbitrary_code_execution=false`.
- Stable OpenFeature concepts are informative/provider-boundary evidence only: optional targeting key for subject identity/fractional evaluation, typed evaluation/default fallback, typed context, privacy caution and standard error vocabulary. No full OpenFeature conformance is claimed.
- END state: R14.11 COMPLETE; R14.12–R14.17 remain PLANNED. R14.12 is not authorized until the exact R14.11 END-head passes fresh R0/Python/UI/R14 Remote Config gates, the implementation PR merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

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

## START authority

- Dedicated branch: `r14/12-content-delivery`.
- Exact branch point: normalized R14.11 `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- R14.11 closure authority: immutable technical source `a58a0cf48a5e2311b5f6e671655f107e92c4645e`; final END-head `ef39e7898abbca5466073bb78a95df829a33d836`; fresh END gates R0 #1863 / `33235110200`, Python Core #1837 / `33235110228`, UI #1804 / `33235110215`, R14 Remote Config #27 / `33235110216` all SUCCESS; PR #277 expected-head merge `a32b62c4e961ed2f5fe66dd5e30c453abb64d9f1`.
- Single R14.11 post-merge normalization head `5356f2354d8c2237ccb6a3957b1c2cde21d4de80` changed only continuity, passed R0 #1865 / `33242852652`, Python Core #1839 / `33242852691`, UI #1806 / `33242852613`, and PR #278 merged with expected-head as normalized `main` `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- START state: R14.1–R14.11 COMPLETE + NORMALIZED; R14.12 IN_PROGRESS; R14.13–R14.17 PLANNED.
- Trust invariants: content identities/manifests/bundles are immutable and hash-addressed; executable/self-modifying payloads are rejected; dependency graphs are acyclic and bounded; client/schema compatibility is explicit; channel promotion is atomic and rollback selects a prior immutable manifest; downloads/cache promotion require exact size/hash verification; cache corruption purges rather than silently serves; external URLs are never accepted from untrusted project/content data without existing allowlist/network authorization.
- Core acceptance uses a deterministic local content provider and local HTTP fixture. No external CDN account/domain/credential is required or claimed. `provider_live_claim=false`.
- Manual intervention: CONDITIONAL / NOT TRIGGERED. External CDN/provider proof is deferred unless explicitly requested later; secrets/tokens must never be supplied through model-visible text or committed evidence.

## Completion record

- Dedicated branch: `r14/12-content-delivery`; exact normalized branch point `71ceb529e89b13be343be76527e9b9b0b419ceda`.
- START synchronization was completed before the first implementation commit; no R14.12 implementation preceded its plan/continuity START authority.
- Rejected candidate `d62a07508cd94aae5446506dd63767f0dffe6178` is NON-AUTHORITATIVE and none of its evidence may be reused. Its evidence fixture was stopped by object authorization before reaching the intended dependency-validation assertion; fixture authorization was corrected without weakening content authority.
- Intermediate `d8576a3ab7cb8b496d321afe98c575375b694c14` is not acceptance authority: audit found generic PR workflows were checking GitHub's pull-request merge ref rather than the literal branch head. R0/Python/UI workflows were hardened to check out and assert `pull_request.head.sha || github.sha` explicitly, with `r14/**` push coverage added.
- Intermediate exact-head candidate `277536f5d5fd22d73ee1b52d0818fc83f1d3ea2a` is SUPERSEDED / NON-AUTHORITATIVE because a frozen-plan audit then found the required real local HTTP fixture was still absent.
- Accepted immutable technical source: `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`, including immutable/hash-addressed content delivery, exact-head CI hardening, governed loopback HTTP fixture/client and end-to-end HTTP regression.
- Technical exact-source gates: R0 Repository Guard #1882 / `33244609227` SUCCESS on Ubuntu + Windows; Python Core #1857 / `33244609228` SUCCESS for Ubuntu/Windows Core, UI-in-core and Ubuntu/Windows package builds; KodeStudio UI Smoke #1822 / `33244609244` SUCCESS; R14 Content Delivery Acceptance #19 / `33244609252` SUCCESS on Ubuntu + Windows.
- Full Ubuntu Python Core: **1674 passed / 13 skipped / 46 warnings**; R7, R8 and R9 integrated acceptance validation also PASS. Standalone KodeStudio UI Smoke: **14 passed**.
- Dedicated R14.12 jobs: Ubuntu `99079798454` SUCCESS; Windows `99079798481` SUCCESS. Focused regression spans R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.11 remote config, R14.12 content delivery, the actual loopback HTTP fixture and backend public-export regression.
- All twenty frozen evidence checks PASS cross-platform: atomic promotion, bounded capacity, cache corruption rebuild, client/schema compatibility, dependency-cycle rejection, environment isolation, ETag cache hit, executable rejection, function authorization, immutable bundle/manifest identity, missing dependency rejection, object authorization, Range/If-Range semantics, redacted evidence, revocation, rollback convergence, stale-promotion rejection, tamper rejection and truncation rejection.
- Real local HTTP regression additionally proves full GET, ETag/If-None-Match `304`, Range `206`, matching If-Range, stale If-Range complete `200`, service promotion/download/cache over actual loopback HTTP, and rejection of non-loopback/HTTPS/path/userinfo fixture endpoints.
- Cross-platform decoded evidence objects are identical. Digests: bundle `2c424688f078fce0d936ef7ec1a5a366c0f8a227601154c0d9f21f0f3cad4aea`; channel/rollback `3727bd7357173626e7e8adc7c9847cd04c34ee84674a1cc817558503f35da9f7`; download `e82789b9374d28edaa742e57abef325f7fa71f3a1000905b6aa5430d56b62aaa`; manifest v1 `fe65b209e4cd5425fcfc70862f1fa70ee661832ff8ddc70563e95fc222b93156`; manifest v2 `eecb207bf893149c6197679e5b5c7d3b42bea6e59ae1354c851a17330be2794b`; state `777e94990f33d32d7a03095957ea0a200dec4c9a4ff8241c1bea6bf3e9b19c62`; trace `f017e23985f805856801b613904d272cb71396daa5692688159f2366a2c43711`.
- Budgets: `max_bundles_per_manifest=16`, `max_cache_bytes=2097152`, `max_cache_entries=32`, `max_channels=8`, `max_manifests=16`, `max_object_bytes=1048576`; fixture counts: 4 bundles, 2 manifests, 400 cache bytes, channel revision 3.
- Canonical artifacts: Ubuntu `9712443954` / `sha256:8a85b0978a537436c4d97ae420b13ff78184777850112f63aa1abdb837cfc320`; Windows `9712439689` / `sha256:900a669e5ee7915f2f1be1c2b92f55ccfe38e6cf82907122f407a66c442a5b33`.
- Evidence schema: `schemas/r14/backend-content-delivery-evidence.schema.json`; evidence reports `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `secrets_exposed=false`, `raw_urls_exposed=false`, `executable_content_allowed=false`.
- RFC 9110/9111, OWASP SSRF guidance and Apple App Review Guidelines are informative compatibility/safety evidence only. No external CDN/provider account, domain, TLS certificate, credential, quota or provider-live proof is claimed.
- END state: R14.12 COMPLETE; R14.13–R14.17 remain PLANNED. R14.13 is not authorized until the exact R14.12 END-head passes fresh R0/Python/UI/R14 Content Delivery gates, PR #279 merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

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

## START authority

- Dedicated branch: `r14/13-events-telemetry-pipeline`.
- Exact branch point: normalized R14.12 `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6`.
- R14.12 closure authority: immutable technical source `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`; final END-head `42db6d1fa84f5bd9b6a2c8e399603b9b9e621417`; fresh END gates R0 #1884 / `33245750516`, Python Core #1859 / `33245750503`, UI #1824 / `33245750507`, R14 Content Delivery #21 / `33245750553` all SUCCESS; PR #279 expected-head merge `a088a081276213e7efa7bfb03b7b8adea2f0a75b`.
- Single R14.12 post-merge normalization head `8ceff867b09c8161e66d57dee936ce493dfc5a77` changed only continuity, passed fresh exact-head R0 #1888 / `33246000936`, Python Core #1863 / `33246001036`, UI #1828 / `33246000984`, and PR #280 merged with expected-head as normalized `main` `2e51e8143949dbca48860ff1ff634ee1acf27cf6`.
- START state: R14.1–R14.12 COMPLETE + NORMALIZED; R14.13 IN_PROGRESS; R14.14–R14.17 PLANNED.
- Frozen event invariants: immutable event identity; typed schema/version; canonical bounded payloads; explicit event/source/subject/trace identities; append-only local authority; duplicate-safe consumption; declared at-least-once semantics with durable checkpoints; replay is bounded, permissioned, dry-run capable and audited; dead-letter state is explicit; retention cannot silently delete uncheckpointed required history; privacy classification/redaction occurs before observability export.
- CloudEvents stable release v1.0.2 is an informative provider-neutral envelope interoperability reference only; Kodepoia keeps an internal governed envelope and does not make any CloudEvents transport binding mandatory.
- OpenTelemetry Specification 1.60.0 is the current provider-neutral observability reference. The bridge exports governed trace/metric/log correlation data only after privacy filtering; no Collector/backend/provider is mandatory. Current OTel security guidance places sensitive-data identification/minimization/redaction responsibility on the implementer.
- Manual intervention: NONE. No external event broker, Kafka cluster, OTel Collector or telemetry SaaS credential is required for core acceptance.

## Completion record

- Dedicated branch: `r14/13-events-telemetry-pipeline`; exact normalized branch point `2e51e8143949dbca48860ff1ff634ee1acf27cf6`; clean START-head `3372b20709eeccefa1b65ea256918206436d8b48` differed from normalized main by plan + continuity only and preceded all implementation bytes.
- Accepted immutable technical source: `b1729cabaffb19ac5491dee8a2c18e1bb5877746`.
- Technical exact-source gates: R0 Repository Guard #1894 / `33247079759` SUCCESS Ubuntu + Windows; Python Core #1869 / `33247079754` SUCCESS for Ubuntu/Windows Core, both package builds and UI-in-core; KodeStudio UI Smoke #1834 / `33247079785` SUCCESS; R14 Event Pipeline Acceptance #1 / `33247079799` SUCCESS Ubuntu + Windows.
- Full Ubuntu Python Core: **1692 passed / 13 skipped / 46 warnings**; R7/R8/R9 integrated acceptance validation also PASS. Focused R14.5/R14.6/R14.13/export regression: **51 passed Ubuntu + 51 passed Windows**.
- Twenty-five frozen evidence checks PASS identically cross-platform: immutable schema/event identity; secret/credential/unknown-field rejection; dedupe; event-ID rebinding rejection; source ordering; function/object authorization; environment isolation; at-least-once redelivery; ordered/idempotent checkpoint ACK; restart restore; dead-letter threshold; dry-run and executed replay checkpoint safety; replay-ID rebinding rejection; retention guard/prune; pruned identity non-reuse; OTel redaction; CloudEvents v1 interoperability shape; bounded capacity; redacted evidence.
- Cross-platform semantic evidence is identical. Digests: schema `648affd6dedf50063100b3b8cf7d26b95a5c56156d541e03a6867b35fe594259`; event `41475424fc7aff50871beeca5335e30e520e0855e7769daea7e42990eb4b77ec`; checkpoint `f08c139275b3256f368253f7f7937e3da8d77e356e9cd066b01e0dca5a48df21`; dead-letter `615b19f9fd8cda3aa7c4b0e5acef04ad1b659c7e3d77f4b2373100e180accf81`; replay preview `54846df765e20b893ee55d8ee0a5cf96c0e886406959e7af1ff4b145038cbf40`; replay execute `1ddf5f711184343bec76eca58ccdaeee5f900ca150fc1dabc55940f3c17eaee2`; OTel `28a93312419d3e390009254d4cfc7872d3ae61d243dd8b1a4939c699842d3bf7`; state `8efdb02adaa57c732d492b0d54eebe8b4a581877864bff3a352fa651c85439c7`; trace `9437f5415724c4f299bcea79da5201a46b59c17b250d2c4a40d4bf18410c4d9a`.
- Evidence counts: 3 acceptance events appended; 2 checkpoints; consumer lag 1 event; 1 dead-letter; 2 replay records; 1 retained event / 27 retained payload bytes after safe pruning; 1 registered schema. Budgets: `max_consumers=16`, `max_dead_letters=16`, `max_events=64`, `max_replay_events=8`, `max_replay_records=16`, `max_retained_payload_bytes=65536`, `max_schemas=16`, `max_trace_records=256`.
- Canonical artifacts: Ubuntu `9713178222` / `sha256:20ac5fdd68f5295d96a198c896e885c470c7cc5a778f9dabcce112f2169770ac`; Windows `9713185126` / `sha256:9c62de0d3ebe042c0d0555a4934d90486dc2b3738d819e638ca9fd64a02c293b`. ZIP metadata differs by platform while decoded evidence objects are identical.
- Evidence schema: `schemas/r14/backend-event-pipeline-evidence.schema.json`; evidence reports `manual_state=none`, `provider_live_claim=false`, `external_broker_required=false`, `otel_collector_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.
- Privacy boundary is explicit: `cloudevent_mapping()` is an internal/provider-neutral event-envelope interoperability mapping and is not a privacy-sanitized telemetry export. `OpenTelemetryEventBridge` is the observability export boundary and redacts `SENSITIVE` payload fields plus hashes subject identity before export; `SECRET` and high-risk credential-like schema fields fail closed at registration/model construction.
- CloudEvents v1.0.2 and OpenTelemetry Specification 1.60.0 are informative interoperability baselines only. No external broker, Kafka cluster, OTel Collector, telemetry SaaS account or credential is required or claimed.
- Manual intervention: **NONE**.
- END state: R14.13 COMPLETE; R14.14–R14.17 remain PLANNED. R14.14 is not authorized until the exact R14.13 END-head passes fresh R0/Python/UI/R14 Event Pipeline gates, the implementation/evidence PR merges with expected-head protection, and exactly one continuity-only post-merge normalization passes fresh R0/Python/UI and merges.

---

## R14.14 START authority

- Dedicated branch: `r14/14-liveops-campaigns-schedules`.
- Exact branch point: normalized R14.13 `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`.
- R14.13 closure authority: immutable technical source `b1729cabaffb19ac5491dee8a2c18e1bb5877746`; final END-head `5461815da316bf9e20b06352dc7dda8699b46525`; fresh END gates R0 #1898 / `33247444761`, Python Core #1873 / `33247444733`, UI #1838 / `33247444748`, R14 Event Pipeline #5 / `33247444765` SUCCESS; PR #281 expected-head merge `e1109c84a4b55761e4bf948b13457aabd327669e`; unique normalization head `6d302f20ba05544d1a1f122ebed48816dd22c76b`; fresh normalization gates R0 #1902 / `33247706878`, Python Core #1877 / `33247706820`, UI #1842 / `33247706847` SUCCESS; PR #282 expected-head merge produced normalized `main` `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`.
- START state: R14.1–R14.13 COMPLETE + NORMALIZED; R14.14 IN_PROGRESS; R14.15–R14.17 PLANNED.
- Time authority baseline: scheduler state is canonical UTC instants; named display/recurrence timezone identifiers remain explicit metadata. IANA Time Zone Database `2026c` (released 2026-07-08) is current compatibility evidence, and RFC 5545 is informative recurrence/TZID guidance. These are versioned evidence, not frozen runtime constants.
- Core acceptance remains provider-neutral and network-free. No production LiveOps provider/account/credential is required. Manual intervention: NONE.

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

- Dedicated branch: `r14/14-liveops-campaigns-schedules`; exact normalized branch point `b56162e0903bf2dc29505dfb6385030ed5d4b9d4`; clean START-head `c17356c7d24fb07544d3f58e65d7f4ef2a2f7624` preceded all implementation bytes.
- Accepted immutable technical source: `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`. Its source tree is `e4908fcdd92e59299310813fb1acd23cd1d9f062`.
- Superseded candidates are NON-AUTHORITATIVE: `25b1da3867d5b067c4345152366cec93aa62bd7f` exposed invalid duplicate regression paths in the persistent gate; `b3a2e8395d34ffd0fa61ae5447fca9d150811ce1` exposed the invalid object wildcard in the acceptance actor; `a1163b4a16eecf788c5afa4d6e0cf0ff111b008d` exposed the missing Remote Config audience object authorization. None of their decision evidence may be reused.
- Technical exact-source gates on `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`: R0 Repository Guard #1930 / `33251838461` SUCCESS; Python Core #1905 / `33251838469` SUCCESS 5/5 jobs; KodeStudio UI Smoke #1870 / `33251838453` SUCCESS; R14 LiveOps Acceptance #4 / `33251838460` SUCCESS on Ubuntu 24.04 and Windows 2025.
- Full Ubuntu Python Core: **1713 passed / 13 skipped / 46 warnings**, with R7/R8/R9 integrated acceptance validation PASS. Dedicated R14.14 focused/export regression: **21 passed Ubuntu + 21 passed Windows**.
- All 23 deterministic LiveOps checks PASS cross-platform: activation idempotency; SafeChange approval idempotency; audience snapshot mismatch rejection; authorization fail-closed; billing environment guard; bounded-capacity fail-closed; exact dependency binding; expiry idempotency; immutable season identity; terminal kill idempotency; missing-dependency rejection; pause without hidden scheduler advance; explicit pause/resume; preview digest clock stability; non-mutating preview; redacted evidence; Remote Config audience targeting; auditable rollback; rotation resolution; UTC/timezone metadata; scheduler replay idempotency; stale-preview rejection; unsafe-schedule rejection.
- Cross-platform evidence is semantically identical. Counts: 1 season, 1 campaign, 1 activation, 1 runtime record, 2 rotations, 7 audit records, 8 trace records and 23 checks. Budgets: `max_seasons=1024`, `max_campaigns=4096`, `max_dependencies=16384`, `max_activations=16384`, `max_audit_records=100000`, `max_trace_records=200000`.
- Frozen digests: season `b248ec4595a757731318705d498d7275aa25cb80416308025b7bf5d318d67e34`; campaign `f8a37a0dcd545f3fae4d13092c4e443d753dba96e6cdd6d6f0e6452ca6295183`; preview `0cc8fa8f6dac0cb882b94149516f98c6d502a041b8bc2e98c7c64b3d79710742`; approval `9e32edb5397b1b3e68cb8d765c5530ddee340667565f7fd4b8f94f73d17721bb`; activation `62aa304aadf785e204a5c3bbb6fa09cdce365e5f8b0ccc82bf02b3fa7b81e723`; audience `c892c99331c1e8904894506ee20724105efa40d2915d5ffdf8bd5eca95953ef5`; state `d24bfdaec041971f4270c46d8ffe60740432bf6805ea63d69857abe6d65f7aa5`; dependencies `3a959c3c83aaca047e0f1c81018e6d506cad10d07a88ff6b14590ddbde9e0336`; audit `bb18bd011fb7a0a6ac128f0426ce8643b416e10250445026e98e810c8653c7f9`; trace `1c0d7d7fd2cb50397c5783faf29ed518a7dea15a39b9463889f5db91129f43e5`; SafeChange `e6fbd826cda283c4d17cdcfce9b753ec503f5880295e701edc35078dfddf4de0`.
- Time authority is canonical UTC with season display TZID `Europe/Paris`, campaign display TZID `America/Edmonton` and evidence `tzdb_version=2026c`.
- Canonical artifacts: Ubuntu `9714598172` / `sha256:8ca1e46462e31f5a41dd97f517f5e98d06081b0d392d77bfe7977bec0b9f99a8`; Windows `9714604219` / `sha256:fc9202c60fb080c95f0106f3c3d62580fff32311fc24d08ae04a3e26f82662f1`. ZIP metadata differs while decoded evidence is identical.
- Evidence schema: `schemas/r14/backend-liveops-evidence.schema.json`; evidence reports `manual_state=none`, `provider_live_claim=false`, `external_provider_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`.
- IANA tzdb `2026c`, RFC 5545 TZID/recurrence semantics and stable OpenFeature evaluation-context/targeting-key concepts are informative compatibility evidence only. No full standards/provider conformance or live-provider capability is claimed.
- Manual intervention: **NONE**. No external LiveOps SaaS, production billing account, CDN, event broker, OTel collector, production credential or network access was required.
- Unique post-merge normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`; fresh exact-head R0 #1944 / `33254094376`, Python Core #1919 / `33254094466` and KodeStudio UI Smoke #1884 / `33254094372` all SUCCESS. PR #284 merged only with `expected_head_sha=8b527170d3b79bfacbdac36f638c8c616689bc61` as normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.
- Final state: **R14.14 COMPLETE + NORMALIZED**. R14.15 is authorized only from normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`; R14.16–R14.17 remain PLANNED.

---

## R14.15 START authority

- Dedicated branch: `r14/15-service-operations-resilience`.
- Exact branch point and sole authorized base: normalized R14.14 `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.
- R14.14 closure authority: immutable technical source `bd7d0130b5241047e5583bd31e0a183be1a1e6f1`; final END-head `d8debf494f4f096e2a9f8a4093852752242e8b9f`; fresh END gates R0 #1938 / `33253609529`, Python Core #1913 / `33253609548`, UI #1878 / `33253609556`, R14 LiveOps Acceptance #5 / `33253609622` SUCCESS; PR #283 expected-head merge `29bf8255277fcbfce721408ec0abab660076f99d`; unique normalization head `8b527170d3b79bfacbdac36f638c8c616689bc61`; fresh normalization gates R0 #1944 / `33254094376`, Python Core #1919 / `33254094466`, UI #1884 / `33254094372` SUCCESS; PR #284 expected-head merge produced normalized `main` `0078a75d473524688e6ab76ccf41b509e2146dea`.
- START state: R14.1–R14.14 COMPLETE + NORMALIZED; R14.15 IN_PROGRESS; R14.16–R14.17 PLANNED.
- Core execution posture: deterministic/local or hosted-CI health, retry/circuit/rate-limit, backup/restore/DR, failure-injection and bounded-load evidence only. No Internet-scale, multi-region, external-provider quota/cost or production-load claim may be inferred from core CI.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. External provider quota/cost/load proof becomes manual/provider-dependent only if explicitly claimed; destructive or high-cost production load is forbidden by default.

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

- Dedicated branch: `r14/15-service-operations-resilience`; exact normalized branch point `0078a75d473524688e6ab76ccf41b509e2146dea`; clean START-head `c3dd8aa5f3a7ec7d5f866ead207cf3a023fedbf0` preceded implementation.
- Accepted immutable technical source: `232bae747e91fd97f4cf3110a019639217d7914b`. START→source surface is exactly seven intended files: resilience implementation, backend public exports, focused tests, export regression, deterministic acceptance script, evidence schema and dedicated workflow; no helper survives.
- Bootstrap/helper commits and runs used while satisfying GitHub workflow-token restrictions are NON-AUTHORITATIVE and must never be reused as decision evidence. Only exact-source gates on `232bae747e91fd97f4cf3110a019639217d7914b` are authoritative.
- Technical exact-source gates: R0 Repository Guard #1959 / `33255887218` SUCCESS Ubuntu + Windows; Python Core #1934 / `33255887265` SUCCESS 5/5; KodeStudio UI Smoke #1899 / `33255887175` SUCCESS; R14 Service Operations Resilience Acceptance #1 / `33255887252` SUCCESS Ubuntu 24.04 + Windows 2025.
- Full Ubuntu Python Core: **1731 passed / 13 skipped / 46 warnings**, with R7/R8/R9 integrated acceptance PASS. Dedicated R14.15 focused/export tests: **18 passed Ubuntu + 18 passed Windows**.
- All 24 deterministic resilience checks PASS identically cross-platform: backup integrity; bulkhead rejection; circuit open/recovery; redacted evidence; bounded failure timeline; graceful drain; load-budget pass/failure detection; no external-load claim; non-idempotent retry rejection; optional dependency degradation; OTel-compatible service observation; production restore rejection; rate-limit rejection; required dependency outage unavailability; isolated restore and payload equality; bounded/deterministic retry delays; transient recovery; bounded RPO/RTO; untrusted-backup rejection.
- Key digests: degraded health `6013bc39f146bc5e564f62cfa9367c9cbde619214dd391879204e43f13df838d`; unavailable health `16e45082480ef5b9a65d09671be1c7075aab119400f71ca5a4f8c139627042e7`; OTel dependency `b775b5ab61cac6c3f2df3eb6cb25840cf19980264257e6fde80e92fb4ca4a066`; retry `7f44cdb44fbb2dc37d0e8b443e97ece9c81b951d286d4cd1c4b00f3187380e3b`; backup `53141385e61fcd1054ab58bb3339777034f058573e9da6f03fbda1eb26445747`; restore `464b5105d0113d69ecf6ad47618e7e47e4930cd690e606a5f7e6701212a3a6cf`; load profile `2bce6ca28c86da6c15c7fd82a50a46e74e60cedc7cabd43ce0cde8cf30e6e9e2`; load result `73814856c829f3e8cccf3731f3da81cb63613be6ebed12f98742f95e3c949616`; operations `81f49a0c335a0f6dacd94017dcd82a74bc2eb9825e26c98bb1ca7d1c58532718`.
- Bounded evidence: retry 3 attempts with delays `[6, 30]` ms inside 400 ms total timeout / 375 ms worst-case policy budget; failure timeline 3 records / 0 dropped; fixture restore provenance `kodepoia_fixture`, encrypted=true, isolated=true, RPO 100 ms, RTO 40 ms; load profile 200 requests, p95 92.0 ms, error rate 0.005, peak concurrency 6, CPU 620 ms, memory 180 MB.
- Technical artifacts: Ubuntu `9715782929` / `sha256:4f5c11edd50677bacdfcd73c88acc77f3e8c2574b9c2b32af9b4a16010c4bb5e`; Windows `9715786195` / `sha256:02b4a0c471c832c06ec2ae7cd80c14fd22e6e169015eae1cf142608a4997bb68`; decoded JSON evidence objects are exactly equal cross-platform.
- Evidence flags: `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `external_load_required=false`, `secrets_exposed=false`, `pii_exposed=false`, `raw_payloads_exposed=false`, `internet_scale_claim=false`, `multi_region_claim=false`, `postgresql_pitr_claim=false`.
- Compatibility boundary: idempotent-only bounded retry/backoff/jitter; OTel `service.name`-compatible observations only; PostgreSQL restore evidence is `fixture_restore_only`. Production PITR requires separate physical/base-backup + WAL evidence and is not claimed by core CI.
- Manual intervention: **CONDITIONAL / NOT TRIGGERED**. No external provider quota/cost/load evidence is required for the accepted core; destructive/high-cost production load remains forbidden by default.
- Final clean END-head `80bd6853664ab9f41fd41fb83f43b43980bef394` is a direct child of immutable source `232bae747e91fd97f4cf3110a019639217d7914b`; source→END changed exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_15_ACCEPTANCE.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.
- Fresh exact-END gates: R0 Repository Guard #1966 / `33257412850` SUCCESS; Python Core #1941 / `33257412849` SUCCESS 5/5 with Ubuntu **1731 passed / 13 skipped / 46 warnings**; KodeStudio UI Smoke #1906 / `33257412847` SUCCESS; R14 Service Operations Resilience Acceptance #3 / `33257412881` SUCCESS Ubuntu + Windows with 24/24 deterministic checks.
- Fresh END artifacts: Ubuntu `9716228073` / `sha256:97f82c4203d6d8987883849069c3bd8f47345b90d6078c2fcedf236c5c237bec`; Windows `9716231809` / `sha256:87fa03305606e02cc7758cdbd334e1f545023792859cc825323afa096eec1573`.
- PR #285 merged only with `expected_head_sha=80bd6853664ab9f41fd41fb83f43b43980bef394` as implementation merge `53373e78c60d4a338e9313496a822c93ab334e68`.
- The unique post-merge normalization head `68a6f106484ab60d9925dfcc60189b509d995393` changed only continuity, passed fresh exact-head R0 #1973 / `33257784369`, Python Core #1948 / `33257784390` (5/5), and UI #1913 / `33257784370`, then PR #286 merged with `expected_head_sha=68a6f106484ab60d9925dfcc60189b509d995393` as normalized main `1f10d7a13f49cb6e931e5e0694f083228ed24070`.
- Post-normalization continuity erratum head `ff8e24a13ae040956f9eff4ebaa19f02f4a142a1` corrected stale wording only; fresh erratum gates R0 #1979 / `33258615852`, Python Core #1954 / `33258615797`, and UI #1919 / `33258615872` all SUCCESS. PR #287 merged with exact expected-head as current main `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`. This erratum is explicitly **not** a second normalization; normalization cardinality remains exactly one.
- R14.15 final state: **COMPLETE + NORMALIZED**. Manual/provider state remains **CONDITIONAL / NOT TRIGGERED**; no external-provider quota/cost/load, Internet-scale, multi-region or production PostgreSQL PITR claim is made. R14.16 START-sync is authorized from the current main carrying the normalized R14.15 state plus the continuity-only erratum.

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

## START authority

- Dedicated branch: `r14/16-cli-kodestudio-liveops-ux`.
- Effective exact branch point: current `main` `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`. R14.15's unique normalized anchor remains `1f10d7a13f49cb6e931e5e0694f083228ed24070`; PR #287 only added the continuity erratum and is not a second normalization.
- START state: R14.1–R14.15 **COMPLETE + NORMALIZED**; R14.16 **IN_PROGRESS**; R14.17 **PLANNED**.
- Scope authority is limited to structured CLI/KodeStudio workflows over existing R14 domain APIs: backend/local-stack status, migration preview/apply, provider capability, lobby/save/progression inspection, entitlement reconciliation preview, config/content/campaign preview/rollout/rollback, event replay preview, and resilience/backup/load reports.
- Trust invariants: no raw shell console; no raw secret values; no ungoverned endpoint/command escape; environment and authority scope remain visible; destructive/live mutations require existing permission/confirmation/SafeChange rules; inspect/preview/dry-run remains the default for migrations, replay, rollout, content and campaign actions; machine-readable CLI JSON must be stable and redacted.
- UX authority includes accessibility and localization regression coverage without weakening server/domain authorization. UI/CLI are adapters, never alternate authority paths.
- Manual intervention: **NONE**. Core R14.16 must remain provider-neutral and testable from local/hosted CI without external account, credential, production deployment or live provider proof.

## Completion record

- Dedicated branch: `r14/16-cli-kodestudio-liveops-ux`; effective normalized-history branch point `8a7eb312d3fa0d642d6b2b77ef35c2b2d3e7de36`; clean START-head `3b0ad3bf666f1e6247699b8ef611b436f836b60a` preceded implementation.
- Accepted immutable technical source: `3c0507ed497d9607218b9d9a50c2e5729d786c87`. START→source contains exactly 13 intended technical/test/evidence files: governed Backend/LiveOps facade, CLI, KodeStudio panel/localization, CLI/app wiring, four regression files including R6.6 pseudo-locale coverage, deterministic acceptance script, evidence schema and cross-platform workflow. No staging helper survives.
- Technical exact-source gates: R0 Repository Guard #2005 / `33260302790` SUCCESS Ubuntu + Windows; Python Core #1980 / `33260302771` SUCCESS 5/5; KodeStudio UI Smoke #1945 / `33260302782` SUCCESS; R14 CLI KodeStudio LiveOps UX Acceptance #2 / `33260302752` SUCCESS Ubuntu 24.04 + Windows 2025.
- Full Ubuntu Python Core: **1752 passed / 14 skipped / 46 warnings**, with R7/R8/R9 integrated acceptance PASS. Dedicated focused R14.16 regression: **26 passed Ubuntu**, with the same focused test step SUCCESS on Windows.
- All **31/31 deterministic acceptance checks PASS**: typed 15-operation catalog/defaults; confirmation-vs-authorization separation; separate production authority; governed mutation path; redaction; raw command/endpoint/token/resource escape rejection; local/test stack restriction; truthful unavailable provider/load/backup claims; stable JSON; EN/FR/qps-ploc localization; structured KodeStudio controls and wiring.
- Evidence flags: `manual_state=none`, `provider_live_claim=false`, `external_provider_required=false`, `secrets_exposed=false`, `raw_command_input_exposed=false`, `raw_endpoint_input_exposed=false`, `automatic_production_publish=false`, `operation_count=15`, `check_count=31`, `passed_count=31`.
- Evidence digests: catalog `f0ac90c20d06d7e6ffdff22756bf65499c5e9d839098fb51ec8a7f1738dc351b`; preview `ff1089d254637027bd959a669cae6b3cc6f82252c2c1883cb24c1878fe418719`; authorized mutation `c809c93458f425b48a7546afc78bd21dff3b412a6a17c3ba203d1c615cdc8c13`.
- Cross-platform decoded evidence JSON is exactly equal: 2245 bytes and SHA-256 `396588f20a03bb555c1a69cfd9b076151e850d11c8842b9ef9a94708a6a7eea2` on both OS. Artifacts: Ubuntu `9717060425` / `sha256:2e53b8fab1bfb5acd0e8197ee79e8475b975e3aecc017c264347bd00c73a607a`; Windows `9717061707` / `sha256:39308eb7833026dc06184ec5e753fe229279898f95693fd55181ee78f1ef6907`.
- Rejected source `1707ca57a325a3187bfbe5327002bc2f30dc34d7` exposed stale R6.6 nav-count plus missing R14 pseudo-locale coverage; rejected source `c6a62355bf58a49c0bc4fc41a0ef29e6d0168825` exposed a missing Ubuntu Qt runtime dependency (`libEGL.so.1`) before business assertions. Neither candidate nor its failed evidence is reused.
- Security boundary: UI/CLI confirmation is intention only, never permission; mutation requires injected domain authority and production requires separate production authority. Project fallback never authorizes mutation. Raw shell/command/endpoint/secret/token/password/DSN/private-key input and automatic production publish remain forbidden.
- Manual intervention: **NONE**. No external provider account, credential, quota, public domain/TLS state, production deployment, destructive load or production PITR proof is required or claimed.
- Final clean END-head `a5797fc7a320eef033e9d2576322fac464b05c67` is a direct child of immutable source `3c0507ed497d9607218b9d9a50c2e5729d786c87`; source→END changed only `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_16_ACCEPTANCE.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md`.
- Fresh exact-END gates: R0 Repository Guard #2010 / `33260771061` SUCCESS Ubuntu + Windows; Python Core #1985 / `33260771060` SUCCESS 5/5; KodeStudio UI Smoke #1950 / `33260771074` SUCCESS; R14 CLI KodeStudio LiveOps UX Acceptance #4 / `33260771052` SUCCESS Ubuntu + Windows. Required PR R0 #2011 / `33260864183` also passed Ubuntu + Windows on the exact END-head.
- PR #288 merged only with `expected_head_sha=a5797fc7a320eef033e9d2576322fac464b05c67` as implementation merge `9c7ed58f20c794e59146813544b3a75aec0bace1`.
- Unique post-merge normalization head `418c41a22c907bdef0693b16824bd2b86fa47acc` changed only `docs/continuity/KODEPOIA_CONTINUITY.md`; fresh exact-head R0 #2013 / `33261708135`, Python Core #1988 / `33261708106` (5/5), and UI #1953 / `33261708116` all SUCCESS. PR #289 required R0 #2014 / `33261833373` passed Ubuntu + Windows and merged with exact expected-head as normalized `main` `f6960db290a570e3a0c3c4ff97600014978d45df`.
- Normalization cardinality is exactly one. R14.16 final state is **COMPLETE + NORMALIZED**, manual **NONE**. R14.17 START-sync is authorized from exact normalized main `f6960db290a570e3a0c3c4ff97600014978d45df`.

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

## START authority

- Dedicated branch: `r14/17-adversarial-integrated-acceptance`.
- Exact normalized branch point: `f6960db290a570e3a0c3c4ff97600014978d45df`, produced by the single R14.16 continuity-only normalization PR #289.
- START state: R14.1–R14.16 **COMPLETE + NORMALIZED**; R14.17 **IN_PROGRESS**.
- Scope is frozen to anti-circular integrated acceptance across the already accepted R14 services: local/test auth, PostgreSQL authority, authoritative server/lobby/reconnect, cloud-save conflict/rollback, progression, entitlement sandbox idempotency, feature config rollback, immutable content, event replay/checkpoint, LiveOps campaign lifecycle, resilience/recovery, and redaction/provider-overclaim boundaries.
- Evidence must bind to one immutable technical source; final report may consume independent gate/artifact identities but may never certify itself or mix SHAs. Local/sandbox evidence cannot imply live-production provider capability.
- Manual state: **CONDITIONAL / NOT TRIGGERED**. Core closure is local/hosted/sandbox only; no real IdP/store/CDN/managed-provider account, public domain/TLS state, credential, secret, destructive production load, or production publish is required or claimed. If any accepted claim later requires such live evidence, stop before completion.

## Completion record

To be appended when accepted.

---

## Phase completion rule

R14 can be marked `COMPLETE` only when every subdivision R14.1–R14.17 is `COMPLETE` with its required exact-head acceptance evidence, or explicitly removed from scope by a recorded roadmap/architecture decision with ADR where required. No hidden or implied subdivision may support a phase completion claim.

After R14.17 implementation/evidence merge, exactly one continuity-only phase normalization must pass fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke and merge. Only then is R14 `COMPLETE + NORMALIZED` and R15 planning authorized.

## Ongoing maintenance rule

Update `R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects or phase ordering changes. Mutable standards/provider facts are updated as versioned evidence with source/effective date; they do not silently mutate the frozen architecture.
