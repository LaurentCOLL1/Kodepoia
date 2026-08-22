# R7.10 — CLI + KodeStudio Research UX — Design

**Status: IMPLEMENTATION IN PROGRESS**  
**Manual intervention: NONE**

## Objective

Expose the already accepted R7.1–R7.9 research capabilities through one structured service consumed by both CLI and KodeStudio, without creating a second trust, permission, provenance or status model.

## Frozen scope

R7.10 implements:

- CLI commands for query, fetch, show, cache inspection, status and media capability;
- a KodeStudio Research surface with source filters, version/freshness/trust/status text, citations, suspicious-content warnings, cancellation and provenance-preserving copy/export;
- accessibility/localization hooks and deterministic offscreen UI smoke coverage;
- explicit provider/capability states when a live provider is not configured.

R7.10 does **not** implement the R7.11 adversarial/integrated phase-closing report, arbitrary browser/terminal functionality, credential-value editing, hidden background crawling, automatic provider login, or a new network/process implementation.

## One service boundary

`ResearchService` is UI-framework-independent. CLI and KodeStudio call the same methods and receive the same typed/redacted view records.

The service reuses:

- `ResearchStore` for typed artifacts/reports;
- `ResearchCacheStore` and R7.9 cache assessment;
- `LocalDocumentAdapter` for project-local/offline official snapshot reads;
- `WebResearchClient` + `GuardedHttpTransport` for governed Web fetches;
- `MediaDoctor` and the accepted R7.7 governed media runner for explicit media capability probes;
- `KodeSecrets`/research redaction for output views;
- `WorkspaceBoundary` for persisted exports.

No Qt widget is allowed to open sockets, read secrets or execute processes directly.

## CLI contract

Structured commands:

- `research-query --query ... [--source ...] [--limit ...]`: search validated persisted R7 reports/artifacts; no network side effect.
- `research-fetch --kind local|official_docs|web --locator ...`: fetch one typed source. Web requires explicit `--allow-network`; without it the result is `BLOCKED`, not silently retried or auto-authorized.
- `research-show <sha256>`: show a typed artifact/report with redaction and provenance.
- `research-cache <cache-key> [--as-of ...]`: load/query the latest R7.9 cache manifest and explicit cache reuse state.
- `research-status`: report accepted source capabilities and current interactive wiring without claiming unavailable live-provider configuration is READY.
- `research-media-capability`: run the accepted R7.7 doctor path and return explicit READY/UNAVAILABLE capability evidence.

Existing `research-media-doctor` and `research-media-acceptance` commands remain unchanged for R7.7 evidence compatibility.

CLI JSON output never prints secret/auth values. Errors use explicit status/reason fields where the underlying accepted research contract can represent them.

## Network permission contract

The R7.10 service does not grant NETWORK by default. A Web fetch requires an explicit caller opt-in. That opt-in creates only a `Capability.NETWORK` grant and still passes through `KodeGuardian`, R7.3 public-address/DNS pinning, GET-only transport, MIME/size/timeout/redirect/rate policies and ResearchGuard.

The interactive service requests Web results with source persistence disabled during transport. It persists the returned artifact only after the operation has completed and the cancellation token is still active. A cancelled operation therefore cannot leave a new artifact presented as a successful fetch.

GitHub, Community and YouTube evidence already persisted by R7.4–R7.6 remains queryable/showable/filterable. R7.10 does not invent missing credential/provider selectors; status reports such interactive live provider configuration explicitly rather than falling back to generic Web and mislabelling its source class.

## Cancellation

`ResearchCancellation` is a thread-safe token checked before dispatch, during bounded persisted-query traversal, and before any post-operation persistence/result promotion.

KodeStudio executes service operations through a Qt worker/thread-pool boundary so network/media work cannot block the GUI event loop. Cancel marks the active token immediately. R7.7 process cancellation remains governed by its existing KillSwitch/ProcessSandbox primitives; R7.10 does not introduce arbitrary process control.

If a transport returns after cancellation, the UI discards the result and the service returns `CANCELLED`; no partial cache/artifact is labelled READY.

## View/provenance contract

A `ResearchViewItem` exposes bounded/redacted display data only:

- source kind/class, source ID and locator;
- status, freshness and trust as text, never color-only semantics;
- title/version/retrieved/published/updated metadata;
- artifact/finding IDs;
- citation IDs and locators;
- suspicious flag and ResearchGuard indicators;
- bounded content/claim preview.

Copy/export serializes the same view structure, so citations and source identity stay attached to the displayed text. Export is confined below `.kodepoia/research/exports/` with `WorkspaceBoundary` and deterministic digest naming.

## KodeStudio Research surface

The page contains keyboard-operable controls with stable object names/accessibility metadata:

- query input;
- source filter;
- Search button;
- typed fetch kind + locator input + explicit network opt-in;
- Fetch button;
- Cancel button;
- results table;
- details pane;
- suspicious-content warning text;
- Copy cited JSON button;
- Export cited JSON button;
- capability/status text.

All status semantics are textual (`READY`, `BLOCKED`, `UNAVAILABLE`, `UNKNOWN`, `STALE`, `CANCELLED`). Focus remains visible through the native Qt focus contract and controls participate in keyboard tab navigation. This is consistent with WCAG 2.2 keyboard/focus guidance; R7.10 uses the existing KodeAccessibility audit rather than claiming Web-content WCAG conformance for the desktop application.

Pseudo-localization must not remove controls or break their accessible names.

## Trust boundary

External content remains external/untrusted data. KodeStudio labels suspicious results and never interprets source content as application instructions. This follows the accepted ResearchGuard architecture and the security principle of segregating untrusted external content and applying least privilege; UI rendering itself confers no authority.

## Deterministic CI strategy

Hosted CI must not require public Internet, credentials, FFmpeg/whisper availability or provider accounts.

Tests use:

- temp-project persisted ResearchStore fixtures;
- injected fixture/fake service results for UI behavior;
- cancellation before/during bounded local query;
- Web permission tests that prove network is blocked before transport unless explicitly granted, with fixture transport when network-path behavior is exercised;
- schema/serialization/redaction/export tests;
- offscreen KodeStudio smoke for control presence, focus/accessibility registration, source/status text and pseudo-localization.

A real live provider probe is not required; manual intervention remains NONE.

## Acceptance gates

R7.10 is accepted only when all succeed on the exact final implementation head:

1. R0 Repository Guard;
2. Python Core, all required jobs, Linux and Windows;
3. KodeStudio UI Smoke Windows;
4. deterministic R7.10 service/CLI/UI tests;
5. no secret in representative outputs;
6. cancel prevents a cancelled operation from being persisted/presented as READY;
7. manual = NONE.

Only after R7.10 normalization is merged may R7.11 begin.

## Rollback

Remove/disable the R7.10 CLI registrations and Research page/service facade. R7.1–R7.9 artifacts, caches, citations and lower-level provider APIs remain independently recoverable and unchanged.
