# Kodepoia next actions

Last synchronized: 2026-09-20 after V2.3.5 implementation PR `#512` merge and post-merge normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

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

## Immediate execution order

### V2.3.6 — Model Lab hardening and integrated acceptance — AUTHORIZED

Implement V2.3.6 only.

Required acceptance coverage:

- adversarial untrusted/project/research text attempting to authorize training or promotion;
- secret-bearing or privacy-ineligible experience;
- missing, ambiguous or revoked license;
- exact and near-duplicate contamination against benchmark holdouts;
- tampered dataset manifest/export digest;
- stale or mismatched base model/tokenizer identity;
- invalid capability report or insufficient RAM/VRAM/storage;
- unsupported quantization/backend;
- mismatched checkpoint/plan lineage, cancellation and recovery;
- tampered run/evaluation/export/conversion/package evidence;
- base/candidate report mismatch;
- critical-domain regression despite aggregate gain;
- quantization/package quality regression;
- invalid promotion evidence and registry rollback integrity;
- unavailable Ollama/Kaggle/runtime capability;
- deterministic empty/missing-evidence UI states;
- Project Knowledge remaining reference-only rather than training authority;
- exact-head Ubuntu and Windows backend acceptance;
- KodeStudio UI smoke/structured-state acceptance.

Permanent boundaries:

- harden and integrate the accepted V2.3 chain; do not create replacement R15/V2.1/V2.2 engines;
- do not weaken ResearchGuard, KodeSecrets, WorkspaceBoundary, ProcessSandbox, KillSwitch, MemoryStore or immutable provenance/evidence gates;
- no public model-hub publishing, automatic training from reference context, arbitrary shell/argv/env/package installation or silent routing/model/tokenizer mutation;
- no V2.4 accelerator production qualification or new multi-GPU semantics;
- no V2.5 orchestration, V2.6 release work, release/TUF/updater mutation or R20 reopening.

Definition of done: Model Lab makes the accepted model-improvement chain usable under adversarial and degraded conditions without allowing ungoverned data ingestion, unsupported training, hidden authority promotion or unsafe model activation.

V2.4+ remain unauthorized until V2.3.6 is exact-head qualified, merged and post-merge normalized.

## Later V2 order

After V2.3.5 is COMPLETE + NORMALIZED, proceed only to V2.3.6 as authorized by the normalized V2.3 authority. V2.4, V2.5 and V2.6 remain later phases.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md. V2.3.5 est COMPLETE + NORMALIZED : PR #512 qualifiée 31/31 sur le head exact ed4197780828e54068f0f6893d5f6d4274c57d3d, acceptance 18/18 PASS Ubuntu/Windows avec evidence SHA-256 bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548, artefacts Ubuntu 10604315201 et Windows 10603926113, puis fusionnée avec expected_head_sha en c13893edb82c350b623af4c0f486a525dce116f0. La seule subdivision autorisée est V2.3.6 — Model Lab hardening and integrated acceptance. Adversarialise et intègre la chaîne V2.3 existante sans réécrire R15/V2.1/V2.2 : texte non fiable tentant d’autoriser training/promotion, privacy/license/revocation/contamination, digests ou identités altérés/stales, capability/resource/backend indisponible, checkpoint/recovery, mismatch base/candidate, critical-regression veto, qualité GGUF/package, promotion/rollback, états Ollama/Kaggle indisponibles, empty/missing-evidence UI, exact-head Ubuntu/Windows et UI smoke. Aucun V2.4+, V2.5, V2.6 release, release/TUF/updater ou R20 ne doit être tiré en avant. Project Knowledge/Research/context reste data-only. Qualifie le head final exact, merge protégé, puis normalise avant toute phase suivante.`
