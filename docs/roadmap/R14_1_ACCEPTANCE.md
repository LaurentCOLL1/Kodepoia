# R14.1 — Acceptance evidence ledger

## Current state

**Status: TECHNICAL_CANDIDATE_PENDING**

R14.1 started from normalized R14 planning `main` `27af7b80072678f509f7092cf2759683efe1224f` on dedicated branch `r14/01-backend-contracts-boundaries`. Mandatory START-sync completed before implementation; its final head was `a5e64a5db3d768ae1ff504cf7ebef6ce70a263a9`, with cumulative changes from normalized main limited to `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`.

No R14.1 technical candidate is accepted until all required exact-head gates below are COMPLETED / SUCCESS on the same immutable implementation head.

## Frozen acceptance claims

R14.1 may claim only:

- provider-neutral backend environment/service/endpoint/capability contracts;
- deterministic canonical/redacted identities and evidence digests;
- bounded runtime timeout/retry/response budgets;
- deny-by-default exact endpoint/host network policies;
- production/staging HTTPS and special-address rejection;
- adversarial SSRF/DNS-rebinding address validation prior to any later transport;
- typed digest-only operation/provider-request contracts;
- direct reuse of R1 PermissionSet / AuditLog / KillSwitch authority;
- structured backend status/error vocabulary;
- strict JSON schemas and focused tests.

R14.1 does not claim concrete auth, database persistence, provider deployment, billing, matchmaking, cloud saves, flags, content delivery, events, LiveOps, production cloud access or any successful external network transaction.

## Required technical-candidate gates

All must bind the exact same head SHA:

1. R0 Repository Guard — PENDING.
2. Full Python Core — PENDING, including Ubuntu/Windows core tests, package builds and internal KodeStudio smoke.
3. KodeStudio UI Smoke — PENDING.

Focused R14.1 tests execute as part of Python Core. A partial matrix, stale head, manually inferred result or successful unrelated workflow is not acceptance evidence.

## Required focused assertions

- deterministic identity/canonical digest behavior;
- strict Draft 2020-12 schema validation and rejection of extra raw URL/argv/token fields;
- `AVAILABLE`/`SUCCEEDED` cannot be manufactured without observed/result evidence;
- runtime budgets are bounded;
- no network policy means deny;
- endpoint and host allowlists are both required;
- redirects disabled and staging/production HTTPS required;
- loopback/private/link-local/metadata/unspecified/multicast/special IPv4+IPv6 addresses fail closed in production;
- mixed public + unsafe DNS answer fails closed;
- repeated authorization resolves again and catches DNS rebinding;
- local/test loopback/private exceptions require explicit policy;
- denied permission and active KillSwitch fail closed and produce valid chained AuditLog evidence;
- allowed operation binds its governance authorization to an AuditLog event hash;
- provider requests contain digests/identities only.

## Exact-head evidence to record after candidate validation

When the first fully accepted technical candidate exists, append without rewriting history:

- accepted immutable technical head SHA;
- focused test counts/results from Python Core;
- R0 run number/id/conclusion;
- Python Core run number/id/conclusion;
- KodeStudio UI Smoke run number/id/conclusion;
- any rejected predecessor head and exact reason it is non-authoritative;
- cumulative implementation diff summary.

## End synchronization and final gates

After a technical candidate is accepted, update `R14_PLAN.md`, this ledger and continuity so R14.1 becomes `COMPLETE` while R14.2 remains `PLANNED`. That documentation-only/end-sync head must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke before the implementation PR is merged with expected-head protection.

After implementation merge, create exactly one continuity-only normalization branch from the merge. It may change only `docs/continuity/KODEPOIA_CONTINUITY.md`, must pass another fresh exact-head R0 + Python Core + UI Smoke family, and must merge with expected-head protection. Only then is R14.1 `COMPLETE + NORMALIZED` and R14.2 authorized.

## Manual intervention

**NONE.** No user-side execution, live provider/account, production endpoint, credential, paid quota or external deployment is required for R14.1 acceptance.
