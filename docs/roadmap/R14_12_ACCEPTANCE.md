# R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback acceptance

**Subdivision:** R14.12 — Content delivery: immutable manifests/bundles, channels, cache + rollback  
**Technical status:** ACCEPTED — END-head candidate ready for fresh gates  
**Immutable technical source:** `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`  
**Exact branch:** `r14/12-content-delivery`  
**Exact normalized base:** `71ceb529e89b13be343be76527e9b9b0b419ceda`  
**Pull request:** #279  
**Manual intervention:** CONDITIONAL / NOT TRIGGERED  
**Provider-live claim:** false

## Accepted scope

R14.12 implements provider-neutral governed content delivery distinct from executable self-update. Content manifests and bundles are immutable/hash-addressed, dependencies are bounded and acyclic, client/schema compatibility is explicit, object/function authorization is enforced, channel promotion is atomic, rollback selects an earlier immutable manifest, revocation is explicit, downloads are size/hash/ETag verified, and cache promotion is verified before becoming authoritative.

Executable or self-modifying payload classes are rejected. External URLs are not accepted from untrusted content/project data. Core acceptance does not require a commercial CDN, public domain, TLS certificate, provider account or provider credential. `provider_live_claim=false` is explicit acceptance state.

The frozen R14.12 scope also requires a real local HTTP fixture rather than only an in-memory transport simulation. The final technical source therefore includes a loopback-only HTTP fixture and client exercising ETag/304, Range/206 and If-Range full-response fallback while rejecting non-loopback or structurally unsafe endpoints.

## Candidate history and rejected evidence

`d62a07508cd94aae5446506dd63767f0dffe6178` is **REJECTED / NON-AUTHORITATIVE** and none of its evidence is reusable. Its evidence fixture was stopped by object authorization before reaching the intended dependency-validation assertion. The fixture authorization list was corrected without weakening production authority checks.

`d8576a3ab7cb8b496d321afe98c575375b694c14` proved an improved implementation but is not the immutable technical source. Audit showed that the generic PR workflows were checking GitHub's pull-request merge ref rather than literally checking out the branch head, so their results could not satisfy the permanent exact-head evidence rule.

The standard R0, Python Core and KodeStudio UI workflows were hardened to derive `KODEPOIA_SOURCE_SHA` from `pull_request.head.sha || github.sha`, check out that exact SHA and assert `git rev-parse HEAD` before testing. Push coverage for `r14/**` was also added for future R14 work.

Intermediate `277536f5d5fd22d73ee1b52d0818fc83f1d3ea2a` demonstrated the exact-head CI correction, but is **SUPERSEDED / NON-AUTHORITATIVE** for final R14.12 acceptance because a frozen-plan audit then found the required local HTTP fixture was still absent.

Final immutable source `9472f9198cdbaeed5c2b4618595480ac65bc4d5e` adds the governed loopback HTTP fixture/client and dedicated end-to-end HTTP regression without weakening content authority, provider posture or network policy.

## Canonical technical gates

All required technical gates are fresh and successful on exact source `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`:

- R0 Repository Guard #1882 / run `33244609227` — Ubuntu + Windows SUCCESS; both jobs explicitly checked out and asserted the exact source SHA.
- Python Core #1857 / run `33244609228` — Ubuntu Core SUCCESS, Windows Core SUCCESS, KodeStudio UI-in-core SUCCESS, Ubuntu package build SUCCESS and Windows package build SUCCESS; every job asserts exact checkout provenance.
- KodeStudio UI Smoke #1822 / run `33244609244` — SUCCESS on exact source; **14 passed**.
- R14 Content Delivery Acceptance #19 / run `33244609252` — Ubuntu job `99079798454` SUCCESS and Windows job `99079798481` SUCCESS on exact source.

Full Ubuntu Python Core on the immutable source: **1674 passed / 13 skipped / 46 warnings**. R7, R8 and R9 integrated acceptance validations also reported PASS in the same Ubuntu Core job.

The dedicated R14.12 workflow compiles and runs focused regression across R14.5 PostgreSQL persistence, R14.6 authoritative server, R14.11 remote config, R14.12 content delivery, the actual loopback HTTP fixture and the public backend export regression. The focused regression completed successfully on both Ubuntu and Windows.

## Frozen semantic/adversarial checks

All twenty schema-required content-delivery checks are `true` on both operating systems:

1. atomic channel promotion;
2. bounded capacity;
3. corrupt cache detection/rebuild;
4. client/schema compatibility;
5. dependency-cycle rejection;
6. environment isolation;
7. ETag cache hit;
8. executable payload rejection;
9. function authorization;
10. immutable bundle identity;
11. immutable manifest identity;
12. missing dependency rejection;
13. object authorization;
14. Range / If-Range semantics;
15. redacted evidence;
16. revocation enforcement;
17. rollback convergence;
18. stale promotion rejection;
19. tampered content rejection;
20. truncated content rejection.

The actual HTTP fixture regression additionally proves full GET, ETag/If-None-Match `304`, single byte range `206`, If-Range match, stale If-Range fallback to complete `200`, end-to-end service promotion/download/cache through real loopback HTTP, and rejection of HTTPS/external-host/path/userinfo endpoints for the fixture client.

## Cross-platform semantic evidence

Ubuntu and Windows evidence artifacts decode to exactly the same JSON object. ZIP packaging and platform line endings differ, but all semantic fields, checks, budgets, counts and digests are identical.

Semantic digests:

- bundle: `2c424688f078fce0d936ef7ec1a5a366c0f8a227601154c0d9f21f0f3cad4aea`;
- channel: `3727bd7357173626e7e8adc7c9847cd04c34ee84674a1cc817558503f35da9f7`;
- download: `e82789b9374d28edaa742e57abef325f7fa71f3a1000905b6aa5430d56b62aaa`;
- manifest v1: `fe65b209e4cd5425fcfc70862f1fa70ee661832ff8ddc70563e95fc222b93156`;
- manifest v2: `eecb207bf893149c6197679e5b5c7d3b42bea6e59ae1354c851a17330be2794b`;
- rollback: `3727bd7357173626e7e8adc7c9847cd04c34ee84674a1cc817558503f35da9f7`;
- state: `777e94990f33d32d7a03095957ea0a200dec4c9a4ff8241c1bea6bf3e9b19c62`;
- trace: `f017e23985f805856801b613904d272cb71396daa5692688159f2366a2c43711`.

Governed budgets:

- `max_bundles_per_manifest=16`;
- `max_cache_bytes=2097152`;
- `max_cache_entries=32`;
- `max_channels=8`;
- `max_manifests=16`;
- `max_object_bytes=1048576`.

Canonical fixture counts/state:

- bundles: `4`;
- manifests: `2`;
- cache bytes: `400`;
- channel revision: `3`.

Evidence posture is `manual_state=conditional_not_triggered`, `provider_live_claim=false`, `secrets_exposed=false`, `raw_urls_exposed=false`, `executable_content_allowed=false`.

## Evidence artifacts

Canonical R14 Content Delivery Acceptance #19 / run `33244609252` artifacts:

- Ubuntu artifact `9712443954`, ZIP digest `sha256:8a85b0978a537436c4d97ae420b13ff78184777850112f63aa1abdb837cfc320`;
- Windows artifact `9712439689`, ZIP digest `sha256:900a669e5ee7915f2f1be1c2b92f55ccfe38e6cf82907122f407a66c442a5b33`.

The decoded JSON evidence is semantically identical cross-platform. Evidence schema: `schemas/r14/backend-content-delivery-evidence.schema.json`.

## HTTP/network security posture

`LoopbackHttpContentFixture` binds only to literal `127.0.0.1` on an ephemeral port and wraps the deterministic immutable local content provider. `LoopbackHttpContentProvider` accepts only plain HTTP to a literal loopback IP with an explicit port; credentials, query, fragment, non-root base paths, external hostnames and non-loopback IPs are rejected. It uses `http.client.HTTPConnection` directly, so it does not follow redirects or accept arbitrary DNS-selected destinations. Timeout and response-size budgets are bounded.

This fixture is intentionally not exported as a production public networking API. It exists to satisfy the frozen local HTTP acceptance requirement while preserving R14's network-off-by-default/provider-allowlist boundary.

## External compatibility/safety evidence

External standards are informative comparison/safety evidence only, never architecture authority or provider-live proof.

- RFC 9110 defines conditional requests and Range/If-Range semantics used by the local fixture: If-Range is meaningful with Range, and a mismatching validator causes the server to ignore the range and send the complete representation; other preconditions such as If-None-Match are evaluated before Range.
- RFC 9111 is informative cache/revalidation evidence for ETag-based caching.
- OWASP SSRF guidance supports explicit trusted-destination allowlisting and avoiding arbitrary user-controlled targets. The R14.12 fixture is stricter: literal loopback IP only.
- Apple App Review Guidelines are informative mobile-release evidence for keeping downloaded live content data distinct from downloaded executable code that changes app functionality.

Official references:

- https://www.rfc-editor.org/rfc/rfc9110
- https://www.rfc-editor.org/rfc/rfc9111
- https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- https://developer.apple.com/app-store/review/guidelines/

## Rollback / recovery

Bundles and manifests are immutable. Channel promotion validates authority, environment, compatibility, dependency, integrity and capacity before mutation. Rollback moves the channel pointer to a prior registered immutable manifest rather than rewriting content history. Revocation is explicit. Cache entries are promoted only after exact verification; corrupt cache state is purged/rebuilt rather than silently served.

The local HTTP fixture owns only loopback-local process/thread state and deterministic fixture bytes; teardown is bounded and no external provider state is created.

## END synchronization rule

No technical implementation byte may change after immutable source `9472f9198cdbaeed5c2b4618595480ac65bc4d5e`. The R14.12 END-head may differ from that source only by:

- `docs/roadmap/R14_PLAN.md`;
- `docs/roadmap/R14_12_ACCEPTANCE.md`;
- `docs/continuity/KODEPOIA_CONTINUITY.md`.

That exact END-head must pass fresh R0 Repository Guard + full Python Core + KodeStudio UI Smoke + R14 Content Delivery Acceptance before PR #279 may merge with `expected_head_sha`. After merge, exactly one continuity-only normalization with fresh R0/Python/UI is required before R14.13 is authorized.

Manual state remains **CONDITIONAL / NOT TRIGGERED**. No external CDN/provider account, domain, TLS certificate, credential, quota or provider-live proof is required or claimed for core R14.12 acceptance.
