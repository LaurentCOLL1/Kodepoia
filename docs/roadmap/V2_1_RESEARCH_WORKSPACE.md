# V2.1 — Research Workspace

Status: **ACTIVE — V2.1.1 COMPLETE + NORMALIZED; V2.1.2 Discovery providers is the current authorized subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Prerequisite: **V2.0 COMPLETE + NORMALIZED** after PR `#474`, exact implementation head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`  
V2.1.1 accepted by PR `#476`, exact head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 PR workflows successful

## 1. Problem statement

The Research page now distinguishes its three real operations. **Search saved research** calls `ResearchService.query()` and searches findings/artifacts already persisted under the active project's research reports. **Search sources** is a separate discovery operation and, after V2.1.1, cannot masquerade as saved-report search or an empty success. **Open/fetch source** remains the guarded acquisition path for one local path or explicit HTTP(S) locator.

V2.0 makes the capability truth explicit and actionable: provider/runtime states distinguish `ready`, `unavailable`, `auth-required`, `network-restricted` and `not-implemented`; capability provenance distinguishes public rc8, live source and acceptance proof; unavailable providers cannot be represented as successful empty searches.

V2.1.1 is now COMPLETE + NORMALIZED. V2.1.2 may add real discovery providers, but it must preserve the semantic and security separation established by V2.1.1.

## 2. User workflow

The target V2.1 workflow is:

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

The primary KodeStudio screen must ultimately let the user:

- enter a natural-language question;
- optionally scope by provider, domain/product, version, time window and active project;
- see which providers are available, disabled, unauthenticated, rate-limited or offline;
- discover candidate sources without already knowing their URLs;
- inspect title, canonical locator, provider, source type, date/version, freshness/trust and fetch state;
- include or exclude evidence deliberately;
- request a synthesis whose factual claims link back to included evidence;
- save selected evidence and synthesis as a governed project-scoped Research Pack;
- refresh stale sources without silently replacing historical evidence.

## 3. Source/provider architecture

Discovery and acquisition are separate contracts.

### Discovery provider

Input:

- normalized natural-language query;
- optional target product/version;
- provider/domain filters;
- requested result bound;
- cancellation token and network policy.

Output: bounded candidate descriptors, not trusted content. Each descriptor should include provider ID, title, canonical locator, snippet if allowed, source kind, dates when known and provider-specific metadata.

### Fetch provider

The existing guarded acquisition model remains authoritative for retrieving content. Discovery never grants permission to fetch or execute anything. A discovered locator must pass the same URL/path, Guardian, size, MIME, timeout, redirect, secret-redaction and ResearchGuard policies as a manually supplied locator.

### Initial provider order

1. official documentation/general Web discovery;
2. GitHub repositories/issues/PRs/code where an authorized provider is available;
3. local project/docs search;
4. forums/community sources;
5. YouTube discovery and transcript metadata;
6. optional STT/frame extraction only after explicit media acceptance.

Provider absence must be a visible capability state, never a silent empty result.

## 4. ResearchGuard boundary

All external source content remains **data, never instruction**.

ResearchGuard must preserve or extend these invariants:

- fetched text cannot grant permissions;
- text such as “ignore previous instructions”, shell commands, tokens or tool directives is treated as source content and may be flagged suspicious;
- discovered/fetched content cannot directly invoke KodeCode, process execution, network access, filesystem mutation, package installation or model promotion;
- source-derived suggestions may be presented to the user but a later action must pass the normal protected tool/permission contract;
- secrets are redacted before persistence/display where the existing secrets boundary applies;
- citations/provenance survive synthesis and export.

## 5. Evidence model and Research Pack

A Research Pack is a project-scoped derived artifact containing at minimum:

- original question and normalized scope;
- exact discovery/fetch timestamps;
- provider and canonical locator for each selected source;
- content/artifact digest and cache identity;
- source version/date/freshness/trust metadata when known;
- ResearchGuard indicators;
- explicit included/excluded state;
- cited synthesis with claim-to-source links;
- model identity/config if an LLM generated the synthesis;
- schema version and pack digest.

A pack must not overwrite previous evidence merely because a source changed. Refetch creates new evidence lineage and marks older evidence stale where appropriate.

## 6. UI contract

The operations must remain unambiguous:

- **Search saved research** — local query over already persisted reports;
- **Search sources** — real discovery through enabled external/local discovery providers; V2.1.2 is responsible for making this operation real for its accepted provider set;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Synthesize** — use only selected fetched evidence;
- **Save to project knowledge** — create/update governed derived knowledge through the Research Pack contract.

The default empty state must explain whether the user has no saved research, no discovery provider, network access is disabled/restricted, authentication is missing or an available provider genuinely returned no matches.

Raw JSON remains available for diagnostics/export but must not be the principal user experience.

## 7. Version awareness and ranking

Research is frequently wrong because it is correct for the wrong version. The workspace therefore ranks and labels evidence using:

- explicit target version from the active Project DNA when available;
- source-declared versions;
- publication/update dates;
- official vs community provenance;
- freshness/cache state;
- conflicts between sources.

The ranking system must not hide conflicting evidence. A synthesis should identify meaningful conflicts and uncertainty rather than manufacture consensus.

## 8. Failure UX

Every external operation returns an actionable state such as:

- network disabled/restricted;
- provider unavailable/not configured;
- authentication required;
- rate/usage limit reached;
- DNS/TLS/timeout failure;
- URL blocked by policy;
- unsupported MIME/oversized response;
- source requires JavaScript or cannot be extracted;
- transcript unavailable;
- cancelled;
- stale cached evidence available.

No user-facing “success” state may represent an empty no-op whose cause is unknown.

## 9. Acceptance plan

### V2.1.1 — Honest UX and diagnostics — COMPLETE + NORMALIZED

Accepted implementation head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, **27/27** PR workflows successful.

Exact-head evidence:

- Ubuntu: `v2-1-1-honest-research-ux-ubuntu-latest-c485083419f492e9c10989f6aadbda5bc436d5cc`, SHA-256 `29bdb2bb193a3a2c7a397e3d2c1307f0d323d07ff5425081803ca28e133d4d26`;
- Windows: `v2-1-1-honest-research-ux-windows-latest-c485083419f492e9c10989f6aadbda5bc436d5cc`, SHA-256 `215a5b7e1a931a04ecb957bb561c01695c8f6b992f3889aaa72026e8f8969aa6`.

The accepted implementation proves saved-report query separately from external discovery semantics, visible capability/network/authentication states, guarded explicit-locator fetch, localized actionable errors/empty states and secondary raw JSON diagnostics.

### V2.1.2 — Discovery providers — CURRENT

- deterministic provider contract and fixtures;
- at least official/general Web plus GitHub discovery path;
- bounded results, cancellation, deduplication and no hidden retries;
- candidate discovery alone performs no protected mutation;
- discovered URL still passes guarded fetch;
- exact-head acceptance and all required PR workflows must succeed before merge;
- continuity must be normalized after merge before V2.1.3 starts.

### V2.1.3 — Evidence workspace

- source cards and inspect/include/exclude flow;
- canonical locator, dates/version/trust/freshness displayed;
- cache/refetch lineage;
- duplicate sources normalized without losing provider provenance.

### V2.1.4 — Cited synthesis and packs

- synthesis cannot cite evidence outside the selected set;
- every persisted citation resolves to stored provenance;
- Research Pack digest is deterministic for its immutable payload;
- pack can be injected into project Context Builder/RAG as untrusted-derived knowledge, never as privileged instruction.

### V2.1.5 — Community/media

- forum/YouTube provider health and explicit limitations;
- transcript path only when legally/technically available;
- STT/frame jobs remain separately governed and cancellable.

### V2.1.6 — Hardening

Acceptance corpus covers prompt injection, malicious redirect, localhost/private-address SSRF attempts, credential-bearing URLs, unsupported MIME, oversized body, timeout, partial provider outage, duplicate results, stale version conflict, suspicious content, cancellation and offline cache behavior.

## 10. Definition of done

V2.1 is complete only when, from KodeStudio on a real project, an ordinary user can type a question they do not already know the answer/URL to, receive useful discoverable sources, inspect and select them, obtain a cited synthesis, save the evidence as governed project knowledge, and understand any failure without reading source code or raw JSON.

A passing test of the old URL fetch primitive alone is not sufficient to mark V2.1 complete.
