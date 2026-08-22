# Kodepoia — R7.4 design

**Subdivision:** R7.4 — GitHub research adapter  
**Architecture:** v1.0 frozen  
**Manual gate:** CONDITIONAL  
**Foundation change:** NONE

## Objective

Add read-only GitHub research over structured repository entities while preserving the R7.1 trust boundary and the R7.3 governed-network model. GitHub is a provider adapter, not a general remote-control surface.

## Accepted design boundaries

- typed owner/repository/resource selectors only;
- read-only REST requests only;
- no model-supplied HTTP method, request body, arbitrary headers, GraphQL document, host, proxy or cookie jar;
- production traffic fixed to `https://api.github.com:443` and still subject to R7.3 public-target/DNS validation;
- existing `KodeGuardian` + `Capability.NETWORK` authorizes socket activity;
- optional credentials are referenced by `(namespace, key)` and resolved through `KodeSecrets` only inside the transport;
- secret values are never included in research requests, artifacts, metadata, logs or acceptance evidence;
- issue, PR, comment, README/file and other provider text always enters `ResearchArtifact.from_content()` and therefore passes through the existing `ResearchGuard`;
- no GitHub write endpoint, Actions administration or branch/PR mutation surface is introduced.

## Resource contract

`GitHubResearchRequest` supports:

- repository metadata;
- exact or resolved commits;
- repository files;
- exact blobs;
- releases and tags;
- issue and issue comments;
- pull request and review comments.

Owner/repository names are validated. File paths are repository-relative and reject parent traversal. Blob requests require an exact object SHA. Issue/PR selectors require a positive numeric identifier. Pagination is bounded to 1–10 pages.

## Immutable provenance

Mutable refs are never cited as immutable file evidence. For `FILE` research the adapter first resolves the requested ref (or HEAD) through the commits endpoint, validates the returned object SHA, then requests file content using that exact SHA. The final human-facing locator is `https://github.com/<owner>/<repo>/blob/<exact-sha>/<path>`.

Commit research validates and exposes the exact returned SHA. Exact blob research accepts only a validated object SHA.

## Pagination and rate limits

GitHub documents REST pagination with response `Link` headers. Kodepoia treats `rel=next` only as evidence that another page exists; it does not follow the header URL directly. The next request is reconstructed from the already validated owner/repository/resource selector on the fixed `api.github.com` origin with bounded `per_page` and `page` parameters. This prevents a hostile or malformed Link value from becoming an SSRF redirect surface.

For every observed response, the adapter records available `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Used`, `X-RateLimit-Reset`, `X-RateLimit-Resource` and `Retry-After` values. A primary-limit exhaustion or 429 becomes explicit `UNAVAILABLE/rate_limited`; the adapter does not hide retries or sleeps. R7.3 host pacing remains a top-level provider-operation guard; provider rate-limit headers are the authoritative remote evidence.

Reference context used during implementation:

- GitHub REST pagination: https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
- GitHub REST rate limits: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
- GitHub REST best practices: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api

These references are context, not compliance claims.

## Content and cache behavior

JSON metadata is serialized deterministically. File/blob text must be base64 provider content, bounded after decode and valid UTF-8; binary/oversized provider content returns explicit `UNAVAILABLE` rather than guessed text. Persistent cache reuse uses the existing content-addressed `ResearchStore`; cached content remains guarded evidence and does not manufacture fresh retrieval timestamps.

## Optional authentication

`GitHubCredentialRef` carries only a secret reference. `GitHubApiTransport` retrieves the credential through `KodeSecrets.delegated_get()` immediately before the fixed GET request and injects `Authorization: Bearer ...` internally. The token is not returned by the transport or persisted in metadata.

R7.4 manual gate is **CONDITIONAL**. It is NOT TRIGGERED for public unauthenticated acceptance. It is triggered only if authoritative acceptance later requires private/authenticated capability that hosted CI cannot exercise; any such token must be least-privilege read-only and OS-backed through KodeSecrets.

## Deterministic test model

CI uses `FixtureWebTransport` plus a deterministic public-IP resolver. No public Internet availability is required. Tests cover:

- typed request surface and invalid selector rejection;
- prompt injection in GitHub metadata/issues;
- mutable ref -> exact SHA -> exact-SHA file citation;
- exact blob handling;
- bounded pagination and explicit truncation;
- hostile Link target not followed;
- rate-limit exhaustion;
- fixed API origin and network permission;
- optional secret injection confined to transport;
- content-addressed cache behavior;
- schema validation and tamper-sensitive evidence shape.

## Deliverables

- `src/kodepoia/intelligence/research/github.py`;
- public exports in `src/kodepoia/intelligence/research/__init__.py`;
- `schemas/github-research-evidence-v1.schema.json`;
- `tests/test_r7_4_github.py`;
- this design document;
- post-acceptance `R7_4_ACCEPTANCE.md`, `R7_STATUS.md` and continuity synchronization.

## Acceptance

R7.4 may be marked COMPLETE only when R0 Repository Guard, Python Core (all jobs) and KodeStudio UI Smoke are SUCCESS on the exact final implementation head, with no unresolved blocker. Manual status for the normal public acceptance path is `CONDITIONAL NOT TRIGGERED`.

## Rollback

Disable/remove the GitHub adapter, exports, schema and fixtures. Remove any optional credential reference without deleting unrelated secrets. No remote state is mutated by R7.4, so rollback is repository-local and cache entries are inert data that can be purged safely.
