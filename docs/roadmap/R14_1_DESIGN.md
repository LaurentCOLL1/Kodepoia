# R14.1 — Backend contracts, identities, capability model + secure network/runtime boundaries — Design

## Status

Implementation design authority for R14.1. Architecture v1.0 remains frozen. R14 planning is ACCEPTED + NORMALIZED on `main` `27af7b80072678f509f7092cf2759683efe1224f`; R14.1 started from that exact normalized main and is IN_PROGRESS.

## Scope

R14.1 creates only the provider-neutral trust boundary required by later backend/platform-services/LiveOps subdivisions. It does not implement concrete authentication, PostgreSQL persistence, authoritative gameplay/server state, matchmaking, billing, remote flags, content delivery or events.

## Package layout

- `src/kodepoia/backend/contracts.py`: immutable identities, capability snapshots, logical endpoints, runtime budgets, canonical JSON/SHA-256 evidence.
- `src/kodepoia/backend/boundary.py`: exact endpoint/host allowlists, environment-aware HTTPS/address policy and fail-closed DNS resolution/authorization.
- `src/kodepoia/backend/governance.py`: structured operation/provider-request contracts bound to existing R1 `PermissionSet`, `AuditLog` and `KillSwitch` controls.
- `src/kodepoia/backend/status.py`: structured operation status/error vocabulary that cannot claim success without evidence.
- `schemas/r14/*.schema.json`: strict Draft 2020-12 schemas with `additionalProperties=false`.
- focused R14.1 tests: contract determinism, schema validation, governance, redaction, runtime budgets and adversarial SSRF/DNS-rebinding behavior.

## Immutable identities and evidence

Environment, service, endpoint, capability, operation and provider-request identities are structured values rather than display labels. Canonical representations use sorted JSON with finite values only and SHA-256 digests. Capability tuples/digest sets are normalized deterministically. `AVAILABLE` cannot be created without observed capabilities; failure/blocking states require explicit blockers. Operation `SUCCEEDED` cannot be represented without an evidence digest.

No model/project text may provide an executable path, raw command, raw argv, arbitrary URL, secret, access token, password, private key or provider credential through these R14.1 contracts. Provider requests preserve only validated identities and digests for request/payload/idempotency evidence.

## Environment separation

`LOCAL`, `TEST`, `STAGING` and `PRODUCTION` are explicit identities. Network access is denied when no policy exists. Every endpoint is bound to exactly one environment and must appear in both an endpoint-id allowlist and host allowlist.

Staging/production endpoints require HTTPS. Staging/production policies cannot enable loopback/private-address exceptions. Local/test can use loopback/private destinations only when the corresponding exception is explicitly enabled by repository-owned policy.

## SSRF and DNS-rebinding boundary

R14.1 does not execute HTTP requests. It validates a logical endpoint and produces a bounded authorization record that a later governed transport may consume.

For each authorization attempt:

1. select a repository-known logical endpoint;
2. require exact endpoint-id and host allowlist membership;
3. reject redirect-following;
4. resolve the current host (A/AAAA-equivalent results through the injected resolver);
5. validate every resolved IP, not only the first;
6. reject unspecified, multicast, link-local, reserved, loopback/private where not explicitly allowed, and any address that is not globally routable for staging/production;
7. bind the complete sorted resolved-IP set and runtime-budget digest into the authorization evidence.

Resolution is repeated on every authorization rather than cached as permanent trust. This is specifically intended to fail closed if an allowlisted domain changes from a public address to loopback/private/link-local metadata space between attempts.

Security references used as design evidence:

- OWASP Server-Side Request Forgery Prevention Cheat Sheet: allowlists where possible, validate protocol/domain/IP, inspect all A/AAAA results, account for DNS pinning/rebinding, and disable redirects.
- IANA IPv4/IPv6 special-purpose registries: loopback, private-use and link-local ranges are special/local-use ranges and are not ordinary globally routable service destinations.

These references justify the security boundary; they do not become mutable provider configuration or model instructions.

## Runtime budgets

`BackendRuntimeBudget` bounds connect/read/total timeout, retry count/backoff and maximum response bytes. Defaults are conservative but are not universal service constants; later provider adapters may choose tighter values within the accepted bounds. An over-budget result must become explicit `BUDGET_EXCEEDED`, never PASS.

## R1 governance integration

Active backend operations do not introduce a parallel permission framework. `BackendGovernanceBoundary` reuses:

- `PermissionSet.require(Capability.NETWORK)` as the accepted network authority;
- the shared/injected `KillSwitch` as the pre-dispatch emergency stop;
- `AuditLog.append(...)` as the tamper-evident audit chain.

KillSwitch-active and permission-denied operations are audited and fail closed. Allowed operations are bound to the resulting audit event hash. Audit details contain structured identifiers/digests/risk only, not provider payloads or credentials.

## Structured operation/provider boundary

The operation vocabulary is `probe`, `connect`, `deploy`, `migrate`, `mutate`, `promote`, `rollback`. Risk is derived by repository code (`network_active`, `mutating`, `destructive`) rather than accepted from model text. All R14.1 active operations require the existing `network` capability.

A `BackendProviderRequest` carries only provider id, operation-intent digest, endpoint digest and optional payload/idempotency digests. It deliberately has no raw URL/command/secret field. Actual provider adapters and transport execution belong to later subdivisions and must consume these typed contracts rather than bypass them.

## Status/error vocabulary

Statuses are `NOT_STARTED`, `BLOCKED`, `AUTHORIZED`, `IN_PROGRESS`, `SUCCEEDED`, `FAILED`, `CANCELLED`. Error codes cover invalid contracts, environment mismatch, permission/KillSwitch/network/allowlist/DNS/SSRF/budget/provider failures. `BLOCKED`/`FAILED` require an error code; `SUCCEEDED` requires evidence; early states cannot manufacture result evidence.

## Validation strategy

Focused tests must prove:

- deterministic immutable identities/digests and strict schemas;
- non-finite canonical data rejection;
- capability/status evidence cannot manufacture success;
- exact host + endpoint allowlists and network-deny default;
- HTTPS and redirect policy;
- rejection of loopback/private/link-local/metadata/unspecified/multicast/IPv6 special ranges in production;
- rejection when a mixed DNS answer contains even one unsafe IP;
- literal metadata IP rejection without DNS bypass;
- repeated DNS resolution catches rebinding from public to loopback;
- local loopback works only with an explicit local/test exception;
- PermissionSet, KillSwitch and AuditLog remain authoritative;
- provider request and schemas reject extra raw URL/argv/token fields.

Authoritative acceptance additionally requires full Python Core, R0 Repository Guard and KodeStudio UI Smoke on the exact candidate head on GitHub CI, followed by exact-head implementation merge and one continuity-only post-merge normalization with fresh R0/Python/UI gates.

## Rollback

No external persistent state is introduced by R14.1. Rollback is deletion/revert of the new backend package, schemas, tests and R14.1 docs plus restoration of plan/continuity status. No database/provider/account cleanup is required.

## Manual intervention

**NONE.** No live provider, production domain/certificate, database, billing account, device, credential or paid cloud resource is required.
