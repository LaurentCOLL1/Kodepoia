# R7.3 — Governed Web fetch + extraction — Acceptance

**Status:** COMPLETE / PASS  
**Accepted implementation head:** `4efd2cb016e774fa3ef06590ffda377606d875e9`  
**Implementation PR:** #64  
**Implementation merge:** `cde4f7fd727c6940c6a434f85fabc2ced27f04c5`  
**Manual intervention:** NONE

## Accepted scope

R7.3 implements the bounded read-only Web research transport required by the frozen R7 plan:

- typed GET-only HTTP(S) requests with no model-authored method/body/header surface;
- deterministic URL normalization and fragment stripping;
- public-target SSRF policy validating every DNS answer;
- rejection of unsafe schemes, credential-bearing URLs, local hostnames, loopback/private/link-local/non-global addresses and non-allowlisted ports;
- redirect revalidation on every hop and bounded redirect depth;
- production socket connection to the already-validated public IP, with original hostname retained for HTTPS TLS certificate verification;
- existing `KodeGuardian` + `Capability.NETWORK` authorization before production socket activity;
- bounded timeout, content length, actual response bytes, MIME types, charset and response encoding;
- deterministic per-host rate limiting without hidden sleeps or retries;
- deterministic no-network `FixtureWebTransport` for CI;
- HTML/text extraction with visible content, title/headings, author/date/canonical and robots metadata when evidenced;
- ETag/Last-Modified capture without fabricated freshness;
- all extracted content becomes an R7.1 `ResearchArtifact` and is passed through the existing `ResearchGuard`;
- `schemas/web-fetch-evidence-v1.schema.json` for normalized Web metadata evidence.

No JavaScript/browser automation, login forms, arbitrary HTTP writes, arbitrary cookies/proxies, GitHub-specialized provider, community/forum provider, YouTube, STT/media, subprocess or Research UI was introduced.

## Exact-head hosted evidence

All final required gates ran against accepted head `4efd2cb016e774fa3ef06590ffda377606d875e9`:

- R0 Repository Guard — run #968 / `32586392901` — SUCCESS;
- Python Core — run #942 / `32586392898` — SUCCESS, 5/5 jobs;
- authoritative Ubuntu full suite — **369 passed / 3 skipped / 46 warnings**;
- KodeStudio UI Smoke — run #909 / `32586392883` — SUCCESS.

PR #64 was merged only after those exact-head gates succeeded, with `expected_head_sha=4efd2cb016e774fa3ef06590ffda377606d875e9`.

## Security invariants proven

- mixed public/private DNS answers fail closed;
- redirects to private/loopback targets are rejected before a second transport request;
- redirect count is bounded;
- oversized, disallowed MIME, compressed/encoded and missing-content-type successful responses fail closed;
- 4xx/5xx without content type remain explicit `UNAVAILABLE`, not fake success;
- hostile prompt-like HTML remains source data and is marked suspicious by `ResearchGuard`; script/style/template-like content is excluded from visible extraction;
- page-provided unsafe canonical metadata cannot steer a network request and is recorded as rejected;
- non-timezone page dates are not promoted into authoritative timestamps;
- cached identical artifacts preserve their original retrieval timestamp;
- production transport requires NETWORK permission before socket activity;
- timeout is surfaced as `WebTransportError` without retry;
- host cadence raises deterministically rather than sleeping;
- Web evidence metadata validates against the v1 JSON Schema;
- hosted tests do not depend on public Internet availability.

## Freshness boundary

R7.3 records validators such as ETag and Last-Modified as evidence only. It does not manufacture `CURRENT` freshness from their presence. Rich version/freshness conflict reasoning remains R7.8 and broader cache orchestration remains R7.9.

## Rollback

R7.3 can be rolled back by removing `web.py`, its exports, metadata schema, focused tests and design/acceptance documentation. Existing R7.1/R7.2 artifacts remain valid. Cached Web artifacts are inert guarded research evidence and may be purged without external mutation.

## Decision

**PASS / COMPLETE.** R7.3 satisfies its frozen acceptance gates with manual intervention `NONE`. The next authorized subdivision after normalization is **R7.4 — GitHub research adapter**.