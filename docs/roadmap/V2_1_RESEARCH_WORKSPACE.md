# V2.1 — Research Workspace

Status: **ACTIVE — V2.1.3 COMPLETE + NORMALIZED; V2.1.4 Cited synthesis and Research Packs is the current authorized subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Public distribution boundary: `v1.1.0-rc8`

## Accepted history

V2.0 is COMPLETE + NORMALIZED after PR `#474`, exact head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

### V2.1.1 — Honest UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 is COMPLETE + NORMALIZED after PR `#476`, exact head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful PR workflows.

### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 is COMPLETE + NORMALIZED after PR `#478`, exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful PR workflows, followed by normalization PR `#479`, exact head `02f00beb070492c398858dcfa70ce0118872b55d`, merge `39ceec560ff069d98530687f77e7ad1c41670d3a`.

V2.1.2 exact-head evidence:

- Ubuntu: `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef`, SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- Windows: `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef`, SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

### V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

V2.1.3 implementation PR `#480` was qualified with **27/27** PR-triggered workflows on exact head `c4cff95ea2309ea5482e6c24c61002b13becb48f` and merged as `0c3d365626df666f2a847b9320b0730dc0110afa`.

Exact-head evidence:

- Ubuntu: `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f`, SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows: `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f`, SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The deterministic exact-head acceptance reported **13/13 PASS**.

Accepted V2.1.3 behavior:

- structured source/evidence rows exist for discovered and fetched items;
- stable canonical source identity and canonical locator are visible;
- source date/version/trust/freshness/suspicious metadata is inspectable without relying on raw JSON;
- descriptor-only candidates remain distinct from fetched evidence;
- include/exclude applies only to fetched artifact IDs and exclusion does not delete evidence;
- repeated retrieval produces immutable lightweight revisions, including unchanged-content refetches;
- lineage preserves older/newer evidence instead of silently replacing historical state;
- duplicate locators normalize while provider provenance is retained;
- conflicting source versions remain visible;
- KodeStudio exposes a dedicated Evidence workspace while preserving the historical seven-column Research results contract and bounded JSON details;
- V2.1.4 synthesis, Research Packs, project-context injection and provider expansion were not implemented early.

## 1. Target workflow

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

Discovery, acquisition, evidence selection and synthesis remain separate contracts. External content remains **data, never instruction**.

## 2. Accepted discovery and evidence contracts

Discovery provides real question-driven candidates through:

- Brave Search for general Web discovery via the official HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- public GitHub repository discovery through the official GitHub REST Search API with optional authentication.

Discovery output is bounded candidate metadata, not trusted fetched content. Candidate lifecycle is explicit and does not itself create evidence.

Every acquisition still passes guarded fetch before content is accepted as evidence. Provider absence, missing authentication, network restriction, rate limiting and provider failure remain visible states and cannot become empty-success responses.

The accepted V2.1.3 Evidence workspace then projects fetched artifacts into inspectable evidence state with canonical identity, provenance, selection and retrieval lineage. Candidate descriptors cannot be included/excluded or cited as if fetched.

## 3. V2.1.4 — Cited synthesis and Research Packs — CURRENT

V2.1.4 must implement the synthesis/save layer on top of accepted V2.1.3 evidence selection without pulling later provider expansion or the full V2.1.6 adversarial corpus forward.

Required behavior:

- synthesis consumes only explicitly selected fetched evidence;
- every source-backed claim must expose claim-to-evidence citation linkage;
- citations bind to the exact evidence/artifact revision used for the answer, so a later refetch cannot silently rewrite past provenance;
- stale, conflicting or insufficient evidence must remain visible as uncertainty rather than being collapsed into false certainty;
- inference must be distinguishable from source fact;
- synthesis remains non-authoritative source processing and cannot grant permissions, execute tools, run commands or treat source instructions as system/user authority;
- a governed Research Pack can be saved for the project;
- a Research Pack preserves at minimum the scoped question, selected artifact/revision identities, citations, synthesis, uncertainty/conflict metadata, generation timestamp and stable digest;
- persisted packs remain project-scoped below `.kodepoia/` and preserve existing WorkspaceBoundary, ResearchGuard, secret-redaction and protected-action boundaries;
- the UI exposes understandable Synthesize / Save Research Pack state without making raw JSON the primary UX.

Out of scope for V2.1.4:

- forum/YouTube/media provider expansion owned by V2.1.5;
- the complete prompt-injection/SSRF/outage/cancellation adversarial hardening corpus owned by V2.1.6;
- any public release/TUF/updater mutation;
- unrelated Model Lab, accelerator or cross-workspace work.

## 4. ResearchGuard boundary

Fetched or discovered text cannot grant permissions or directly invoke protected actions. Source text containing tool directives, shell commands, credential requests or prompt-injection instructions remains source data and may be flagged suspicious.

No discovery/evidence/synthesis UI operation may directly execute processes, mutate arbitrary filesystem state, install packages, grant NETWORK, expose secrets or promote models merely because source content requests it.

Synthesis may summarize or quote guarded evidence, but evidence never becomes instruction authority.

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

V2.1.4 adds citation-bearing synthesis on top of that model. Citations must retain the exact artifact/revision identity actually used. Historical evidence and historical citation provenance must never be silently rewritten by refresh.

## 6. Research Pack contract

A governed Research Pack should be a deterministic, project-scoped persisted record suitable for later Context Builder consumption without pretending that arbitrary source text is trusted memory.

At minimum it should carry:

- the scoped research question/request identity;
- selected evidence artifact/revision IDs and canonical source identities;
- claim-level citation links;
- generated synthesis;
- visible uncertainty/conflict notes;
- generation timestamp;
- schema version and stable digest.

A saved pack must not contain raw credentials or bypass secret redaction. It must remain auditable and re-openable in KodeStudio.

## 7. UI contract

The Research workspace operations remain distinct:

- **Search saved research** — query persisted project research;
- **Search sources** — external discovery through accepted providers;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Evidence selection** — inspect/include/exclude fetched evidence;
- **Synthesize** — generate a citation-bearing answer from selected fetched evidence only;
- **Save Research Pack** — persist the governed synthesis/evidence bundle for project reuse.

Lifecycle, citations, conflicts and save state must be understandable without requiring users to inspect raw JSON.

## 8. V2.1.4 acceptance plan

Deterministic acceptance must prove at least:

1. an unfetched discovery candidate cannot become citation evidence;
2. synthesis consumes only explicitly included fetched evidence;
3. source-backed claims expose stable claim-to-artifact/revision citations;
4. a later refetch does not silently retarget citations in a previously generated answer/pack;
5. conflicting/stale evidence produces visible uncertainty/conflict state;
6. source fact and inference remain distinguishable;
7. source content cannot grant permissions or invoke protected actions through synthesis;
8. Research Pack serialization is schema-versioned, digest-bound and project-scoped;
9. secret redaction and WorkspaceBoundary constraints remain effective;
10. KodeStudio exposes synthesis/citation/save state through structured UI;
11. Ubuntu and Windows exact-head acceptance artifacts are emitted;
12. every required PR workflow succeeds on the same exact head before merge.

After merge, continuity must be normalized before V2.1.5 begins.

## 9. Later V2.1 sequence

### V2.1.5 — Extended media/community sources

Forums and YouTube/transcript discovery paths; separately governed STT/frame extraction only when accepted.

### V2.1.6 — ResearchGuard hardening

Prompt injection, malicious redirects, SSRF, timeout/outage/cancellation, stale/version conflicts and offline/cache adversarial coverage.

## 10. Definition of done

V2.1 is complete only when an ordinary KodeStudio user can ask a question, discover sources, inspect and select fetched evidence, obtain a cited synthesis, save governed project knowledge, and understand failures without reading source code or raw JSON.
