# R14.6 — Authoritative server command/state acceptance

## Acceptance authority

This ledger records R14.6 only. It must not claim matchmaking policy, cloud-save behavior, product-specific gameplay authority, public deployment or provider-specific realtime hosting.

## Implemented surface

- `src/kodepoia/backend/authority.py`
  - authoritative domain/actor/command/state/event identities;
  - explicit actor/session/function/object authorization boundary;
  - revision + per-session sequence validation;
  - digest-bound idempotency and duplicate replay semantics;
  - provider-neutral `AuthorityStore` protocol;
  - deterministic transactional `InMemoryAuthorityStore` fixture;
  - bounded `AuthoritativeCommandProcessor`;
  - server-issued lease registry;
  - bounded realtime event buffer with reconnect/resync semantics;
  - transport-neutral request/realtime envelope.
- `scripts/r14_6_authority_acceptance.py`
  - deterministic multi-client adversarial acceptance.
- `.github/workflows/r14-authority-acceptance.yml`
  - Ubuntu + Windows exact-source acceptance.
- strict R14 command and evidence JSON Schemas.
- focused concurrency/adversarial tests.

## Required checks

The immutable technical candidate must pass, on the exact same source SHA:

1. R0 Repository Guard — Ubuntu + Windows;
2. full Python Core — Ubuntu + Windows, package builds and internal UI smoke;
3. KodeStudio UI Smoke — Windows;
4. R14 Authority Acceptance — Ubuntu + Windows.

R14 Authority Acceptance must report all checks true:

- `forgery`;
- `stale_revision`;
- `duplicate`;
- `out_of_order`;
- `reconnect`;
- `backpressure`;
- `transaction_event_consistency`;
- `deterministic_multiclient`;
- `lease_expiry`;
- `reserved_fields`.

Evidence must validate against `schemas/r14/backend-authority-evidence.schema.json`, bind the exact source SHA and report `secrets_exposed=false`.

## Adversarial assertions

- A client cannot forge another account or session.
- Function authorization and target-object authorization are separate checks.
- Authorization occurs before idempotency lookup.
- A stale revision cannot overwrite a newer state.
- An out-of-order command cannot consume the next expected session sequence.
- Duplicate delivery is mutation-free.
- One idempotency key cannot be rebound to a different command digest.
- Handler failure is atomic: no state/event/sequence/idempotency partial commit.
- Concurrent clients starting at one revision cannot both commit that revision.
- Client payloads cannot set server-owned revision/time/event/lease fields.
- Realtime buffering is bounded by count and bytes.
- A reconnect cursor older than retained history requires resync.
- Lease issuance/expiry uses only the server clock.
- Request/realtime transport selection cannot alter authority semantics.

## Standards/security basis

- RFC 9110 HTTP Semantics.
- RFC 6455 WebSocket Protocol.
- RFC 8441 WebSockets over HTTP/2.
- RFC 9220 WebSockets over HTTP/3.
- OWASP API Security Top 10 2023 object/function authorization and resource-consumption guidance.

These references inform transport/security compatibility only. They do not create application permissions or trusted state.

## Technical evidence

- Immutable technical source: `a1425b53e1228f9c88ba373cdfabf1459393a7cf`.
- Fresh exact-head gates on that unchanged source all completed `SUCCESS`:
  - R0 Repository Guard #1795 / `33193110717`;
  - Python Core #1769 / `33193110651`;
  - KodeStudio UI Smoke #1736 / `33193110643`;
  - R14 Authority Acceptance #3 / `33193110695`.
- R14 Authority Acceptance #3 completed successfully on both `ubuntu-latest` and `windows-latest`; focused authority regression, deterministic multi-client acceptance, evidence-schema validation and exact-source validation all succeeded on both jobs.
- All ten required semantic checks are `true`: `forgery`, `stale_revision`, `duplicate`, `out_of_order`, `reconnect`, `backpressure`, `transaction_event_consistency`, `deterministic_multiclient`, `lease_expiry`, and `reserved_fields`.
- Ubuntu evidence artifact: `r14-6-authority-evidence-ubuntu-latest-a1425b53e1228f9c88ba373cdfabf1459393a7cf`, artifact id `9694600447`, ZIP digest `sha256:ec252c2e055cdb8aa9f94b0f6273f87e6e2724b22f715b8a8e986047766b194a`.
- Windows evidence artifact: `r14-6-authority-evidence-windows-latest-a1425b53e1228f9c88ba373cdfabf1459393a7cf`, artifact id `9694625857`, ZIP digest `sha256:5a2b0ad3d0841649ee3d20cc8057b3def7644f208d44e7a5bfc8154053409464`.
- Both evidence payloads bind the exact source SHA and report `status=pass`, `secrets_exposed=false` with identical semantic results across platforms.
- Final authoritative fixture state: domain `world`, target `object-a`, revision `3`, payload value `13`, state digest `59c1afb567245df4f3521052564d0bdfbaa4a5423eb7db7997c1e20160a988a3`.
- Authoritative event stream: 3 events, sequence `1..3`, digest `3adad95a513ee4812126d7d9695cc297d2f57287263a5686ee1ee5c08a15e4a1`.
- Cross-platform trace digest: `839f65c4ffbe019c43f6aad988ee8258945c328f348135ffef9320955102f178`.
- Manual intervention: `NONE`.

The immutable technical source is accepted. END synchronization may now change only `docs/roadmap/R14_PLAN.md`, this ledger and `docs/continuity/KODEPOIA_CONTINUITY.md` before fresh final exact-head re-gates.

## END synchronization

After technical acceptance, only `docs/roadmap/R14_PLAN.md`, this ledger and `docs/continuity/KODEPOIA_CONTINUITY.md` may change before final re-gates. Then the implementation/evidence PR merges with expected-head protection, followed by exactly one continuity-only post-merge normalization before R14.7 starts.

## Manual intervention

**NONE.** Core acceptance uses deterministic local/provider-neutral fixtures and hosted CI only.
