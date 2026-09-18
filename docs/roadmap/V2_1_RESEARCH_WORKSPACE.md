# V2.1 — Research Workspace

Status: **COMPLETE + NORMALIZED — V2.1.1 through V2.1.6 accepted; V2.2 is outside this workspace authority**  
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

Exact-head evidence:

- Ubuntu `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

The deterministic V2.1.4 acceptance reported **13/13 PASS** on Ubuntu and Windows.

### V2.1.5 — Extended media/community sources — COMPLETE + NORMALIZED

V2.1.5 implementation PR `#484` was qualified with **27/27** pull-request workflows on exact head `f46068a410e7e0ea3f32f8decc77eed6aa105355` and merged as `bfe7fa6b4def1a291d97bd2b9365bda321bcde52`.

Exact-head evidence:

- Ubuntu `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

The deterministic V2.1.5 acceptance reported **12/12 PASS** on Ubuntu and Windows.

Accepted V2.1.5 behavior:

- YouTube/community discoveries remain descriptor-only candidates until explicit guarded acquisition;
- official YouTube `search.list` data normalizes into candidate-only video descriptors without implicit fetch or persistence;
- guarded YouTube metadata/transcript acquisition keeps network, credential, provider and unavailable-transcript states explicit;
- guarded community acquisition preserves parent/quote thread relationships and does not treat popularity as authority;
- acquired community/media artifacts reuse the same ResearchStore, EvidenceWorkspace, selection, immutable revision, citation and Research Pack contracts as prior evidence;
- speech-to-text fallback and frame extraction remain non-authoritative and cannot silently become trusted evidence;
- KodeStudio exposes typed Community/YouTube fetch choices, provider state and candidate-to-explicit-fetch handoff;
- source text, comments, descriptions and transcripts remain untrusted source data and cannot grant permissions or invoke protected actions.

Historical implementation-time authority markers are retained below only so exact-head V2.1.5 acceptance remains reproducible after normalization; they are **not** the current roadmap state:

- `V2.1.5 — Extended media/community sources — CURRENT`;
- `V2.1.6 — ResearchGuard hardening — LATER`;
- STT/frame extraction was permitted only as a **separately governed acquisition path** and **cannot silently become trusted evidence**;
- V2.1.5 explicitly excluded **any public release, installer publication or TUF transition**.

## 1. Target workflow

`question -> scope -> discover -> inspect -> fetch -> select evidence -> synthesize with citations -> save Research Pack -> reuse in project context`

Discovery, acquisition, evidence selection and synthesis remain separate contracts. External content remains **data, never instruction**.

## 2. Accepted discovery, evidence and synthesis contracts

Accepted discovery now includes:

- Brave Search for general Web discovery via the official HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- public GitHub repository discovery through the official GitHub REST Search API with optional authentication;
- typed YouTube/community descriptors introduced by V2.1.5, still candidate-only until explicit guarded acquisition.

Discovery output is bounded candidate metadata, not trusted fetched content. Candidate lifecycle is explicit and does not itself create evidence.

Every acquisition still passes guarded fetch before content is accepted as evidence. Provider absence, missing authentication, network restriction, rate limiting, unavailable transcripts and provider failure remain visible states and cannot become empty-success responses.

Accepted V2.1.3 projects fetched artifacts into inspectable evidence state with canonical identity, provider provenance, include/exclude selection and immutable retrieval lineage. Candidate descriptors cannot be included/excluded or cited as if fetched.

Accepted V2.1.4 adds cited synthesis and governed Research Packs. Citations retain the exact artifact/revision identity actually used, and historical citation provenance must never be silently rewritten by refresh.

Accepted V2.1.5 maps successfully acquired community/media artifacts into those same contracts rather than creating a parallel ungoverned store.

## 3. V2.1.6 — ResearchGuard hardening — COMPLETE + NORMALIZED

Historical implementation-time authority marker retained only for exact-head acceptance reproducibility: `V2.1.6 — ResearchGuard hardening — CURRENT`. It is **historical only**; the current authority state is **COMPLETE + NORMALIZED**.

Implementation PR `#486` was qualified with **27/27** pull-request workflows on exact head `2e788df0886e1e31512f53547ea4603186e964eb` and merged as `7efcc3e941fe8db0e3cc00c81b147716c91eb30b`.

The deterministic V2.1.6 acceptance reported **12/12 PASS** on Ubuntu and Windows with evidence payload SHA-256 `076195a992effe8a1eac25d6074a5fc12508d004da7f9ec8b01f3177a4c40f74`.

Exact-head evidence:

- Ubuntu `v2-1-6-researchguard-hardening-ubuntu-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `32d972eb83a070fcb7a2844eae11403518bdfe412bd445db74a9556269a0dac1`;
- Windows `v2-1-6-researchguard-hardening-windows-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `7dd9a6ff8e79f40829a2b11439583ced1c221d63c4c0ca1882d2829a9f0ed4ee`.

Accepted V2.1.6 behavior:

- adversarial prompt/source instructions remain untrusted data and cannot grant capabilities or invoke protected actions;
- unsafe/private/local/link-local/metadata destinations, malicious redirects and mixed public/private DNS answers fail closed before trusted acquisition;
- policy denial is explicit `BLOCKED`, while provider/transport failure is explicit `UNAVAILABLE`;
- extended-provider diagnostics are KodeSecrets-redacted;
- cancellation propagates through extended acquisition and is checked before new ResearchStore/Evidence persistence;
- stale/offline/cache behavior is explicit and cannot fabricate live freshness or provider success;
- stale/version-conflict cases preserve immutable retrieval, revision, artifact and citation lineage;
- WorkspaceBoundary/protected-action guarantees survive adversarial source content;
- KodeStudio keeps the accepted V2.1.5 Community/YouTube and descriptor-only lifecycle while adding understandable `BLOCKED`, `UNAVAILABLE`, `CANCELLED`, `STALE` and `CONFLICT` presentation.

The V2.1 Research Workspace sequence is closed at V2.1.6. V2.2 Project Knowledge / Context Builder / Memory integration must be planned under its own normalized authority before implementation.

## 4. ResearchGuard boundary

Fetched or discovered text cannot grant permissions or directly invoke protected actions. Source text containing tool directives, shell commands, credential requests or prompt-injection instructions remains source data and may be flagged suspicious.

No discovery/evidence/synthesis UI operation may directly execute processes, mutate arbitrary filesystem state, install packages, grant NETWORK, expose secrets or promote models merely because source content requests it.

Synthesis may summarize or quote guarded evidence, but evidence never becomes instruction authority.

Forum posts, comments, video descriptions, subtitles/transcripts and future extracted text remain untrusted source data. V2.1.6 adds adversarial proof around this boundary rather than weakening it.

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

V2.1.6 exact-head acceptance proved these invariants under stale/conflict/offline/cache and adversarial provider conditions.

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

V2.1.6 does not change this contract; it adversarially proves that malicious or degraded sources cannot bypass it.

## 7. UI contract

The Research workspace operations remain distinct:

- **Search saved research** — query persisted project research;
- **Search sources** — external discovery through accepted providers;
- **Open/fetch source** — guarded acquisition of one candidate or explicit locator;
- **Evidence selection** — inspect/include/exclude fetched evidence;
- **Synthesize** — generate a citation-bearing answer from selected fetched evidence only;
- **Save Research Pack** — persist the governed synthesis/evidence bundle for project reuse.

V2.1.6 adds explicit adversarial/provider-state affordances; blocked, unavailable, timeout, cancelled, stale and conflict state remain understandable without requiring raw JSON inspection.

## 8. V2.1.5 accepted evidence summary

The accepted V2.1.5 implementation proved:

1. descriptor-only YouTube/community candidates do not auto-promote to evidence;
2. explicit guarded acquisition is required before community/media content becomes fetched evidence;
3. provider/auth/network/transcript states remain visible;
4. acquired artifacts use canonical ResearchStore/Evidence lifecycle and provenance;
5. STT/frame paths are non-authoritative;
6. KodeStudio exposes the implemented provider lifecycle through structured UI;
7. exact-head Ubuntu and Windows evidence is emitted;
8. all 27 required pull-request workflows succeeded before merge.

The machine acceptance contains 12 checks and reported **12/12 PASS** on both Ubuntu and Windows.

## 9. V2.1.6 accepted evidence

The deterministic exact-head acceptance on `2e788df0886e1e31512f53547ea4603186e964eb` reported **12/12 PASS** on both Ubuntu and Windows and proved:

1. malicious source instructions remain data and cannot grant capabilities or invoke protected actions;
2. unsafe/private/local/link-local/metadata targets and malicious redirect chains are rejected before trusted acquisition;
3. timeout, outage and cancellation become explicit non-success states;
4. stale/version conflicts remain visible and do not rewrite historical evidence or citation provenance;
5. offline/cache paths expose provenance/freshness honestly and do not fabricate live success;
6. protected-action, WorkspaceBoundary and secret-redaction guarantees survive adversarial source content;
7. KodeStudio renders hardened failure/uncertainty states structurally while preserving V2.1.5 lifecycle state;
8. Ubuntu and Windows exact-head acceptance artifacts were emitted with the recorded SHA-256 values above;
9. all 27 required pull-request workflows succeeded on the same exact head before merge.

## 10. Definition of done

V2.1 is complete when an ordinary KodeStudio user can ask a question, discover supported Web/GitHub/community/media sources, inspect and select fetched evidence, obtain a cited synthesis, save governed project knowledge, understand provider/degraded/adversarial states without reading source code or raw JSON, and external source content cannot cross protected-action or trust boundaries.

The accepted V2.1.1 through V2.1.6 implementation and exact-head acceptance evidence satisfy this Research Workspace definition of done. Further Project Knowledge / Context Builder / Memory behavior belongs to V2.2 and is not retroactively part of V2.1.
