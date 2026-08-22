# R7.3 — Governed Web fetch + extraction — Design

**Phase:** R7 — Research sécurisé  
**Subdivision:** R7.3  
**Architecture:** v1.0 frozen  
**Manual intervention:** NONE

## Objective

R7.3 adds a bounded, read-only HTTP(S) research path without turning Kodepoia into a general browser agent. It consumes the R7.1 typed research contracts and single `ResearchGuard` trust boundary and the R7.2 project-local content-addressed store.

The production path is intentionally narrower than a generic HTTP client: the model-facing request contains only a URL, a retrieval timestamp and a cache-persistence flag. There is no model-authored HTTP method, body, arbitrary header set, proxy, executable, cookie jar, login flow or JavaScript execution surface.

## Components

### `WebPolicy`

Owns deterministic transport bounds:

- timeout: bounded 0.1–60 seconds;
- response size: bounded up to 16 MiB, default 2 MiB;
- redirects: bounded 0–10, default 5;
- host cadence: deterministic minimum interval, default 250 ms;
- default allowed ports: 80/443 only;
- explicit textual/structured MIME allowlist.

Policy violations fail closed and never become silent successful research.

### URL normalization and target resolution

`resolve_public_target()`:

1. accepts only `http` and `https`;
2. rejects control characters and credential-bearing URLs;
3. normalizes IDNA hostnames, default ports and removes fragments;
4. rejects local hostnames and non-allowlisted ports;
5. resolves all DNS answers;
6. rejects the target if **any** returned address is not globally routable, covering loopback, private, link-local, unspecified/reserved and similar local address classes;
7. returns a typed target containing the selected already-validated public IP.

Every redirect destination is re-normalized and re-resolved before a second request is sent. A redirect to loopback/private/link-local therefore fails before the transport receives it.

### Pinned production transport

`GuardedHttpTransport` first calls the existing `KodeGuardian` with `ActionType.NETWORK`. The pre-existing `PermissionSet` must contain `Capability.NETWORK`; absence fails before a socket is created.

After authorization the transport connects to the public IP already validated by the resolver. HTTPS keeps the original hostname as TLS `server_hostname`, preserving certificate hostname verification while avoiding a second hostname resolution at connection time. This closes the ordinary DNS-rebinding gap between policy evaluation and the socket connection.

Requests are fixed to:

- method `GET`;
- fixed Host/User-Agent/Accept/Accept-Encoding/Connection headers;
- `Accept-Encoding: identity`;
- no body;
- no proxy/browser/login automation.

Compressed/encoded responses other than identity are rejected. `Content-Length` and actual bytes are both bounded. Timeout/socket/TLS/HTTP failures become explicit `WebTransportError`; there are no hidden retries.

### Rate limiting

`HostRateLimiter` is owned by the research client and persists across top-level research calls. It raises rather than sleeping when a host is requested before the configured interval. Redirects within the same top-level request do not consume the same-host cadence twice; redirects to a new host do.

### Deterministic fixture transport

`FixtureWebTransport` implements the same one-request transport protocol but never opens a socket. CI can therefore exercise redirects, policy failures, hostile HTML, MIME/size/encoding limits and extraction with deterministic route fixtures. Public-looking fixture IPs are supplied by an injected resolver solely to exercise the same target policy.

### Extraction

The stdlib HTML parser extracts normalized visible text, title, headings/sections, author metadata, canonical-link metadata, publication/update metadata when it is timezone-qualified ISO-8601, and observed robots metadata. Script/style/noscript/template content is excluded from visible extraction.

Dates that are present but cannot safely become timezone-qualified source timestamps remain raw metadata rather than fabricated normalized dates.

For plain text/JSON/XML allowed MIME types, decoded text is retained directly.

### Untrusted metadata

Page-provided canonical links are untrusted content. A candidate canonical URL is validated through the same public-target policy; an unsafe candidate is recorded as rejected and does not change the fetched source locator or trigger a fetch.

HTTP redirects are transport control data and must satisfy the full target policy before following.

### Research artifacts and cache evidence

Successful extracted content becomes an R7.1 `ResearchArtifact` with `ResearchSourceKind.WEB`; `ResearchArtifact.from_content()` invokes the existing `ResearchGuard`. Suspicious instructions are preserved as evidence and marked, never promoted to tool instructions.

Web metadata includes:

- metadata schema version;
- content type and charset;
- raw response SHA-256;
- HTTP status;
- redirect chain;
- ETag and Last-Modified when observed;
- safe canonical URL or rejection marker;
- robots/X-Robots-Tag when observed.

`schemas/web-fetch-evidence-v1.schema.json` validates this metadata shape. ETag/Last-Modified are evidence only: R7.3 does not claim a cached artifact is freshly revalidated merely because validators exist. Full cache orchestration belongs to R7.9.

Existing content-addressed artifact reuse preserves the original `retrieved_at` evidence instead of rewriting it as a fresh retrieval.

## Status semantics

- policy/SSRF/redirect-limit/oversize/MIME/encoding violations: deterministic exception, fail closed;
- transport/DNS/timeout failure: explicit `WebTransportError`;
- HTTP 4xx/5xx: `UNAVAILABLE` with exact status reason;
- unsupported non-2xx/non-redirect status: `UNAVAILABLE`;
- successful permitted 2xx textual response: `READY` artifact;
- Web freshness remains `UNKNOWN` in R7.3 unless later version-aware logic establishes more. R7.8 owns richer freshness/version conflict reasoning.

## Explicit non-goals

R7.3 does not implement JavaScript/browser automation, POST/PUT/PATCH/DELETE, authentication forms, arbitrary cookies/headers, arbitrary ports by default, download execution, subprocesses, GitHub-specialized semantics, forums, YouTube, STT/media or UI.

## Acceptance focus

The focused suite must prove:

- unsafe scheme/credential/local/private/link-local targets are rejected;
- mixed public/private DNS answers fail closed;
- redirects are revalidated and redirect loops/limits are bounded;
- response byte/MIME/encoding limits fail closed;
- 4xx/5xx remain explicit unavailable states;
- hostile extracted instructions are preserved and flagged by `ResearchGuard` while script content is excluded;
- canonical metadata cannot steer a request to a private target;
- ETag/Last-Modified/robots and normalized source timestamps are evidence only;
- no custom method/body/header request surface exists;
- NETWORK permission is required before production socket activity;
- socket timeout is mapped without retry;
- rate limiting raises deterministically without sleeping;
- metadata conforms to its v1 JSON Schema;
- all CI remains independent of public Internet availability.

Final subdivision acceptance additionally requires R0 Repository Guard, Python Core and KodeStudio UI Smoke SUCCESS on the exact final implementation head.