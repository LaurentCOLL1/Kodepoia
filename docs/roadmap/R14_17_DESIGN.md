# R14.17 — Adversarial integrated backend/platform-services/LiveOps acceptance design

Status at technical implementation: `IN_PROGRESS`.

## Purpose

R14.17 is the anti-circular phase gate for the whole R14 backend/platform-services/LiveOps surface. It proves that the already normalized R14.1–R14.16 capabilities still execute together on one immutable source SHA and that the resulting evidence cannot silently promote local/test/sandbox behavior into a provider-live, Internet-scale, multi-region or production-publication claim.

The integrated report is deliberately not allowed to certify itself. Fresh workflow evidence is created first. The checked-in CI authority binds those independent workflow/run/artifact identities. The canonical `R14_INTEGRATED_ACCEPTANCE.json` is then built offline from repository files whose bytes are independently hash-bound; its own output path is excluded from its input set.

## Frozen authority and source discipline

- Exact R14.17 base: normalized R14.16 `main` `f6960db290a570e3a0c3c4ff97600014978d45df`.
- R14.1–R14.16 acceptance documents remain immutable inputs.
- R13 integrated semantic digest remains `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`.
- Every fresh R14.17 technical, CI-authority and final report object carries the exact immutable R14.17 technical source SHA.
- Evidence from a rejected/superseded SHA must never be rebound to a later SHA.

## Integrated scenario

The dedicated runner executes these existing deterministic acceptance surfaces in one bounded process tree on the exact source SHA:

1. local/test identity and session creation through `LocalAuthProvider`;
2. PostgreSQL 18 authoritative persistence, migrations, transactions, deadlock/retry and restore;
3. authoritative command/state/revision/event boundary;
4. lobby, reservation, presence and reconnect;
5. cloud-save immutable revisions, explicit conflict handling and rollback;
6. authoritative progression and leaderboard semantics;
7. sandbox entitlement ingestion/reconciliation with duplicate and out-of-order protection;
8. stable remote-config/feature-flag evaluation and rollback;
9. immutable content manifest/cache/download and rollback;
10. event ingestion, duplicate-safe consumption, checkpoint/replay and redaction;
11. LiveOps preview, activation, pause/expiry/rollback/kill scheduling;
12. service health, retry/circuit/rate-limit, backup/restore and bounded load evidence;
13. governed CLI/KodeStudio LiveOps inspection/preview/mutation UX.

The integrated runner requires every underlying acceptance report to say `status=pass`, to carry the exact source SHA, to contain a non-empty all-true check map and to avoid true values for provider-live/sensitive/high-scale claims. R14.5–R14.10 critical semantic digests are re-pinned directly against the previously normalized authorities; the complete frozen digest ledger for R14.5–R14.16 is included in the scenario evidence so drift is reviewable.

## Trust boundaries

- Client/UI/CLI input is intent, never authoritative state.
- R14.4 identity/session state remains local/test for core acceptance.
- PostgreSQL CI credentials are disposable workflow fixture credentials and are never copied into evidence.
- Billing is sandbox/fixture provider state only; no production store query or credential is used.
- Content uses governed local/loopback capability unless a later explicit provider-live gate exists.
- LiveOps cannot auto-publish to production; confirmation is not authorization.
- Event/telemetry exports stay redacted before observability exposure.
- Resilience acceptance is bounded CI evidence only, not Internet-scale, multi-region or production PITR proof.

## Anti-circular evidence model

`src/kodepoia/backend/integrated_acceptance.py` defines strict typed bindings for:

- the accepted R13 integrated report;
- R14.1–R14.16 acceptance document bytes;
- R14.17 design bytes;
- the exact-head integrated scenario evidence;
- independent CI run identities and the integrated scenario artifact;
- the canonical R14 integrated report.

`R14_INTEGRATED_ACCEPTANCE.json` never appears in its own bound input set. The offline verifier re-reads every bound file and compares exact byte length + SHA-256 before accepting the report. Source-SHA mixing, semantic-digest drift, provider-live fabrication, sensitive-data exposure, production-publish claims and non-empty blockers fail closed.

## Fresh workflow authority

The technical source and every later byte-changing END candidate require fresh exact-head:

- `R0 Repository Guard`;
- `Python Core`;
- `KodeStudio UI Smoke`;
- `R14 Integrated Acceptance`.

The integrated workflow runs the complete service scenario on Ubuntu 24.04 with PostgreSQL 18 and also runs the portable anti-circular verifier/tests on Windows 2025. Its scenario artifact is an independent CI object; the checked-in CI-authority file is generated only after run IDs, run numbers, conclusion and artifact SHA-256 are observed.

## Current external compatibility baseline

The R14.17 design keeps the already frozen provider-neutral architecture. Current external references are compatibility evidence only:

- PostgreSQL 18.6 is the current stable PostgreSQL 18 update released 2026-08-13; pre-release PostgreSQL 19 builds are not accepted as production authority.
- OpenTelemetry Specification 1.60.0 remains the provider-neutral observability reference used by the R14 telemetry/operations boundaries.
- Existing RFC/OIDC/WebAuthn/OWASP/CloudEvents/OpenFeature/store documentation cited by R14.4–R14.16 remains informative rather than architecture authority.

## Manual/provider posture

Core R14.17 manual state is `CONDITIONAL / NOT TRIGGERED`.

No real external IdP, public TLS/domain, production App Store/Google Play account, external CDN, managed broker, OTel SaaS account, production database, provider quota/cost proof or destructive/high-cost production load is needed for core closure. If a later claim explicitly requires any such proof, that claim must remain `UNAVAILABLE`/`BLOCKED` until a separately authorized manual/provider gate is completed.

## Finalization sequence

1. Freeze the technical source containing the integrated model, runner, schema, tests, builders, workflow and this design.
2. Run fresh exact-source R0/Python/UI/R14-integrated gates.
3. Bind the successful independent run identities and integrated artifact in `R14_17_CI_ACCEPTANCE.json`.
4. Check in the deterministic exact-source scenario evidence.
5. Build and validate canonical `R14_INTEGRATED_ACCEPTANCE.json` from the immutable source inputs.
6. END-sync `R14_PLAN.md`, `R14_17_ACCEPTANCE.md` and continuity without changing technical implementation.
7. Re-run fresh exact-END R0/Python/UI/R14-integrated gates because evidence/document bytes changed.
8. Merge the implementation/evidence PR only with exact `expected_head_sha` protection.
9. Create exactly one post-merge continuity-only normalization, run fresh R0/Python/UI on that exact head, and merge only with exact expected-head protection.
10. Only the resulting normalized `main` may mark R14 `COMPLETE + NORMALIZED` and authorize R15 planning.
