# R14.7 — Matchmaking, lobby, reservations, presence + reconnect acceptance

**Status:** TECHNICAL ACCEPTED — END synchronization pending final exact-head re-gates  
**Immutable technical source:** `d04c841fcef9eb9f963085da68e579dbb58186da`  
**Normalized R14.6 base:** `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`  
**Implementation PR:** #269  
**Manual intervention:** NONE

## Scope accepted

R14.7 adds provider-neutral deterministic lobby membership/roles, matchmaking tickets with canonical criteria and bounded queueing, deterministic oldest-first fixture matching, server-issued match reservations with expiry, authoritative presence revisions, cancellation terminality, and short-lived reconnect grants bound to authenticated account/session/reservation/match authority. It does not claim commercial matchmaking-provider integration, Internet-scale capacity, or product-specific MMR tuning.

## Rejected predecessor

Candidate `12071ee561717ac436f4ffa0457361685214c989` is rejected and is not valid decision evidence. R14 Matchmaking Acceptance #2 detected that `update_presence(IN_MATCH)` could authorize against a reservation whose server-clock expiry had elapsed because the expiry sweep was not performed on that path. The implementation was corrected so reservation expiry is processed before presence authorization. No gate or artifact from the rejected SHA is reused below.

## Exact-source technical gates

- R0 Repository Guard #1803 / run `33203286519`: SUCCESS.
- Python Core #1777 / run `33203286537`: SUCCESS.
- KodeStudio UI Smoke #1744 / run `33203286514`: SUCCESS.
- R14 Matchmaking Acceptance #4 / run `33203286510`: SUCCESS on Ubuntu and Windows.
- Additional regression signal: R14 Authority Acceptance #8 / `33203286523` and R14 PostgreSQL Acceptance #11 / `33203286601` also succeeded on the same candidate; these are corroborating regressions, not substitutes for the four required gates.

## Test evidence

Python Core Ubuntu: **1543 passed, 13 skipped, 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS; internal KodeStudio smoke SUCCESS.

The focused R14.7/R14.6/R14.5/R14.4 regression set passed **66 tests on Ubuntu and 66 tests on Windows**. The dedicated acceptance reports all fourteen checks true on both operating systems:

1. lobby lifecycle;
2. object authorization;
3. duplicate join is mutation-free;
4. recursive reserved authoritative fields are rejected;
5. duplicate ticket identity is idempotent;
6. deterministic matching;
7. incompatible criteria do not match;
8. matched tickets are not double-assigned;
9. cancellation reaches one authoritative terminal state;
10. reservation expiry uses the server clock;
11. stale presence revisions fail closed;
12. reconnect identity is account/session/reservation/match bound;
13. reconnect expiry fails closed;
14. queue/reservation capacity is bounded.

## Deterministic evidence

Ubuntu and Windows produced identical semantic values:

- state digest: `ae9ecc0893537e5c12cc8a78247197ed53d094b1a811c386c17161fac10c0c19`;
- lobby digest: `27bcd90471e3775b859ce21e977c5ac534909a898deab0eb2c27cd44b86db0cf`;
- reservation digest: `e8423de1a2d1a92873bbfa466111ab4a07168adeafca4bde4d62c64a70a9f690`;
- presence digest: `5f2ca6c7402bba1a3b2d195d9f63d1c8b758c01d577d4581785559d92de24f0f`;
- trace digest: `5f25c8f15da7e4f9dd45fbf072dd72101d3f32deef349c28069beeb83d954bd3`;
- terminal ticket states: `ticket-a=matched`, `ticket-b=matched`, `ticket-c=cancelled`.

Evidence budgets: `max_queued_tickets=8`, `max_active_reservations=3`, `max_ticket_ttl_ms=60000`, `max_reservation_ttl_ms=20000`, `max_reconnect_ttl_ms=5000`.

Artifacts:

- Ubuntu artifact `9698619713`, ZIP digest `sha256:f8bd9f43b431bb9a5f9b194da245a57381b000795a5c8ccacb51a866c371b1df`.
- Windows artifact `9698629064`, ZIP digest `sha256:1e3b191e9d1de0844b49c62bcd36c79798a23315e93edf20393b862d1fb44c1c`.

Both evidence documents are bound to `d04c841fcef9eb9f963085da68e579dbb58186da`, validate against `schemas/r14/backend-matchmaking-evidence.schema.json`, and assert `provider_live_claim=false` and `secrets_exposed=false`.

## External reference posture

External references are informative compatibility/security evidence, never provider lock-in. Open Match documents separation between validated frontend ticket creation and matchmaking pool/function/allocation concepts. Amazon GameLift/FlexMatch documents explicit ticket lifecycle and server-issued player-session handoff concepts. OWASP API1:2023 requires object-level authorization for actions using client-supplied object identifiers. Kodepoia implements its own provider-neutral contracts on top of accepted R14.6 authority rather than copying a provider API.

## Rollback / recovery

No live external player pool is owned. Rollback cancels/expires local owned tickets/reservations, resets deterministic fixture state, and returns to normalized R14.6 main `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`. Rejected-candidate evidence is never promoted.

## Final closure rule

Relative to `d04c841fcef9eb9f963085da68e579dbb58186da`, END synchronization may change only `docs/roadmap/R14_PLAN.md`, this acceptance document, and continuity. The final END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Matchmaking Acceptance. PR #269 may then merge only with expected-head protection. Exactly one continuity-only post-merge normalization must subsequently pass fresh R0/Python/UI and merge before R14.7 becomes COMPLETE + NORMALIZED and R14.8 is authorized.
