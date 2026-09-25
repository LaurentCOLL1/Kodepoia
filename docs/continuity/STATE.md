# Kodepoia continuity state

Last synchronized: 2026-09-21 after V2.4.4 implementation PR `#524` merge and post-merge normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; V2.1 completed Research authority is `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`, normalized V2.2 authority is `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`, and the normalized V2.3 authority is `docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## V2.0 — COMPLETE + NORMALIZED

Roadmap preparation PR `#472` remains the accepted V2 planning authority. V2.0 implementation was completed by PR `#474` on exact head `79749ab25d58faaca6421bcda4eb460194a3683c`; all **27/27** PR-triggered workflows succeeded and PR `#474` merged as `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

## V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 implementation PR `#476` was qualified with **27/27** PR-triggered workflows on exact head `c485083419f492e9c10989f6aadbda5bc436d5cc` and merged as `16ef244e9cad922421f2440ef8185e9e896a164d`.

## V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 implementation PR `#478` was qualified with **27/27** PR-triggered workflows on exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef` and merged as `347068de7f9be9275754bbda7c55f4e0d5e66bac`. Its normalization PR `#479` merged as `39ceec560ff069d98530687f77e7ad1c41670d3a`.

Accepted V2.1.2 product truth remains:

- general Web discovery uses the official Brave Search HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- GitHub public repository discovery uses the official GitHub REST Search API with optional authentication;
- discovery returns bounded descriptor-only candidates marked `candidate-only` / `unfetched` and never automatically fetches, persists or promotes them to evidence;
- provider failure, missing authentication, rate limiting and network restriction remain explicit and cannot masquerade as successful empty discovery;
- every later acquisition remains subject to guarded fetch and ResearchGuard/protected-action boundaries.

## V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

Implementation PR `#480` was qualified with **27/27** PR-triggered workflows on exact head `c4cff95ea2309ea5482e6c24c61002b13becb48f` and merged as `0c3d365626df666f2a847b9320b0730dc0110afa`.

Exact-head evidence:

- Ubuntu `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The deterministic exact-head acceptance reported **13/13 PASS**.

## V2.1.4 — Cited synthesis and Research Packs — COMPLETE + NORMALIZED

Implementation PR `#482` was qualified with **27/27** pull-request workflows on exact head `7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` and merged as `a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda`.

The V2.1.4 deterministic acceptance reported **13/13 PASS** on Ubuntu and Windows. Accepted exact-head evidence is:

- Ubuntu artifact `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows artifact `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

Accepted V2.1.4 product truth remains:

- synthesis consumes only explicitly persisted INCLUDED fetched evidence; descriptor-only candidates cannot become citations;
- source-backed claims expose citations bound to immutable artifact ID, evidence revision ID, canonical source identity and content digest;
- later refetches cannot silently retarget historical citation provenance;
- stale/conflicting evidence remains visible as uncertainty/conflict state;
- source facts and synthesis inferences remain explicitly distinguishable;
- source content is treated as guarded data and cannot grant permissions or invoke protected actions;
- Research Packs are deterministic, schema-versioned, digest-bound, reopenable and project-scoped below `.kodepoia/research/packs/`;
- secret redaction and WorkspaceBoundary constraints remain effective;
- KodeStudio exposes structured synthesis/save/citation state.

## V2.1.5 — Extended media/community sources — COMPLETE + NORMALIZED

Implementation PR `#484` was qualified on exact head:

`f46068a410e7e0ea3f32f8decc77eed6aa105355`

All **27/27** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35265257329`;
- `Python Core` run `35265257418`;
- `KodeStudio UI Smoke` run `35265257290`;
- `R17 Windows Installer` run `35265257386`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35265257328`.

PR `#484` merged from the unchanged exact head as merge commit:

`bfe7fa6b4def1a291d97bd2b9365bda321bcde52`

The deterministic V2.1.5 acceptance reported **12/12 PASS** on Ubuntu and Windows. Accepted exact-head evidence is:

- Ubuntu artifact `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows artifact `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

Accepted V2.1.5 product truth:

- recognized YouTube/community discovery results are typed descriptor-only candidates and remain unfetched/unpersisted until an explicit guarded acquisition succeeds;
- official YouTube `search.list` payloads normalize into bounded video descriptors without implicit fetch;
- guarded YouTube metadata/transcript acquisition keeps network, missing credentials, provider failure and transcript-unavailable states explicit;
- guarded community acquisition preserves typed thread relationships such as parent/quote linkage while refusing to equate popularity with authority;
- successfully acquired community/media artifacts enter the same canonical ResearchStore/EvidenceWorkspace/selection, revision, citation and Research Pack lifecycle as prior fetched evidence;
- STT fallback and frame extraction are not trusted evidence paths in V2.1.5;
- KodeStudio exposes typed Community/YouTube choices, provider state and candidate-to-explicit-fetch handoff;
- external descriptions, comments, posts and transcripts remain untrusted source data and cannot grant permissions or invoke protected actions;
- no V2.1.6 adversarial corpus or release/TUF/updater mutation was pulled forward.

## V2.1.6 — ResearchGuard hardening — COMPLETE + NORMALIZED

Implementation PR `#486` was qualified on exact head:

`2e788df0886e1e31512f53547ea4603186e964eb`

All **27/27** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35356758819`;
- `Python Core` run `35356758688`;
- `KodeStudio UI Smoke` run `35356758347`;
- `R17 Windows Installer` run `35356758789`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35356758637`.

PR `#486` merged from the unchanged exact head as merge commit:

`7efcc3e941fe8db0e3cc00c81b147716c91eb30b`

The deterministic V2.1.6 acceptance reported **12/12 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`076195a992effe8a1eac25d6074a5fc12508d004da7f9ec8b01f3177a4c40f74`

Accepted exact-head artifacts:

- Ubuntu `v2-1-6-researchguard-hardening-ubuntu-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `32d972eb83a070fcb7a2844eae11403518bdfe412bd445db74a9556269a0dac1`;
- Windows `v2-1-6-researchguard-hardening-windows-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `7dd9a6ff8e79f40829a2b11439583ced1c221d63c4c0ca1882d2829a9f0ed4ee`.

Accepted V2.1.6 product truth:

- extended-source candidate typing fails closed for unsafe, non-HTTP(S) or credential-bearing locators;
- private/local/link-local/metadata targets, mixed public/private DNS answers and malicious redirect chains are rejected before trusted acquisition;
- policy/security denial is represented as `BLOCKED`, while provider/transport failure is represented as `UNAVAILABLE`;
- provider diagnostics are redacted through KodeSecrets before display;
- cancellation is propagated through extended acquisition and checked before any new ResearchStore/Evidence persistence;
- offline/cache state remains explicit as stale or unavailable and cannot fabricate live provider success;
- stale/version-conflict evidence preserves immutable revision/artifact lineage and historical citation provenance;
- adversarial source instructions remain untrusted data and cannot authorize protected actions or escape WorkspaceBoundary;
- KodeStudio preserves the accepted V2.1.5 provider/candidate lifecycle while also rendering `BLOCKED`, `UNAVAILABLE`, `CANCELLED`, `STALE` and `CONFLICT` states structurally.

## V2.1 authorization

V2.1.1 through V2.1.6 are **COMPLETE + NORMALIZED**. The Research Workspace sequence is closed at V2.1.6; no additional V2.1 subdivision is authorized.

## V2.2 planning — COMPLETE + NORMALIZED

Planning PR `#488` was qualified on exact head:

`face3a8b9b1053962635518d083b01a92a4ed2af`

All **25/25** pull-request workflows associated with that final planning head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35385962901`;
- `KodeStudio UI Smoke` run `35385962916`;
- `Python Core` run `35385962938`;
- `R12 Tauri2 Acceptance` run `35385963079`, successful on attempt 2 on the unchanged head after an isolated WebView2 runtime-probe failure on attempt 1;
- `R17 Windows Installer` run `35385962997`.

PR `#488` merged from that exact head with `expected_head_sha` protection as merge commit:

`875149032078beb681816604663056f66a2e1344`

The planning authority freezes six subdivisions:

1. V2.2.1 — Project Knowledge catalog and contracts;
2. V2.2.2 — Bounded semantic retrieval;
3. V2.2.3 — Explainable Context Builder;
4. V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle;
5. V2.2.5 — Project Memory bridge and workspace consumption;
6. V2.2.6 — Project Knowledge hardening and integrated acceptance.

Accepted planning invariants:

- reuse immutable Research Packs rather than rewriting historical source provenance;
- keep project-file access inside WorkspaceBoundary;
- reuse R16.7-hardened MemoryStore integrity, provenance, quarantine and project-scope rules;
- keep research-derived/project knowledge data-only and untrusted;
- no retrieval score or context-selection decision grants protected authority;
- no implicit global-memory or training-dataset promotion;
- no cross-project retrieval;
- V2.2 planning does not authorize release/TUF/updater mutation, R20 reopening or V2.3+ work.

## V2.2.1 — Project Knowledge catalog and contracts — COMPLETE + NORMALIZED

Implementation PR `#490` was qualified on exact final head:

`f5c6e90783476117d90ee86ea7edbed014d691a7`

All **27/27** pull-request workflows associated with that final head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35392522030`;
- `KodeStudio UI Smoke` run `35392521860`;
- `Python Core` run `35392522031`;
- `R16.7 Memory Context Poisoning Acceptance` run `35392521989`;
- `R17 Windows Installer` run `35392521882`.

The deterministic V2.2.1 acceptance reported **11/11 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`f5c695efe34fa86ea0c4a85dddfe5fef7650e86250c6a2a676c7798fc35b8a59`

Accepted exact-head artifacts:

- `v2-2-1-project-knowledge-ubuntu-latest-f5c6e90783476117d90ee86ea7edbed014d691a7`;
- `v2-2-1-project-knowledge-windows-latest-f5c6e90783476117d90ee86ea7edbed014d691a7`.

PR `#490` merged from that unchanged exact head with `expected_head_sha` protection as:

`6341dbe6599505edc8d354e629d0fc962587f8ac`

Accepted V2.2.1 product truth:

- `ProjectKnowledgeItem` / catalog / state contracts are deterministic and explicitly project-scoped;
- canonical knowledge identity binds project scope to source identity, while item/catalog digests bind normalized projected content/provenance;
- the derived catalog persists atomically under `.kodepoia/knowledge/catalog-v1.json`;
- immutable Research Packs are projected without rewriting source evidence;
- project-file projection is WorkspaceBoundary-confined, bounded to UTF-8 text, secret-redacted and guarded;
- only verified active-project memory is projected;
- the accepted `MemoryStore.list_project_scope()` path prefilters one project before integrity verification, preventing unrelated valid project memory from being read or quarantined;
- semantic ranking/retrieval, context injection, memory writes, V2.2.3+, release/TUF/updater and R20 work were not pulled forward.

## V2.2.2 — Bounded semantic retrieval — COMPLETE + NORMALIZED

Implementation PR `#492` was qualified on exact final head:

`c3294815ddf4b76f75f04cb29ee2fdfe1d27248d`

All **26/26** pull-request workflows associated with that final head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35398389155`;
- `KodeStudio UI Smoke` run `35398389451`;
- `Python Core` run `35398389163`, successful on attempt 2 on the unchanged head after an isolated Windows `WinError 32` temporary-directory lock in historical `test_r16_16_resource_soak`;
- `R17 Windows Installer` run `35398389099`.

The deterministic V2.2.2 acceptance reported **10/10 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`e9eddabeec7b15a7901cd28722ef402e2b6d3fd2306ebe8fda582f0f46594cdf`

Accepted exact-head artifacts:

- `v2-2-2-semantic-retrieval-ubuntu-latest-c3294815ddf4b76f75f04cb29ee2fdfe1d27248d`;
- `v2-2-2-semantic-retrieval-windows-latest-c3294815ddf4b76f75f04cb29ee2fdfe1d27248d`.

PR `#492` merged from that unchanged exact head with `expected_head_sha` protection as:

`2d332945c3b1f8d76cc98d651606679c89791485`

Accepted V2.2.2 product truth:

- project-scoped retrieval request/result contracts are bounded and deterministic;
- `ready`, valid `empty`, `embedding_unavailable` and `candidate_limit_exceeded` are structurally distinct outcomes;
- project scope and explicit candidate bounds are enforced before provider access or scoring;
- the retriever never constructs a hidden provider or triggers network/model download;
- semantic cosine scoring and tie-breaking are deterministic;
- excluded/invalidated knowledge is not scored; optional source-kind filtering is explicit;
- duplicate content is normalized while retaining all source/provenance references;
- retrieval performs no catalog persistence, memory writes or protected-action promotion;
- V2.2.3 Context Builder/UI, V2.2.4 lifecycle work, V2.2.5 workspace consumption, V2.3+, release/TUF/updater and R20 work were not pulled forward.

## V2.2.3 — Explainable Context Builder — COMPLETE + NORMALIZED

Implementation PR `#494` was qualified on exact final head:

`ac9ad68938cc13cd819bb078839c5963d03a794e`

All **27/27** pull-request workflows associated with that final head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35404034479`;
- `KodeStudio UI Smoke` run `35404034456`;
- `R12 Tauri2 Acceptance` run `35404034501`;
- `R13 Integrated Release Readiness` run `35404034505`;
- `Python Core` run `35404034510`;
- `R17 Windows Installer` run `35404034515`.

The deterministic V2.2.3 exact-head acceptance reported **11/11 PASS** on both Ubuntu and Windows with identical evidence payload SHA-256:

`35c18af0424d15b54694ce537f89ae80de98dff262ea8168afe8ef73f5ef9765`

Accepted exact-head artifacts:

- `v2-2-3-explainable-context-ubuntu-latest-ac9ad68938cc13cd819bb078839c5963d03a794e` — artifact ID `10571726324`;
- `v2-2-3-explainable-context-windows-latest-ac9ad68938cc13cd819bb078839c5963d03a794e` — artifact ID `10571666306`.

PR `#494` merged from that unchanged exact head with `expected_head_sha` protection as:

`363bf1a3afa06949269208aa6d3639e439c899e5`

Accepted V2.2.3 product truth:

- `ProjectContextCandidate`-style context candidates retain source identity, retrieval score, trust, freshness/version and token estimate;
- selected/omitted rationale is deterministic, including `user_included`, `user_excluded`, `mandatory`, `within_budget` and `budget_exceeded`;
- the existing `ContextBuilder` / `ContextItem` primitive is reused with explicit token-budget accounting rather than creating a parallel context engine;
- mandatory or explicit Include affects selection only and never promotes trust or instruction authority;
- source, knowledge and citation traceability survives rendered context;
- project/research-derived content remains inside the existing `<UNTRUSTED_DATA>` boundary;
- KodeStudio Research exposes source, score, trust, freshness/version, token cost, decision/rationale, budget and Auto/Include/Exclude before final assembly;
- V2.2.4 lifecycle persistence/refresh/delete and V2.2.5 workspace consumption were not pulled forward.

This normalization closes V2.2.3 and authorizes **V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle** only.

## V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle — COMPLETE + NORMALIZED

Implementation PR `#496` was qualified on exact final head:

`c17e673d944dd0582f9c0e24368c0adf45dd3f40`

All **27/27** pull-request workflows associated with that final head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35413101428`;
- `KodeStudio UI Smoke` run `35413101469`;
- `R12 Tauri2 Acceptance` run `35413101488`;
- `R13 Integrated Release Readiness` run `35413101477`;
- `Python Core` run `35413101460`;
- `R17 Windows Installer` run `35413101474`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35413101409`.

The deterministic V2.2.4 exact-head acceptance reported **13/13 PASS** on both Ubuntu and Windows with identical evidence payload SHA-256:

`5ee068e69dc60eba21c840f33a1cabe88008ac247eeb9ed43a7b7fbf90f1f363`

Accepted exact-head artifacts:

- `v2-2-4-version-aware-lifecycle-ubuntu-latest-c17e673d944dd0582f9c0e24368c0adf45dd3f40` — artifact ID `10575435457`;
- `v2-2-4-version-aware-lifecycle-windows-latest-c17e673d944dd0582f9c0e24368c0adf45dd3f40` — artifact ID `10574915924`.

PR `#496` merged from that unchanged exact head with `expected_head_sha` protection as:

`ca27459ca04abbeba8275cc32ba7166e37acfd5a`

Accepted V2.2.4 product truth:

- derived Project Knowledge has explicit source/version fingerprint contracts and per-item version dependency keys;
- lifecycle outcomes are deterministic and visible as fresh, stale, invalidated or missing with explicit reasons such as source/version change;
- stale/invalidated derived knowledge projects to `ProjectKnowledgeState.INVALIDATED`, preserving the existing V2.2.2 retrieval exclusion gate;
- refresh/rebuild reuses the accepted `ProjectKnowledgeBuilder` / `ProjectKnowledgeStore` path and does not rewrite immutable source evidence;
- Auto/Include/Exclude selection state persists across refresh/rebuild;
- delete-derived is bounded and cannot delete Research Packs, project files, memory source records or historical citation evidence;
- KodeStudio Research exposes lifecycle state plus explicit Auto/Include/Exclude, Refresh/Rebuild and Delete-derived controls with a visible source-delete versus derived-delete boundary;
- V2.2.5 workspace consumption / Memory bridge and V2.2.6 hardening were not pulled forward.

This normalization closes V2.2.4 and authorizes **V2.2.5 — Project Memory bridge and workspace consumption** only.

## V2.2.5 — Project Memory bridge and workspace consumption — COMPLETE + NORMALIZED

Implementation PR `#498` was qualified on exact final head:

`d29d10e5456623d1b7063bb37386693c1eec625a`

All **31/31** pull-request workflows associated with that final head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35423380639`;
- `KodeStudio UI Smoke` run `35423380566`;
- `R12 Tauri2 Acceptance` run `35423380651`;
- `R13 Integrated Release Readiness` run `35423380709`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35423380706`;
- `R18.7 Update Discovery Channel UX Acceptance` run `35423380678`;
- `Python Core` run `35423380620`;
- `R17 Windows Installer` run `35423380625`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35423380657`.

The deterministic V2.2.5 exact-head acceptance reported **13/13 PASS** on both Ubuntu and Windows with identical evidence payload SHA-256:

`22a8a287c8eead8530d2289fb19b9595e8774f0809f28c71754384b914ea8144`

Accepted exact-head artifacts:

- `v2-2-5-project-workspace-ubuntu-latest-d29d10e5456623d1b7063bb37386693c1eec625a` — artifact ID `10578666529`;
- `v2-2-5-project-workspace-windows-latest-d29d10e5456623d1b7063bb37386693c1eec625a` — artifact ID `10578731421`.

On the unchanged final head, `python-core-windows-latest` succeeded on attempt 2 after an isolated historical R16.16 temporary-directory `WinError 32` cleanup lock. Ubuntu passed the same full test suite, the V2.2.5 acceptance was already 13/13 PASS on both OSes, no source/workflow/criterion changed, and only the failed Windows job was rerun.

PR `#498` merged from that unchanged exact head with `expected_head_sha` protection as:

`11479e63dc48c45f2ec97f9950430cf35c986e8c`

Accepted V2.2.5 product truth:

- one project-scoped governed context snapshot is shared across Chat, KodeCode and specialist KodeStudio workspaces rather than each surface reading unrestricted stores;
- the workspace session is bound to the exact project retrieval/context pair and rejects global/cross-project scope mismatches;
- source identity, content/source digests, trust, freshness/version and citation IDs survive workspace consumption;
- Research publishes only the explicitly assembled governed context bundle into the shared session;
- Chat consumes the snapshot as reference data only inside the existing `<UNTRUSTED_DATA>`/data-only boundary and never as instruction or permission authority;
- KodeCode exposes the same context through an explicitly governed read-only tool policy and does not directly import/read durable MemoryStore;
- R11-R15 specialist surfaces expose read-only visibility into the same active context sources;
- `ProjectMemoryBridge` reuses R16.7 `MemoryStore` integrity, replay/version, quarantine and authority-spoof protections;
- durable project-context memory requires explicit opt-in, remains `derived_summary` / derived-untrusted, is project scoped, and cannot silently promote to global memory or training data;
- historical V2.2.3 preview construction and older KodeStudio factory contracts remain preserved;
- V2.2.6 integrated hardening, V2.3+, V2.5 cross-workspace orchestration and release/TUF/updater/R20 work were not pulled forward.

This normalization closes V2.2.5 and authorizes **V2.2.6 — Project Knowledge hardening and integrated acceptance** only.

## V2.2.6 — Project Knowledge hardening and integrated acceptance — COMPLETE + NORMALIZED

Implementation PR `#500` was qualified on exact final head:

`add97a4889c68b7aed79125563917ddce8b70863`

All **26/26** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35438155760`;
- `KodeStudio UI Smoke` run `35438155732`;
- `R12 Tauri2 Acceptance` run `35438155744`;
- `R13 Integrated Release Readiness` run `35438155814`;
- `Python Core` run `35438155746`;
- `R17 Windows Installer` run `35438155755`.

The deterministic V2.2.6 exact-head acceptance reported **16/16 PASS** on both Ubuntu and Windows with identical evidence payload SHA-256:

`646071eb27ecf8e08ae7dfde3bd74e0f7d32a9dbd6e3d284a85c9093c5b5cc6d`

Accepted exact-head artifacts:

- `v2-2-6-project-knowledge-hardening-ubuntu-latest-add97a4889c68b7aed79125563917ddce8b70863` — artifact ID `10582792728`;
- `v2-2-6-project-knowledge-hardening-windows-latest-add97a4889c68b7aed79125563917ddce8b70863` — artifact ID `10582857766`.

PR `#500` merged from that unchanged exact head with `expected_head_sha` protection as:

`2c122c913b57c0034f73ba25c34f3fd32507fafa`

Accepted V2.2.6 product truth:

- cross-project retrieval is rejected before embedding-provider access;
- R16.7 replay, version-conflict, stale-version, integrity verification and quarantine semantics remain fail closed before project-memory projection;
- tampered Research Packs and digest mismatches fail immutable pack/synthesis validation;
- changed project-file or engine/tool fingerprints make affected derived knowledge stale/invalidated and therefore retrieval-ineligible;
- prompt-injection/source-instruction text from Research Packs, project files and memory stays suspicious, untrusted and data-only through retrieval, Context Builder and Chat/KodeCode/specialist consumption;
- secret-bearing project-file content is redacted and secret-bearing durable memory is rejected;
- Include/Exclude state remains deterministic across lifecycle refresh and final context assembly;
- delete-derived cannot delete project files or immutable Research Packs;
- retrieval ordering, context-budget omission and unavailable-versus-valid-empty capability state remain deterministic and explicit;
- existing cancellable Research acquisition still prevents post-cancel persistence;
- KodeStudio explainability and active workspace context preserve source/citation/trust visibility without authority promotion;
- V2.2.6 required no runtime product-code change: the accepted implementation is an adversarial integrated test/acceptance layer plus exact-head CI evidence over the already accepted V2.2 contracts.

**V2.2 is now COMPLETE + NORMALIZED.** No V2.2.7 is reserved or authorized.

## V2.3 planning — Model Lab governed improvement UX — COMPLETE + NORMALIZED

Planning PR `#502` was qualified on exact final head:

`8a13bb5c7a334b500cebaedec8bf7988d10147c3`

All **25/25** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35447327711`;
- `KodeStudio UI Smoke` run `35447327644`;
- `Python Core` run `35447327756`;
- `R12 Tauri2 Acceptance` run `35447327773`;
- `R13 Integrated Release Readiness` run `35447327678`;
- `R17 Windows Installer` run `35447327730`.

PR `#502` merged from that unchanged head with `expected_head_sha` protection as:

`4744cc47827ca28c61395fc6c8e5064a18ae2b0c`

The accepted V2.3 planning authority is:

`docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md`

It freezes exactly six subdivisions:

1. V2.3.1 — Model Lab shell, inventory and lineage;
2. V2.3.2 — Governed experience and dataset curation workspace;
3. V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX;
4. V2.3.4 — Governed training plan, execution and recovery UX;
5. V2.3.5 — Candidate evaluation, export, promotion and rollback UX;
6. V2.3.6 — Model Lab hardening and integrated acceptance.

Accepted planning invariants include:

- V2.3 is a UX/governance layer over the accepted R15 Experience / KodeBench / Fine-tuning backend rather than a parallel training stack;
- Project Knowledge, Research Packs, chats, memory, retrieved context and tool output do not become training data automatically;
- training eligibility continues through the accepted R15 Experience governance/dedup/contamination/immutable-dataset path;
- `NO_TRAIN` remains a valid evidence-backed first-class outcome;
- exact dataset/model/tokenizer/capability identities remain mandatory;
- critical-domain regressions veto promotion;
- promotion/rollback remains an explicit separate registry mutation;
- Kaggle T4×2 remains two distinct 16 GiB devices and V2.4 retains accelerator production/multi-GPU qualification;
- TPU v5e-8 remains deferred;
- no public publishing, arbitrary command surface, silent dependency installation, release/TUF/updater work or R20 reopening.

This planning normalization authorized **V2.3.1 — Model Lab shell, inventory and lineage only**.

## V2.3.1 — Model Lab shell, inventory and lineage — COMPLETE + NORMALIZED

Implementation PR `#504` was qualified on exact final head:

`33d30747ebd915ab2bad56d3154f55a907830061`

All **28/28** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35456063171`;
- `KodeStudio UI Smoke` run `35456063151`;
- `Python Core` run `35456063128`;
- `R12 Tauri2 Acceptance` run `35456063201`;
- `R13 Integrated Release Readiness` run `35456063202`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35456063364`;
- `R17 Windows Installer` run `35456063263`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35456063159`.

The deterministic V2.3.1 acceptance reported **14/14 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`

Accepted exact-head artifacts:

- `v2-3-1-model-lab-shell-ubuntu-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588052972`;
- `v2-3-1-model-lab-shell-windows-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588422645`.

PR `#504` merged from that unchanged exact head with `expected_head_sha` protection as:

`1a7454f52bcd78ac2b44c3db467f6faa39df3a62`

Accepted V2.3.1 product truth:

- KodeStudio now has a dedicated structured Model Lab entry while the accepted R15 Experience / Tune page remains available;
- Model Lab discovers accepted project-scoped R15 experience, dataset, benchmark and tuning evidence through bounded read-only JSON inspection rather than a new training backend;
- specialized-model registry records are inspected through the accepted R15.14 digest/integrity contract and tampered registry evidence remains explicit;
- dataset/training/evaluation/export/registry digests are projected into a read-only lineage view;
- saved Ollama role preferences are visible without contacting Ollama, while installed-model inventory refresh is an explicit read-only runtime action;
- Kaggle doctor/quota state is queried only on explicit refresh and does not change accelerator behavior;
- training dependency capability is introspected without installing packages or drivers;
- missing, invalid, stale, tampered and unavailable states remain explicit; raw JSON is diagnostics-only rather than the primary UX;
- the Model Lab shell exposes no dataset-build, training, conversion/package, promotion or rollback mutation;
- FR/EN/pseudo-localization and the central KodeStudio accessibility contract include the new Model Lab controls;
- Project Knowledge, Research Packs, chats, memory and retrieved context remain reference data only and do not become training examples.

Two integration defects were corrected before the final accepted head: historical R15.15 Ruff import ordering and registration of the new Model Lab controls in the existing accessibility contract. No gate was weakened; only the final head above is accepted.

This V2.3.1 post-merge normalization authorized **V2.3.2 — Governed experience and dataset curation workspace only**.

## V2.3.2 — Governed experience and dataset curation workspace — COMPLETE + NORMALIZED

Implementation PR `#506` was qualified on exact final head:

`f419e125fa28f72bbb11dce855047a64dc3be574`

All **28/28** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35472245615`;
- `KodeStudio UI Smoke` run `35472245629`;
- `Python Core` run `35472245626`;
- `R12 Tauri2 Acceptance` run `35472245665`;
- `R13 Integrated Release Readiness` run `35472245591`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35472245579`;
- `R17 Windows Installer` run `35472245703`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35472245622`.

The deterministic V2.3.2 acceptance reported **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`

Accepted exact-head artifacts:

- `v2-3-2-governed-curation-ubuntu-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10593690427`;
- `v2-3-2-governed-curation-windows-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10592989545`.

PR `#506` merged from that unchanged exact head with `expected_head_sha` protection as:

`cefcffbfa55fdd0de096ebe8f029a2123c735d08`

Accepted V2.3.2 product truth:

- KodeStudio exposes a dedicated structured Data Curation workspace alongside the accepted Model Lab and R15 Experience / Tune surfaces;
- experience eligibility/provenance/project scope/authorization/license/privacy/sanitization/benchmark protection/revocation/quarantine/integrity are visible without reading raw experience payloads;
- deduplication and benchmark-contamination outcomes are structured and contaminated groups remain excluded;
- immutable dataset manifest/card identity and digests are inspected without reading JSONL payload rows;
- dataset preview is non-mutating and summarizes candidate/excluded rows, reasons, licenses, domains, tasks and split-policy availability;
- curation and dataset-build mutations delegate exclusively to typed R15 handlers, preserve dry-run, explicit confirmation and configured-backend gates, and reject cross-project R15 service binding;
- Project Knowledge, Research Packs, chat, memory and retrieved context remain reference-only and are not auto-ingested as training examples;
- no training, conversion/package, promotion, rollback or new accelerator behavior was pulled forward;
- FR/EN/pseudo-localization and accessibility coverage include the new workspace.

Two qualification-only corrections preceded the final accepted head: V2.3.1 localization acceptance was made forward-compatible without weakening its historical Model Lab assertion, and the V2.3.2 tamper fixture was corrected to actually diverge. No gate was weakened.

This V2.3.2 post-merge normalization authorized **V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX only**.

## V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX — COMPLETE + NORMALIZED

Implementation PR `#508` was qualified on exact final head:

`e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7`

All **32/32** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35480915764`;
- `KodeStudio UI Smoke` run `35480915669`;
- `Python Core` run `35480915728`;
- `R12 Tauri2 Acceptance` run `35480915657`;
- `R13 Integrated Release Readiness` run `35480915772`;
- `R15.6 KodeBench v2 Acceptance` run `35480915683`;
- `R15.7 Gap Decision Acceptance` run `35480915716`;
- `R15.10 Base Adapter Evaluation Acceptance` run `35480915666`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35480915765`;
- `R17 Windows Installer` run `35480915745`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35480915748`.

The deterministic V2.3.3 acceptance reported **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`8c1b92bdee6e6236f653afb749a5ea29b464b22d63ef95bd078b739a7684d064`

Accepted exact-head artifacts:

- `v2-3-3-bench-decision-ubuntu-latest-e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7` — ID `10595259236`;
- `v2-3-3-bench-decision-windows-latest-e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7` — ID `10596176144`.

PR `#508` merged from that unchanged exact head with `expected_head_sha` protection as:

`b2943239885b5fc4e3791d48dfacf5b6947851a2`

Accepted V2.3.3 product truth:

- KodeStudio now exposes a structured **Bench & Decision** workspace over the existing R15 KodeBench and gap-decision authority rather than a parallel benchmark/decision engine;
- KodeBench evidence is projected by suite/task/domain with exact model identity, suite/config/report digests, task scores/categories and explicit digest-integrity/tamper state;
- gap decisions expose the exact base model, benchmark binding, governed dataset identity/digest when present, target domains, acceptance targets, evidence digest, policy digest, blockers and reasons;
- diagnostics distinguish tool, retrieval, router, context, prompt and product components, while the existing R15.7 `GapDecisionEngine` remains the deterministic decision authority;
- `prompt` is represented through the existing typed `DiagnosticComponent` contract without changing the historical mandatory-probe set; a prompt defect remains `FIX_SYSTEM_FIRST`, not `TRAIN`;
- persisted dispositions remain fail-closed and visible, including `TRAIN`, `NO_TRAIN`, `FIX_SYSTEM_FIRST`, `INSUFFICIENT_DATA`, `UNSUPPORTED`, `LICENSE_BLOCKED`, `BUDGET_BLOCKED` and `INCONCLUSIVE` as produced by accepted contracts;
- benchmark status/run and gap diagnosis delegate to typed R15 UX actions with dry-run and explicit confirmation semantics; cross-project R15 binding is rejected;
- V2.3.3 exposes no training launch/cancel/recovery, conversion/package, promotion or rollback mutation;
- Project Knowledge, Research Packs and retrieved context remain data-only diagnostic references and never gain instruction authority or automatic training-data status;
- FR/EN/qps-ploc and accessibility coverage include the new workspace.

Qualification corrections before the final accepted head aligned the exact KodeBench scorer-digest projection, the historical pseudo-locale navigation count, the deterministic two-model baseline fixture and the historical V2.3.2 localization acceptance with the newly authorized V2.3.3 surface. No gate was weakened; all prior-SHA results were invalidated after each corrective commit.

This post-merge normalization closes V2.3.3 and authorizes **V2.3.4 — Governed training plan, execution and recovery UX only**. V2.3.5+ remain unauthorized until V2.3.4 is implemented, exact-head qualified, merged and post-merge normalized.

## V2.3.4 — Governed training plan, execution and recovery UX — COMPLETE + NORMALIZED

Implementation PR `#510` was qualified on exact final head:

`4f25fb6331ba76dfe51cd13c8a1560f66142a862`

All **31/31** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35489030766`;
- `KodeStudio UI Smoke` run `35489030819`;
- `Python Core` run `35489030825`;
- `R12 Tauri2 Acceptance` run `35489030843`;
- `R13 Integrated Release Readiness` run `35489030751`;
- `R15.8 Training Runtime Acceptance` run `35489030774`;
- `R15.9 QLoRA SFT Acceptance` run `35489030804`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35489030861`;
- `R17 Windows Installer` run `35489030828`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35489030758`.

The deterministic V2.3.4 exact-head acceptance reported **18/18 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`f8be65eaffcc71080551c30c2fc7eff56b20509f7fed74b30ceeb0ccf29e8113`

Accepted exact-head artifacts:

- `v2-3-4-governed-training-ubuntu-latest-4f25fb6331ba76dfe51cd13c8a1560f66142a862` — artifact ID `10598522634`;
- `v2-3-4-governed-training-windows-latest-4f25fb6331ba76dfe51cd13c8a1560f66142a862` — artifact ID `10597613394`.

PR `#510` merged from that unchanged exact head with `expected_head_sha` protection as:

`0e88eb5e5f4a2fc7f80038dc28e580c8e93332b2`

Accepted V2.3.4 product truth:

- KodeStudio now exposes a structured **Training** workspace over accepted R15 training/runtime contracts rather than a parallel training engine;
- immutable TrainingPlan identity remains bound to exact base model, tokenizer, governed dataset, accepted evidence-backed `TRAIN` decision and verified capability report;
- capability/resource preflight is fail closed before launch;
- local and Kaggle remain explicit selectable backends without fabricated readiness, pooled-VRAM or new multi-GPU semantics;
- doctor/plan/run/status/cancel/resume use typed R15 UX actions, with dry-run and explicit confirmation for mutation paths;
- run state, losses, resource evidence, checkpoints and resume lineage remain bound to immutable plan/run identities;
- cancellation/recovery does not bypass ProcessSandbox/KillSwitch or checkpoint/plan lineage rules;
- Project Knowledge, Research Packs and retrieved context remain reference/data only and cannot authorize or auto-populate training;
- candidate evaluation/export/conversion/package, promotion, rollback and public publishing remain outside V2.3.4.

Qualification corrections before the final accepted head fixed only integration/test-contract defects: KodeStudio import ordering for Ruff and the V2.3.4 KodeBench fixture's use of the persisted report contract. Every corrective commit invalidated prior-head CI evidence; only the exact final head above is accepted.

This post-merge normalization closes V2.3.4 and authorizes **V2.3.5 — Candidate evaluation, export, promotion and rollback UX only**. V2.3.6+ remain unauthorized until V2.3.5 is implemented, exact-head qualified, merged and post-merge normalized.

## V2.3.5 — Candidate evaluation, export, promotion and rollback UX — COMPLETE + NORMALIZED

Implementation PR `#512` was qualified on exact final head:

`ed4197780828e54068f0f6893d5f6d4274c57d3d`

All **31/31** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35506019032`;
- `KodeStudio UI Smoke` run `35506019100`;
- `Python Core` run `35506019089`;
- `R12 Tauri2 Acceptance` run `35506019204`;
- `R13 Integrated Release Readiness` run `35506019023`;
- `R15.8 Training Runtime Acceptance` run `35506019092`;
- `R15.9 QLoRA SFT Acceptance` run `35506019090`;
- `R15.15 CLI KodeStudio UX Acceptance` run `35506019193`;
- `R17 Windows Installer` run `35506019002`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35506019081`.

The deterministic V2.3.5 exact-head acceptance reported **18/18 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548`

Accepted exact-head artifacts:

- `v2-3-5-candidate-lifecycle-ubuntu-latest-ed4197780828e54068f0f6893d5f6d4274c57d3d` — artifact ID `10604315201`;
- `v2-3-5-candidate-lifecycle-windows-latest-ed4197780828e54068f0f6893d5f6d4274c57d3d` — artifact ID `10603926113`.

PR `#512` merged from that unchanged exact head with `expected_head_sha` protection as:

`c13893edb82c350b623af4c0f486a525dce116f0`

Accepted V2.3.5 product truth:

- KodeStudio now exposes a structured **Candidate lifecycle** workspace over accepted R15.10-R15.14 evidence/runtime contracts rather than parallel evaluation/export/conversion/package/registry engines;
- persisted paired base/candidate comparison evidence keeps exact suite/config/holdout identity, task/domain deltas and critical-regression vetoes visible;
- training-loss, overfit and resource evidence is projected when present without becoming a new decision engine;
- export, GGUF conversion/quantization and Ollama packaging expose exact identities, digests, lineage, quality/integrity state and honest unavailable/rejected/tampered outcomes;
- the R15 UX facade was extended only for demonstrated typed gaps: governed export run/status, conversion run, Ollama package and exact registry role selection;
- export/conversion/package/promotion/rollback preserve dry-run plus explicit confirmation before mutation;
- promotion requires the exact accepted evaluation/export/conversion/package chain, immutable registry record, eligible role and exact artifact/current/proposed mapping;
- rollback requires the exact immutable prior role mapping and fails closed when it is absent or stale;
- Project Knowledge, Research Packs, chat, memory and retrieved context remain reference/data only and cannot authorize export, promotion or rollback;
- no public model-hub publishing, arbitrary shell/argv/env/package install, silent base/tokenizer/routing replacement, new accelerator behavior or V2.4 work was pulled forward.

No corrective implementation commit was required after the first V2.3.5 head; only the exact accepted head above is qualified.

This post-merge normalization closes V2.3.5 and authorizes **V2.3.6 — Model Lab hardening and integrated acceptance only**. V2.4+ remain unauthorized until V2.3.6 is implemented, exact-head qualified, merged and post-merge normalized.

## V2.3.6 — Model Lab hardening and integrated acceptance — COMPLETE + NORMALIZED

Implementation PR `#514` was qualified on exact final head:

`cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e`

All **26/26** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35525471455`;
- `KodeStudio UI Smoke` run `35525471438`;
- `Python Core` run `35525471317`;
- `R12 Tauri2 Acceptance` run `35525471447`;
- `R13 Integrated Release Readiness` run `35525471466`;
- `R17 Windows Installer` run `35525471410`.

The deterministic V2.3.6 exact-head acceptance reported **21/21 PASS** on Ubuntu and Windows with identical evidence payload SHA-256:

`935e35c549571a9ae578515bf2acd5cf9353b264b90da5fefb644a62a6d0e8cd`

Accepted exact-head artifacts:

- `v2-3-6-model-lab-hardening-ubuntu-latest-cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e` — artifact ID `10609481837`;
- `v2-3-6-model-lab-hardening-windows-latest-cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e` — artifact ID `10610285166`.

PR `#514` merged from that exact head with `expected_head_sha` protection as:

`d511c1ef081ddc02c3071892862e2f83ed5ba8c0`

Accepted V2.3.6 product truth:

- hardening is acceptance over existing V2.3/R15 services rather than a new evaluation/training/export/conversion/package/registry engine;
- untrusted Project Knowledge, Research Packs, chat, memory and retrieved context remain reference/data only and cannot authorize training or promotion;
- privacy/license/revocation/contamination and tampered/stale dataset/model/tokenizer/evidence states remain fail closed;
- capability/resource/backend and checkpoint/plan lineage failures remain explicit and block unsupported execution/recovery;
- paired base/candidate evidence remains exact and aggregate gain cannot mask a critical regression;
- GGUF requantization/quality, Ollama package quality/provider truth and model-registry promotion/rollback integrity remain governed;
- Ollama/Kaggle/runtime unavailability remains honest and deterministic empty/missing-evidence UI states remain accessible;
- no public model-hub publishing, silent model/tokenizer/routing mutation, V2.4 accelerator behavior, release/TUF/updater mutation or R20 reopening was introduced.

The initial V2.3.6 head exposed only test-contract issues. Two corrective commits aligned hardening assertions and ineligible-experience fixtures with already accepted live contracts; no product code or gate was weakened. Every new commit invalidated all CI evidence from the previous SHA.

**V2.3 is now COMPLETE + NORMALIZED through V2.3.6.**

V2.4 planning, V2.4.1, V2.4.2, V2.4.3 and **V2.4.4 are COMPLETE + NORMALIZED**. V2.4.4 implementation PR `#524` was qualified **29/29** on exact final head `1abf4917566f065ac26b71a02e02d8fb3506fe1a`, with deterministic acceptance **25/25 PASS on Ubuntu** and **25/25 PASS on Windows**, common evidence SHA-256 `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`, then merged as `779a9c8282e153b7dba35fb22be89ec5c622e1d3`. The only authorized implementation work is **V2.4.5 — Model Lab accelerator UX and live Kaggle qualification**. V2.4.6+ remain unauthorized until V2.4.5 is implemented, exact-head qualified, merged and post-merge normalized. V2.5+ remain unauthorized.

## V2.4 planning — Kaggle T4×2 production qualification and explicit multi-GPU — COMPLETE + NORMALIZED

Planning was performed from normalized live `main`:

`586d55a3cbccaadbb2a868c5fd5e0ed0123bf8b0`

Normative planning document under qualification:

`docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md`

The plan freezes exactly six subdivisions:

1. V2.4.1 — Accelerator topology and provider truth;
2. V2.4.2 — Strategy, effective-batch and resource planning contract;
3. V2.4.3 — Governed explicit two-GPU execution;
4. V2.4.4 — Distributed checkpoint, cancellation and recovery;
5. V2.4.5 — Model Lab accelerator UX and live Kaggle qualification;
6. V2.4.6 — Production hardening and integrated acceptance.

Live-source planning findings:

- `NvidiaTeslaT4` requests Kaggle GPU T4 ×2, but provider metadata is not accepted as runtime topology proof;
- R15.8 currently probes one `cuda:0` and serializes one device plus one free/total VRAM pair;
- the current Kaggle kernel launches one training worker and binds no explicit world size/rank strategy;
- existing reports/checkpoints are not yet topology/strategy-aware;
- deterministic Kaggle control-plane tests already prove private bundle/CLI/output integrity without live provider access and must remain offline.

Planning invariants:

- two T4s remain two distinct devices; no 32 GiB pooled-VRAM claim;
- per-device resource admission is fail closed;
- `single_gpu` remains an explicit baseline;
- only `replicated_data_parallel` across exactly two verified devices is reserved as the V2.4 multi-GPU intent;
- replicated data parallel improves throughput semantics only and does not create sharded model memory;
- no FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism or TPU is authorized;
- topology/strategy/world-size/device ordinals/effective batch must become exact lineage;
- distributed launch remains repository-owned and typed; prompt/project/model text cannot become launcher argv/env/rendezvous/package installs;
- KillSwitch/ProcessSandbox must terminate the complete worker group;
- live Kaggle production qualification is separate from deterministic CI and must be honestly unavailable when auth/network/quota is absent;
- V2.5+, release/TUF/updater mutation and R20 reopening remain unauthorized.

Planning PR `#516` completed **25/25** exact-head workflows on final head `8c78ff19cf05b3009a05e2e5337ce31303e9d8b7`, including R0 Repository Guard run `35535395734`, KodeStudio UI Smoke run `35535395763`, Python Core run `35535395830`, R13 Integrated Release Readiness run `35535395854` and R17 Windows Installer run `35535395721`. It merged with `expected_head_sha` protection as `a14190f529a465e8e42ee0dd90a0248bc38e1b9c`.

The initial planning head `7142659d00cea3ae6faf427ed100fb84ce28668e` failed only two historical V2.3.5 acceptance assertions after the authority wording advanced to V2.4 planning. Corrective commit `8c78ff19cf05b3009a05e2e5337ce31303e9d8b7` made the V2.3.5/V2.3.6 authority checks forward-compatible and fixed the duplicated `NEXT.md` heading; no runtime product code, security boundary, workflow criterion or product gate was weakened.

This post-merge normalization records **V2.4 planning COMPLETE + NORMALIZED** and authorizes **V2.4.1 — Accelerator topology and provider truth only**. V2.4.2+ remain unauthorized until V2.4.1 is implemented, exact-head qualified, merged and post-merge normalized.

## V2.4.1 — Accelerator topology and provider truth — COMPLETE + NORMALIZED

Implementation PR:

`#518 — feat: implement V2.4.1 accelerator topology truth`

Exact final accepted head:

`544b7d172499594f32c464c46753bfc5fb378fe0`

Base:

`96c95116be0e863c364e94dc96a69c6880deb9cc`

Qualification:

- **30/30** pull-request workflows `completed/success` on the unchanged exact head;
- V2.4.1 deterministic acceptance **22/22 PASS Ubuntu**;
- V2.4.1 deterministic acceptance **22/22 PASS Windows**;
- identical evidence payload SHA-256 on both OS: `3049f1d4fb07d8edb4d8722ffaf1a1d8e503186972eec2dfb000a5057f519c6d`;
- Ubuntu artifact: `v2-4-1-accelerator-topology-ubuntu-latest-544b7d172499594f32c464c46753bfc5fb378fe0`, artifact ID `10614179278`;
- Windows artifact: `v2-4-1-accelerator-topology-windows-latest-544b7d172499594f32c464c46753bfc5fb378fe0`, artifact ID `10614546908`;
- selected successful runs include R0 `35540624489`, R15.8 Training Runtime `35540624402`, R15 Kaggle Remote Training `35540624433`, R15.9 QLoRA SFT `35540624448`, Python Core `35540624471`, R15 Integrated `35540624649`, R13 Integrated Release Readiness `35540624507`, R17 Windows Installer `35540624572`.

Merge:

`3ebed48b8aa113635ddc9516827d867ce346fe0f`

Accepted product truth:

- historical R15.8 capability schema/version 1 remains intact;
- a separate `kodepoia.v2.4.1.accelerator-topology` report owns topology evidence;
- runtime probe enumerates actual CUDA/ROCm device count and bounded per-device ordinal/name/free/total VRAM;
- legacy scalar `device` and VRAM fields remain bound to device 0 for historical compatibility;
- Kaggle `NvidiaTeslaT4` is an explicit provider request for two CUDA T4-class devices, never runtime proof;
- provider request digest and observed topology digest are separate;
- duplicate/missing/non-contiguous device identity and provider/runtime count/name mismatches fail closed;
- `single_gpu` selection binds one verified device and uses only that device's VRAM budget;
- unknown selected-device VRAM blocks;
- no aggregate/pseudo-32-GiB pool exists;
- ProcessSandbox/fixed argv/empty-env probing remains authoritative;
- no distributed launch, `replicated_data_parallel`, torchrun, DDP, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism or TPU was introduced;
- required CI remains deterministic and needs no live Kaggle/GPU/provider quota.

This post-merge normalization marks **V2.4.1 COMPLETE + NORMALIZED**.

## V2.4.2 — Strategy, effective-batch and resource planning contract — COMPLETE + NORMALIZED

Implementation PR:

`#520 — feat: implement V2.4.2 strategy planning contract`

Exact final accepted head:

`abf9d396ef4f2800c5e9de9bd62a9b680a2be758`

Base:

`5ab7947c13c6bd38d005cd07dd9d879a694e0207`

Qualification:

- **29/29** pull-request workflows `completed/success` on the unchanged exact head;
- deterministic acceptance **23/23 PASS Ubuntu**;
- deterministic acceptance **23/23 PASS Windows**;
- identical evidence payload SHA-256: `f10a620c34ea3928ce6de4e44002485120654c031d6073bbf00f5f3bddf68ffa`;
- Ubuntu artifact: `v2-4-2-strategy-planning-ubuntu-latest-abf9d396ef4f2800c5e9de9bd62a9b680a2be758`, artifact ID `10620663114`;
- Windows artifact: `v2-4-2-strategy-planning-windows-latest-abf9d396ef4f2800c5e9de9bd62a9b680a2be758`, artifact ID `10620827996`;
- selected successful runs include R0 `35557259551`, R15.8 Training Runtime `35557259491`, R15.9 QLoRA SFT `35557259534`, Python Core `35557259581`, R15 Integrated `35557259570`, R13 Integrated Release Readiness `35557259591`, and R17 Windows Installer `35557259506`.

Merge:

`4d411df6b0923b1443017ff25f06b1c04453a7f6`

Accepted product truth:

- V2.4.2 adds a separate immutable execution-strategy planning contract and does not reinterpret historical R15.9 TrainingRunner execution;
- each strategy plan binds the exact TrainingPlan digest, topology report digest and observed topology digest;
- only `single_gpu` and `replicated_data_parallel` are accepted strategy intents;
- `single_gpu` binds world size 1 and an exact ordinal; replicated planning binds world size 2 and two exact ordinals;
- VRAM admission remains per-device and never pools two T4s into 32 GiB;
- host RAM/storage remain independent single-host budgets;
- per-device batch, gradient accumulation and effective global batch are explicit and digest-bound;
- paired plans must preserve the TrainingPlan effective global batch exactly or fail closed;
- deterministic rank/data seed policy is `offset_by_rank_v1`;
- paired benchmark evidence binds same plan/topology/config/work/effective-batch semantics and records independent per-device peak VRAM plus run/checkpoint integrity;
- normative repository policy requires at least **1.25x throughput speedup** and permits **0.0 eval-loss regression**;
- missing quality evidence is inconclusive rather than promotable;
- benchmark evidence has `launch_authorized=false` and cannot launch distributed workers;
- no `torchrun`, Accelerate two-rank execution, DDP worker launch, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism or TPU was introduced;
- mandatory CI remains deterministic and requires no live Kaggle/GPU/provider quota.

This post-merge normalization marks **V2.4.2 COMPLETE + NORMALIZED**.

## V2.4.3 — Governed explicit two-GPU execution — COMPLETE + NORMALIZED

Implementation PR:

`#522 — feat: implement V2.4.3 governed two-GPU execution`

Exact final accepted head:

`81c5709ff457da375fd2f8f8ef13aad4b59aced0`

Base:

`6d58881ee92b4b00b365847ca482e951dcdeee46`

Qualification:

- **30/30** pull-request workflows `completed/success` on the unchanged exact head;
- deterministic acceptance **22/22 PASS Ubuntu**;
- deterministic acceptance **22/22 PASS Windows**;
- identical evidence payload SHA-256: `fbcad387a86924c1ed7384b4408e2910c63c550f6dd9283e7c020b03b8ffbbc7`;
- Ubuntu artifact: `v2-4-3-distributed-execution-ubuntu-latest-81c5709ff457da375fd2f8f8ef13aad4b59aced0`, artifact ID `10646496287`;
- Windows artifact: `v2-4-3-distributed-execution-windows-latest-81c5709ff457da375fd2f8f8ef13aad4b59aced0`, artifact ID `10646575915`;
- selected successful runs include R0 `35614891252`, R15.8 Training Runtime `35614891434`, R15.9 QLoRA SFT `35614891273`, Python Core `35614891412`, R15 Integrated `35614891265`, R13 Integrated Release Readiness `35614891015`, R13 Android Signing `35614891044` and R17 Windows Installer `35614891251`;
- R13 Android Signing Windows required one failed-job rerun on the **same SHA**; Ubuntu remained successful, no source/workflow/criterion changed, and the rerun succeeded.

Merge:

`975d46a071f52a27a48de15227432d9d4911e142`

Accepted product truth:

- distributed execution requires governed `TRAIN` authorization, real SFT/QLoRA mode, explicit governed dataset paths, an accepted `replicated_data_parallel` strategy and exact qualified V2.4.2 benchmark evidence;
- execution plan binds TrainingPlan, strategy plan, benchmark report, topology report and topology digests;
- launch policy is fixed to one node, exactly two ranks, no restarts, and repository-owned `kodepoia.tuning.distributed_worker`;
- only accepted `CUDA_VISIBLE_DEVICES` is injected; callers cannot provide launcher argv/env/rendezvous settings;
- rank/local-rank/world-size/restart state is read from trusted launcher state and validated fail closed;
- rank RNG/data seed and the shared sampler seed are bound to accepted strategy lineage;
- only rank zero may emit canonical R15.9 output; per-rank evidence is subordinate and integrity-bound;
- nonzero launcher exit, timeout, cancellation, missing rank or mismatched rank evidence prevents partial success;
- ProcessSandbox registers a managed process group with KillSwitch and terminates the whole group on timeout/cancellation;
- V2.4.3 reuses the accepted R15.9 real worker implementation rather than introducing a parallel training engine;
- `resume_authorized=false`: distributed checkpoint/recovery remains outside V2.4.3;
- no sharded-memory strategy, pooled VRAM or TPU path was introduced;
- required CI remains deterministic and needs no live Kaggle/GPU/provider quota.

This post-merge normalization marks **V2.4.3 COMPLETE + NORMALIZED**.

## V2.4.4 — Distributed checkpoint, cancellation and recovery — COMPLETE + NORMALIZED

Implementation PR:

`#524 — feat: implement V2.4.4 distributed checkpoint recovery`

Exact final accepted head:

`1abf4917566f065ac26b71a02e02d8fb3506fe1a`

Base:

`fb3f3f5f18834183524f5a61c29b572cdb79b5db`

Qualification:

- **29/29** pull-request workflows `completed/success` on the unchanged exact head;
- deterministic acceptance **25/25 PASS Ubuntu**;
- deterministic acceptance **25/25 PASS Windows**;
- identical evidence payload SHA-256: `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`;
- Ubuntu artifact: `v2-4-4-distributed-recovery-ubuntu-latest-1abf4917566f065ac26b71a02e02d8fb3506fe1a`, artifact ID `10654524114`;
- Windows artifact: `v2-4-4-distributed-recovery-windows-latest-1abf4917566f065ac26b71a02e02d8fb3506fe1a`, artifact ID `10655573341`;
- selected successful runs include R0 `35633506877`, R15.8 Training Runtime `35633506917`, R15.9 QLoRA SFT `35633506716`, Python Core `35633506815`, R15 Integrated `35633506982`, R13 Integrated Release Readiness `35633506771`, and R17 Windows Installer `35633506891`.

Merge:

`779a9c8282e153b7dba35fb22be89ec5c622e1d3`

Accepted product truth:

- checkpoint manifests derive from a completed exact-lineage V2.4.3 distributed report, rank-zero canonical worker output and both rank evidences;
- exact execution plan, TrainingPlan, strategy, qualified benchmark, topology, world size and device ordinals remain immutable recovery lineage;
- checkpoint metadata and adapter artifact are independently digest-verified;
- only checkpoints strictly before declared max steps are resumable;
- recovery uses the same fixed one-node/two-rank repository-owned `torch.distributed.run` boundary and accepted R15.9 resume semantics;
- recovery injects only accepted `CUDA_VISIBLE_DEVICES` and exposes no caller argv/env/rendezvous/package-install surface;
- each resumed rank emits checkpoint-manifest/recovery-plan/resumed-step evidence;
- completed recovery requires both rank evidences and every rank completed;
- timeout, cancellation, nonzero exit, missing rank evidence, tampered checkpoint/manifest or changed topology/strategy/world-size lineage is terminal for the whole group;
- historical V2.4.3 `resume_authorized=false` remains preserved; V2.4.4 uses a separate explicit recovery plan with `resume_authorized=true`;
- no pooled VRAM, sharded-memory strategy, TPU or live Kaggle/Model Lab qualification was introduced;
- mandatory CI remains deterministic and requires no live Kaggle/GPU/provider quota.

This post-merge normalization marks **V2.4.4 COMPLETE + NORMALIZED**.

## V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — CURRENT

Authorized scope is strictly accelerator UX plus exact-source live provider qualification:

- structured Model Lab display of requested provider shape versus observed topology;
- separate device rows and per-device VRAM, never a summed 32 GiB pool;
- explicit strategy selector/status with `single_gpu` versus `replicated_data_parallel`;
- effective batch, world size and exact device mapping visible before launch;
- exact V2.4.1-V2.4.4 lineage and live-evidence status visible;
- honest auth/network/quota/provider-unavailable states;
- no automatic provider calls at application startup;
- exact-source live Kaggle qualification workflow with private bundle/kernel and downloaded evidence revalidation;
- paired single-vs-replicated live run evidence bound to the exact source;
- FR/EN/qps-ploc and accessibility;
- deterministic PR CI for all non-provider-dependent logic;
- live qualification may require operator Kaggle credentials/quota; if so, stop in V2.4.5 and request only the exact bounded operator action.

Bounded V2.4.5 live-qualification workload bootstrap amendment (authorized 2026-09-22):

- this amendment stays inside V2.4.5 and does not add, split, renumber or authorize any later subdivision;
- it exists only because exact-source live qualification requires immutable model/tokenizer/dataset/`TRAIN`/capability lineage and no such eligible lineage is present in the operator's product-recognized R15 evidence stores;
- the bootstrap must reuse the accepted R15.5/R15.7/R15.8/R15.9 and V2.4.1-V2.4.4 primitives; it may not create a parallel dataset, benchmark, decision, training, topology, strategy, execution or recovery engine;
- the qualification corpus must be repository-owned, purpose-built and isolated from user projects; Project Knowledge, Research Packs, chat, memory, retrieved context, arbitrary project files and CI fixtures remain ineligible as authority or training input;
- the only pre-authorized external base-model candidate is `TinyLlama/TinyLlama-1.1B-Chat-v1.0` at immutable revision `fe8a4ea1ffedaf415f4da2f062534de366a451e6`, with Apache-2.0 licence evidence revalidated when the bootstrap is materialized; model/tokenizer content digests must be measured and bound before any `TRAIN` decision;
- a repository-owned before-benchmark, immutable governed dataset, R15.8 capability report and R15.7 gap decision must be produced from real evidence; if R15.7 does not return `TRAIN`, or any licence/provenance/contamination/capability/budget/rollback gate fails, the bootstrap stops and V2.4.5 remains not production-qualified;
- any resulting `TrainingPlan` is qualification-only, exact-source and non-promotable; it cannot modify ModelRouter, the specialized-model registry, Ollama roles or any public model/dataset registry;
- paired `single_gpu` and `replicated_data_parallel` live runs must use the same accepted model/tokenizer/dataset/evaluation configuration and effective global batch, and remain subject to the existing >=1.25x throughput threshold, zero eval-loss regression allowance, critical-regression veto, run/checkpoint integrity and downloaded-evidence revalidation;
- the topology probe remains private with Internet disabled; later private training kernels may use only the already accepted Kaggle/R15 dependency and exact pinned-model download path, with no arbitrary shell/argv/env/package-install surface;
- deterministic CI remains provider-independent; real Kaggle account/quota actions remain explicit operator actions;
- nothing in this amendment authorizes V2.4.6, V2.5+, release/TUF/updater mutation, public publishing, pooled VRAM, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, R20 reopening or R20.7.

Bounded V2.4.5 R15.8 CUDA subprocess-environment repair amendment (authorized 2026-09-24):

- this amendment stays strictly inside V2.4.5; it authorizes one repair-and-requalification cycle for the accepted R15.8 capability path and does not authorize V2.4.6 or any later subdivision;
- the triggering live evidence is exact-source head `6f6dce852177ab563fba442234d6917e64d0bdee`: its private provider probe observed CUDA with two distinct Tesla T4 devices and topology digest `8a8e514a43c919a762b40dd4f973b7cb36c1dea7ed051124b399b82d1d52a025`, while its governed bootstrap completed and downloaded evidence revalidated successfully;
- on that same exact source, R15.8 capability evidence digest `f2fbc3ee4e8a0a14fd62a944d8cb20a9fc1025b70dde653f959256ef53f0aee1` failed closed as `backend_capability=unsupported` with blocker `backend_unavailable`, `device=null`, unknown VRAM and no dtype/four-bit/model-load result; R15.7 decision digest `0d24431e885c0bb4cdba648b5774dd02fb089b1509ce98348a6530f0c203b5fa` therefore returned `unsupported`, `train_authorized=false` and no `TrainingPlan`;
- live source inspection demonstrates a bounded propagation defect: the R15.8 worker is launched through `ProcessSandbox` with a replacement environment whose base allowlist omits provider CUDA/NVIDIA runtime variables even though the enclosing Kaggle kernel exposes both T4 devices; this amendment authorizes repairing only that R15.8/tuning subprocess boundary;
- the repair must keep the global `ProcessSandbox` base environment policy unchanged and must not broaden arbitrary subprocess environment inheritance; the tuning capability path may copy from its already-trusted parent process only this fixed non-secret allowlist when present: `LD_LIBRARY_PATH`, `CUDA_VISIBLE_DEVICES`, `CUDA_DEVICE_ORDER`, `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`;
- those values must originate only from the provider/runtime parent environment, with exact fixed variable names; user text, model output, project files, Research Packs, Project Knowledge, chat, memory, retrieved context and caller-supplied arbitrary names/values cannot become environment variables;
- no wildcard/prefix environment passthrough, shell surface, caller-controlled argv, rendezvous setting, package-install request or credential propagation is authorized; Kaggle/Hugging Face secrets remain outside reports/bundles and outside the newly permitted environment set;
- deterministic tests must prove the fixed allowlist, prove absent variables remain absent, prove non-allowlisted and secret-like variables are not forwarded, preserve `shell=False`, and prove the global sandbox allowlist is unchanged;
- every implementation commit creates a new exact source SHA and makes all probe/bootstrap/R15.7 evidence from `6f6dce852177ab563fba442234d6917e64d0bdee` historical only; the full exact-head PR workflow set and Ubuntu/Windows V2.4.5 acceptance must be requalified before new live provider evidence is accepted;
- after deterministic qualification, the private T4×2 provider probe, governed bootstrap, downloaded capability evidence and R15.7 decision must all be recreated from the new exact head; the old `unsupported` decision is never edited, overridden or treated as success;
- the repaired R15.8 evidence must still fail closed unless it actually proves the accepted CUDA backend/device/resource/dtype/four-bit/model-load gates; unknown VRAM or any capability blocker remains terminal;
- only if the newly calculated R15.7 decision returns real `TRAIN` may a new qualification-only, non-promotable `TrainingPlan` be created and the paired `single_gpu` / `replicated_data_parallel` live qualification continue; if R15.7 again returns anything other than `TRAIN`, V2.4.5 stops again;
- all existing >=1.25x replicated-throughput, zero eval-loss regression, critical-regression veto, run/checkpoint integrity, exact-lineage, no-pooled-VRAM and downloaded-evidence gates remain unchanged;
- this amendment does not authorize public publishing, ModelRouter/registry/Ollama mutation, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, release/TUF/updater changes, V2.5+, R20 reopening or R20.7.

Bounded V2.4.5 R15.8 local-snapshot model-load dry-run repair amendment (authorized 2026-09-24):

- this amendment remains strictly inside V2.4.5 and authorizes one repair-and-requalification cycle for the R15.8 `model_load_dry_run_failed` blocker observed only after the CUDA subprocess-environment repair succeeded; it does not authorize V2.4.6 or any later subdivision;
- the triggering exact-source head is `a9de7a74a640d1fb33f8fbfbd27932b3cc087204`; its private provider probe was `ready` on two distinct Tesla T4 devices, its governed bootstrap completed and downloaded evidence revalidated, and R15.8 proved `backend_capability=supported`, concrete CUDA device/VRAM, `dtype_supported=true` and `four_bit_supported=true`;
- the same R15.8 report digest `666b5274931550e1c9f1680c92e6095d61755b5d4231e370523a4123d6bec291` failed closed only on `model_load=unsupported` with blocker `model_load_dry_run_failed`; R15.7 decision digest `2af56cac2256f6a3ebe6bbbd60da3837a5f7be1e17a81785d2abbcfb985373f2` therefore returned `unsupported`, `train_authorized=false` and no `TrainingPlan`;
- source inspection shows the bootstrap already downloads the authorized TinyLlama snapshot at immutable revision `fe8a4ea1ffedaf415f4da2f062534de366a451e6`, validates the required files and pinned `model.safetensors` SHA-256, and successfully loads that exact local snapshot for the before-benchmark; the separate R15.8 model-load worker instead receives the remote model/tokenizer identifiers and calls `from_pretrained(..., local_files_only=True)`, which can fail if the subprocess cannot resolve the parent process's Hugging Face cache location;
- the authorized repair is to stage only the already downloaded, already validated required snapshot files into a fixed runtime-owned directory under the bootstrap working root, then bind the R15.8 dry-run to one fixed safe relative local identifier for that directory; the public model/tokenizer identity, immutable revision and measured content digests remain the authoritative lineage and must not be replaced by the local directory name;
- the staged files must be copied from the exact validated snapshot only after the existing required-file/hash checks succeed; missing, unexpected, tampered or hash-mismatched required files must fail closed before R15.8;
- the R15.8 worker must keep `local_files_only=True` and `trust_remote_code=False`; no network lookup, remote fallback, arbitrary cache lookup, dynamic repo/path discovery or caller-controlled filesystem path is authorized;
- this amendment does not authorize forwarding `HF_HOME`, `HF_HUB_CACHE`, `HF_TOKEN`, `HUGGINGFACE_HUB_CACHE` or any other Hugging Face credential/cache environment variable into the sandbox; the CUDA/NVIDIA environment allowlist authorized by the prior amendment remains unchanged;
- no absolute path, `..`, symlink escape, wildcard/prefix path selection, shell surface, caller-controlled argv/env/rendezvous/package-install surface or credential propagation is authorized; the staging path and relative identifier must be repository/runtime constants;
- deterministic tests must prove exact-file staging, fixed local identifier binding, rejection of tampered/missing files and path escape, preservation of `local_files_only=True` / `trust_remote_code=False`, unchanged CUDA env allowlist and unchanged global `ProcessSandbox` base policy;
- every implementation commit creates a new exact source SHA and makes all probe/bootstrap/R15.7 evidence from `a9de7a74a640d1fb33f8fbfbd27932b3cc087204` historical only; the full exact-head PR workflow set and Ubuntu/Windows V2.4.5 acceptance must be requalified before new live evidence is accepted;
- after deterministic qualification, the private T4×2 probe, governed bootstrap, downloaded capability evidence and R15.7 decision must all be recreated from the new exact head; the old `unsupported` decision is never edited, overridden or treated as success;
- only if the newly calculated R15.8 evidence actually proves all accepted CUDA/device/resource/dtype/four-bit/model-load gates and the newly calculated R15.7 decision returns real `TRAIN` may the qualification-only non-promotable `TrainingPlan` and paired live `single_gpu` / `replicated_data_parallel` qualification continue; otherwise V2.4.5 stops again;
- all existing >=1.25x replicated-throughput, zero eval-loss regression, critical-regression veto, run/checkpoint integrity, exact-lineage, no-pooled-VRAM and downloaded-evidence gates remain unchanged;
- this amendment does not authorize public publishing, ModelRouter/registry/Ollama mutation, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, release/TUF/updater changes, V2.5+, R20 reopening or R20.7.

Bounded V2.4.5 TrainingPlan safe-path materialization repair amendment (authorized 2026-09-24):

- this amendment remains strictly inside V2.4.5 and authorizes one repair-and-requalification cycle for the TrainingPlan materialization defect observed only after the local-snapshot R15.8 repair succeeded and the newly calculated R15.7 decision returned real `TRAIN`; it does not authorize V2.4.6 or any later subdivision;
- the triggering exact-source head is `d86eb3e7975a501cbd8fe396e2ed133f6ecb5102`; deterministic qualification completed `20/20 PASS` on Ubuntu and `20/20 PASS` on Windows with common evidence SHA-256 `05d85ab3463c5f3cd6be9c04e9d3193e4872941ccacad4475bd6ba392f21b89b`, and all `31/31` pull-request workflows completed successfully;
- its private bootstrap used dataset `laurent1985/kodepoia-v245-bootstrap-data-d86eb3e7` version 1 and kernel `laurent1985/kodepoia-v245-bootstrap-d86eb3e7` version 1, which reached `KernelWorkerStatus.COMPLETE`; downloaded bootstrap evidence SHA-256 `66e0d97fc358e945de5f26892b769bb86cabe0d9ca4c645ce3f577c01d560fed` revalidated against request digest `196fbe3400301aacb84d050e9fac55c417ef6836e072dab447b79fc214277549`;
- on that exact source, R15.8 capability report digest `0cc84f01f634d34a173bd2f30e594267ab065ca1b022851b61a931a2bf333827` is `ready` with `backend=cuda`, concrete Tesla T4 device/VRAM, `dtype_supported=true`, `four_bit_supported=true`, `model_load=supported` and `blockers=[]`; the prior `model_load_dry_run_failed` blocker is historical for this source;
- the same exact-source R15.7 evaluation returned real `TRAIN` with decision digest `0ec67e57adbf70c2df969b5848fd827876b2237774d355735e58b68a49a6e946`, `blockers=[]`, and serialized `gap-decision.json` SHA-256 `99f6d0e1dc0bfa80f099f5d0a75c4304c06677f18e1e8cf85397d9befdc26b74`; this historical decision must never be edited, overridden or recreated as forced TRAIN;
- no `training-plan.json` or `bootstrap-result.json` was produced on `d86eb3e7` because TrainingPlan materialization failed after the real TRAIN decision when `DatasetBinding` rejected a repository-relative governed export path beginning with `.kodepoia/` as not matching the existing bounded safe-identifier contract;
- the authorized repair is limited to binding the already governed and digest-verified train/validation exports through fixed repository/runtime-owned relative identifiers that begin with an alphanumeric character and already satisfy the existing R15.9 safe-reference contract; implementation may stage exact copies into one fixed qualification-runtime location only after source digests are revalidated and staged digests are proven identical;
- `_SAFE_REF` and all existing R15.9 path validation must remain unchanged and must not be broadened or weakened; no absolute path, `..`, symlink escape, wildcard/prefix selection, dynamic path discovery, caller-controlled path, user/project/model-controlled path, shell, argv, environment, rendezvous, package-install or credential surface is authorized;
- the repaired binding must preserve exactly the governed dataset identity, manifest digest, train export digest, validation export digest, split semantics, model/tokenizer identity and revision, workload, contamination/protection/dedup lineage, R15.8 capability requirements and R15.7 decision policy; it must not change the corpus, split, model, tokenizer, benchmark or decision criteria;
- deterministic tests must cover the actual `TRAIN` branch of `finalize_live_bootstrap()` and prove successful TrainingPlan creation with safe distinct confined train/validation identifiers whose bytes match the governed export digests; negative coverage must reject absolute paths, `..`, symlink escape, pre-existing/tampered staged exports and digest divergence;
- every implementation commit creates a new exact source SHA and makes all provider/bootstrap/R15.8/R15.7 evidence from `d86eb3e7975a501cbd8fe396e2ed133f6ecb5102` historical only; the full exact-head PR workflow set and Ubuntu/Windows V2.4.5 acceptance must be requalified before any new live provider evidence is accepted;
- no dataset/kernel from `d86eb3e7` may be modified, versioned or rerun for the repaired head; new exact-head private dataset/kernel IDs are required for the next live bootstrap;
- after deterministic qualification, the private T4×2 probe, governed bootstrap, downloaded R15.8 evidence and R15.7 decision must all be recreated from the new exact head; only if the new R15.8 is accepted, the new R15.7 returns real `TRAIN`, and a qualification-only non-promotable TrainingPlan is successfully materialized may the paired live `single_gpu` / `replicated_data_parallel` qualification continue;
- all existing >=1.25x replicated-throughput, zero eval-loss regression, critical-regression veto, run/checkpoint integrity, exact-lineage, no-pooled-VRAM and downloaded-evidence gates remain unchanged;
- this amendment does not authorize V2.4.6, V2.5+, public publishing, ModelRouter/registry/Ollama mutation, pooled VRAM, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, release/TUF/updater changes, R20 reopening or R20.7.

Bounded V2.4.5 qualification-only initial replicated live-run amendment (authorized 2026-09-25):

- this amendment remains strictly inside V2.4.5 and authorizes only the bounded repair-and-requalification cycle needed to break the initial live-pair authorization cycle; it does not authorize V2.4.6 or any later subdivision;
- the triggering exact-source head is `7d0fe50f60f041ae6220f28e5b486e396ed2ec2e`; PR `#529` is qualified with all `31/31` pull-request workflows successful and deterministic V2.4.5 acceptance `20/20 PASS` on Ubuntu plus `20/20 PASS` on Windows with common evidence SHA-256 `9d6167d740758f1094592118b6920079cc0ec0d63fb5504ef7781efc5e1e6230`;
- its private provider probe is `laurent1985/kodepoia-v2-4-5-live-7d0fe50f`, which proved two distinct Tesla T4 CUDA devices, topology disposition `ready` and no topology blockers; its private bootstrap dataset `laurent1985/kodepoia-v245-bootstrap-data-7d0fe50f` version 1 and private bootstrap kernel `laurent1985/kodepoia-v245-bootstrap-7d0fe50f` version 1 completed without creating a second version;
- the exact bootstrap request digest is `cf0e3dcd82b6adc105a55d7be49eca24b5b86782c44da41ef5184ea4517cf2a5`; downloaded bootstrap evidence SHA-256 is `b7339c128578b0eaa1a20952341f121c95a07167272821a575e3ffb237dc5598`; R15.8 capability report digest `952ad943ba320871438d781ad7872245c896abe4d63b945f89fa65cd13215ee5` is `ready` with CUDA/T4, supported dtype/four-bit/model-load and `blockers=[]`;
- the exact R15.7 evaluation returned real `TRAIN` with decision digest `ff0e711b676b46d544b71221335f369a859c07c01853837ed5327eb57d9fc181`, `blockers=[]`; TrainingPlan digest `92dd6a8d5d3e3905f03f48110afa772efdcc6ba1d85ef9173835953a616f048a` is qualification-only and non-promotable, and bootstrap result digest is `a3eb430f89dcfbf4dfffcb75426f618f05e7490df4664f3b654459a6f42848a0`;
- source inspection identifies the remaining authorization cycle: the accepted V2.4.3 distributed launch path requires an exact `StrategyBenchmarkReport` whose disposition is already `QUALIFIED`, while the real `replicated_data_parallel` measurement needed to calculate that benchmark cannot exist until the initial replicated candidate has executed; no existing repository-owned pre-qualification launch path resolves this cycle;
- the only authorized change is a typed, explicit, exact-lineage `qualification-only` permit for the initial replicated live candidate measurement; this permit must never be represented as a `StrategyBenchmarkReport QUALIFIED`, must never set or imply `production_qualified=true`, and must remain non-promotable;
- the provisional qualification path must reuse the existing `DistributedTrainingRunner`, `distributed_worker`, repository-owned fixed `torch.distributed.run` launch, exactly two ranks, ProcessSandbox/KillSwitch boundary, rank/local-rank/world-size/device-ordinal checks, deterministic seed/sampler semantics, canonical rank-zero authority and accepted R15.9 worker validation; no second distributed engine or independent raw `torchrun` path is authorized;
- the permit must bind the exact source SHA, exact TrainingPlan digest, exact ready topology report/topology digests, exact `replicated_data_parallel` strategy plan, world size 2 and device ordinals `(0, 1)`; any mismatch must fail closed before launch;
- this provisional path is eligible only after a private T4×2 provider probe is `ready`, R15.8 is accepted, R15.7 has returned real `TRAIN`, and the exact TrainingPlan is qualification-only and non-promotable; it cannot be reused as a normal production launch bypass;
- the normal V2.4.3 `build_distributed_execution_plan()` benchmark gate must remain unchanged for ordinary/product execution; no general weakening from `StrategyBenchmarkDisposition.QUALIFIED` is authorized;
- the live `single_gpu` baseline and provisional replicated candidate must use the same accepted model/tokenizer identity and revision, dataset and train/validation export digests, optimization/training policy, max steps, evaluation cadence, quantization, benchmark configuration and effective global batch semantics;
- after both live outputs are downloaded and revalidated, Kodepoia must construct the real `StrategyBenchmarkMeasurement` values from those outputs and call the existing `evaluate_strategy_benchmark(...)`; no fixture, fabricated timing, copied historical measurement or forced disposition may substitute for the live measurements;
- the replicated strategy becomes accepted only if the real benchmark returns `QUALIFIED`, including replicated throughput >=1.25x the single-GPU baseline, zero allowed eval-loss regression, valid per-device VRAM evidence, run integrity and checkpoint integrity;
- final V2.4.5 qualification must still pass the critical-regression veto, exact-source/model/tokenizer/dataset/topology/strategy lineage, genuine two-rank evidence, secret scan, downloaded-evidence revalidation and all existing `validate_live_evidence(...)` gates before `production_qualified=true` is possible;
- deterministic tests must prove the provisional permit is qualification-only/non-promotable, exact-source/TrainingPlan/topology/strategy bound, limited to world size 2 and ordinals `(0, 1)`, rejected on lineage or prerequisite mismatch, unable to serialize as a qualified benchmark or production qualification, and unable to weaken the ordinary V2.4.3 benchmark requirement;
- every implementation commit creates a new exact source SHA and makes all provider/probe/bootstrap/R15.8/R15.7/TrainingPlan evidence from `7d0fe50f60f041ae6220f28e5b486e396ed2ec2e` historical only; the full exact-head workflow set and Ubuntu/Windows V2.4.5 acceptance must be requalified before any new live evidence is accepted;
- no dataset or kernel from `7d0fe50f` may be modified, versioned or rerun for the repaired head; all subsequent provider probe, bootstrap and live-pair Kaggle IDs must be new exact-head IDs;
- this amendment does not authorize benchmark fixtures as live evidence, forced TRAIN, pooled VRAM, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, arbitrary shell/argv/env/rendezvous/package-install surfaces, public publishing, ModelRouter/registry/Ollama mutation, release/TUF/updater changes, V2.4.6+, V2.5+, R20 reopening or R20.7.




Bounded V2.4.5 qualification-only live-pair bootstrap amendment (authorized 2026-09-25):

- this amendment remains strictly inside V2.4.5 and authorizes only the repair of the live-pair authorization cycle discovered after exact-source head `7d0fe50f60f041ae6220f28e5b486e396ed2ec2e` reached a real qualification-only TrainingPlan; it does not authorize V2.4.6 or any later subdivision;
- triggering exact-head deterministic evidence remains historical once implementation begins: PR #529 had all `31/31` pull-request workflows successful, V2.4.5 acceptance was `20/20 PASS` on Ubuntu and Windows with common digest `9d6167d740758f1094592118b6920079cc0ec0d63fb5504ef7781efc5e1e6230`;
- exact-head live provider evidence remains historical: private probe `laurent1985/kodepoia-v2-4-5-live-7d0fe50f` proved two distinct Tesla T4 devices, ready topology and no blockers;
- exact-head bootstrap evidence remains historical: private dataset `laurent1985/kodepoia-v245-bootstrap-data-7d0fe50f` version 1, private kernel `laurent1985/kodepoia-v245-bootstrap-7d0fe50f` version 1, request digest `cf0e3dcd82b6adc105a55d7be49eca24b5b86782c44da41ef5184ea4517cf2a5`, downloaded evidence SHA-256 `b7339c128578b0eaa1a20952341f121c95a07167272821a575e3ffb237dc5598`;
- exact-head R15.8 capability report digest `952ad943ba320871438d781ad7872245c896abe4d63b945f89fa65cd13215ee5` was `ready` with CUDA/T4, dtype/four-bit/model-load supported and blockers=[]; exact-head R15.7 decision digest `ff0e711b676b46d544b71221335f369a859c07c01853837ed5327eb57d9fc181` returned real `TRAIN` with blockers=[];
- exact-head TrainingPlan digest `92dd6a8d5d3e3905f03f48110afa772efdcc6ba1d85ef9173835953a616f048a` was successfully materialized as qualification-only and non-promotable, and bootstrap result digest was `a3eb430f89dcfbf4dfffcb75426f618f05e7490df4664f3b654459a6f42848a0`;
- the blocker is strictly the V2.4.3 launch cycle: normal replicated launch requires a `StrategyBenchmarkReport` already `QUALIFIED`, while the real live replicated measurement required to produce that exact benchmark cannot exist until the candidate has executed;
- the authorized repair is one explicit typed qualification-only launch permit for the initial V2.4.5 replicated candidate; it must bind exact source SHA, TrainingPlan digest, topology report/digest, strategy plan digest, two device ordinals, world size 2 and non-promotable qualification intent;
- this permit must never be serialized or interpreted as a `StrategyBenchmarkReport QUALIFIED`, must never set `production_qualified=true`, and cannot authorize a normal/product launch;
- the qualification-only path must reuse the existing `DistributedTrainingRunner`, `distributed_worker`, repository-owned `torch.distributed.run` boundary, exactly two ranks, ProcessSandbox/KillSwitch, rank/local-rank/world-size/device checks, seeds/sampler semantics and R15.9 validation; no second distributed engine or raw torchrun path is authorized;
- the existing `build_distributed_execution_plan()` qualified-benchmark requirement must remain unchanged for normal execution; any qualification-only bypass must be isolated to a separate typed constructor/entry point with fail-closed preconditions;
- qualification-only replicated launch is permitted only after ready two-T4 topology, accepted R15.8, real R15.7 TRAIN, materialized qualification-only/non-promotable TrainingPlan, and exact `replicated_data_parallel` strategy over ordinals `(0,1)`;
- the paired `single_gpu` and qualification-only replicated candidate must preserve exact model/tokenizer/dataset/train+validation exports, max steps, evaluation cadence, quantization, effective global batch, benchmark configuration and quality policy;
- downloaded results must be revalidated before constructing real `StrategyBenchmarkMeasurement` objects; the repository-owned `evaluate_strategy_benchmark(...)` must then calculate the real benchmark with the existing >=1.25x throughput threshold, zero eval-loss regression allowance and run/checkpoint/per-device-VRAM integrity gates;
- only a real resulting `StrategyBenchmarkReport QUALIFIED` may satisfy the benchmark lineage for subsequent accepted distributed evidence; no fixture, fabricated measurement or historical benchmark may substitute for the live pair;
- final V2.4.5 qualification still requires critical-regression veto, exact-source lineage, two-rank evidence, secret scan, downloaded-evidence revalidation and all `validate_live_evidence(...)` gates;
- every implementation commit creates a new exact source SHA and makes all live provider/bootstrap/R15.8/R15.7/TrainingPlan evidence from `7d0fe50f60f041ae6220f28e5b486e396ed2ec2e` historical only; full exact-head workflows, Ubuntu/Windows acceptance, private probe, private bootstrap, R15.8, R15.7 and TrainingPlan must be recreated before the live pair;
- no dataset/kernel from `7d0fe50f` may be modified, versioned or rerun; new exact-head IDs are mandatory;
- always forbidden: forced TRAIN, fixture/fabricated live benchmark, pooled VRAM, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU/XLA, arbitrary shell/argv/env/rendezvous/package-install surfaces, public publishing, ModelRouter/registry/Ollama mutation, release/TUF/updater mutation, V2.4.6+, V2.5+, R20 reopening or R20.7.

Still unauthorized:

- V2.4.6 production hardening/integrated acceptance;
- public provider/model-hub publishing;
- pooled VRAM or hidden strategy changes;
- FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism;
- TPU/XLA/JAX/PyTorch-XLA;
- V2.4.6+;
- V2.5+, release/TUF/updater mutation and R20 reopening.

V2.4.6+ remain unauthorized until V2.4.5 is implemented, exact-head qualified, merged with `expected_head_sha` protection and post-merge normalized.

## Accepted V2 capability truth

The runtime truth model distinguishes:

- capability provenance/classification: `public-validated`, `source-available`, `acceptance-proven`, `experimental`, `unavailable`;
- provider/runtime state: `ready`, `unavailable`, `auth-required`, `network-restricted`, `not-implemented`;
- accelerator state: `priority`, `available`, `experimental`, `deferred`, `unsupported`.

Presence on live `main` does not imply presence in public rc8. Acceptance proof is separately bound to exact source evidence.

## Accelerator authority

Kaggle **T4×2** remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. The GPUs remain two separate 16 GiB devices; no component may present them as a single 32 GiB pool.

TPU v5e-8 remains **deferred**. Do not create or claim a distinct XLA/JAX or PyTorch/XLA backend unless a concrete benchmark demonstrates a material advantage that justifies its own implementation and acceptance surface.

## Release/updater boundary

Roadmap V2 does not reserve a new public release version and authorizes no release/TUF mutation. The rc8 source/tag/installer/TUF and real-machine E2E authority remain documented in `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` and the release evidence. Post-rc8 source capabilities on `main` remain development capabilities until separately qualified for a future public release.

All accepted fail-closed invariants remain in force: exact source/artifact binding, TUF signature/threshold/rollback/version/expiry checks, exact target length/SHA-256, target-scoped Authenticode policy, installer identity verification, explicit user consent and no private signing material in Git/CI/public artifacts/chat.

## Resume rule

For future work:

1. re-fetch live `main`, `STATE.md`, `NEXT.md`, `KODEPOIA_CURRENT_AUTHORITY.md`, `KODEPOIA_ROADMAP_V2.md` and `V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md`;
2. verify V2.4.4 remains **COMPLETE + NORMALIZED** from PR `#524`, exact head `1abf4917566f065ac26b71a02e02d8fb3506fe1a`, **29/29** workflows, acceptance 25/25 on both OS, evidence digest `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed` and merge `779a9c8282e153b7dba35fb22be89ec5c622e1d3`;
3. implement **V2.4.5 — Model Lab accelerator UX and live Kaggle qualification only**;
4. preserve exact V2.4.1-V2.4.4 topology/strategy/execution/recovery lineage and per-device VRAM truth;
5. add deterministic UX/provider-state tests without live Kaggle/GPU requirements;
6. prepare exact-source private Kaggle qualification with downloaded evidence revalidation and paired single-vs-replicated live evidence;
7. if live Kaggle credentials/quota are required, stop only at V2.4.5 and request the exact bounded operator action;
8. merge only after all required deterministic workflows succeed on the unchanged exact head and required live evidence is accepted;
9. post-merge normalize before authorizing V2.4.6;
10. keep V2.4.6+, V2.5+, release/TUF/updater mutation, R20 reopening and R20.7 unauthorized.
