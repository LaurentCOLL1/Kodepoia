# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 28 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.6 COMPLETE + NORMALIZED. R14.7 COMPLETE at technical/evidence level on immutable source `d04c841fcef9eb9f963085da68e579dbb58186da`; R14.8–R14.17 PLANNED pending final END re-gates, merge and normalization.** R14.7 est partie exactement du `main` normalisé `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`. Le START-sync du plan est `8dc25375e40c045b8831278faa0f55ad74cf6df1`; la continuité est synchronisée dans le même work cycle avant toute implémentation. Frozen scope R14.7 : matchmaking provider-neutral déterministe, lobbies, memberships/roles, tickets/criteria, queueing borné, reservations/expiry, match identity, authoritative presence revisions, short-lived reconnect leases/tokens, cancellation, concurrency/fairness/budget evidence. Manual intervention: NONE.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R12 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest : `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 : **COMPLETE + NORMALIZED**.
- R13 canonical integrated digest : `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`.
- R13 normalized phase main : `b5b75b826bedabf64957494f7e2228ec1c9ff2d3` after implementation/evidence PR #253 and normalization PR #254.
- R14 planning : **ACCEPTED + NORMALIZED**.
- R14.1–R14.6 : **COMPLETE + NORMALIZED**.
- R14.7 : **COMPLETE at technical/evidence level**, immutable source `d04c841fcef9eb9f963085da68e579dbb58186da`; final END re-gates/merge/normalization still required before COMPLETE + NORMALIZED.
- R14.8–R14.17 : **PLANNED**.
- R14.7 manual state : **NONE**.

## Historical continuity preservation

The detailed pre-R14.7 continuity is not lost: the full prior continuity blob is immutable as Git blob `550034dd27208dacec3730a62845fa8a4aa17351`, present on normalized R14.6 `main` `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`. This current file is the forward recovery authority from R14.7 onward. Historical phase details are also preserved in the repository phase plans and acceptance documents. Do not infer stale statuses from the older blob; use the current status below for execution.

## Permanent R-phase execution rule

For every R phase/subdivision:

1. dedicated branch from the immediately preceding **normalized** `main`;
2. mandatory **START-sync before implementation**: phase plan + continuity state all prior normalized subdivisions `COMPLETE`, current subdivision `IN_PROGRESS`, later subdivisions `PLANNED`;
3. implementation + focused/adversarial tests;
4. required exact-head gates on one immutable technical source;
5. truthful manual state; if a conditional/manual gate triggers, stop before the next subdivision and provide bounded user actions/evidence without requesting secrets;
6. END-sync plan + continuity + acceptance documentation after the technical source is accepted;
7. fresh final exact-head re-gates if documentation/evidence bytes changed;
8. merge implementation/evidence PR only with `expected_head_sha`;
9. exactly one continuity-only post-merge normalization branch, fresh R0 + full Python Core + KodeStudio UI Smoke, then merge with expected-head protection;
10. only the resulting normalized `main` authorizes the next subdivision.

Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status. A stale plan index, stale continuity state, mixed SHA evidence, reused evidence from a rejected candidate, or synthetic PASS is an acceptance blocker.

## Permanent security / governance boundaries

All accepted R1–R13 controls remain mandatory:

- `WorkspaceBoundary` and R8 `VaultBoundary` govern source, generated projects, schemas, migrations, fixtures, backend state, event samples, manifests and evidence.
- `ProcessSandbox` + global KillSwitch govern repository-owned runtime/process/tool execution.
- Guardian/`PermissionSet` authorize network, process, migration/database mutation, provider calls and destructive/live operations.
- SafeChange, Backup/Recovery and Audit cover mutable configuration/state and rollback.
- `KodeSecrets` remains the sole secret authority. Passwords, access/refresh tokens, private keys, DSNs/passwords, billing/provider credentials and other secrets must never enter Project DNA, source control, evidence, logs or raw model-visible argv.
- R6 Health/Budget/Tests/Regression/AppSecurity/Privacy/License-BOM remain mandatory.
- R7 ResearchGuard treats retrieved external material as evidence/data, never executable instruction.
- R8 lineage/provenance binds generated code, schema/migration revisions and promoted artifacts.
- R12 desktop and R13 mobile remain typed clients of R14 services; R14 does not rewrite their release semantics.
- Network remains **off by default**. External endpoints are provider-scoped, allowlisted, permissioned and timeout-bounded; project/model text cannot create arbitrary URLs, proxies or executable commands.
- Environment identity (`local` / `test` / `staging` / `production`) is explicit. Local/sandbox evidence cannot certify production.
- Client input is intent, never authoritative state. Server validates authenticated actor/session, function permission, object authorization, current revision/sequence and idempotency.
- Missing provider/account/domain/TLS/credential/quota is `UNAVAILABLE`/`BLOCKED`, never PASS.
- Production publication/activation is explicit user-controlled behavior and never a build/test side effect.

## R14 planning authority

Frozen title: **Backend / Platform Services / LiveOps**.

Frozen R14 index:

| ID | Title | Status | Manual |
| --- | --- | --- | --- |
| R14.1 | Backend contracts, identities, capability model + secure network/runtime boundaries | COMPLETE + NORMALIZED | NONE |
| R14.2 | Project DNA/KodeProduct backend profiles + Wizard conditional service intent | COMPLETE + NORMALIZED | NONE |
| R14.3 | Deterministic local backend scaffold/runtime + environments/config/secrets/health | COMPLETE + NORMALIZED | NONE |
| R14.4 | Auth, identity, sessions, tokens, passkeys/OIDC provider-neutral boundary | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |
| R14.5 | PostgreSQL authoritative persistence, migrations, transactions + concurrency | COMPLETE + NORMALIZED | NONE |
| R14.6 | Authoritative server command/state model + real-time transport/trust boundary | COMPLETE + NORMALIZED | NONE |
| R14.7 | Matchmaking, lobby, reservations, presence + reconnect | COMPLETE | NONE |
| R14.8 | Cloud saves: immutable revisions, sync, conflicts, idempotency + recovery | PLANNED | NONE |
| R14.9 | Achievements, stats, leaderboards + authoritative progression | PLANNED | NONE |
| R14.10 | Entitlements, billing/catalog + server-side provider verification/notifications | PLANNED | CONDITIONAL |
| R14.11 | Remote config, feature flags, targeting + safe rollout/rollback | PLANNED | NONE |
| R14.12 | Content delivery: immutable manifests/bundles, channels, cache + rollback | PLANNED | CONDITIONAL |
| R14.13 | Events/telemetry pipeline: typed envelopes, dedupe, replay, retention + OTel bridge | PLANNED | NONE |
| R14.14 | LiveOps campaigns, seasons, schedules, rotations, activation + rollback | PLANNED | NONE |
| R14.15 | Service operations/resilience: health, limits, retries, backup/restore, DR + load budgets | PLANNED | CONDITIONAL |
| R14.16 | CLI + KodeStudio Backend/LiveOps UX, local stack control + dry-run/provider status | PLANNED | NONE |
| R14.17 | Adversarial integrated backend/platform-services/LiveOps acceptance | PLANNED | CONDITIONAL |

R14 planning itself was accepted on candidate `343b7834d8b5826d5012bf78926102725b66db7f`, merged by PR #255 as `808e5215e45a3a90d3037efb1a3749f01b285b9c`; its single planning normalization `150f7f8a127a068eb79f479d0354d25ee1262c64` passed R0/Python/UI and PR #256 merged as normalized `main` `27af7b80072678f509f7092cf2759683efe1224f`.

## R14.1 closure authority

- Accepted immutable technical source : `84972d283f6f530ae46ebf6c0452188927b178ff`.
- Technical gates : R0 #1752 / `33140670364`, Python Core #1726 / `33140670445`, UI #1693 / `33140670391`, SUCCESS.
- Final END-head : `75e5d68752a56b8a21fa4842e803d86f772f7468`; fresh R0 #1757, Python #1731, UI #1698 SUCCESS.
- PR #257 merged as `6059b6d706d1208fdcad102c9fa217abaf31d099`.
- Continuity-only normalization `5f5624d9ce0a5cca0d112c0cf338f8cf6292eff9` passed R0 #1759, Python #1733, UI #1700; PR #258 merged as normalized `main` `41f0775731c405a6b208baec8910bdb36a78d10e`.
- Status : **COMPLETE + NORMALIZED**, manual NONE.

## R14.2 closure authority

- Accepted immutable technical source : `4e04812380a495dd799e1d7b9e96741d8688de31`.
- Technical gates : R0 #1761 / `33143230642`, Python #1735 / `33143230580`, UI #1702 / `33143230613`, SUCCESS.
- Final END-head `cc034784b6b3350f3e24ece55e5d2304fa60705c`; R0 #1766, Python #1740, UI #1707 SUCCESS.
- PR #259 merged as `ad5de7c1697d061946bf75220420c75b73851531`.
- Normalization `b3587acf2a9c37d2e407a62bc1e805863f553564` passed R0 #1768, Python #1742, UI #1709; PR #260 merged as normalized `main` `bf66970f358df580d5fe15b1ac1f8ed2cb13b09d`.
- Status : **COMPLETE + NORMALIZED**, manual NONE.

## R14.3 closure authority

- Accepted immutable technical source : `4de5036e7a37f949ec64ae68d9ee45e57ac99631`.
- Technical gates : R0 #1770 / `33146235062`, Python #1744 / `33146235104`, UI #1711 / `33146235181`, SUCCESS; full Ubuntu 1477 passed / 13 skipped / 46 warnings and Windows core SUCCESS.
- Final END-head `8411ce92da962a37cb9a5936bdac740d9a132204`; R0 #1775, Python #1749, UI #1716 SUCCESS.
- PR #261 merged as `d288772a90d5877cabe35adb6e71f0ede32f6b8d`.
- Normalization `b8151f3729d2648d5f1e4d6ecd3bc9afb3c3c401`; PR #262 merged as normalized `main` `f28e6762830ec9a2b22ddedc24bdc9a446e5f4b2` after fresh gates.
- Status : **COMPLETE + NORMALIZED**, manual NONE.

## R14.4 closure authority

- Accepted immutable technical source : `3660f351649e85450324df25888d577afb02b19a`.
- Technical gates : R0 #1779 / `33187747722`, Python #1753 / `33187747723`, UI #1720 / `33187747872`, SUCCESS; Ubuntu 1494 passed / 13 skipped / 46 warnings.
- Core uses deterministic local auth/provider fixtures; real IdP/domain/TLS/passkey relying-party is not required.
- Final END-head `05b16a796bb65d513de0b631eca432195ee01461`; R0 #1783, Python #1757, UI #1724 SUCCESS.
- PR #263 merged as `cae2a1ddcaa79390ff923336ee331eba81937e84`.
- Normalization `8601ac19b87635648aef1c5f5c37a6cb899c26be` passed R0 #1785, Python #1759, UI #1726; PR #264 merged as normalized `main` `45dc68f1cd3bf05c62aede1b2519c6c513c67166`.
- Status : **COMPLETE + NORMALIZED**, manual CONDITIONAL / NOT TRIGGERED.

## R14.5 closure authority

- Accepted immutable technical source : `3273ac50b43b64f6f365522f170765f44f45eedf`.
- Technical gates : R0 #1787 / `33190672723`, Python #1761 / `33190672676`, UI #1728 / `33190672761`, PostgreSQL Acceptance #1 / `33190672769`, SUCCESS.
- PostgreSQL focused acceptance : 44 tests passed against PostgreSQL 18.6 (`server_version_num=180006`); fresh apply, rollback/reapply, atomicity, optimistic conflict, row lock, idempotency, bounded retry, backup/restore passed; real `40P01` deadlock detected.
- Migration digest `b96484ae6d56fe54b013b975572310d8daf44cf43116c5c43edc73845856b71b`; restore digest `bcc5ae8b707231568263e0f52c8426dd956a67e4e131bcf97becb4b45ccb9f6e`; `secrets_exposed=false`.
- Final END-head `9606436453c6cc2bed90120bc3f9069311ef65e0`; R0 #1791, Python #1765, UI #1732, PostgreSQL #5 SUCCESS.
- PR #265 merged as `39d8aa12e3d36a618376f7060d1088f9fe61ba32`.
- Normalization `721c9949914a0952b2afe8543dd37da5f8146545` passed R0 #1793, Python #1767, UI #1734; PR #266 merged as normalized `main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`.
- Status : **COMPLETE + NORMALIZED**, manual NONE.

## R14.6 closure authority

- Dedicated branch : `r14/06-authoritative-server-state`, started exactly from normalized R14.5 `main` `1b1f40334b640afb75d8a669ad312dacb96b4e6d`.
- Mandatory START-sync : `5278559563b05d42e132518b3d8581531bd06ac3`.
- Accepted immutable technical source : `a1425b53e1228f9c88ba373cdfabf1459393a7cf`.
- Technical gates : R0 #1795 / `33193110717`, Python #1769 / `33193110651`, UI #1736 / `33193110643`, R14 Authority Acceptance #3 / `33193110695`, all SUCCESS.
- Authority Acceptance passed Ubuntu and Windows with all ten frozen checks true: forgery, stale revision, duplicate, out-of-order, reconnect/resync, bounded backpressure, transaction/event consistency, deterministic multi-client conflict, server-clock lease expiry and recursive reserved-field rejection.
- Cross-platform digests: state `59c1afb567245df4f3521052564d0bdfbaa4a5423eb7db7997c1e20160a988a3`; event `3adad95a513ee4812126d7d9695cc297d2f57287263a5686ee1ee5c08a15e4a1`; trace `839f65c4ffbe019c43f6aad988ee8258945c328f348135ffef9320955102f178`; `secrets_exposed=false`.
- Final END-head `cf5a14295fdc3ff92ca72384b061e3a2c844e725` changed only `R14_PLAN.md`, `R14_6_ACCEPTANCE.md`, and continuity relative to the immutable technical source and passed fresh R0 #1798 / `33195032726`, Python #1772 / `33195032703`, UI #1739 / `33195032677`, Authority #6 / `33195032645`, all SUCCESS.
- PR #267 merged with `expected_head_sha=cf5a14295fdc3ff92ca72384b061e3a2c844e725` as implementation/evidence merge `6033e5610a811a690a2998eb07183f19183fa557`.
- Single continuity-only normalization head `9dafc361e909157dedf5cb89d7a39cdbb6ffff14` changed exactly continuity and passed R0 #1800 / `33195413481`, Python Core #1774 / `33195413472`, UI #1741 / `33195413558`, all SUCCESS.
- Normalization PR #268 merged with `expected_head_sha=9dafc361e909157dedf5cb89d7a39cdbb6ffff14` as normalized `main` `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`.
- Frozen authority model remains provider-neutral: clients submit intent; authenticated actor/session/function/object authorization, revision + sequence validation, digest-bound idempotency, atomic state/event commit, bounded transport/reconnect/backpressure and server-issued lease/clock semantics are authoritative.
- Status : **COMPLETE + NORMALIZED**, manual NONE.

## R14.7 start authority

- Dedicated branch : **`r14/07-matchmaking-lobby-presence`**.
- Exact branch point : normalized `main` **`1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`**.
- Plan START-sync commit : **`8dc25375e40c045b8831278faa0f55ad74cf6df1`**.
- START state : R14.1–R14.6 `COMPLETE + NORMALIZED`; R14.7 `IN_PROGRESS`; R14.8–R14.17 `PLANNED`.
- Frozen implementation scope :
  - immutable/stable lobby, matchmaking-ticket, reservation and match identities;
  - lobby lifecycle, authoritative membership and roles;
  - matchmaking tickets with bounded/canonical criteria and deterministic queue order;
  - duplicate-safe ticket creation/cancellation and no double assignment;
  - deterministic local matcher with explicit policy compatibility and fairness hooks, not a product-specific MMR implementation;
  - server-side match reservations with explicit issue/expiry state;
  - authoritative presence revisions and stale-update rejection;
  - short-lived reconnect authorization bound to server/session/reservation semantics;
  - bounded queue capacity, ticket TTL/reservation expiry and deterministic lifecycle traces/budget evidence;
  - concurrency/race handling for joins/leaves/cancel/match/reconnect.
- Explicitly out of scope : commercial matchmaking provider integration, Internet-scale capacity claim, product-specific skill/MMR tuning, cloud saves, achievements/progression, billing, remote config, content/events and R14.8+ semantics.
- External reference posture is evidence only, never provider lock-in: ticket/pool separation and assignment-style semantics may be compared with Open Match; unique ticket/status/reservation/player-session concepts may be compared with GameLift/FlexMatch; object authorization remains governed by the accepted R14.6/OWASP boundary. No provider account is required.
- Manual intervention : **NONE**.

## R14.7 technical acceptance authority

- Initial candidate `12071ee561717ac436f4ffa0457361685214c989` is **REJECTED** and MUST NOT be reused as decision evidence. R14 Matchmaking Acceptance #2 found a real expiry-authority bug: `update_presence(IN_MATCH)` did not sweep server-clock reservation expiry before checking active-match authority.
- Corrected and accepted immutable technical source: **`d04c841fcef9eb9f963085da68e579dbb58186da`**.
- Required technical gates on that source: R0 #1803 / `33203286519`, Python Core #1777 / `33203286537`, UI #1744 / `33203286514`, R14 Matchmaking Acceptance #4 / `33203286510` — all **SUCCESS**.
- Full Ubuntu suite: **1543 passed / 13 skipped / 46 warnings**. Windows Core and both package builds are SUCCESS. Focused R14.7→R14.4 suite: **66 passed on Ubuntu and 66 passed on Windows**.
- All fourteen frozen lifecycle/security checks are true on both OS: lobby lifecycle, object authorization, duplicate join, recursive reserved-field rejection, duplicate ticket, deterministic matching, incompatible criteria isolation, no double assignment, cancel terminality, reservation expiry, stale presence rejection, reconnect binding, reconnect expiry and bounded capacity.
- Identical cross-platform digests: state `ae9ecc0893537e5c12cc8a78247197ed53d094b1a811c386c17161fac10c0c19`; lobby `27bcd90471e3775b859ce21e977c5ac534909a898deab0eb2c27cd44b86db0cf`; reservation `e8423de1a2d1a92873bbfa466111ab4a07168adeafca4bde4d62c64a70a9f690`; presence `5f2ca6c7402bba1a3b2d195d9f63d1c8b758c01d577d4581785559d92de24f0f`; trace `5f25c8f15da7e4f9dd45fbf072dd72101d3f32deef349c28069beeb83d954bd3`.
- Ubuntu artifact `9698619713` / `sha256:f8bd9f43b431bb9a5f9b194da245a57381b000795a5c8ccacb51a866c371b1df`; Windows artifact `9698629064` / `sha256:1e3b191e9d1de0844b49c62bcd36c79798a23315e93edf20393b862d1fb44c1c`.
- Evidence is provider-neutral and explicitly states `provider_live_claim=false` and `secrets_exposed=false`.
- Manual intervention: **NONE**.
- R14.7 is now COMPLETE only at technical/evidence level. R14.8 remains locked until END-sync docs are freshly re-gated, PR #269 merges with expected-head protection, and exactly one continuity-only normalization passes fresh R0/Python/UI and merges.

## R14.7 acceptance target

Before R14.7 can become COMPLETE at technical/evidence level, the immutable candidate must prove at minimum:

1. lobby owner/member lifecycle and role authorization;
2. unauthorized/cross-lobby membership mutation rejection;
3. duplicate lobby join is mutation-free/idempotent;
4. duplicate ticket identity cannot create multiple active queue entries;
5. deterministic queue/match selection from the same inputs;
6. incompatible criteria do not match;
7. matched tickets cannot be double-assigned;
8. cancel-vs-match race has one authoritative terminal outcome;
9. reservation expiry is server-clock based and releases/invalidates connection authority;
10. presence increments authoritative revisions and stale presence writes fail closed;
11. reconnect authorization is short-lived, actor/session/match bound and cannot escalate lobby/match membership;
12. queue/reservation capacity/backpressure is bounded;
13. lifecycle traces/digests are deterministic on Ubuntu and Windows where applicable;
14. no secret/provider credential is exposed and no provider-live claim is synthesized.

Required standard gates remain R0 Repository Guard + full Python Core + KodeStudio UI Smoke on the exact technical head. A dedicated R14.7 focused workflow/acceptance may be introduced if needed to obtain independent cross-platform lifecycle evidence; any such workflow is repository-owned and exact-head bound.

## R14.7 rollback/recovery target

R14.7 owns no live external player pool. Rollback is cancellation/expiry of owned tickets/reservations, deterministic fixture/store reset and restoration to normalized R14.6 `main` `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`. Failed/rejected candidates do not authorize reuse of decision evidence.

## External research baseline for R14.7 — retrieved 2026-08-28

These are versioned evidence/context, not frozen architecture constants:

- Open Match models a ticket created after the game frontend validates the player; tickets enter pools and are later proposed/assigned by matchmaking/director components. Kodepoia adopts only the provider-neutral separation of validated ticket intent from allocation authority.
- Amazon GameLift FlexMatch uses unique ticket IDs, explicit ticket lifecycle states and optional acceptance timeouts. Kodepoia may model similarly explicit bounded lifecycles but does not copy provider-specific state/API contracts as architecture.
- GameLift player-session APIs illustrate that an allocated player slot uses a server-issued session identity presented on connection and validated server-side. Kodepoia reconnect/reservation authority follows the same security principle using its own provider-neutral contracts.
- OWASP API1:2023 requires object-level authorization checks for every endpoint/action that accepts an object identifier; simply trusting IDs sent by a client is unsafe. R14.7 therefore validates lobby/ticket/reservation/match ownership/membership server-side before mutation.

## Next authorized action

Treat `d04c841fcef9eb9f963085da68e579dbb58186da` as immutable technical authority. Complete this END synchronization with exactly `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_7_ACCEPTANCE.md`, and `docs/continuity/KODEPOIA_CONTINUITY.md` changed relative to that source. Run fresh exact-head R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Matchmaking Acceptance. If all are SUCCESS, merge PR #269 only with `expected_head_sha=<final END-head>`. Then create exactly one `r14/07-continuity-normalization` branch from that merge, change continuity only, require fresh R0/Python/UI, merge with expected-head protection, and only then authorize R14.8. Manual intervention remains **NONE**.
