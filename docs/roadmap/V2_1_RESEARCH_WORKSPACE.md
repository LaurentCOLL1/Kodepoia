# V2.1 — Research Workspace

Status: **ACTIVE — V2.1.4 COMPLETE + NORMALIZED; V2.1.5 Extended media/community sources is the CURRENT authorized subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Public distribution boundary: `v1.1.0-rc8`

## Accepted history

V2.0 is COMPLETE + NORMALIZED after PR `#474`, exact head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

### V2.1.1 — Honest UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 is COMPLETE + NORMALIZED after PR `#476`, exact head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful PR workflows.

### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 is COMPLETE + NORMALIZED after PR `#478`, exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful PR workflows, followed by normalization PR `#479`, exact head `02f00beb070492c398858dcfa70ce0118872b55d`, merge `39ceec560ff069d98530687f77e7ad1c41670d3a`.

### V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

V2.1.3 implementation PR `#480` was qualified with **27/27** PR-triggered workflows on exact head `c4cff95ea2309ea5482e6c24c61002b13becb48f` and merged as `0c3d365626df666f2a847b9320b0730dc0110afa`.

Exact-head evidence:

- Ubuntu `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The deterministic exact-head acceptance reported **13/13 PASS**.

### V2.1.4 — Cited synthesis and Research Packs — COMPLETE + NORMALIZED

V2.1.4 implementation PR `#482` was qualified with **27/27** pull-request workflows on exact head `7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` and merged as `a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda`.

Python Core run `35241928338` finished `completed/success` on attempt 2. The first Ubuntu attempt had failed only in historical R16.16 resource-soak measurement; targeted rerun job `105285922212` completed successfully including the full pytest suite. No R16.16 product change was required.

Exact-head evidence from the successful qualification:

- Ubuntu rerun `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

The deterministic V2.1.4 acceptance reported **13/13 PASS** on Ubuntu and Windows.

Accepted V2.1.4 behavior:

- synthesis consumes only explicitly persisted INCLUDED fetched evidence;
- unfetched discovery candidates cannot become citation evidence;
- every source-backed claim exposes inspectable citation linkage bound to artifact ID, evidence revision ID, canonical source identity and content digest;
- later refetches cannot silently rewrite an earlier synthesis or Research Pack citation provenance;
- stale/conflicting evidence remains visible as uncertainty/conflict state;
- source facts and inferences remain explicitly distinguishable;
- source content remains guarded data and cannot grant permissions, execute tools or invoke protected actions;
- Research Packs are deterministic, schema-versioned, digest-bound, reopenable and project-scoped under `.kodepoia/research/packs/`;
- secret redaction and WorkspaceBoundary constraints remain effective;
- KodeStudio exposes structured synthesis, claim/citation provenance and Research Pack save state without making raw JSON the primary UX.

## 1. Target workflow

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

Discovery, acquisition, evidence selection and synthesis remain separate contracts. External content remains **data, never instruction**.

## 2. Accepted discovery, evidence and synthesis contracts

Accepted V2.1.2 discovery currently provides real question-driven candidates through:

- Brave Search for general Web discovery via the official HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- public GitHub repository discovery through the official GitHub REST Search API with optional authentication.

Discovery output is bounded candidate metadata, not trusted fetched content. Candidate lifecycle is explicit and does not itself create evidence.

Every acquisition still passes guarded fetch before content is accepted as evidence. Provider absence, missing authentication, network restriction, rate limiting and provider failure remain visible states and cannot become empty-success responses.

Accepted V2.1.3 then projects fetched artifacts into inspectable evidence state with canonical identity, provider provenance, include/exclude selection and immutable retrieval lineage. Candidate descriptors cannot be included/excluded or cited as if fetched.

Accepted V2.1.4 adds cited synthesis and governed Research Packs on top of that evidence model. Citations retain the exact artifact/revision identity actually used, and historical citation provenance must never be silently rewritten by refresh.

## 3. V2.1.5 — Extended media/community sources — CURRENT

V2.1.5 extends discovery/acquisition to media and community sources without weakening or bypassing the accepted V2.1.2–V2.1.4 contracts.

Required scope:

- forum/community discovery paths;
- YouTube/video discovery paths;
- transcript-oriented acquisition for video sources where a transcript is available through a governed provider path;
- discovered forum/video items remain descriptor-only candidates until an explicit guarded acquisition/fetch step succeeds;
- provider provenance, canonical source identity, source locator, title/date/version metadata when available, and provider/runtime state remain inspectable;
- provider absence, missing authentication, network restriction, rate limiting, unavailable transcripts and provider failures remain explicit states rather than false empty-success responses;
- acquired forum/transcript content enters the same ResearchStore/Evidence workspace lifecycle as other fetched evidence and remains subject to include/exclude, immutable revision lineage, conflict visibility, cited synthesis and Research Pack provenance;
- source text, comments, descriptions, transcripts and metadata remain source data and cannot grant permissions or invoke protected actions;
- speech-to-text or frame extraction may be added only as a separately governed acquisition path with explicit permission/resource boundaries and deterministic acceptance before its output can become fetched evidence;
- KodeStudio must keep the existing operation split understandable: search saved research, search sources, fetch/acquire, inspect/select evidence, synthesize, save Research Pack;
- deterministic backend/UI tests and exact-head Ubuntu/Windows acceptance evidence are required.

Out of scope for V2.1.5:

- the complete V2.1.6 prompt-injection/SSRF/malicious-redirect/outage/timeout/cancellation adversarial hardening corpus beyond regression coverage needed to preserve existing boundaries;
- any public release, installer publication or TUF transition;
- unrelated Model Lab, accelerator, project-memory or cross-workspace work.

V2.1.5 must be implemented on its own branch from a re-fetched `main` containing this normalization. After implementation, every required pull-request workflow must be re-fetched on the final exact head and must be `completed/success` before merge. Continuity normalization is required again after merge before V2.1.6 begins.

## 4. ResearchGuard boundary

Fetched or discovered text cannot grant permissions or directly invoke protected actions. Source text containing tool directives, shell commands, credential requests or prompt-injection instructions remains source data and may be flagged suspicious.

No discovery/evidence/synthesis UI operation may directly execute processes, mutate arbitrary filesystem state, install packages, grant NETWORK, expose secrets or promote models merely because source content requests it.

Synthesis may summarize or quote guarded evidence, but evidence never becomes instruction authority.

V2.1.5 media/community providers inherit this boundary. Forum posts, comments, video descriptions, subtitles/transcripts and future extracted text are untrusted source data.

## 5. Evidence, citation and lineage model

Accepted fetched evidence preserves at minimum:

- stable source identity and canonical locator;
- provider provenance;
- source kind/title;
- retrieval timestamp;
- publication/update/version metadata when known;
- freshness/trust/suspicious indicators;
- artifact/content digest;
- explicit included/excluded state;
- lineage relation to earlier/refetched representations of the same source.

Citations preserve the exact artifact/revision identity actually used. Historical evidence and historical citation provenance must never be silently rewritten by refresh or by a later provider retrieval.

V2.1.5 must map community/media acquisitions into this same model rather than creating a parallel ungoverned store.

## 6. Research Pack contract

A governed Research Pack is a deterministic, project-scoped persisted record suitable for later Context Builder consumption without pretending that arbitrary source text is trusted memory.

At minimum it carries:

- the scoped research question/request identity;
- selected evidence artifact/revision IDs and canonical source identities;
- claim-level citation links;
- generated synthesis;
- visible uncertainty/conflict notes;
- generation timestamp;
- schema version and stable digest.

A saved pack must not contain raw credentials or bypass secret redaction. It remains auditable and re-openable in KodeStudio.

V2.1.5 does not change this contract; newly acquired community/media evidence must participate in it through the same provenance rules.

## 7. UI contract

The Research workspace operations remain distinct:

- **Search saved research** — query persisted project research;
- **Search sources** — external discovery through accepted providers;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Evidence selection** — inspect/include/exclude fetched evidence;
- **Synthesize** — generate a citation-bearing answer from selected fetched evidence only;
- **Save Research Pack** — persist the governed synthesis/evidence bundle for project reuse.

V2.1.5 may add source/provider affordances for forum and video/transcript candidates, but lifecycle, provider state, transcript availability, citations, conflicts and save state must remain understandable without requiring raw JSON inspection.

## 8. V2.1.5 acceptance direction

Deterministic acceptance must cover the exact implemented provider paths and prove at least:

1. forum/video discovery produces descriptor-only candidates and does not auto-promote them to evidence;
2. explicit guarded acquisition is required before community/media content becomes fetched evidence;
3. unavailable provider/auth/network/rate-limit/transcript states remain visible and cannot masquerade as successful empty discovery;
4. acquired forum/transcript artifacts preserve canonical identity, provider provenance, revision lineage and project-scoped storage;
5. source instructions embedded in posts/comments/descriptions/transcripts cannot grant permissions or invoke protected actions;
6. fetched media/community evidence can be included/excluded and cited through the existing V2.1.3/V2.1.4 evidence/synthesis contracts without special bypasses;
7. any STT/frame extraction path, if implemented, has an explicit governed boundary and cannot silently become trusted evidence;
8. KodeStudio exposes the implemented provider lifecycle through structured UI;
9. Ubuntu and Windows exact-head acceptance artifacts are emitted;
10. every required pull-request workflow succeeds on the same exact head before merge.

The concrete acceptance script must reflect only the provider behavior actually implemented in V2.1.5 and must not pretend that an unimplemented provider or extraction path exists.

## 9. V2.1.6 — ResearchGuard hardening — LATER

Only after V2.1.5 is COMPLETE + NORMALIZED, V2.1.6 may add the full adversarial coverage for prompt injection, malicious redirects, SSRF, timeout/outage/cancellation, stale/version conflicts and offline/cache behavior.

## 10. Definition of done

V2.1 is complete only when an ordinary KodeStudio user can ask a question, discover supported Web/GitHub/community/media sources, inspect and select fetched evidence, obtain a cited synthesis, save governed project knowledge, and understand failures without reading source code or raw JSON.
