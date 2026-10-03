# Kodepoia — Roadmap V2

Status: **ACTIVE — V2.1, V2.2 and V2.3 COMPLETE + NORMALIZED; V2.4 COMPLETE + NORMALIZED through V2.4.6; V2.5 CROSS-WORKSPACE ORCHESTRATION PLANNING CURRENT**  
Created: 2026-09-15  
Public Windows distribution baseline: `v1.1.0-rc8`

## Authority checkpoints

- V2 roadmap preparation: PR `#472`, merge `87fc09e16531260d64cf3d5fb59f511295e2b703`, 25/25 exact-head PR workflows successful.
- V2.0: PR `#474`, accepted head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`, 27/27 successful.
- V2.1.1: PR `#476`, accepted head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful.
- V2.1.2: PR `#478`, accepted head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful; normalization PR `#479`, head `02f00beb070492c398858dcfa70ce0118872b55d`, merge `39ceec560ff069d98530687f77e7ad1c41670d3a`.
- V2.1.3: PR `#480`, accepted head `c4cff95ea2309ea5482e6c24c61002b13becb48f`, merge `0c3d365626df666f2a847b9320b0730dc0110afa`, 27/27 successful.
- V2.1.4: PR `#482`, accepted head `7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921`, merge `a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda`, 27/27 successful.
- V2.1.5: PR `#484`, accepted head `f46068a410e7e0ea3f32f8decc77eed6aa105355`, merge `bfe7fa6b4def1a291d97bd2b9365bda321bcde52`, 27/27 successful; deterministic acceptance 12/12 PASS on Ubuntu and Windows.
- V2.1.6: PR `#486`, accepted head `2e788df0886e1e31512f53547ea4603186e964eb`, merge `7efcc3e941fe8db0e3cc00c81b147716c91eb30b`, 27/27 successful; deterministic acceptance 12/12 PASS on Ubuntu and Windows.
- V2.2.1: PR `#490`, accepted head `f5c6e90783476117d90ee86ea7edbed014d691a7`, merge `6341dbe6599505edc8d354e629d0fc962587f8ac`, 27/27 successful; deterministic acceptance 11/11 PASS on Ubuntu and Windows; R16.7 Memory Context Poisoning Acceptance also passed.
- V2.2.2: PR `#492`, accepted head `c3294815ddf4b76f75f04cb29ee2fdfe1d27248d`, merge `2d332945c3b1f8d76cc98d651606679c89791485`, 26/26 successful; deterministic acceptance 10/10 PASS on Ubuntu and Windows; Python Core Windows succeeded on attempt 2 on the unchanged head after an isolated historical R16.16 temp-directory lock.
- V2.2.3: PR `#494`, accepted head `ac9ad68938cc13cd819bb078839c5963d03a794e`, merge `363bf1a3afa06949269208aa6d3639e439c899e5`, 27/27 successful; deterministic acceptance 11/11 PASS on Ubuntu and Windows.
- V2.2.4: PR `#496`, accepted head `c17e673d944dd0582f9c0e24368c0adf45dd3f40`, merge `ca27459ca04abbeba8275cc32ba7166e37acfd5a`, 27/27 successful; deterministic acceptance 13/13 PASS on Ubuntu and Windows.
- V2.2.5: PR `#498`, accepted head `d29d10e5456623d1b7063bb37386693c1eec625a`, merge `11479e63dc48c45f2ec97f9950430cf35c986e8c`, 31/31 successful; deterministic acceptance 13/13 PASS on Ubuntu and Windows.
- V2.2.6: PR `#500`, accepted head `add97a4889c68b7aed79125563917ddce8b70863`, merge `2c122c913b57c0034f73ba25c34f3fd32507fafa`, 26/26 successful; deterministic integrated acceptance 16/16 PASS on Ubuntu and Windows with evidence SHA-256 `646071eb27ecf8e08ae7dfde3bd74e0f7d32a9dbd6e3d284a85c9093c5b5cc6d`.
- V2.3.3: PR `#508`, accepted head `e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7`, merge `b2943239885b5fc4e3791d48dfacf5b6947851a2`, 32/32 successful; deterministic acceptance 16/16 PASS on Ubuntu and Windows with evidence SHA-256 `8c1b92bdee6e6236f653afb749a5ea29b464b22d63ef95bd078b739a7684d064`.
- V2.3.4: PR `#510`, accepted head `4f25fb6331ba76dfe51cd13c8a1560f66142a862`, merge `0e88eb5e5f4a2fc7f80038dc28e580c8e93332b2`, 31/31 successful; deterministic acceptance 18/18 PASS on Ubuntu and Windows with evidence SHA-256 `f8be65eaffcc71080551c30c2fc7eff56b20509f7fed74b30ceeb0ccf29e8113`.
- V2.3.5: PR `#512`, accepted head `ed4197780828e54068f0f6893d5f6d4274c57d3d`, merge `c13893edb82c350b623af4c0f486a525dce116f0`, 31/31 successful; deterministic acceptance 18/18 PASS on Ubuntu and Windows with evidence SHA-256 `bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548`.
- V2.3.6: PR `#514`, accepted head `cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e`, merge `d511c1ef081ddc02c3071892862e2f83ed5ba8c0`, 26/26 successful; deterministic integrated acceptance 21/21 PASS on Ubuntu and Windows with evidence SHA-256 `935e35c549571a9ae578515bf2acd5cf9353b264b90da5fefb644a62a6d0e8cd`.


V2 does not reopen R20, does not create `R20.7`, and does not turn post-rc8 source capabilities into public rc8 capabilities.

## V2.1 — Research Workspace

Target flow:

`question -> provider discovery -> source cards -> guarded fetch -> inspect/include/exclude -> cited synthesis -> governed Research Pack -> project context/RAG`

### V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

Saved research, external discovery and explicit-locator fetch are distinct operations. Provider/network/auth failures are explicit rather than empty-success states.

### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

Accepted scope:

- Brave Search general-Web discovery through its official HTTPS API when NETWORK is explicitly allowed and credentials are referenced through KodeSecrets;
- public GitHub repository discovery through the official REST Search API with optional authentication;
- bounded descriptor-only candidates marked `candidate-only` / `unfetched`;
- discovery never automatically fetches, persists or promotes candidates to evidence;
- provider/auth/network/rate-limit failures remain explicit;
- KodeStudio `Search sources` performs real discovery only under NETWORK permission;
- discovery remains separate from guarded `ResearchService.fetch()`.

### V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

Accepted scope:

- structured source/evidence rows rather than raw-JSON-only inspection;
- stable canonical source identity and visible canonical locator;
- visible publication/update/version, trust, freshness and suspicious indicators;
- explicit candidate-only versus fetched lifecycle;
- include/exclude state only for fetched artifact IDs;
- immutable lightweight retrieval revisions and inspectable refetch lineage, including unchanged-content refetches;
- duplicate source identities normalized while provider provenance is retained;
- stale/conflicting versions remain inspectable;
- dedicated KodeStudio Evidence workspace preserving the historical seven-column Research results contract.

Exact-head acceptance on `c4cff95ea2309ea5482e6c24c61002b13becb48f` reported **13/13 PASS**.

Exact-head evidence:

- Ubuntu `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

### V2.1.4 — Cited synthesis and Research Packs — COMPLETE + NORMALIZED

Accepted scope:

- synthesis from explicitly persisted INCLUDED fetched evidence only;
- claim-linked citations bound to artifact ID, evidence revision ID, canonical source identity and content digest;
- immutable historical citation provenance across later refetches;
- visible stale/conflict uncertainty and explicit source-fact versus inference distinction;
- guarded source content that cannot grant permissions or invoke protected actions;
- deterministic, schema-versioned, digest-bound and reopenable Research Packs stored below `.kodepoia/research/packs/`;
- secret redaction and WorkspaceBoundary preservation;
- structured KodeStudio synthesis, claim/citation and Research Pack save UI.

Exact-head acceptance on `7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` reported **13/13 PASS** on Ubuntu and Windows, and all **27/27** pull-request workflows completed successfully before merge.

Exact-head evidence:

- Ubuntu `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

### V2.1.5 — Extended media/community sources — COMPLETE + NORMALIZED

Accepted scope:

- recognized YouTube/community discovery items are typed descriptor-only candidates until explicit guarded acquisition;
- official YouTube `search.list` results normalize into bounded candidate-only video descriptors without implicit fetch or persistence;
- guarded YouTube metadata/transcript acquisition exposes network, missing-credential, provider and transcript-unavailable states instead of false empty-success results;
- guarded community acquisition preserves semantic thread relationships including parent/quote linkage and does not treat popularity as authority;
- acquired community/media artifacts reuse the canonical `ResearchStore`, `EvidenceWorkspace`, selection, immutable revision, citation and Research Pack contracts from V2.1.3–V2.1.4;
- speech-to-text fallback and frame extraction remain explicitly non-authoritative and cannot silently become trusted evidence;
- KodeStudio exposes structured Community/YouTube provider state, typed fetch choices and candidate-to-explicit-fetch handoff;
- descriptions, posts, comments and transcripts remain source data and cannot grant permissions or invoke protected actions.

Exact-head acceptance on `f46068a410e7e0ea3f32f8decc77eed6aa105355` reported **12/12 PASS** on Ubuntu and Windows, and all **27/27** pull-request workflows completed successfully before merge.

Exact-head evidence:

- Ubuntu `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

### V2.1.6 — ResearchGuard hardening — COMPLETE + NORMALIZED

Implementation PR `#486` was qualified with **27/27** pull-request workflows on exact head `2e788df0886e1e31512f53547ea4603186e964eb` and merged as `7efcc3e941fe8db0e3cc00c81b147716c91eb30b`.

The deterministic V2.1.6 acceptance reported **12/12 PASS** on Ubuntu and Windows with evidence payload SHA-256 `076195a992effe8a1eac25d6074a5fc12508d004da7f9ec8b01f3177a4c40f74`.

Exact-head evidence:

- Ubuntu `v2-1-6-researchguard-hardening-ubuntu-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `32d972eb83a070fcb7a2844eae11403518bdfe412bd445db74a9556269a0dac1`;
- Windows `v2-1-6-researchguard-hardening-windows-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `7dd9a6ff8e79f40829a2b11439583ced1c221d63c4c0ca1882d2829a9f0ed4ee`.

Accepted scope and product truth:

- prompt-injection/source-instruction content remains untrusted data across discovery, fetched evidence and synthesis inputs;
- unsafe/private/local/link-local/metadata targets, malicious redirects and mixed public/private DNS fail closed before trusted acquisition;
- timeout/outage/provider failure remains explicit and distinct from policy denial, with `UNAVAILABLE` versus `BLOCKED` semantics;
- cancellation is propagated and checked before new evidence persistence;
- provider diagnostics are secret-redacted;
- stale/offline/cache and version-conflict behavior remains visible while immutable evidence and citation lineage is preserved;
- protected actions and WorkspaceBoundary remain fail closed under adversarial source content;
- KodeStudio structurally exposes `BLOCKED`, `UNAVAILABLE`, `CANCELLED`, `STALE` and `CONFLICT` without regressing V2.1.5 provider/candidate state.

V2.1 is therefore complete through the ResearchGuard hardening boundary. No V2.1.7 is reserved or authorized.

### V2.2 — Project Knowledge, Context Builder and Memory integration — COMPLETE + NORMALIZED

Normative planning contract: `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`.

Planning PR `#488` was qualified **25/25** on exact head `face3a8b9b1053962635518d083b01a92a4ed2af` and merged with exact-head protection as `875149032078beb681816604663056f66a2e1344`.

Key final planning gates included `R0 Repository Guard` `35385962901`, `KodeStudio UI Smoke` `35385962916`, `Python Core` `35385962938`, `R12 Tauri2 Acceptance` `35385963079` and `R17 Windows Installer` `35385962997`. Tauri2 succeeded on attempt 2 on the unchanged head after an isolated first-attempt WebView2 runtime-probe failure; no code or gate was weakened.


Goal: make accepted research useful without repeatedly copying text into prompts while preserving project scope, source traceability and untrusted-data boundaries.

Planned subdivisions:

- **V2.2.1 — Project Knowledge catalog and contracts** — deterministic project-scoped knowledge projection over governed Research Packs, project files and verified project memory.
- **V2.2.2 — Bounded semantic retrieval** — semantic retrieval over accepted project knowledge with explicit capability state, deterministic ranking and no hidden mutation.
- **V2.2.3 — Explainable Context Builder** — selected/omitted rationale, token-budget accounting, trust/provenance visibility and explicit include/exclude before context assembly.
- **V2.2.4 — Version-aware invalidation and derived-knowledge lifecycle** — stale/invalidation fingerprints plus deliberate refresh/rebuild/delete-derived controls without rewriting immutable source evidence.
- **V2.2.5 — Project Memory bridge and workspace consumption** — Chat, KodeCode and specialist consumption through one project-scoped governed context/memory boundary, without V2.5 orchestration.
- **V2.2.6 — Project Knowledge hardening and integrated acceptance** — adversarial cross-project, tamper, poisoning, stale/invalidation, secret, prompt-injection and integrated UI/workspace proof.

Planning and V2.2.1 through V2.2.6 are implemented/qualified as applicable, merged and normalized.

V2.2.3 implementation PR `#494` was qualified **27/27** on exact head `ac9ad68938cc13cd819bb078839c5963d03a794e`, with deterministic **11/11 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `35c18af0424d15b54694ce537f89ae80de98dff262ea8168afe8ef73f5ef9765`, then merged with exact-head protection as `363bf1a3afa06949269208aa6d3639e439c899e5`. Its accepted product truth is explainable, token-budgeted context selection with deterministic rationale, source/citation/trust visibility, preserved `<UNTRUSTED_DATA>` semantics and explicit Auto/Include/Exclude without authority promotion.

V2.2.4 implementation PR `#496` was qualified **27/27** on exact head `c17e673d944dd0582f9c0e24368c0adf45dd3f40`, with deterministic **13/13 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `5ee068e69dc60eba21c840f33a1cabe88008ac247eeb9ed43a7b7fbf90f1f363`, then merged with exact-head protection as `ca27459ca04abbeba8275cc32ba7166e37acfd5a`. Its accepted product truth is version-aware, per-item lifecycle invalidation plus derived-only refresh/rebuild/delete and persisted selection state, without rewriting immutable source evidence.

V2.2.5 implementation PR `#498` was qualified **31/31** on exact head `d29d10e5456623d1b7063bb37386693c1eec625a`, with deterministic **13/13 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `22a8a287c8eead8530d2289fb19b9595e8774f0809f28c71754384b914ea8144`, then merged with exact-head protection as `11479e63dc48c45f2ec97f9950430cf35c986e8c`. Its accepted product truth is one project-scoped governed context snapshot shared across Chat/KodeCode/specialists plus explicit-opt-in R16.7-backed derived project memory, with traceability preserved and no authority/global/training promotion.

V2.2.6 implementation PR `#500` was qualified **26/26** on exact head `add97a4889c68b7aed79125563917ddce8b70863`, with deterministic **16/16 PASS** integrated acceptance on Ubuntu and Windows and identical evidence SHA-256 `646071eb27ecf8e08ae7dfde3bd74e0f7d32a9dbd6e3d284a85c9093c5b5cc6d`, then merged with exact-head protection as `2c122c913b57c0034f73ba25c34f3fd32507fafa`. Its accepted truth is adversarial proof of the full V2.2 scope/trust/lifecycle/cross-surface contract without a runtime product-code change.

V2.2 is therefore **COMPLETE + NORMALIZED** through V2.2.6. No V2.2.7 is reserved or authorized.

The only authorized next work is **planning V2.3 — Model Lab governed improvement UX**. V2.3 implementation must wait for a dedicated planning authority to be exact-head qualified, merged and post-merge normalized.

### V2.3 — Model Lab governed improvement UX — PLANNING COMPLETE + NORMALIZED

Normative planning contract:

`docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md`

Planning PR `#502` was qualified **25/25** on exact head `8a13bb5c7a334b500cebaedec8bf7988d10147c3` and merged with `expected_head_sha` protection as `4744cc47827ca28c61395fc6c8e5064a18ae2b0c`.

V2.3 reuses the accepted R15 Experience / Bench / Fine-tuning backend rather than creating a parallel model-improvement stack.

Frozen subdivisions:

- **V2.3.1 — Model Lab shell, inventory and lineage** — structured read-only Model Lab state over existing datasets, benchmarks, training/evaluation/export evidence, installed models and specialized-model registry lineage.
- **V2.3.2 — Governed experience and dataset curation workspace** — structured eligibility/provenance/privacy/license/revocation/dedup/contamination UX plus explicit immutable dataset build.
- **V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX** — KodeBench evidence, model-vs-system gap diagnosis and explicit evidence-backed decision before training.
- **V2.3.4 — Governed training plan, execution and recovery UX** — exact model/tokenizer/dataset-bound SFT/QLoRA plan, capability/resource preflight, explicit launch, status/cancel/checkpoint/recovery using accepted local/Kaggle backends.
- **V2.3.5 — Candidate evaluation, export, promotion and rollback UX** — paired base/candidate evaluation, critical-regression veto, export/GGUF/Ollama lineage and explicit registry promotion/rollback.
- **V2.3.6 — Model Lab hardening and integrated acceptance** — adversarial proof of the complete UX/governance chain.

Planning invariants remain binding:

- Project Knowledge/Research/context remain reference data and never become training data automatically;
- training eligibility continues to require the accepted R15 Experience governance -> dedup/contamination -> immutable dataset path;
- `TRAIN` / `NO_TRAIN` remains evidence-backed and `NO_TRAIN` is a valid first-class outcome;
- exact model/tokenizer/dataset/capability identities remain mandatory;
- critical regressions veto promotion;
- promotion/rollback remains an explicit separate registry mutation;
- Kaggle T4×2 remains two separate 16 GiB devices; V2.3 does not claim V2.4 production/multi-GPU qualification;
- no public publishing, arbitrary command surface, silent dependency install, release/TUF/updater mutation or R20 reopening.

V2.3.1 implementation PR `#504` was qualified **28/28** on exact final head `33d30747ebd915ab2bad56d3154f55a907830061`, with deterministic **14/14 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`, then merged with `expected_head_sha` protection as `1a7454f52bcd78ac2b44c3db467f6faa39df3a62`. Its accepted product truth is a dedicated structured read-only Model Lab over existing R15 evidence/model infrastructure, with bounded inventory, registry integrity, lineage, explicit Ollama/Kaggle runtime refresh, capability introspection without installation and explicit degraded states, while exposing no dataset-build/training/conversion/promotion/rollback mutation.

V2.3.1 is therefore **COMPLETE + NORMALIZED**.

V2.3.2 implementation PR `#506` was qualified **28/28** on exact final head `f419e125fa28f72bbb11dce855047a64dc3be574`, with deterministic **16/16 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`, then merged with `expected_head_sha` protection as `cefcffbfa55fdd0de096ebe8f029a2123c735d08`. Its accepted product truth is a structured Data Curation workspace over accepted R15 Experience/dataset governance: metadata-only eligibility/provenance/license/privacy/revocation/quarantine/integrity, safe dedup/contamination evidence, immutable dataset digest inspection, non-mutating preview and typed R15-only curation/dataset-build mutations with explicit guards; Project Knowledge/Research/context remains reference-only and no training/conversion/promotion/rollback mutation was pulled forward.

V2.3.2 is therefore **COMPLETE + NORMALIZED**.

V2.3.3 implementation PR `#508` was qualified **32/32** on exact final head `e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7`, with deterministic **16/16 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `8c1b92bdee6e6236f653afb749a5ea29b464b22d63ef95bd078b739a7684d064`, then merged with `expected_head_sha` protection as `b2943239885b5fc4e3791d48dfacf5b6947851a2`. Its accepted product truth is a structured Bench & Decision workspace over existing R15 KodeBench/GapDecision authority, with reproducible suite/task/domain/model/report lineage, explicit system-vs-model diagnostics and evidence-bound fail-closed decision states, while training launch/cancel/recovery, conversion/package and promotion/rollback remain outside V2.3.3.

V2.3.3 is therefore **COMPLETE + NORMALIZED**.

V2.3.4 implementation PR `#510` was qualified **31/31** on exact final head `4f25fb6331ba76dfe51cd13c8a1560f66142a862`, with deterministic **18/18 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `f8be65eaffcc71080551c30c2fc7eff56b20509f7fed74b30ceeb0ccf29e8113`, then merged with `expected_head_sha` protection as `0e88eb5e5f4a2fc7f80038dc28e580c8e93332b2`. Its accepted product truth is a structured governed Training workspace over accepted R15 contracts with immutable TRAIN/model/tokenizer/dataset/capability binding, explicit local/Kaggle backend truth, fail-closed capability/resource preflight, dry-run/confirmation, typed run/status/cancel/resume and lineage-safe checkpoint recovery; candidate evaluation/export/conversion/package/promotion/rollback remains later scope.

V2.3.4 is therefore **COMPLETE + NORMALIZED**.

V2.3.5 implementation PR `#512` was qualified **31/31** on exact final head `ed4197780828e54068f0f6893d5f6d4274c57d3d`, with deterministic **18/18 PASS** acceptance on Ubuntu and Windows and identical evidence SHA-256 `bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548`, then merged with `expected_head_sha` protection as `c13893edb82c350b623af4c0f486a525dce116f0`. Its accepted product truth is a structured Candidate lifecycle workspace over accepted R15.10-R15.14 contracts with paired comparison evidence and critical-regression veto, exact export/GGUF/Ollama/registry lineage, typed guarded export/conversion/package actions, role-specific evidence-bound promotion and immutable rollback; reference context remains data-only and no public publishing or silent model/tokenizer/routing replacement is exposed.

V2.3.5 is therefore **COMPLETE + NORMALIZED**.

V2.3 is **COMPLETE + NORMALIZED** through V2.3.6. V2.4 planning and V2.4.1 through **V2.4.6 are COMPLETE + NORMALIZED**. V2.4.5 implementation PR `#529` was qualified **32/32** on exact final head `71e6a989db0426e0b33ac27c203bf3f812e4ed71`, with **22/22 PASS Ubuntu + 22/22 PASS Windows**, common evidence SHA-256 `fa4a45de78a46ac43df74a92628d32794d2bb04e96be1654705c809436011366`, accepted exact-source Kaggle T4×2 `production_qualified=true`, live report digest `1faae30d6bbdd73c6fdda00a570c7332e2d55901ee4e243bc2333711568246c8`, and merge `a105794b1b890c4c704f0bc05f084d6ec5671628`. V2.4.6 implementation PR `#535` was qualified **26/26** on exact final head `b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce` and merged with exact-head protection as `3799e51d21e64cb6fe90d73968d243fe2161d693`. **V2.4 is COMPLETE + NORMALIZED through V2.4.6.** V2.5+ remain unauthorized pending separate explicit authority. Project Knowledge/Research/context remains data-only.

## Remaining V2 sequence

- V2.2 — Project Knowledge, Context Builder and Memory integration — **COMPLETE + NORMALIZED through V2.2.6**.
- V2.3 — Model Lab governed improvement UX — **COMPLETE + NORMALIZED through V2.3.6**.
- V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU — **COMPLETE + NORMALIZED through V2.4.6**.
- V2.5 — Cross-workspace orchestration.
- V2.6 — V2 hardening and next public Windows release.

### V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU — COMPLETE + NORMALIZED THROUGH V2.4.6

Normative planning contract under qualification:

`docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md`

Planning base:

`586d55a3cbccaadbb2a868c5fd5e0ed0123bf8b0`

Planning PR `#516` was qualified **25/25** on exact final head `8c78ff19cf05b3009a05e2e5337ce31303e9d8b7` and merged with `expected_head_sha` protection as `a14190f529a465e8e42ee0dd90a0248bc38e1b9c`. The final planning head includes only docs plus historical V2.3 acceptance compatibility; no V2.4 product behavior was implemented.

Frozen planned subdivisions:

- **V2.4.1 — Accelerator topology and provider truth** — versioned observed two-device topology and per-device resource truth; no distributed launch.
- **V2.4.2 — Strategy, effective-batch and resource planning contract** — explicit `single_gpu` / `replicated_data_parallel`, world size/device mapping/effective batch and paired strategy benchmark.
- **V2.4.3 — Governed explicit two-GPU execution** — repository-owned two-rank PyTorch/Accelerate execution with no arbitrary launcher surface.
- **V2.4.4 — Distributed checkpoint, cancellation and recovery** — topology/strategy-bound checkpoints, group cancellation and fail-closed partial-rank handling.
- **V2.4.5 — Model Lab accelerator UX and live Kaggle qualification** — device-by-device UX plus exact-source private Kaggle provider proof.
- **V2.4.6 — Production hardening and integrated acceptance** — adversarial deterministic and live-evidence closure.

Planning invariants include:

- `NvidiaTeslaT4` provider metadata is not runtime proof;
- two T4s are two devices with separate VRAM and are never one 32 GiB pool;
- `single_gpu` is the paired baseline;
- replicated data parallel is throughput semantics, not sharded-memory semantics;
- no FSDP/DeepSpeed/ZeRO/tensor/pipeline parallelism or TPU is reserved;
- topology/strategy/world size/device mapping/effective batch becomes exact lineage;
- ProcessSandbox/KillSwitch and fixed typed launch boundaries remain authoritative;
- deterministic CI requires no live Kaggle/GPU/network/quota;
- live Kaggle production evidence is separate and mandatory before a production claim;
- V2.5+, release/TUF/updater and R20 remain unauthorized.

V2.4.3 and V2.4.4 remain accepted and normalized. V2.4.5 implementation PR `#529` is qualified **32/32** on exact final head `71e6a989db0426e0b33ac27c203bf3f812e4ed71`, with **22/22 PASS** on both Ubuntu and Windows and common evidence SHA-256 `fa4a45de78a46ac43df74a92628d32794d2bb04e96be1654705c809436011366`. Its exact-source private Kaggle T4×2 qualification returned `production_qualified=true`, blockers `[]`, throughput speedup `2.6390424987850745x`, canonical eval-loss delta `-0.0066643714904786044`, and live report digest `1faae30d6bbdd73c6fdda00a570c7332e2d55901ee4e243bc2333711568246c8`; PR `#529` then merged with `expected_head_sha` protection as `a105794b1b890c4c704f0bc05f084d6ec5671628`. **This post-merge normalization marks V2.4.5 COMPLETE + NORMALIZED and authorizes V2.4.6 — Production hardening and integrated acceptance only.** V2.5+ remain unauthorized.

The V2.4 planning authority and V2.4.1 through V2.4.6 are qualified and normalized. The accepted topology/strategy/execution/recovery/live-evidence chain remains frozen unless a later explicit authority changes scope; V2.5 remains unauthorized.

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

## Accelerator authority

Kaggle `GPU T4 x2` remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. Treat the two T4 devices as two separate 16 GiB GPUs, never a fictitious single 32 GiB pool.

TPU v5e-8 remains deferred. A distinct XLA/JAX or PyTorch/XLA backend is authorized only if a concrete benchmark demonstrates a material Kodepoia advantage that justifies its own implementation and acceptance surface.

## Acceptance discipline

For every subdivision:

1. re-fetch live `main` and continuity authority;
2. branch from an exact SHA;
3. implement only the authorized scope;
4. add deterministic tests and exact-head acceptance evidence;
5. re-fetch every required workflow for the exact head;
6. merge only after every required workflow succeeds on that same head;
7. normalize continuity after merge before the next subdivision;
8. stop only for a genuine manual intervention that cannot be performed through connected tooling.

No V2 step by itself authorizes release/TUF/updater mutation. The public reference remains `v1.1.0-rc8` until a future release is separately scoped and qualified.


## V2.4.6 — Production hardening and integrated acceptance — COMPLETE + NORMALIZED

Implementation PR `#535` was qualified on exact final head:

`b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce`

All **26/26** pull-request workflows associated with that exact head completed with conclusion `success`, including `Python Core`, `KodeStudio UI Smoke`, `R0 Repository Guard`, `R17 Windows Installer` and the retained cross-platform acceptance set.

The deterministic V2.4.6 acceptance completed on Ubuntu and Windows. Exact-head artifacts are:

- `v2-4-6-production-hardening-ubuntu-latest-b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce`;
- `v2-4-6-production-hardening-windows-latest-b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce`.

Accepted V2.4.6 truth is adversarial proof of the already accepted V2.4 topology/strategy/execution/recovery/live-evidence chain: provider/runtime mismatch, duplicate or inconsistent device/VRAM state, no pooled VRAM, strategy/world-size/device binding, fixed non-shell launcher trust boundary, whole-rank-group crash/timeout/cancellation behavior, orphan-process containment, rank evidence disagreement, tampered lineage, incompatible recovery, provider degradation, honest KodeStudio missing/blocked-live-evidence states, deterministic provider-independent CI, and exact-source live-evidence separation.

PR `#535` merged from the unchanged exact head with `expected_head_sha` protection as:

`3799e51d21e64cb6fe90d73968d243fe2161d693`

V2.4 planning and V2.4.1 through V2.4.6 are therefore **COMPLETE + NORMALIZED**.

This normalization does **not** authorize V2.5 planning or implementation. V2.5+, public publishing, release/TUF/updater mutation, R20 reopening and R20.7 remain unauthorized pending separate explicit authority.

Historical V2.4.6 acceptance compatibility marker (superseded): **V2.4.6 CURRENT**. This literal records the pre-normalization checkpoint only; current roadmap authority is V2.4 COMPLETE + NORMALIZED through V2.4.6 and V2.5+ remain unauthorized.


### V2.5 — Cross-workspace orchestration — PLANNING CURRENT

Normative planning contract under qualification:

`docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md`

Planning base:

`4e049eb10b9781c14eb3e81a2c027575c26dbaf1`

The user explicitly authorized progression from completed V2.4 into V2.5 and required that the next public release wait until V2 is completely finished. Therefore this authority permits **V2.5 planning only**. No V2.5 implementation subdivision is authorized until the planning PR is exact-head qualified, merged with `expected_head_sha`, and post-merge normalized.

Frozen proposed subdivisions under qualification:

- **V2.5.1 — Workspace registry, identity and relationship graph**;
- **V2.5.2 — Cross-workspace context handoff and provenance**;
- **V2.5.3 — Orchestration plan, dependency DAG and routing**;
- **V2.5.4 — Governed execution, approval, cancellation and recovery**;
- **V2.5.5 — KodeStudio orchestration workspace and operational history**;
- **V2.5.6 — Cross-workspace hardening and integrated acceptance**.

Planning invariants:

- reuse existing project sessions, Project DNA, Project Knowledge/Context, KodeCode tool policy, WorkspaceBoundary, ProcessSandbox and KillSwitch;
- cross-workspace context remains data-only and cannot grant destination mutation authority;
- no hidden global/shared memory or arbitrary disk project discovery;
- destination mutations require destination-owned preflight and explicit user confirmation;
- model/source text cannot become shell/argv/env/package/rendezvous/credential authority;
- deterministic CI remains provider-independent;
- **V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until V2.5 is COMPLETE + NORMALIZED**;
- R20 remains terminal and no R20.7 is authorized.

Historical compatibility note: the pre-V2.5 checkpoint text **V2.5+ remain unauthorized pending separate explicit authority** is retained elsewhere in this document as superseded historical acceptance context. Current authority is V2.5 planning only.


### V2.5 planning — COMPLETE + NORMALIZED; V2.5.1 CURRENT

Planning PR `#537` was qualified **25/25** on exact final head `8ff8555acdb1f089da8fd497f9eee1daee4336cd` and merged with exact-head protection as `9c8d53b724e1c887ee795fba4b497b469e97a44a`.

The six frozen V2.5 subdivisions in `docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md` are now normative. **V2.5.1 only** is authorized for implementation. V2.5.2+, V2.6 and release/TUF/updater work remain unauthorized.


### V2.5.1 — COMPLETE + NORMALIZED; V2.5.2 CURRENT

Implementation PR `#539` was qualified **30/30** on exact final head `f6a8f2c47ce876db1abcab7ab18c523243f917c8` and merged with exact-head protection as `414c680e901fbc4dd25c0aa714bc242c39f72ba9`.

Accepted V2.5.1 provides validated deterministic workspace identity, a bounded selected-workspace registry, explicit relationship edges and a read-only KodeStudio inventory while preserving project isolation. **V2.5.2 only** is now authorized for implementation. V2.5.3+, V2.6 and release/TUF/updater work remain unauthorized.


### V2.5.2 — COMPLETE + NORMALIZED; V2.5.3 CURRENT

Implementation PR `#541` was qualified **27/27** on exact final head `9aca5d635d2d3fdee3a17cf729fae0b3ad709c08` and merged with exact-head protection as `37b27bd469c435ed2464650a08cdd80c03bca908`.

Accepted V2.5.2 provides immutable data-only cross-workspace handoff over existing governed Project Workspace snapshots, explicit provenance/selection and integrity verification without authority promotion or execution. **V2.5.3 only** is now authorized for implementation. V2.5.4+, V2.6 and release/TUF/updater work remain unauthorized.


### V2.5.3 — COMPLETE + NORMALIZED; V2.5.4 CURRENT

Implementation PR `#543` was qualified **27/27** on exact final head `e93bbf97ae536457bfe33b918d78987c25ab79af` and merged with exact-head protection as `8956116e5c90e630b4d35982484f7c52ad688054`.

Accepted V2.5.3 provides deterministic typed orchestration plans, workspace-owned tasks, fixed routing and visible effects/blockers without protected execution. **V2.5.4 only** is now authorized for implementation. V2.5.5+, V2.6 and release/TUF/updater work remain unauthorized.


### V2.5.4 — COMPLETE + NORMALIZED; V2.5.5 CURRENT

Implementation PR `#545` was qualified **26/26** on exact final head `044ea9147fcb6e534af46254f54993a7a3e6e0a8` and merged with exact-head protection as `5db682ca11ba89e2fb1857961f2b15d601844598`.

Accepted V2.5.4 provides exact lineage-bound mutation approval, destination-owned execution routing, bounded conflict control/concurrency, KillSwitch cancellation, downstream blocking and lineage-safe recovery. **V2.5.5 only** is now authorized for implementation. V2.5.6, V2.6 and release/TUF/updater work remain unauthorized.


### V2.5.5 — COMPLETE + NORMALIZED; V2.5.6 CURRENT

Implementation PR `#547` was qualified **30/30** on exact final head `05cb36f5fed085838644d22a7aaa1225574ff023` and merged with exact-head protection as `5f1f27ef7a8001f5b9c649a84b67e9360c1a5ce4`.

Accepted V2.5.5 provides the integrated KodeStudio orchestration workspace, explicit approval/execution/cancel/recovery controls over accepted V2.5 contracts, persistent hash-chained operational history, localization/accessibility and honest degraded states without new orchestration semantics. **V2.5.6 only** is now authorized. V2.6 and release/TUF/updater work remain unauthorized.

### V2.5.6 — COMPLETE + NORMALIZED; V2.5 COMPLETE

Implementation PR `#549` was qualified **27/27** on exact final head `b05d77d2b37976dcef71543e718cde245026a7e4` and merged with exact-head protection as `cd62836229466607672ec8aaae47d9871443c0d0`.

The deterministic V2.5.6 exact-head acceptance reported **20/20 PASS** on Ubuntu and Windows. Accepted V2.5.6 provides adversarial proof and fail-closed hardening across workspace identity, cross-workspace handoff freshness/integrity, missing evidence, fixed routing, destination mutation approval, concurrent write conflicts, cancellation/partial-success, lineage-safe recovery, project move/delete, secret sanitization, hash-chained history corruption and degraded KodeStudio states.

V2.5 planning and V2.5.1 through V2.5.6 are now **COMPLETE + NORMALIZED**. The six-subdivision V2.5 sequence is closed; no V2.5.7 is authorized.

V2.6 remains the listed next roadmap phase, but **V2.6 planning and implementation are not authorized by this normalization**. A separate explicit authority and planning contract are required before V2.6 work begins. Release/tag/installer/TUF/updater mutation remains unauthorized; `v1.1.0-rc8` remains the public baseline.

### V2.6 — V2 hardening and next public Windows release — PLANNING CURRENT

V2.5 planning and V2.5.1 through V2.5.6 are **COMPLETE + NORMALIZED**. The user explicitly authorized continuation into V2.6 on 2026-10-03.

Normative V2.6 planning contract under qualification:

`docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md`

Planning base:

`65ef3ac66494b4b801274b81141d136a4830d7be`

This authority permits **V2.6 planning only**. No implementation or live release effect is authorized before planning qualification and post-merge normalization.

Frozen proposed subdivisions under qualification:

- **V2.6.1 — Terminal V2 scope, release identity and compatibility freeze**;
- **V2.6.2 — Full V2 integrated regression and adversarial hardening**;
- **V2.6.3 — Exact-source Windows release candidate, SBOM, provenance and signing truth**;
- **V2.6.4 — Production TUF transition and updater compatibility staging**;
- **V2.6.5 — Installed Windows release rehearsal and pre-publication go/no-go**;
- **V2.6.6 — Governed public Windows release, updater activation and terminal V2 closure**.

Release sequencing is explicit: no public release/TUF/updater mutation in planning or V2.6.1-V2.6.5. V2.6.6 may perform live publication only after the preceding V2.6 subdivisions are COMPLETE + NORMALIZED on the frozen candidate.

The current public baseline remains `v1.1.0-rc8`; successor version/channel and Authenticode posture are deliberately deferred to V2.6.1 rather than guessed during planning. R20 remains terminal and no R20.7 or V2.7 is authorized.

### V2.6 planning — COMPLETE + NORMALIZED; V2.6.1 CURRENT

Planning PR `#551` was qualified **25/25** on exact final head `f6f6cb80092af2ee790bc3e81e1f7c620fe2d751` and merged with exact-head protection as `b7af0d3024ac3bcdbf75835941873aabcb0be345`.

The six frozen V2.6 subdivisions in `docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md` are now normative.

**V2.6.1 only** is authorized for implementation. V2.6.2 through V2.6.6 remain unauthorized until sequential qualification and post-merge normalization.

The public release boundary remains unchanged: no public release/tag/asset/TUF/updater/WinGet mutation is authorized in V2.6.1. The current public baseline remains `v1.1.0-rc8`.
### V2.6.1 — COMPLETE + NORMALIZED; V2.6.2 CURRENT

Implementation PR `#553` was qualified **33/33** on exact final head `272f72d3dabf3ee6219dc847d1afaf78e23c6ca6` and merged with exact-head protection as `75fa3f38ec4039cfa6972e1adf930423d16320b3`.

The accepted terminal release freeze is Kodepoia `1.1.0` stable/release/`v1.1.0`, while the current public/runtime baseline remains `v1.1.0-rc8`. Exact candidate source binding remains deferred to V2.6.3; production Authenticode signing remains unverified; WinGet publication is OUT; and observed expired production TUF snapshot/timestamp metadata remains fail-closed pending the authorized V2.6.4 transition stage.

The terminal no-new-feature freeze is now effective. **V2.6.2 — Full V2 integrated regression and adversarial hardening only** is authorized. V2.6.3 through V2.6.6 remain unauthorized until sequential exact-head qualification, merge and post-merge normalization.

No public release/tag/asset/TUF/updater/WinGet mutation is authorized in V2.6.2. Live publication remains reserved to V2.6.6 after V2.6.1 through V2.6.5 are COMPLETE + NORMALIZED.

