# R14.2 — Acceptance evidence ledger

## Current state

**Status: IMPLEMENTATION_CANDIDATE_PENDING**

R14.2 starts from R14.1 normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e` on dedicated branch `r14/02-backend-service-intent`. Mandatory START-sync completed before implementation on head `936056c0fd614ae11df2b9c2435cd7a6e56341c1`; cumulative START-sync changes were limited to `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

## Frozen acceptance claims

R14.2 may claim only:

- optional provider-neutral backend service intent in Project DNA v1;
- backward-compatible disabled/absent default;
- deterministic service dependency validation;
- conditional Project Wizard/KodeStudio backend questions;
- deterministic KodeProduct requirements/acceptance derivation;
- descriptive runtime intents with no transport/provisioning side effect;
- strict schemas that reject provider/credential/raw endpoint contamination.

R14.2 does not claim concrete authentication, database implementation, authoritative server implementation, matchmaking implementation, cloud storage, billing provider integration, feature-flag service, CDN, event ingestion, provisioning, deployment or production access.

## Required focused assertions

- legacy/offline fixture loads with no backend profile and emits zero runtime intent;
- legacy DNA round-trip does not manufacture `backend`;
- enabled service sets are deterministic and deduplicated;
- disabled profiles cannot hide selected services;
- enabled profiles require at least one service;
- matchmaking without authoritative state/session is rejected;
- billing without catalog and entitlement is rejected;
- database/liveops cannot appear as Project DNA service intent;
- generated runtime intents are deterministic and provider/secret free;
- strict Draft 2020-12 schemas reject additional provider/account/token/raw URL fields;
- old and enabled Project DNA fixtures validate and round-trip;
- contradictory fixtures fail both schema and model validation;
- Wizard backend-question snapshots are conditional and deterministic;
- offline/default Wizard produces no backend profile/runtime intent;
- online product signal asks for opt-in but does not manufacture services;
- KodeProduct mapping is disabled by default, deterministic and idempotent;
- profile semantics are independent of the client platform.

## Required technical candidate gates

The first accepted implementation candidate must bind the exact same head SHA to fresh:

1. R0 Repository Guard — COMPLETED / SUCCESS.
2. full Python Core — COMPLETED / SUCCESS, including Ubuntu/Windows core, package builds and internal UI smoke.
3. KodeStudio UI Smoke — COMPLETED / SUCCESS.

A failed/partial/stale head is non-authoritative and its evidence cannot be reused.

## End synchronization and normalization

After a technical candidate is accepted, update `R14_PLAN.md`, this ledger and continuity only for END-sync, then run fresh exact-head R0 + Python Core + KodeStudio UI Smoke. Merge the implementation/evidence PR with expected-head protection. Then create exactly one continuity-only normalization from that merge, re-run the same three gate families and merge with expected-head protection. Only then is R14.2 COMPLETE + NORMALIZED and R14.3 authorized.

## Manual intervention

**NONE.** No provider account, secret, paid quota, live backend, device or external deployment is required for R14.2 acceptance.
