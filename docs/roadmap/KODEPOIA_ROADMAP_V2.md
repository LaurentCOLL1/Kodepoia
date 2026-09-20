# Kodepoia — Roadmap V2

Status: **ACTIVE — V2.1, V2.2 and V2.3 COMPLETE + NORMALIZED; V2.4 docs-only planning in progress; V2.4 implementation unauthorized**  
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

V2.3 is **COMPLETE + NORMALIZED** through V2.3.6. **V2.4 docs-only planning is now in progress** under `docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md`, based on exact normalized `main` `586d55a3cbccaadbb2a868c5fd5e0ed0123bf8b0`. No V2.4 implementation is authorized until the planning head is qualified, merged and separately normalized. Project Knowledge/Research/context remains data-only; V2.5+ remain unauthorized.

## Remaining V2 sequence

- V2.2 — Project Knowledge, Context Builder and Memory integration — **COMPLETE + NORMALIZED through V2.2.6**.
- V2.3 — Model Lab governed improvement UX — **COMPLETE + NORMALIZED through V2.3.6**.
- V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU — **docs-only planning in progress; implementation remains unauthorized pending exact-head planning qualification/merge/normalization**.
- V2.5 — Cross-workspace orchestration.
- V2.6 — V2 hardening and next public Windows release.

### V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU — PLANNING

Normative planning contract under qualification:

`docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md`

Planning base:

`586d55a3cbccaadbb2a868c5fd5e0ed0123bf8b0`

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

This planning work is docs-only. **V2.4.1 is not authorized by this planning branch or by the planning PR merge alone.** Only a post-merge normalization after exact-head planning qualification may authorize V2.4.1.

The dedicated V2.4 planning authority must be created and qualified before any production accelerator or explicit multi-GPU implementation begins.

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
