# R14.9 — Authoritative progression acceptance

**Subdivision:** R14.9 — Achievements, stats, leaderboards + authoritative progression  
**Technical status:** ACCEPTED — END synchronization pending  
**Immutable technical source:** `155119282af7f4bf71840fc45c2d3de8891f73cd`  
**Exact branch:** `r14/09-progression-leaderboards`  
**Exact normalized base:** `433c86cc5d43bfea41adb529451367e10c75a30b`  
**Manual intervention:** NONE

## Accepted scope

R14.9 implements a provider-neutral authoritative progression service in which clients cannot directly write trusted leaderboard scores. Stat, achievement and leaderboard definitions are immutable/versioned; progression enters through authorized server-side stat events; event identity and idempotency are separately bound; achievement unlocks are terminal/idempotent; leaderboard order, update, tie and period policies are explicit; recurring periods derive period-local state from the server clock; ranking snapshots are deterministic; privacy filtering is applied before ranks are exposed; and capacities are bounded.

Provider publication/configuration is not part of core acceptance. Steamworks, Apple Game Center and Google Play Games documentation are compatibility/comparison evidence only. `provider_live_claim=false`.

## Rejected candidate

`dc3ea916dd5bfbcc5751a7fbe0128532f3a1298f` is **REJECTED** and none of its evidence is reusable. Its first dedicated acceptance run failed because the new test fixture attempted to construct `AuthorityActorContext` with wildcard `authorized_object_ids=("*",)`, while the pre-existing R14.6 authority constructor requires stable explicit object identifiers. The production authority boundary was deliberately **not weakened**. The fixture and deterministic acceptance actor were corrected to enumerate authorized definition/object IDs explicitly.

## Semantic defect detected and corrected before acceptance

The initial implementation could derive the first score of a recurring leaderboard period from a lifetime `SUM` stat. That would visually switch periods while leaking previous-period progress into the new period. The accepted implementation derives recurring leaderboard candidates from period-local state: the first event in a period establishes the period baseline, subsequent events aggregate within that period according to `SUM`, `MAX` or `MIN`, while classic leaderboards can continue to reflect lifetime stat state. Server-clock period boundaries are validated and future occurrences cannot be queried as current authority.

## Technical gates on immutable source

All decision gates below are attached to immutable technical source `155119282af7f4bf71840fc45c2d3de8891f73cd` / PR #273 and completed successfully:

- R0 Repository Guard **#1836** — run `33210136515` — Ubuntu SUCCESS, Windows SUCCESS.
- Python Core **#1810** — run `33210136766` — Ubuntu Core SUCCESS, Windows Core SUCCESS, Ubuntu package build SUCCESS, Windows package build SUCCESS, internal KodeStudio smoke SUCCESS.
- KodeStudio UI Smoke **#1777** — run `33210136531` — SUCCESS.
- R14 Progression Acceptance **#3** — run `33210136498` — Ubuntu SUCCESS, Windows SUCCESS.

The full Ubuntu Python suite is **1590 passed / 13 skipped / 46 warnings**. Windows Core also completed successfully.

## Focused/adversarial regression

The dedicated progression gate ran **96 tests on Ubuntu and 96 tests on Windows**, combining R14.9 with R14.8 cloud saves, R14.7 matchmaking/lobby/presence, R14.6 authoritative server and R14.5 PostgreSQL persistence regression coverage.

The fifteen frozen semantic/adversarial checks are `true` on both operating systems:

1. authoritative event application;
2. bounded capacity;
3. direct client score rejection;
4. event-ID rebind rejection;
5. function authorization;
6. deterministic higher-is-better ordering;
7. idempotency-key rebind rejection;
8. mutation-free idempotent replay;
9. immutable definition version;
10. deterministic lower-is-better ordering;
11. object authorization;
12. server-clock period boundary;
13. privacy filtering;
14. recurring rollover without lifetime-state bleed;
15. terminal/idempotent achievement unlock.

Additional focused tests cover activation rollback between definition versions, missing-definition rejection, fail-closed enum contracts, invalid server clock, recursive reserved metadata rejection, stat bounds before commit, `AT_MOST` achievement semantics, `KEEP_BEST` and `FORCE_UPDATE`, shared and ordinal ties, recurring `SUM`/`MAX`, future-period rejection, owner/private-read visibility, event/account/definition/leaderboard capacities, concurrent duplicate events, and cross-run digest determinism.

## Cross-platform semantic evidence

Ubuntu and Windows produced the same semantic values:

- definition digest: `0ff0b8c2215dabf637f852f3d049959a02dbd7cb3e8e26c5cf2fa680682cb686`
- state digest: `a8d7bed52649c7f6cea1d2f07793a011058afbdd2973e568ade69f7b3811d49d`
- trace digest: `c1180c3bc5326a6fd268dc6bd54f9bd13c99bba837a7bc931d1b55c206d9bec3`
- classic snapshot digest: `49a5655892db2649f2f9a926aff2e2cda14f8b51ef3f9901acc4c227c96e306c`
- lower-is-better snapshot digest: `2869ce012f10c143be8128f356288c21bc028793d18fae5ea2cb79b6f2b18859`
- recurring period 0 snapshot digest: `a3fd0f5b9a06a093b0961626950ef0ddf9c3acb0ebd9f69e67bf4bb0dd6b9380`
- recurring period 1 snapshot digest: `4d22f10134f62e6449fce47bee6e13ef4ed9556d7922889c0749dc3000ffd2fd`
- event count: `6`
- unlock count: `2`

Acceptance budgets are `max_events=128`, `max_accounts=32`, `max_definition_versions=32`, `max_entries_per_leaderboard_period=32`, `max_metadata_bytes=1024`.

## Evidence artifacts

Canonical PR #273 / R14 Progression Acceptance #3 artifacts:

- Ubuntu artifact `9701251718`, ZIP digest `sha256:fb8be016598d8bf1450047102b2c44e26aa975bf78c78f62e1e7043f4f64e69a`, final size 1139 bytes.
- Windows artifact `9701266161`, ZIP digest `sha256:065fac3a244258b4047f51b229b66b1adfe3ec0714d556b7ba6e42220568b02e`, final size 1145 bytes.

Evidence schema: `schemas/r14/backend-progression-evidence.schema.json`, JSON Schema Draft 2020-12. The schema requires all fifteen acceptance checks to be true, exact 40-character source SHA provenance, SHA-256-shaped semantic digests, positive governed budgets, `provider_live_claim=false`, and `secrets_exposed=false`.

## External compatibility evidence

- Steamworks `ISteamLeaderboards` documents trusted leaderboard writes in which client score setting can be disabled and publisher-server Web API writes are required. This informs the R14.9 trust boundary but is not a dependency.
- Apple Game Center documents classic leaderboards whose scores do not reset and recurring leaderboards whose scores reset according to configured recurrence, with explicit score sort order. This informs period/order semantics but is not a dependency.
- Provider-specific account setup, publication and credentials remain outside provider-neutral core acceptance.

## Rollback / recovery

Definitions are immutable and active versions can be rolled back by activation rather than mutation. Progression state has canonical deterministic snapshots/digests and is designed to be recomputable from authoritative events where a durable event source is available in later integrated persistence. No provider-side state is created by this acceptance.

## END synchronization rule

No technical implementation byte may change after the immutable source above. The R14.9 END-head may differ from `155119282af7f4bf71840fc45c2d3de8891f73cd` only by:

- `docs/roadmap/R14_PLAN.md`
- `docs/roadmap/R14_9_ACCEPTANCE.md`
- `docs/continuity/KODEPOIA_CONTINUITY.md`

That exact END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Progression Acceptance before PR #273 may merge with `expected_head_sha`. After merge, exactly one continuity-only normalization with fresh R0/Python/UI is required before R14.10 is authorized.

The assertion-guarded anchored END synchronization completed without any implementation-byte change. This user-authored documentation revision is the sole R14.9 END candidate for the fresh exact-head re-gates.