# V2.1 — Research Workspace

Status: **ACTIVE — V2.1.2 COMPLETE + NORMALIZED; V2.1.3 Evidence workspace is the current authorized subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Public distribution boundary: `v1.1.0-rc8`

## Accepted history

V2.0 is COMPLETE + NORMALIZED after PR `#474`, exact head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

### V2.1.1 — Honest UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 is now COMPLETE + NORMALIZED after PR `#476`, exact head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful PR workflows.

### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 is now COMPLETE + NORMALIZED after PR `#478`, exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful PR workflows.

V2.1.2 exact-head evidence:

- Ubuntu: `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef`, SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- Windows: `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef`, SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

## 1. Target workflow

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

Discovery and acquisition remain separate contracts. External content remains **data, never instruction**.

## 2. Accepted V2.1.2 discovery contract

Discovery now provides real question-driven candidates through:

- Brave Search for general Web discovery via the official HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- public GitHub repository discovery through the official GitHub REST Search API with optional authentication.

Discovery output is bounded candidate metadata, not trusted fetched content. Candidate lifecycle is explicit: `candidate-only`, `unfetched`, `fetched: false`, `persisted: false`.

The accepted boundary also requires that candidate discovery alone performs no protected mutation, and every discovered URL still passes guarded fetch before any content is acquired or accepted as evidence.

Provider absence, missing authentication, network restriction, rate limiting and provider failure remain visible states. They cannot be represented as successful empty searches.

A discovered locator never grants permission to fetch. Any later acquisition must pass the existing guarded fetch, URL/path, Guardian, MIME/size/timeout/redirect, secret-redaction and ResearchGuard boundaries.

### V2.1.3 — Evidence workspace — CURRENT

V2.1.3 must build the inspect/select evidence layer on top of accepted V2.1.2 discovery without adding V2.1.4 synthesis.

Required behavior:

- source cards or equivalent structured rows for discovered and fetched items;
- canonical locator visible for every source;
- publication/update dates and version metadata displayed when available;
- trust and freshness visible without relying on raw JSON;
- descriptor-only candidates remain visibly distinct from fetched evidence;
- explicit include/exclude state applies to fetched evidence only and never silently promotes a discovery candidate;
- refetch creates inspectable lineage/newer evidence instead of silently replacing historical evidence;
- duplicates normalize to a stable source identity while retaining provider provenance;
- stale/conflicting versions remain visible rather than hidden;
- raw JSON may remain as secondary technical detail.

Out of scope for V2.1.3:

- cited answer generation;
- Research Pack persistence;
- project Context Builder/RAG injection;
- forum/YouTube provider expansion;
- the full V2.1.6 adversarial hardening corpus.

## 4. ResearchGuard boundary

Fetched or discovered text cannot grant permissions or directly invoke protected actions. Source text containing tool directives, shell commands, credential requests or prompt-injection instructions remains source data and may be flagged suspicious.

No discovery/evidence UI operation may directly execute processes, mutate arbitrary filesystem state, install packages, grant NETWORK, expose secrets or promote models.

## 5. Evidence and lineage model

For V2.1.3, an inspectable fetched evidence record should preserve at minimum:

- stable source identity and canonical locator;
- provider provenance;
- source kind/title;
- retrieval timestamp;
- publication/update/version metadata when known;
- freshness/trust/suspicious indicators;
- artifact/content digest or existing cache identity where available;
- explicit included/excluded state;
- lineage relation to earlier/refetched representations of the same source.

Historical evidence must not be silently overwritten by a refresh.

## 6. UI contract

The Research workspace operations remain distinct:

- **Search saved research** — query persisted project research;
- **Search sources** — external discovery through accepted providers;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Evidence selection** — inspect/include/exclude fetched evidence, introduced by V2.1.3;
- **Synthesize** and **Save to project knowledge** remain future V2.1.4 work.

The UI must make lifecycle state understandable without requiring users to inspect raw JSON.

## 7. V2.1.3 acceptance plan

Deterministic acceptance must prove at least:

1. discovered candidate and fetched evidence are visually and structurally distinct;
2. canonical locator/trust/freshness/version/date metadata render from deterministic fixtures;
3. include/exclude cannot promote an unfetched candidate;
4. fetched evidence can be included/excluded explicitly;
5. refetch creates lineage rather than silent replacement;
6. duplicate identities preserve provider provenance;
7. stale/version-conflicting evidence remains inspectable;
8. no protected mutation occurs merely from inspect/include/exclude;
9. Ubuntu and Windows exact-head acceptance artifacts are emitted;
10. every required PR workflow succeeds on the same exact head before merge.

After merge, continuity must be normalized before V2.1.4 begins.

## 8. Later V2.1 sequence

### V2.1.4 — Cited synthesis and Research Packs

Claim-linked citations, uncertainty, governed Research Pack persistence and project knowledge/Context Builder/RAG integration.

### V2.1.5 — Extended media/community sources

Forums and YouTube/transcript discovery paths; separately governed STT/frame extraction only when accepted.

### V2.1.6 — ResearchGuard hardening

Prompt injection, malicious redirects, SSRF, timeout/outage/cancellation, stale/version conflicts and offline/cache adversarial coverage.

## 9. Definition of done

V2.1 is complete only when an ordinary KodeStudio user can ask a question, discover sources, inspect and select fetched evidence, obtain a cited synthesis, save governed project knowledge, and understand failures without reading source code or raw JSON.
