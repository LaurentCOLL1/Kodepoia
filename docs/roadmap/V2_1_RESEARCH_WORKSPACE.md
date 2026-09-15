# V2.1 — Research Workspace

Status: **PLANNED — implementation must be qualified subdivision by subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## 1. Problem statement

The current Research page is not a full Internet/search assistant. Its “Search” action calls `ResearchService.query()`, which searches findings and artifacts already persisted under the active project's research reports. It does not discover new Web results. The separate “Fetch” action accepts one local path or one explicit HTTP(S) locator and, for Web access, requires the network permission path to be enabled.

This distinction is technically defensible but poor product UX: a user naturally expects to type a question such as “Godot 4.7 navigation changes” and receive relevant sources. Instead, a new project may return an empty result because no previous research report exists, while Web acquisition expects the user to already know the URL.

V2.1 makes these semantics explicit and adds real governed discovery before fetch/synthesis.

## 2. User workflow

The target workflow is:

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

The primary KodeStudio screen must let the user:

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

The current ambiguous controls must be replaced or relabeled so these operations cannot be confused:

- **Search saved research** — local query over already persisted reports;
- **Search sources** — real discovery through enabled external/local discovery providers;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Synthesize** — use only selected fetched evidence;
- **Save to project knowledge** — create/update governed derived knowledge through the Research Pack contract.

The default empty state must explain whether the user has no saved research, no discovery provider, network access is disabled, authentication is missing or the provider returned no matches.

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

- network disabled;
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

### V2.1.1 — Honest UX and diagnostics

- prove saved-report query separately from external discovery;
- new project empty state explains that no saved reports exist;
- provider/network state is visible;
- fetch-by-URL remains available and guarded;
- errors are actionable, localized and test-covered.

### V2.1.2 — Discovery providers

- deterministic provider contract and fixtures;
- at least official/general Web plus GitHub discovery path;
- bounded results, cancellation, deduplication and no hidden retries;
- candidate discovery alone performs no protected mutation;
- discovered URL still passes guarded fetch.

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
