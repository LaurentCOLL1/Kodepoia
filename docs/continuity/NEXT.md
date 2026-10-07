# Kodepoia next actions

Last synchronized: 2026-10-06 after V2.6.6 terminal live-updater closure qualification  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0`** is now the stable distribution authority. The terminal live closure proved real installed `v1.1.0-rc8 -> 1.1.0` upgrade and post-upgrade `up-to-date`; rc8 remains historical baseline evidence only. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0 and V2.1.1 through V2.1.6 are **COMPLETE + NORMALIZED**.

## V2.1.5 accepted implementation

V2.1.5 implementation PR `#484` was qualified with **27/27** `completed/success` pull-request workflows on exact head:

`f46068a410e7e0ea3f32f8decc77eed6aa105355`

It merged from that unchanged head as:

`bfe7fa6b4def1a291d97bd2b9365bda321bcde52`

The final exact-head qualification included:

- `R0 Repository Guard` run `35265257329` = `completed/success`;
- `Python Core` run `35265257418` = `completed/success`;
- `KodeStudio UI Smoke` run `35265257290` = `completed/success`;
- `R17 Windows Installer` run `35265257386` = `completed/success`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35265257328` = `completed/success`.

V2.1.5 exact-head evidence:

- Ubuntu artifact `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows artifact `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

The deterministic V2.1.5 acceptance reported **12/12 PASS** on Ubuntu and Windows. Accepted product truth includes:

- YouTube and community discovery items remain descriptor-only `candidate-only` / `unfetched` candidates until an explicit guarded acquisition succeeds;
- official YouTube `search.list` payloads are normalized into bounded video descriptors without implicit fetch or persistence;
- YouTube metadata/transcript acquisition uses the existing guarded provider path and keeps network, credential, provider and transcript-unavailable states explicit;
- community acquisition remains guarded and preserves semantic thread relationships such as parent/quote linkage without treating popularity as authority;
- acquired community/media content enters the canonical `ResearchStore` / `EvidenceWorkspace` / selection lifecycle with existing provenance, revision, citation and Research Pack contracts;
- speech-to-text and frame extraction remain explicitly non-authoritative and cannot silently become trusted evidence;
- KodeStudio exposes typed Community/YouTube fetch choices, provider state and candidate-to-explicit-fetch handoff without collapsing discovery into acquisition;
- source content remains untrusted data and cannot grant permissions or invoke protected actions;
- V2.1.6 adversarial hardening and all release/TUF/updater work remained out of scope.

## V2.1.6 accepted implementation

Implementation PR `#486` was qualified on exact head `2e788df0886e1e31512f53547ea4603186e964eb` with **27/27** successful pull-request workflows and merged as `7efcc3e941fe8db0e3cc00c81b147716c91eb30b`.

The deterministic acceptance reported **12/12 PASS** on Ubuntu and Windows with evidence payload SHA-256 `076195a992effe8a1eac25d6074a5fc12508d004da7f9ec8b01f3177a4c40f74`.

Exact-head artifacts:

- Ubuntu `v2-1-6-researchguard-hardening-ubuntu-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `32d972eb83a070fcb7a2844eae11403518bdfe412bd445db74a9556269a0dac1`;
- Windows `v2-1-6-researchguard-hardening-windows-latest-2e788df0886e1e31512f53547ea4603186e964eb` — SHA-256 `7dd9a6ff8e79f40829a2b11439583ced1c221d63c4c0ca1882d2829a9f0ed4ee`.

Accepted product truth includes:

- unsafe extended-source locators, private/local/link-local/metadata targets, mixed public/private DNS and malicious redirects fail closed before trusted acquisition;
- `BLOCKED` is reserved for policy/security denial and `UNAVAILABLE` for provider/transport failure;
- provider diagnostics are KodeSecrets-redacted;
- cancellation cannot persist new extended-source evidence after the cancellation gate trips;
- stale/offline/cache and version-conflict states remain explicit while immutable evidence/citation lineage is preserved;
- adversarial source text remains data-only and cannot grant capabilities, escape WorkspaceBoundary or invoke protected actions;
- KodeStudio preserves V2.1.5 Community/YouTube and descriptor-only lifecycle semantics while structurally surfacing V2.1.6 degraded states.

## V2.2 planning accepted

Planning PR `#488` was qualified with **25/25** pull-request workflows on exact head `face3a8b9b1053962635518d083b01a92a4ed2af` and merged with exact-head protection as `875149032078beb681816604663056f66a2e1344`.

The final exact-head gate set included:

- `R0 Repository Guard` `35385962901` = success;
- `KodeStudio UI Smoke` `35385962916` = success;
- `Python Core` `35385962938` = success;
- `R12 Tauri2 Acceptance` `35385963079` = success on attempt 2 on the same unchanged head after one isolated WebView2 runtime-probe failure;
- `R17 Windows Installer` `35385962997` = success, including custom-directory install/updater smoke/uninstall.

The normalized plan is `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md`.

## V2.2.1 accepted implementation

Implementation PR `#490` was qualified with **27/27** pull-request workflows on exact head `f5c6e90783476117d90ee86ea7edbed014d691a7` and merged with exact-head protection as `6341dbe6599505edc8d354e629d0fc962587f8ac`.

The final exact-head gate set included:

- `R0 Repository Guard` `35392522030` = success;
- `KodeStudio UI Smoke` `35392521860` = success;
- `Python Core` `35392522031` = success;
- `R16.7 Memory Context Poisoning Acceptance` `35392521989` = success;
- `R17 Windows Installer` `35392521882` = success.

The deterministic V2.2.1 acceptance reported **11/11 PASS** on both Ubuntu and Windows with evidence payload SHA-256 `f5c695efe34fa86ea0c4a85dddfe5fef7650e86250c6a2a676c7798fc35b8a59`.

Accepted product truth includes deterministic project-scoped knowledge contracts, atomic derived-catalog persistence, immutable Research Pack projection, WorkspaceBoundary-confined/redacted file projection, verified active-project memory projection, and a non-destructive `MemoryStore.list_project_scope()` path that does not inspect/quarantine unrelated project rows.

## V2.2.2 accepted implementation

Implementation PR `#492` was qualified with **26/26** pull-request workflows on exact head `c3294815ddf4b76f75f04cb29ee2fdfe1d27248d` and merged with exact-head protection as `2d332945c3b1f8d76cc98d651606679c89791485`.

The final exact-head gate set included:

- `R0 Repository Guard` `35398389155` = success;
- `KodeStudio UI Smoke` `35398389451` = success;
- `Python Core` `35398389163` = success on attempt 2 on the unchanged head after one isolated Windows `WinError 32` temporary-directory lock in historical R16.16 resource-soak cleanup;
- `R17 Windows Installer` `35398389099` = success.

The deterministic V2.2.2 acceptance reported **10/10 PASS** on both Ubuntu and Windows with evidence payload SHA-256 `e9eddabeec7b15a7901cd28722ef402e2b6d3fd2306ebe8fda582f0f46594cdf`.

Accepted product truth includes bounded project-scoped semantic retrieval, explicit valid-empty versus embedding-unavailable state, project-scope/candidate-bound enforcement before provider access, deterministic cosine scoring/tie-breaks, caller-supplied provider only, duplicate-content normalization with full provenance retention, and zero retrieval-side catalog/memory mutation.

## V2.2.3 accepted implementation

Implementation PR `#494` was qualified with **27/27** pull-request workflows on exact head `ac9ad68938cc13cd819bb078839c5963d03a794e` and merged with `expected_head_sha` protection as `363bf1a3afa06949269208aa6d3639e439c899e5`.

The final exact-head gate set included:

- `R0 Repository Guard` `35404034479` = success;
- `KodeStudio UI Smoke` `35404034456` = success;
- `R12 Tauri2 Acceptance` `35404034501` = success;
- `R13 Integrated Release Readiness` `35404034505` = success;
- `Python Core` `35404034510` = success;
- `R17 Windows Installer` `35404034515` = success.

The deterministic V2.2.3 acceptance reported **11/11 PASS** on both Ubuntu and Windows with evidence payload SHA-256 `35c18af0424d15b54694ce537f89ae80de98dff262ea8168afe8ef73f5ef9765`.

Accepted product truth includes explainable project-context candidates, deterministic selected/omitted rationale, explicit token-budget accounting through the existing ContextBuilder, no trust/authority promotion from mandatory or Include, preserved source/knowledge/citation traceability and `<UNTRUSTED_DATA>` semantics, plus KodeStudio Research preview and Auto/Include/Exclude overrides before assembly.

## V2.2.4 accepted implementation

Implementation PR `#496` was qualified with **27/27** pull-request workflows on exact head `c17e673d944dd0582f9c0e24368c0adf45dd3f40` and merged with `expected_head_sha` protection as `ca27459ca04abbeba8275cc32ba7166e37acfd5a`.

The final exact-head gate set included:

- `R0 Repository Guard` `35413101428` = success;
- `KodeStudio UI Smoke` `35413101469` = success;
- `R12 Tauri2 Acceptance` `35413101488` = success;
- `R13 Integrated Release Readiness` `35413101477` = success;
- `Python Core` `35413101460` = success;
- `R17 Windows Installer` `35413101474` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35413101409` = success.

The deterministic V2.2.4 acceptance reported **13/13 PASS** on both Ubuntu and Windows with evidence payload SHA-256 `5ee068e69dc60eba21c840f33a1cabe88008ac247eeb9ed43a7b7fbf90f1f363`.

Accepted product truth includes per-item source/version fingerprints and version dependencies, deterministic fresh/stale/invalidated/missing lifecycle state, stale exclusion from retrieval, derived-only refresh/rebuild, persisted Auto/Include/Exclude, bounded delete-derived with immutable source preservation, and explicit KodeStudio lifecycle controls/source-delete boundary.

## V2.2.5 accepted implementation

Implementation PR `#498` was qualified with **31/31** pull-request workflows on exact head `d29d10e5456623d1b7063bb37386693c1eec625a` and merged with `expected_head_sha` protection as `11479e63dc48c45f2ec97f9950430cf35c986e8c`.

The final exact-head gate set included:

- `R0 Repository Guard` `35423380639` = success;
- `KodeStudio UI Smoke` `35423380566` = success;
- `R12 Tauri2 Acceptance` `35423380651` = success;
- `R13 Integrated Release Readiness` `35423380709` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35423380706` = success;
- `R18.7 Update Discovery Channel UX Acceptance` `35423380678` = success;
- `Python Core` `35423380620` = success;
- `R17 Windows Installer` `35423380625` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35423380657` = success.

The deterministic V2.2.5 acceptance reported **13/13 PASS** on both Ubuntu and Windows with evidence payload SHA-256 `22a8a287c8eead8530d2289fb19b9595e8774f0809f28c71754384b914ea8144`.

The unchanged final head needed one rerun of only the failed `python-core-windows-latest` job after an isolated historical R16.16 `WinError 32` temp-directory cleanup lock; no source/workflow/acceptance criterion changed.

Accepted product truth is one project-scoped governed context snapshot shared by Chat/KodeCode/specialists; exact project/retrieval-context binding; preserved source/citation/trust/version traceability; Chat data-only semantics; KodeCode read-only policy/no direct MemoryStore read; specialist source visibility; and explicit-opt-in R16.7-backed derived project memory with no global/training promotion.

## V2.2.6 accepted implementation

Implementation PR `#500` was qualified with **26/26** pull-request workflows on exact head `add97a4889c68b7aed79125563917ddce8b70863` and merged with `expected_head_sha` protection as `2c122c913b57c0034f73ba25c34f3fd32507fafa`.

The final exact-head gate set included:

- `R0 Repository Guard` `35438155760` = success;
- `KodeStudio UI Smoke` `35438155732` = success;
- `R12 Tauri2 Acceptance` `35438155744` = success;
- `R13 Integrated Release Readiness` `35438155814` = success;
- `Python Core` `35438155746` = success;
- `R17 Windows Installer` `35438155755` = success.

The deterministic V2.2.6 acceptance reported **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `646071eb27ecf8e08ae7dfde3bd74e0f7d32a9dbd6e3d284a85c9093c5b5cc6d`.

Accepted exact-head artifacts:

- `v2-2-6-project-knowledge-hardening-ubuntu-latest-add97a4889c68b7aed79125563917ddce8b70863` — ID `10582792728`;
- `v2-2-6-project-knowledge-hardening-windows-latest-add97a4889c68b7aed79125563917ddce8b70863` — ID `10582857766`.

Accepted product truth is adversarial integrated proof of the complete V2.2 project-knowledge contract: cross-project rejection; MemoryStore replay/version/tamper/quarantine; Research Pack digest validation; source/version invalidation; prompt-injection and secret handling; Include/Exclude and delete-derived boundaries; deterministic retrieval/budget/capability state; cancellation non-regression; KodeStudio explainability; and Chat/KodeCode/specialist traceability/trust. No runtime product source was changed by V2.2.6.

**V2.2 is COMPLETE + NORMALIZED. No V2.2.7 is authorized.**

## V2.3 planning accepted

Planning PR `#502` was qualified **25/25** on exact head `8a13bb5c7a334b500cebaedec8bf7988d10147c3` and merged with `expected_head_sha` protection as `4744cc47827ca28c61395fc6c8e5064a18ae2b0c`.

Key exact-head gates:

- `R0 Repository Guard` `35447327711` = success;
- `KodeStudio UI Smoke` `35447327644` = success;
- `Python Core` `35447327756` = success;
- `R12 Tauri2 Acceptance` `35447327773` = success;
- `R13 Integrated Release Readiness` `35447327678` = success;
- `R17 Windows Installer` `35447327730` = success.

The normalized V2.3 authority is `docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md`.

## V2.3.1 accepted implementation

Implementation PR `#504` was qualified **28/28** on exact final head `33d30747ebd915ab2bad56d3154f55a907830061` and merged with `expected_head_sha` protection as `1a7454f52bcd78ac2b44c3db467f6faa39df3a62`.

Key exact-head gates:

- `R0 Repository Guard` `35456063171` = success;
- `KodeStudio UI Smoke` `35456063151` = success;
- `Python Core` `35456063128` = success;
- `R12 Tauri2 Acceptance` `35456063201` = success;
- `R13 Integrated Release Readiness` `35456063202` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35456063364` = success;
- `R17 Windows Installer` `35456063263` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35456063159` = success.

Deterministic V2.3.1 acceptance: **14/14 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`.

Accepted exact-head artifacts:

- `v2-3-1-model-lab-shell-ubuntu-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588052972`;
- `v2-3-1-model-lab-shell-windows-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588422645`.

Accepted product truth: dedicated structured Model Lab; bounded read-only R15 evidence inventory; existing specialized-model registry integrity validation; lineage projection; saved Ollama roles plus explicit installed-model refresh; explicit Kaggle doctor/quota refresh; dependency capability introspection without installation; explicit missing/invalid/stale/tampered/unavailable state; raw JSON diagnostics secondary; no dataset build, training, conversion/package, promotion or rollback mutation; Project Knowledge/Research/context remains reference-only.

**V2.3.1 is COMPLETE + NORMALIZED.**

## V2.3.2 accepted implementation

Implementation PR `#506` was qualified **28/28** on exact final head `f419e125fa28f72bbb11dce855047a64dc3be574` and merged with `expected_head_sha` protection as `cefcffbfa55fdd0de096ebe8f029a2123c735d08`.

Key exact-head gates:

- `R0 Repository Guard` `35472245615` = success;
- `KodeStudio UI Smoke` `35472245629` = success;
- `Python Core` `35472245626` = success;
- `R12 Tauri2 Acceptance` `35472245665` = success;
- `R13 Integrated Release Readiness` `35472245591` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35472245579` = success;
- `R17 Windows Installer` `35472245703` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35472245622` = success.

Deterministic V2.3.2 acceptance: **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`.

Accepted exact-head artifacts:

- `v2-3-2-governed-curation-ubuntu-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10593690427`;
- `v2-3-2-governed-curation-windows-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10592989545`.

Accepted product truth: dedicated structured Data Curation workspace; metadata-only experience eligibility/provenance/license/privacy/sanitization/revocation/quarantine/integrity; safe dedup/contamination outcomes; immutable dataset identity/digest inspection without JSONL payload reads; non-mutating dataset preview; typed R15-only curation/dataset-build mutations with dry-run/confirmation/backend gates; cross-project binding rejection; Project Knowledge/Research/context remains reference-only; no training/conversion/promotion/rollback mutation.

**V2.3.2 is COMPLETE + NORMALIZED.**

## V2.3.3 accepted implementation

Implementation PR `#508` was qualified **32/32** on exact final head `e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7` and merged with `expected_head_sha` protection as `b2943239885b5fc4e3791d48dfacf5b6947851a2`.

Key exact-head gates:

- `R0 Repository Guard` `35480915764` = success;
- `KodeStudio UI Smoke` `35480915669` = success;
- `Python Core` `35480915728` = success;
- `R12 Tauri2 Acceptance` `35480915657` = success;
- `R13 Integrated Release Readiness` `35480915772` = success;
- `R15.6 KodeBench v2 Acceptance` `35480915683` = success;
- `R15.7 Gap Decision Acceptance` `35480915716` = success;
- `R15.10 Base Adapter Evaluation Acceptance` `35480915666` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35480915765` = success;
- `R17 Windows Installer` `35480915745` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35480915748` = success.

Deterministic V2.3.3 acceptance: **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `8c1b92bdee6e6236f653afb749a5ea29b464b22d63ef95bd078b739a7684d064`.

Accepted exact-head artifacts:

- `v2-3-3-bench-decision-ubuntu-latest-e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7` — ID `10595259236`;
- `v2-3-3-bench-decision-windows-latest-e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7` — ID `10596176144`.

Accepted product truth: structured Bench & Decision workspace over existing R15 KodeBench/GapDecision evidence; exact suite/config/report/model/dataset lineage and tamper state; task/domain gap results; tool/retrieval/router/context/prompt/product diagnosis; explicit fail-closed decision dispositions with blockers/reasons/targets; typed R15 bench/gap actions only; data-only Project Knowledge/Research/context; no training launch/cancel/recovery, conversion/package or promotion/rollback mutation.

**V2.3.3 is COMPLETE + NORMALIZED.**

## V2.3.4 accepted implementation

Implementation PR `#510` was qualified **31/31** on exact final head `4f25fb6331ba76dfe51cd13c8a1560f66142a862` and merged with `expected_head_sha` protection as `0e88eb5e5f4a2fc7f80038dc28e580c8e93332b2`.

Key exact-head gates:

- `R0 Repository Guard` `35489030766` = success;
- `KodeStudio UI Smoke` `35489030819` = success;
- `Python Core` `35489030825` = success;
- `R12 Tauri2 Acceptance` `35489030843` = success;
- `R13 Integrated Release Readiness` `35489030751` = success;
- `R15.8 Training Runtime Acceptance` `35489030774` = success;
- `R15.9 QLoRA SFT Acceptance` `35489030804` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35489030861` = success;
- `R17 Windows Installer` `35489030828` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35489030758` = success.

Deterministic V2.3.4 acceptance: **18/18 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `f8be65eaffcc71080551c30c2fc7eff56b20509f7fed74b30ceeb0ccf29e8113`.

Accepted exact-head artifacts:

- `v2-3-4-governed-training-ubuntu-latest-4f25fb6331ba76dfe51cd13c8a1560f66142a862` — ID `10598522634`;
- `v2-3-4-governed-training-windows-latest-4f25fb6331ba76dfe51cd13c8a1560f66142a862` — ID `10597613394`.

Accepted product truth: structured Training workspace over existing R15 contracts; immutable plan/model/tokenizer/dataset/TRAIN/capability binding; fail-closed capability/resource preflight; explicit local/Kaggle backend truth; typed doctor/plan/run/status/cancel/resume actions; dry-run/confirmation for mutation; bounded run/loss/checkpoint/resource state and lineage-safe recovery; no arbitrary command/dependency-install surface; Project Knowledge/Research/context remains reference-only; no candidate evaluation/export/conversion/package/promotion/rollback/public publishing pulled forward.

**V2.3.4 is COMPLETE + NORMALIZED.**

## V2.3.5 accepted implementation

Implementation PR `#512` was qualified **31/31** on exact final head `ed4197780828e54068f0f6893d5f6d4274c57d3d` and merged with `expected_head_sha` protection as `c13893edb82c350b623af4c0f486a525dce116f0`.

Key exact-head gates:

- `R0 Repository Guard` `35506019032` = success;
- `KodeStudio UI Smoke` `35506019100` = success;
- `Python Core` `35506019089` = success;
- `R12 Tauri2 Acceptance` `35506019204` = success;
- `R13 Integrated Release Readiness` `35506019023` = success;
- `R15.8 Training Runtime Acceptance` `35506019092` = success;
- `R15.9 QLoRA SFT Acceptance` `35506019090` = success;
- `R15.15 CLI KodeStudio UX Acceptance` `35506019193` = success;
- `R17 Windows Installer` `35506019002` = success;
- `R18.11 Integrated Adversarial Release Update Acceptance` `35506019081` = success.

Deterministic V2.3.5 acceptance: **18/18 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548`.

Accepted exact-head artifacts:

- `v2-3-5-candidate-lifecycle-ubuntu-latest-ed4197780828e54068f0f6893d5f6d4274c57d3d` — ID `10604315201`;
- `v2-3-5-candidate-lifecycle-windows-latest-ed4197780828e54068f0f6893d5f6d4274c57d3d` — ID `10603926113`.

Accepted product truth: structured Candidate lifecycle workspace over existing R15.10-R15.14 contracts; paired base/candidate suite/config/holdout evidence with explicit critical-regression veto; task/domain deltas plus training-loss/overfit/resource evidence where present; exact export/GGUF/Ollama/registry lineage and integrity states; typed export/conversion/package actions plus exact registry role selection only where a real R15 UX gap existed; dry-run and explicit confirmation for mutation; evidence-bound promotion showing candidate/artifact/registry/role/current/proposed mapping; rollback tied to the immutable prior mapping; honest unavailable/tampered/rejected states; no parallel engines, public model-hub publishing, arbitrary shell/argv/env/package install or silent base/tokenizer/routing replacement; Project Knowledge/Research/chat/memory/retrieved context remains reference/data only.

**V2.3.5 is COMPLETE + NORMALIZED.**

## V2.3.6 accepted implementation

Implementation PR `#514` was qualified **26/26** on exact final head `cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e` and merged with `expected_head_sha` protection as `d511c1ef081ddc02c3071892862e2f83ed5ba8c0`.

Key exact-head gates:

- `R0 Repository Guard` `35525471455` = success;
- `KodeStudio UI Smoke` `35525471438` = success;
- `Python Core` `35525471317` = success;
- `R12 Tauri2 Acceptance` `35525471447` = success;
- `R13 Integrated Release Readiness` `35525471466` = success;
- `R17 Windows Installer` `35525471410` = success.

Deterministic V2.3.6 acceptance: **21/21 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `935e35c549571a9ae578515bf2acd5cf9353b264b90da5fefb644a62a6d0e8cd`.

Accepted exact-head artifacts:

- `v2-3-6-model-lab-hardening-ubuntu-latest-cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e` — ID `10609481837`;
- `v2-3-6-model-lab-hardening-windows-latest-cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e` — ID `10610285166`.

Accepted product truth: V2.3.6 hardens and adversarially proves the existing V2.3/R15 chain without adding a replacement engine or product page; untrusted project/research text stays data-only; privacy/license/revocation/contamination and tampered/stale evidence remain fail closed; capability/resource/backend and checkpoint lineage failures remain explicit; base/candidate comparison keeps exact pairing and critical-regression veto; GGUF/Ollama quality and registry promotion/rollback integrity remain binding; unavailable runtime states stay honest; empty/missing-evidence UI is deterministic and accessible; no V2.4 accelerator implementation, public publishing, silent model/tokenizer/routing mutation, release/TUF/updater mutation or R20 reopening was pulled forward.

Qualification required two test-only corrections after the initial head: one aligned hardening assertions with the live accepted contracts, and one aligned ineligible-experience fixtures with valid contract states. Every new commit invalidated prior-head CI; only the final head above is accepted.

**V2.3.6 is COMPLETE + NORMALIZED. V2.3 is closed.**

## Immediate execution order

### V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — COMPLETE + NORMALIZED

V2.4 planning, V2.4.1, V2.4.2, V2.4.3 and **V2.4.4 are COMPLETE + NORMALIZED**.

V2.4.4 accepted evidence:

- implementation PR: `#524 — feat: implement V2.4.4 distributed checkpoint recovery`;
- exact final head: `1abf4917566f065ac26b71a02e02d8fb3506fe1a`;
- exact-head qualification: **29/29 `completed/success`**;
- deterministic acceptance: **25/25 PASS Ubuntu + 25/25 PASS Windows**;
- identical evidence SHA-256: `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`;
- Ubuntu artifact ID: `10654524114`;
- Windows artifact ID: `10655573341`;
- protected merge: `779a9c8282e153b7dba35fb22be89ec5c622e1d3`.

Accepted V2.4.4 truth to preserve:

- rank-zero canonical checkpoint lineage plus both rank evidences;
- exact execution/TrainingPlan/strategy/benchmark/topology/world-size/device binding;
- independently verified checkpoint metadata and adapter digests;
- resume only before max steps and only on exact compatible lineage;
- fixed one-node/two-rank repository-owned recovery launcher;
- R15.9 real resume semantics reused rather than a parallel engine;
- both ranks required for successful recovery;
- timeout/cancel/nonzero/missing/tampered/mismatched evidence is whole-group terminal;
- historical V2.4.3 resume authority remains false; V2.4.4 recovery authority is separate and explicit.

Accepted V2.4.5 final authority:

- implementation PR `#529`, exact final head `71e6a989db0426e0b33ac27c203bf3f812e4ed71`;
- **32/32** exact-head workflows completed/success;
- deterministic acceptance **22/22 PASS Ubuntu + 22/22 PASS Windows**, common evidence SHA-256 `fa4a45de78a46ac43df74a92628d32794d2bb04e96be1654705c809436011366`;
- exact-source private Kaggle T4×2 live report `production_qualified=true`, blockers `[]`, live report digest `1faae30d6bbdd73c6fdda00a570c7332e2d55901ee4e243bc2333711568246c8`;
- throughput speedup `2.6390424987850745x`, canonical eval-loss delta `-0.0066643714904786044`, critical-regression/download/secret gates passed;
- protected merge `a105794b1b890c4c704f0bc05f084d6ec5671628`.

Authorized V2.4.5 scope:

- structured Model Lab requested-provider versus observed-topology view;
- separate per-device rows/VRAM with no summed 32 GiB pool;
- explicit `single_gpu` / `replicated_data_parallel` strategy state;
- effective batch/world size/device mapping visible before launch;
- exact topology/strategy/execution/recovery/live-evidence lineage visible;
- honest auth/network/quota/provider-unavailable states;
- no automatic provider calls at startup;
- exact-source live Kaggle qualification with private bundle/kernel and downloaded evidence revalidation;
- paired live single-vs-replicated evidence;
- FR/EN/qps-ploc and accessibility;
- deterministic CI for non-provider-dependent logic.

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

Definition of done: the user can see what Kaggle actually provided, what strategy will run, and whether live production qualification exists for the exact source. This definition is satisfied by the accepted exact-source V2.4.5 live evidence above.

### V2.4.6 — Production hardening and integrated acceptance — COMPLETE + NORMALIZED

V2.4.6 is complete and normalized. PR `#535` was qualified **26/26** on exact head `b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce` and merged as `3799e51d21e64cb6fe90d73968d243fe2161d693`; its acceptance adversarially proves the accepted topology/strategy/execution/recovery/live-evidence chain without redefining V2.4 truth.

V2.5+ remain unauthorized pending separate explicit authority. Public publishing, release/TUF/updater mutation, R20 reopening and R20.7 also remain unauthorized.

## Later V2 order

V2.4 is complete through V2.4.6. No V2.5 planning or implementation is authorized yet; V2.5 orchestration and V2.6 release work remain later authority gates.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md. V2.4 planning et V2.4.1 à V2.4.6 sont COMPLETE + NORMALIZED. V2.4.6 : PR #535, head exact b3fa9914cfaa6f1f0b40b64ab06bb5c2cc17a7ce, 26/26 workflows success, acceptance déterministe Ubuntu/Windows, merge protégé 3799e51d21e64cb6fe90d73968d243fe2161d693. Re-fetch main et les autorités avant mutation. V2.5+, public publishing, release/TUF/updater, R20 reopening et R20.7 restent non autorisés tant qu'une autorité explicite distincte ne les autorise pas.`


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


Historical acceptance compatibility note: the superseded post-V2.4.5 checkpoint was **V2.4.6 — Production hardening and integrated acceptance — CURRENT**. This literal historical marker is retained only so earlier exact-head acceptance remains reproducible; current authority is V2.4.6 COMPLETE + NORMALIZED, and V2.5+ remain unauthorized.

Historical V2.4.6 acceptance compatibility marker (superseded): **V2.4.6 — Production hardening and integrated acceptance — CURRENT**. This literal records the pre-normalization checkpoint only; current authority is V2.4.6 COMPLETE + NORMALIZED and V2.5+ remain unauthorized.


## Current next action — V2.5 planning only

The user explicitly authorized progression into **V2.5 — Cross-workspace orchestration** and required the next public release to wait until V2 is fully complete.

Immediate work is limited to qualifying the planning contract at:

`docs/roadmap/V2_5_CROSS_WORKSPACE_ORCHESTRATION.md`

Planning branch base: `4e049eb10b9781c14eb3e81a2c027575c26dbaf1`.

Do not implement V2.5.1 until the planning PR is exact-head qualified, merged with `expected_head_sha`, and post-merge normalized. After normalization, authorize **V2.5.1 only** and continue subdivision by subdivision through V2.5.6.

Do not start V2.6 or any release/tag/installer/TUF/updater mutation during V2.5. The user's release boundary is explicit: **release only after V2 is completely finished**. The public reference remains `v1.1.0-rc8`.

Resume sequence:

1. re-fetch live `main` and all current authorities;
2. verify V2.4 remains COMPLETE + NORMALIZED;
3. re-fetch the V2.5 planning branch/PR and exact head;
4. qualify all required workflows on that exact head;
5. merge only with unchanged-head protection;
6. normalize planning and authorize V2.5.1 only;
7. keep V2.6/release work unauthorized until V2.5.6 completes and normalizes.

Historical compatibility note: earlier wording that **V2.5+ remain unauthorized pending separate explicit authority** remains historical evidence; the explicit authority now covers V2.5 planning only, not implementation or V2.6.


## Current next action — V2.5.1 only

V2.5 planning is **COMPLETE + NORMALIZED** from PR `#537`, exact head `8ff8555acdb1f089da8fd497f9eee1daee4336cd`, **25/25** successful workflows and merge `9c8d53b724e1c887ee795fba4b497b469e97a44a`.

Implement **V2.5.1 — Workspace registry, identity and relationship graph** only.

Required scope: bounded selected-workspace registry; stable workspace identity/project-scope binding; explicit relationship graph; duplicate/path-alias/symlink/cross-scope rejection; read-only KodeStudio workspace inventory. Do not implement task orchestration, context handoff execution, destination mutation or any later V2.5 subdivision yet.

V2.5.2+, V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until their own gates are satisfied.


## Current next action — V2.5.2 only

V2.5.1 is **COMPLETE + NORMALIZED** from PR `#539`, exact head `f6a8f2c47ce876db1abcab7ab18c523243f917c8`, **30/30** successful workflows and merge `414c680e901fbc4dd25c0aa714bc242c39f72ba9`.

Implement **V2.5.2 — Cross-workspace context handoff and provenance** only.

Required scope: source/destination workspace binding; governed Project Workspace context snapshot reuse; citations/trust/freshness/version visibility; immutable packet digest/tamper rejection; explicit include/exclude selection; data-only authority marker; no global/shared-memory promotion and no mutating task execution.

V2.5.3+, V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until their own sequential qualification and normalization gates are satisfied.


## Current next action — V2.5.3 only

V2.5.2 is **COMPLETE + NORMALIZED** from PR `#541`, exact head `9aca5d635d2d3fdee3a17cf729fae0b3ad709c08`, **27/27** successful workflows and merge `37b27bd469c435ed2464650a08cdd80c03bca908`.

Implement **V2.5.3 — Orchestration plan, dependency DAG and routing** only.

Required scope: deterministic typed task DAG; workspace ownership; explicit dependencies; fixed existing-service/specialist routing catalog; capability/effect visibility; dependency/blocker propagation; cycle rejection; immutable plan digest/preview. Do not implement protected destination mutation, approval execution, concurrency, cancellation or recovery yet.

V2.5.4+, V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until their own sequential qualification and normalization gates are satisfied.


## Current next action — V2.5.4 only

V2.5.3 is **COMPLETE + NORMALIZED** from PR `#543`, exact head `e93bbf97ae536457bfe33b918d78987c25ab79af`, **27/27** successful workflows and merge `8956116e5c90e630b4d35982484f7c52ad688054`.

Implement **V2.5.4 — Governed execution, approval, cancellation and recovery** only.

Required scope: explicit mutation preview/confirmation; destination-owned tool/service policy enforcement; bounded conflict control/concurrency; KillSwitch-compatible cancellation; downstream blocking on failure/cancel; lineage-safe recovery tied to the accepted plan/task/workspace/handoff digests. No raw shell/argv/env/package surface, no hidden authority composition and no release mutation.

V2.5.5+, V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until their own sequential qualification and normalization gates are satisfied.


## Current next action — V2.5.5 only

V2.5.4 is **COMPLETE + NORMALIZED** from PR `#545`, exact head `044ea9147fcb6e534af46254f54993a7a3e6e0a8`, **26/26** successful workflows and merge `5db682ca11ba89e2fb1857961f2b15d601844598`.

Implement **V2.5.5 — KodeStudio orchestration workspace and operational history** only.

Required scope: workspace/relationship management; task DAG/status display; handoff inspection; explicit approval controls for mutation-proposed tasks; evidence/output timeline; cancellation/recovery controls; persistent operational history over accepted V2.5.1-V2.5.4 contracts; EN/FR/qps-ploc and accessibility; honest empty/degraded states. Do not add new orchestration semantics, weaken approvals, or perform V2.5.6 hardening yet.

V2.5.6, V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until their own sequential qualification and normalization gates are satisfied.


## Current next action — V2.5.6 only

V2.5.5 is **COMPLETE + NORMALIZED** from PR `#547`, exact head `05cb36f5fed085838644d22a7aaa1225574ff023`, **30/30** successful workflows and merge `5f1f27ef7a8001f5b9c649a84b67e9360c1a5ce4`.

Implement **V2.5.6 — Cross-workspace hardening and integrated acceptance** only.

Required scope: adversarially prove the full V2.5 chain against path/symlink/identity confusion, authority spoofing, stale/revoked/tampered handoffs, dependency cycles/missing evidence, malicious routing/service/tool text, unauthorized destination writes, concurrent write conflicts, cancellation/orphan/partial-success handling, incompatible recovery, project deletion/move between planning and execution, secret leakage and deterministic degraded UI states; add exact-head Ubuntu/Windows integrated acceptance. Do not add new product capability or begin V2.6/release work.

V2.6 and all release/tag/installer/TUF/updater mutation remain unauthorized until V2.5.6 itself is qualified, merged and post-merge normalized.

## Current next action — V2.5 closed; V2.6 requires separate explicit authority

V2.5.6 is **COMPLETE + NORMALIZED** from implementation PR `#549`, exact final head `b05d77d2b37976dcef71543e718cde245026a7e4`, **27/27** successful pull-request workflows and merge `cd62836229466607672ec8aaae47d9871443c0d0`.

The V2.5 sequence is terminal: planning plus V2.5.1 through V2.5.6 are **COMPLETE + NORMALIZED**. The V2.5.6 deterministic exact-head acceptance reported **20/20 PASS** on Ubuntu and Windows and the integrated KodeStudio UI smoke passed on the same exact source.

Do not create a V2.5.7 subdivision. Do not begin V2.6 planning or implementation, and do not mutate release/tag/installer/TUF/updater state, until a separate explicit V2.6 authority is established.

When such authority is explicitly granted, first re-fetch live `main` and all current continuity/roadmap authorities, then create a dedicated V2.6 planning contract before implementation. The public distribution reference remains `v1.1.0-rc8`.

## Current next action — V2.6 planning only

The user explicitly authorized progression beyond completed V2.5 by instructing Kodepoia to continue.

V2.5 planning and V2.5.1 through V2.5.6 are **COMPLETE + NORMALIZED**. Exact live planning base:

`65ef3ac66494b4b801274b81141d136a4830d7be`

Qualify the dedicated V2.6 planning contract:

`docs/roadmap/V2_6_HARDENING_NEXT_PUBLIC_WINDOWS_RELEASE.md`

Do not implement V2.6.1 until the planning PR is exact-head qualified, merged with `expected_head_sha`, and post-merge normalized. After that normalization, authorize **V2.6.1 only**.

Do not publish a release, create/repoint a release tag, upload public release assets, mutate live production TUF/update metadata, or submit WinGet during planning. The public baseline remains `v1.1.0-rc8`.

The next public Windows release is sequenced only after terminal V2 hardening: live publication is reserved to the final V2.6.6 subdivision after V2.6.1-V2.6.5 complete and normalize sequentially.

## Current next action — V2.6.1 only

V2.6 planning is **COMPLETE + NORMALIZED** from PR `#551`, exact head `f6f6cb80092af2ee790bc3e81e1f7c620fe2d751`, **25/25** successful workflows and merge `b7af0d3024ac3bcdbf75835941873aabcb0be345`.

Implement **V2.6.1 — Terminal V2 scope, release identity and compatibility freeze** only.

Required scope: freeze the exact successor release version/channel/build type/tag and release identity; validate monotonic transition from the installed/public `v1.1.0-rc8` baseline; freeze Windows installer and update-target identity; record truthful Authenticode posture without inventing production signing capability; freeze release-note/known-limitation contract; freeze supported installed-upgrade baseline; explicitly decide whether WinGet publication is in or out of the terminal release; and establish a no-new-feature freeze after identity acceptance.

Do not publish a release, create/repoint a public release tag, upload public release assets, mutate live production TUF/update metadata, provision or expose signing secrets, or submit WinGet in V2.6.1.

V2.6.2 through V2.6.6 remain unauthorized until their own sequential qualification and normalization gates are satisfied.

## Current next action — V2.6.2 only

V2.6.1 is **COMPLETE + NORMALIZED** from implementation PR `#553`, exact final head `272f72d3dabf3ee6219dc847d1afaf78e23c6ca6`, **33/33** successful pull-request workflows and merge `75fa3f38ec4039cfa6972e1adf930423d16320b3`.

Implement **V2.6.2 — Full V2 integrated regression and adversarial hardening** only, under the terminal no-new-feature freeze.

Required scope: integrated V2.0 through V2.5 regression; security/privacy/secrets/tools/workspaces/memory/research/Model Lab/orchestration adversarial coverage; packaged Windows UI and project-durability checks; cancellation/recovery/resource-soak checks; updater local-availability and fail-closed invariants; critical-veto aggregation; and deterministic exact-head Ubuntu/Windows evidence.

Preserve the V2.6.1 release freeze exactly: target identity remains `1.1.0` stable/release/`v1.1.0`; current public/runtime baseline remains `v1.1.0-rc8`; candidate source SHA remains unset until V2.6.3; production Authenticode signing remains unverified; WinGet stays OUT; and expired production TUF snapshot/timestamp metadata must continue to fail closed and must not be repaired live in V2.6.2.

Do not publish a release, create/repoint a public release tag, upload public release assets, mutate production TUF/update metadata, activate a live updater target, provision signing secrets or submit WinGet.

V2.6.3 through V2.6.6 remain unauthorized until their own sequential qualification and post-merge normalization gates are satisfied.

## Current next action — V2.6.3 only

V2.6.2 is **COMPLETE + NORMALIZED** from implementation PR `#555`, exact final head `5badcfb68b5593432f24ef4cf53eafd596d109cd`, **33/33** successful pull-request workflows and merge `2453c5122c096d807e5b49840d33a61e1bcc5e92`.

Its deterministic terminal hardening evidence reported **12/12 PASS on Ubuntu** and **12/12 PASS on Windows**, `critical_veto=false`, with common evidence SHA-256 `91031f1462e46d9c24d17cc10fde5811d948c75a91597432861d0a211a16bfe0`. Full `pytest` passed before evidence emission on both operating systems.

Implement **V2.6.3 — Exact-source Windows release candidate, SBOM, provenance and signing truth** only.

Required scope: freeze the exact candidate source from the qualified V2.6.3 head; build the R17 Windows installer; generate the release bundle/manifest; record installer SHA-256 and byte length; generate/validate SBOM and provenance; verify artifact attestation where available; record truthful Authenticode status without inventing production signing capability; perform clean install, packaged smoke and uninstall; perform deterministic/two-build comparison where required by the accepted R18 contract; and stage an immutable GitHub-release description bound to exact evidence.

Preserve all V2.6.1/V2.6.2 release boundaries. The current public/runtime baseline remains `v1.1.0-rc8`; target identity remains `1.1.0` stable/release/`v1.1.0`; production signing remains unverified unless exact V2.6.3 evidence proves otherwise; WinGet remains OUT; expired production TUF metadata remains fail-closed and belongs to V2.6.4.

Do not publish a GitHub Release, create or repoint the public `v1.1.0` tag, upload public release assets, mutate production TUF/update metadata, activate a live updater target, provision secrets, or submit WinGet.

V2.6.4 through V2.6.6 remain unauthorized until their own sequential qualification and post-merge normalization gates are satisfied.

## Current next action — V2.6.4 only

V2.6.3 is **COMPLETE + NORMALIZED** from implementation PR `#557`, exact final head `46ed800888b4f19da9e984232dd1ad6cdb639cc1`, **56/56** successful pull-request workflows and merge `9c709ad02273a388cddc66e0c00d2f3397d20af3`.

The accepted actual-Windows candidate reported **17/17 PASS**. Freeze these V2.6.3 inputs for the next subdivision:

- candidate source SHA: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- candidate identity: `1.1.0` / stable / release / `v1.1.0`;
- `KodepoiaSetup.exe`: 38,834,833 bytes, SHA-256 `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- Authenticode truth: unsigned, no production trust claim;
- public/runtime baseline: `v1.1.0-rc8`;
- production Snapshot/Timestamp freshness remains fail-closed and unresolved.

Implement **V2.6.4 — Production TUF transition and updater compatibility staging** only.

Required scope: verify production Root continuity and packaged-root pinning; prepare the exact stable target path/version/source/hash/length binding for the frozen candidate; exercise rollback/freeze/expiry/threshold/root-continuity and historical-target preservation/revocation rules; prove `rc8 -> 1.1.0` discovery and verification against isolated staged transport; preserve explicit target-scoped Authenticode-policy truth; exercise updater cache/offline behavior; and emit a deterministic metadata-transition request/evidence package suitable for the later governed live signing/publication stage.

The expired production online metadata must remain visibly fail-closed until a valid staged successor is produced. Do not weaken expiry checks, fabricate freshness, substitute synthetic keys for production authority, or mutate live production metadata.

Do **not** publish the GitHub Release or tag, upload public assets, mutate the live update repository, activate a live updater target, provision/expose production signing secrets, or submit WinGet. V2.6.5 and V2.6.6 remain unauthorized until V2.6.4 itself is exact-head qualified, merged and post-merge normalized.


## Current next action — V2.6.5 only

V2.6.4 is **COMPLETE + NORMALIZED** from implementation PR `#559`, exact final head `addbaf43b286f825ce42a11176c6647d15748845`, **52/52** successful pull-request workflows and merge `96375fb4105366b0e69eae320b0071738c59c89e`.

The dedicated transition-staging gate reported **14/14 PASS on Ubuntu** and **14/14 PASS on Windows** with common evidence SHA-256 `9620238de4344883fd43cffed621ea027d0bde4e4ed4cee051c9c32053809008`. The reviewed transition-request digest is `a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea`.

Preserve these frozen inputs:

- release candidate source SHA `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- `KodepoiaSetup.exe`: 38,834,833 bytes, SHA-256 `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- target identity `1.1.0` / stable / `channels/stable/windows-x86_64/1.1.0/46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe`;
- current public/runtime baseline `v1.1.0-rc8`;
- production Root continuity v1 packaged -> v2 public, threshold 2-of-3;
- current production Targets v8 / Snapshot v10 / Timestamp v10, with Snapshot/Timestamp still expired and fail-closed;
- future staged transition intent Root v2 / Targets v9 / Snapshot v11 / Timestamp v11, preserving historical targets and exact-target `allow-unsigned` truth.

Implement **V2.6.5 — Installed Windows release rehearsal and pre-publication go/no-go** only.

Required scope: clean install of the exact candidate; installed `v1.1.0-rc8 -> 1.1.0` upgrade rehearsal through isolated staged verified update material; packaged restart and installed-version confirmation; subsequent staged update check; custom installation directory preservation; project/settings/user-data preservation; uninstall behavior; incident rollback/recovery rehearsal; final critical-veto report; and freeze of exact publication inputs for the later governed live release.

Do **not** publish the GitHub Release or `v1.1.0` tag, upload public assets, mutate/sign live production TUF metadata, activate the live updater, provision/expose production signing secrets, or submit WinGet.

V2.6.6 remains unauthorized until V2.6.5 is exact-head qualified, merged with unchanged-head protection and post-merge normalized.


## Current next action — V2.6.6 only

V2.6.5 is **COMPLETE + NORMALIZED** from implementation PR `#561`, exact final head `d12eebe6f2e837de2617b3ef196fb26fc74ab2a6`, **53/53** successful pull-request workflows and merge `1db22c30ca36cd17de7ce27f4ee05361708d552d`.

The dedicated actual-Windows release rehearsal reported **13/13 PASS**, `critical_veto=false`, `go_no_go=GO`, evidence SHA-256 `b9eba6470e0d57e1384ef28d4e35caf512fa669a3771293555c69cdb64c18f9b`, and publication-input digest `7c0085dcce704fe19c54f4f175b28518ec86c38888f0b87c063add908c53d416`.

Freeze these terminal publication inputs:

- public installed baseline: `v1.1.0-rc8`, source `fa787ab7ef76f2556b56ac1f058916a1425455af`, installer 37,730,750 bytes, SHA-256 `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`;
- release candidate: `1.1.0` / stable / release / tag `v1.1.0`;
- candidate source SHA: `46ed800888b4f19da9e984232dd1ad6cdb639cc1`;
- candidate `KodepoiaSetup.exe`: 38,834,833 bytes, SHA-256 `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`;
- stable target path: `channels/stable/windows-x86_64/1.1.0/46ed800888b4f19da9e984232dd1ad6cdb639cc1/KodepoiaSetup.exe`;
- exact-target Authenticode policy: `allow-unsigned`;
- V2.6.3 evidence SHA-256: `80192b517ebd6a607536f52892e5b23d05448138e63d7d222c30c7f4444dc3d8`;
- V2.6.4 transition request digest: `a44914e80fb2fafb6b03f2a9847a78805b1ccb2a87fafedae9199f66c88bacea`;
- V2.6.5 publication-input digest: `7c0085dcce704fe19c54f4f175b28518ec86c38888f0b87c063add908c53d416`;
- WinGet decision: OUT.

Implement **V2.6.6 — Governed public release, production TUF transition and live updater activation** only.

Required sequence: re-fetch `main`, public `v1.1.0` tag/release state, exact V2.6.3 candidate artifact, production TUF metadata and required live signing authority; refuse if any frozen input drift exists; perform only the authorized production metadata transition with fresh Snapshot/Timestamp and preserved history; publish the immutable GitHub `v1.1.0` release/tag/assets exactly once from the frozen candidate; re-fetch and verify all public release assets; then prove the live installed `v1.1.0-rc8 -> 1.1.0` stable updater path and post-upgrade `up-to-date` state without bypassing TUF/hash/length/identity/consent checks.

Do not rebuild/substitute the candidate, weaken expiry/rollback/Root/signature checks, invent Authenticode trust, expose signing secrets, repoint an existing `v1.1.0` tag, overwrite a conflicting public asset, or submit WinGet. If required production signing material or any other live authority is unavailable, stop at the exact manual/operator boundary rather than fabricating success.

## Current next action — V2 terminally complete; await separate explicit post-V2 authority

V2.6.6 is **COMPLETE + NORMALIZED** and the complete V2 roadmap is closed.

Current public Windows distribution authority is **Kodepoia 1.1.0** / tag `v1.1.0`, exact source `46ed800888b4f19da9e984232dd1ad6cdb639cc1`, installer SHA-256 `8197bc9d8272b97394170a2c7c27b17c1e2f2849931587d21c7bdfda126da2ef`, with live production TUF Root v2 / Targets v9 / Snapshot v11 / Timestamp v11.

There is no authorized V2.7 and no R20.7. Do not reopen V2, R20, release publication, TUF mutation, updater activation or WinGet submission merely to continue numbering. Any post-V2 work requires a new, separate explicit authority and must begin from a fresh re-fetch of live `main` and the then-current continuity documents.


## Kodepoia 1.1.1 V2 terminal consolidation — PREPARATION CURRENT

The V2 roadmap remains **terminally COMPLETE + NORMALIZED**. This release work does not reopen V2,
does not authorize V2.7 or R20.7, and adds no product capability.

The user authorized a **1.1.1 consolidation release** from terminal V2 main
`913aef2cf4673a2c8b8b7874204fe1b11edcf225`. Canonical source identity is advanced to 1.1.1 only for the new consolidation
candidate. Historical V2.6.1-V2.6.6 evidence remains bound to its accepted 1.1.0 authorities.

Until exact-source candidate qualification, production TUF transition, public publication and live
updater closure all pass, the current public distribution authority remains **Kodepoia 1.1.0**.

Current next action: qualify the exact-source **1.1.1 consolidation candidate** only. Do not create
`v1.1.1`, publish a Release, mutate production TUF or activate the updater before that candidate
is qualified from an unchanged merged main.


## Kodepoia 1.1.1 — candidate qualified; offline Targets custody next

The exact-source 1.1.1 consolidation candidate is qualified from
`aa1c80389b10f5ef44737241bf192c04f847e4ec` with installer SHA-256
`c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd`
and byte length `38880869`. Candidate evidence SHA-256 is
`19a1fb1e73693f64cae7d1571c529b3f35625046ac4210375ad23ed2ac2b0d97`.

The reviewed transition request is
`docs/release/V1_1_1_TUF_TRANSITION_REQUEST.json` with request SHA-256
`03f9225ae1529b1816f3e745f7c6a4f2e84400c7570f4c3ff02172102e857abe`.

No 1.1.1 public release exists yet. Production TUF remains Root v2 / Targets v9 /
Snapshot v11 / Timestamp v11. The next effect boundary is the operator-held offline Targets
ceremony; no private key or passphrase may be pasted into chat, committed, uploaded, or emitted
by CI.


## Offline Targets v10 qualified — online Snapshot/Timestamp v12 next

The operator-held Targets custody ceremony completed successfully on 2026-10-07 using the
already-authorized Targets role. The accepted public-only outputs are frozen under
`docs/release/evidence/V1_1_1_TARGETS_V10.json`,
`V1_1_1_TARGETS_V10_CEREMONY_REPORT.json` and
`V1_1_1_TARGETS_V10_CEREMONY_SUMMARY.txt`.

Accepted offline transition truth:

- release source: `aa1c80389b10f5ef44737241bf192c04f847e4ec`;
- installer: 38,880,869 bytes;
- installer SHA-256: `c8e7949ead2e1e14adece7cb9826f0b1be689b81ac814eef2f041760b9f738cd`;
- Targets v9 -> v10;
- Targets v10 SHA-256: `94107eb8bba745603eb27dc04c2060796c15d3977bd1a68abb3cb1bf74c7148e`;
- Targets v10 length: `5902`;
- all historical targets preserved; exactly one stable 1.1.1 target added;
- Targets signature threshold satisfied by an already-authorized signer;
- Authenticode policy remains `allow-unsigned`;
- no private key path, private material, passphrase or secret value is recorded;
- `applied=false`, `offline_targets_only=true`, `online_metadata_generated=false`.

The next legitimate effect is the protected `Kodepoia 1.1.1 Online Metadata Transition`
workflow on an unchanged `main`. It may generate Snapshot v12 and Timestamp v12 around this
exact Targets v10 using the existing `tuf-production-signing` environment, but it remains
read-only and must not mutate production metadata or create the public 1.1.1 Release.
