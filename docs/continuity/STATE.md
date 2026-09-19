# Kodepoia continuity state

Last synchronized: 2026-09-19 after V2.2.5 implementation PR `#498` merge and post-merge normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; V2.1 historical/current Research authority is `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`, and the normalized V2.2 authority is `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`.

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

## V2.2.6 authorization — CURRENT

V2.2.6 must implement only the normalized plan scope:

- adversarial cross-project retrieval attempts;
- tampered or quarantined memory plus replay/version-conflicting memory;
- tampered Research Pack or digest mismatch;
- stale/invalidated file and engine/tool version fingerprints;
- prompt-injection/source-instruction text inside Research Packs, files and memory;
- secret-bearing content;
- include/exclude override consistency;
- delete-derived versus source-delete separation;
- deterministic retrieval ordering and context budget truncation/omission;
- unavailable embedding capability and valid empty result;
- cancellation where applicable;
- KodeStudio explainability state;
- Chat/KodeCode/specialist consumption preserving traceability and trust;
- exact-head Ubuntu and Windows acceptance artifacts.

V2.2.6 must **not** pull forward V2.3+, V2.5 orchestration, release/TUF/updater changes or R20 reopening.

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

1. re-fetch live `main`, `STATE.md`, `NEXT.md`, `KODEPOIA_ROADMAP_V2.md` and `V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`;
2. verify V2.2.5 remains **COMPLETE + NORMALIZED** from implementation PR `#498`, exact head `d29d10e5456623d1b7063bb37386693c1eec625a`, merge `11479e63dc48c45f2ec97f9950430cf35c986e8c`, **31/31** exact-head workflows and **13/13 PASS** Ubuntu/Windows evidence `22a8a287c8eead8530d2289fb19b9595e8774f0809f28c71754384b914ea8144`;
3. the only authorized implementation is **V2.2.6 — Project Knowledge hardening and integrated acceptance**;
4. branch V2.2.6 from the exact normalized live `main`, implement only its frozen adversarial/integrated hardening scope, add deterministic exact-head Ubuntu+Windows evidence, re-fetch all PR workflows on the final head, merge only if every required gate succeeds, then normalize before any V2.3 work;
5. preserve immutable Research Pack provenance, V2.2.1 project scope, V2.2.2 retrieval bounds, V2.2.3 context trust/budget/traceability, V2.2.4 lifecycle/delete boundaries, V2.2.5 project-only Memory/workspace contract, WorkspaceBoundary, KodeSecrets, ResearchGuard and R16.7 MemoryStore hardening;
6. do not pull forward V2.3+, V2.5 cross-workspace orchestration, release/TUF/updater work, R20 reopening or R20.7;
7. if a genuine manual intervention is required, stop at V2.2.6 and state exactly what the operator must do rather than bypassing a gate.
