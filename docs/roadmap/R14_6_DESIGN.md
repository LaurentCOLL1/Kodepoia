# R14.6 — Authoritative server command/state + realtime trust boundary design

## Scope

R14.6 establishes provider-neutral server authority. Clients submit intent; they do not submit trusted state. Matchmaking policy, cloud saves and product gameplay rules remain outside this subdivision.

The implementation is intentionally transport-neutral. HTTP request/response and realtime transports can carry the same typed command contract, but transport success never implies application authorization or state acceptance.

## External compatibility/security references

Current work-cycle references:

- RFC 9110 — HTTP Semantics: method idempotency and retry behavior are transport semantics; application commands that mutate state still require explicit server-side idempotency and replay handling.
- RFC 6455 — The WebSocket Protocol: bidirectional framing is a transport capability, not an authority grant.
- RFC 8441 and RFC 9220 — WebSocket bootstrapping over HTTP/2 and HTTP/3 are compatibility references only.
- OWASP API Security Top 10 2023 — explicit object-level/function-level authorization and bounded resource-consumption controls remain mandatory for every client-controlled object identity or operation.

No standards text can create application authority, permissions, URLs, queue capacity or protocol commands.

## Trust model

Trusted server-owned values include:

- current state revision;
- event sequence;
- server timestamp;
- authorization result;
- lease identity/lifetime;
- realtime retention/capacity state.

`AuthorityCommand` carries an `expected_revision` and per-session `sequence` as client assertions. The server compares them with authoritative state; it never treats them as truth.

Reserved server fields are rejected recursively when they appear inside client payloads: `authorization`, `authorized`, `revision`, `server_revision`, `server_time_ms`, `event_sequence`, and `lease_id`.

## Command flow

`AuthoritativeCommandProcessor` performs the following order:

1. bounded pending-command admission;
2. actor identity match;
3. session identity match;
4. function/command permission check;
5. target object authorization;
6. handler resolution;
7. one `AuthorityStore.process_atomic()` operation;
8. duplicate/idempotency lookup;
9. client sequence check;
10. current revision check;
11. handler execution against a copy of current state;
12. server generation of next state revision, event sequence, event identity and server time;
13. atomic commit of state + session sequence + event + idempotency record.

Authorization intentionally precedes idempotency lookup so an unauthorized caller cannot probe whether an idempotency key exists.

## Storage boundary

`AuthorityStore` is a protocol. R14.6 ships `InMemoryAuthorityStore` as the deterministic local/core acceptance fixture. It stages all validation and handler work before mutating state, then commits under one re-entrant lock. A handler exception therefore leaves state, event sequence, session sequence and idempotency state unchanged.

The protocol is designed so durable implementations can use the R14.5 PostgreSQL transaction boundary without changing command semantics. R14.6 does not introduce product-specific tables or managed-database provisioning.

## Idempotency and ordering

Each command has both a `command_id` and `idempotency_key`.

- Same key + same command digest returns the original authoritative state/event as `duplicate` and performs no second mutation.
- Same key + different digest is rejected as `idempotency_conflict`.
- Each `(domain_id, session_id)` has an authoritative monotonically increasing command sequence.
- Out-of-order and stale-revision rejects do not consume the expected next session sequence.

## Concurrency

The deterministic store serializes the atomic compare-and-commit boundary. Two clients that concurrently submit commands against the same revision cannot both commit. Exactly one can advance the revision; the other observes the new revision and is rejected as stale.

## Realtime and reconnect

`RealtimeAuthorityBuffer` is a bounded event buffer. It enforces:

- strictly increasing event sequences;
- maximum event count;
- maximum retained bytes;
- explicit acknowledgements;
- resume from an authoritative event cursor;
- `AuthorityResyncRequired` when a reconnect cursor predates retained history;
- `AuthorityBackpressureError` instead of unbounded buffering.

The buffer is a provider-neutral semantic contract; it does not expose raw WebSocket control frames or model-selected protocol operations.

## Server clock / leases

`AuthorityLeaseRegistry` issues leases from a server clock and caps TTL. Clients cannot choose issuance time or expiry. Validation checks the server clock and session binding; expired, revoked or mismatched leases fail closed.

## Evidence and privacy

The acceptance runner records only canonical digests, boolean checks, state/event summaries, standards labels and the exact source SHA. It contains no bearer token, password, DSN, secret or raw network credential.

## Rollback

The deterministic fixture is disposable. A future durable store implementation must use the R14.5 transaction/SafeChange/rollback boundaries; changing the `AuthorityStore` implementation must not change accepted command semantics.
