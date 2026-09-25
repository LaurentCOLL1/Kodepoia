# Kodepoia — Current Authority

**Current public state:** R1–R20 COMPLETE + NORMALIZED; R20 terminal; no R20.7 authorized. The updater corrective/validation sequence ending with rc8 is complete and the exercised updater incident is **CLOSED**.  
**Current development direction:** Roadmap V2; V2.1, V2.2 and V2.3 are COMPLETE + NORMALIZED. V2.4 planning, V2.4.1, V2.4.2 and V2.4.3 are COMPLETE + NORMALIZED. **V2.4.4 is COMPLETE + NORMALIZED.** V2.4.4 implementation PR `#524` was qualified **29/29** on exact final head `1abf4917566f065ac26b71a02e02d8fb3506fe1a`, with deterministic V2.4.4 acceptance **25/25 PASS on Ubuntu and 25/25 PASS on Windows**, common evidence SHA-256 `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`, then merged with `expected_head_sha` protection as `779a9c8282e153b7dba35fb22be89ec5c622e1d3`. **V2.4.5 — Model Lab accelerator UX and live Kaggle qualification is the only authorized implementation subdivision.** V2.4.6+ remain unauthorized until V2.4.5 is implemented, exact-head qualified, merged and post-merge normalized.

This compact file summarizes the current cross-phase/public-release and development authority. It does not replace immutable historical phase evidence. For any future mutation, read it together with `docs/continuity/STATE.md` and `docs/continuity/NEXT.md`, then re-fetch the live GitHub state rather than assuming a previously recorded `main` SHA is still HEAD.

## Current repository and release

- Repository: `LaurentCOLL1/Kodepoia`.
- Canonical branch: `main`.
- Current public beta prerelease: **`v1.1.0-rc8`**.
- Exact qualified rc8 source/tag target: `fa787ab7ef76f2556b56ac1f058916a1425455af`.
- Source PR: `#462`; exact-source qualification: **40/40** PR-triggered workflows `completed/success` before merge.
- Accepted Windows installer: `KodepoiaSetup.exe`.
- Installer size: `37,730,750` bytes.
- Installer SHA-256: `6d4a02dc448b075341baf4b6fb0caf4d0a116e1b82a6937a5911efc863611422`.
- Installer claim: `production_signed=false`; rc8 is a prerelease/beta, not a production-signed stable release.
- Target-scoped TUF policy for this exact artifact: `authenticode_policy="allow-unsigned"`.
- Authoritative R17 exact-source run: `34871154670`; artifact ID: `10360685910`.
- Qualified rc8 TUF transition: PR `#464`, exact head `10804c629ca81de8b5e54ddfbfaf53370e88a201`, **30/30** PR-triggered workflows `completed/success`, merged as `1deb84e1b63581ed78ea90480fde2019623d01de` only after the public release/tag/asset were reverified.
- Closure-time CI normalization: PR `#466`, exact head `ab86b7c5b504189c69c4317317a9b7e330a33239`, **25/25** PR-triggered workflows `completed/success`, merged as `6d53794aa71a7740ca7157e41f2ae37f60f33a80`.
- Canonical rc8 E2E closure: PR `#467`, exact head `a6e67e0ad052275e6b2bf069a50c127ec4043fdf`, **25/25** PR-triggered workflows `completed/success`, merged as `e40477699d98bda2f804c269339929de719556b5`; its seven push-triggered post-merge workflows also completed successfully.

The historical `rc5 -> rc6` validation attempt remains **failed/incomplete** and must never be relabeled successful. rc7 is the corrective predecessor that restored a healthy installed baseline; rc8 is the validation-only candidate that completed the real Windows updater proof.

## Current TUF generation

- Root: **v2**, SHA-256 `c92b2165bcbf39f74599fbdf8cc30e203f8c93cc2f24c5c74012821646850ee7`, threshold 2-of-3, expiry `2027-09-08T14:59:19Z`.
- Targets: **v8**, SHA-256 `800028c1c2d42d99ed0c71f5b9a8c68cf37dd9aa36250764765f17827394acce`, length `4525`, expiry `2027-09-12T20:49:31Z`, signed by offline Targets keyid `70e86d478a769ffbefbf6febc37435a2a4563197df03d6dcda6627282fa5cf00`.
- Targets v8 preserves rc3 through rc7 and authorizes rc8 at exact source, payload URL, length and SHA-256 with `withdrawn=false` and target-scoped `authenticode_policy="allow-unsigned"`.
- Snapshot: **v10**, SHA-256 `61c8292e1eca986cd48f3523bdd0dfcbd82769fc740b126737e5ce6dcc103592`, length `470`, expiry `2026-09-17T19:48:41Z`, signed by online keyid `fac1c790b4d6dbeb04ca4a803bd80e6fde19127fc7ada34003cef5d6b50506d8`.
- Timestamp: **v10**, SHA-256 `c1b7eab48908c29ad63dc3ad2a3dfffafa157d9d15e07faf7a34ea666a7c58c7`, length `472`, expiry `2026-09-16T19:48:41Z`, signed by distinct online keyid `8d81006fd9de63660d74c43b6926ed664b2e9f1bdf81a9556367232533d5a2ad`.
- Snapshot v10 binds exact Targets v8 bytes/version/hash/length; Timestamp v10 binds exact signed Snapshot v10 bytes/version/hash/length.
- Root/Targets private custody remains outside Git/repository/CI. Snapshot/Timestamp remain distinct low-authority online signing roles.

## Real Windows updater acceptance

The complete installed updater path succeeded:

`installed rc7 -> discover rc8 -> download -> verify -> explicit consent -> installer launch -> upgrade -> restart -> confirm rc8 -> check again`

The terminal post-upgrade state showed KodeStudio running as `1.1.0-rc8`, Beta selected, candidate `1.1.0-rc8`, source `tuf-verified-metadata`, declared size `37730750` bytes and status that the installed version is current, with download/install controls disabled. Full evidence is in `docs/release/RC8_WINDOWS_E2E_ACCEPTANCE.md`.

## V2 development authority

Roadmap V1/R1–R20 remains frozen historical authority. Roadmap V2 is the active development track layered on that accepted foundation.

V2.1 Research Workspace is **COMPLETE + NORMALIZED** through V2.1.6. Its accepted chain remains:

`discovery -> candidate-only/unfetched -> explicit guarded fetch -> persisted evidence -> explicit include/exclude -> cited synthesis -> governed Research Pack`

V2.2 planning and V2.2.1 through V2.2.6 are **COMPLETE + NORMALIZED**.

Planning PR `#488` was qualified **25/25** on exact head `face3a8b9b1053962635518d083b01a92a4ed2af` and merged as `875149032078beb681816604663056f66a2e1344`.

V2.2.1 implementation PR `#490` was qualified **27/27** on exact head `f5c6e90783476117d90ee86ea7edbed014d691a7` and merged as `6341dbe6599505edc8d354e629d0fc962587f8ac`. Its deterministic acceptance reported **11/11 PASS** on Ubuntu and Windows; R16.7 also passed.

V2.2.2 implementation PR `#492` was qualified **26/26** on exact head `c3294815ddf4b76f75f04cb29ee2fdfe1d27248d` and merged with exact-head protection as `2d332945c3b1f8d76cc98d651606679c89791485`. Its deterministic acceptance reported **10/10 PASS** on Ubuntu and Windows with evidence payload SHA-256 `e9eddabeec7b15a7901cd28722ef402e2b6d3fd2306ebe8fda582f0f46594cdf`. Python Core Windows succeeded on attempt 2 on the unchanged head after an isolated historical R16.16 temp-directory lock; no source or acceptance criterion changed.

V2.2.3 implementation PR `#494` was qualified **27/27** on exact head `ac9ad68938cc13cd819bb078839c5963d03a794e` and merged with `expected_head_sha` protection as `363bf1a3afa06949269208aa6d3639e439c899e5`. Its deterministic acceptance reported **11/11 PASS** on Ubuntu and Windows with evidence payload SHA-256 `35c18af0424d15b54694ce537f89ae80de98dff262ea8168afe8ef73f5ef9765`. Exact-head artifacts were `v2-2-3-explainable-context-ubuntu-latest-ac9ad68938cc13cd819bb078839c5963d03a794e` (ID `10571726324`) and `v2-2-3-explainable-context-windows-latest-ac9ad68938cc13cd819bb078839c5963d03a794e` (ID `10571666306`).

V2.2.4 implementation PR `#496` was qualified **27/27** on exact head `c17e673d944dd0582f9c0e24368c0adf45dd3f40` and merged with `expected_head_sha` protection as `ca27459ca04abbeba8275cc32ba7166e37acfd5a`. Its deterministic acceptance reported **13/13 PASS** on Ubuntu and Windows with evidence payload SHA-256 `5ee068e69dc60eba21c840f33a1cabe88008ac247eeb9ed43a7b7fbf90f1f363`. Exact-head artifacts were `v2-2-4-version-aware-lifecycle-ubuntu-latest-c17e673d944dd0582f9c0e24368c0adf45dd3f40` (ID `10575435457`) and `v2-2-4-version-aware-lifecycle-windows-latest-c17e673d944dd0582f9c0e24368c0adf45dd3f40` (ID `10574915924`).

V2.2.5 implementation PR `#498` was qualified **31/31** on exact head `d29d10e5456623d1b7063bb37386693c1eec625a` and merged with `expected_head_sha` protection as `11479e63dc48c45f2ec97f9950430cf35c986e8c`. Its deterministic acceptance reported **13/13 PASS** on Ubuntu and Windows with evidence payload SHA-256 `22a8a287c8eead8530d2289fb19b9595e8774f0809f28c71754384b914ea8144`. Accepted exact-head artifacts were `v2-2-5-project-workspace-ubuntu-latest-d29d10e5456623d1b7063bb37386693c1eec625a` (ID `10578666529`) and `v2-2-5-project-workspace-windows-latest-d29d10e5456623d1b7063bb37386693c1eec625a` (ID `10578731421`). Python Core Windows succeeded on attempt 2 on the unchanged head after an isolated historical R16.16 temporary-directory cleanup lock; no source/workflow/acceptance criterion changed.

V2.2.6 implementation PR `#500` was qualified **26/26** on exact head `add97a4889c68b7aed79125563917ddce8b70863` and merged with `expected_head_sha` protection as `2c122c913b57c0034f73ba25c34f3fd32507fafa`. Its deterministic integrated acceptance reported **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `646071eb27ecf8e08ae7dfde3bd74e0f7d32a9dbd6e3d284a85c9093c5b5cc6d`. Accepted exact-head artifacts were `v2-2-6-project-knowledge-hardening-ubuntu-latest-add97a4889c68b7aed79125563917ddce8b70863` (ID `10582792728`) and `v2-2-6-project-knowledge-hardening-windows-latest-add97a4889c68b7aed79125563917ddce8b70863` (ID `10582857766`). V2.2.6 added adversarial integrated tests/acceptance and CI evidence without changing runtime product source.

Accepted V2.2.1 capability truth remains a deterministic project-scoped knowledge catalog over immutable Research Packs, WorkspaceBoundary-confined project files and verified active-project memory. Accepted V2.2.2 capability truth adds bounded, deterministic project-scoped semantic retrieval with explicit empty/unavailable/bound-exceeded states, project-scope enforcement before provider access, caller-supplied embeddings only, provenance-preserving duplicate normalization and no retrieval-side mutation. Accepted V2.2.3 capability truth adds explainable context candidates, deterministic selected/omitted rationale, explicit token-budget accounting through the existing ContextBuilder, preserved source/knowledge/citation traceability and `<UNTRUSTED_DATA>` rendering, and KodeStudio Auto/Include/Exclude preview without trust or authority promotion. Accepted V2.2.4 capability truth adds explicit per-item source/version fingerprints, deterministic lifecycle invalidation, derived-only refresh/rebuild/delete, persisted selection state and KodeStudio lifecycle controls while preserving immutable source evidence and retrieval exclusion of stale/invalidated items. Accepted V2.2.5 capability truth adds one project-scoped governed context snapshot consumed by Chat/KodeCode/specialists, preserves source/citation/trust/version traceability, keeps Chat data-only and KodeCode read-only, and permits durable project-context memory only through explicit-opt-in R16.7-backed derived project memory with no global/training promotion.

Active V2 authority documents are:

- `docs/roadmap/KODEPOIA_ROADMAP_V2.md`;
- `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md` — completed V2.1 Research authority;
- `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md` — completed normalized V2.2 authority;
- `docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md` — completed normalized V2.3 authority; V2.3 is closed.

V2.2 is closed at V2.2.6. No V2.2.7 is reserved or authorized.

V2.3 planning is **COMPLETE + NORMALIZED**.

Planning PR `#502` was qualified **25/25** on exact head `8a13bb5c7a334b500cebaedec8bf7988d10147c3` and merged with exact-head protection as `4744cc47827ca28c61395fc6c8e5064a18ae2b0c`.

V2.3.1 implementation PR `#504` was qualified **28/28** on exact final head `33d30747ebd915ab2bad56d3154f55a907830061` and merged with `expected_head_sha` protection as `1a7454f52bcd78ac2b44c3db467f6faa39df3a62`. Its deterministic acceptance reported **14/14 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`. Exact-head artifacts were `v2-3-1-model-lab-shell-ubuntu-latest-33d30747ebd915ab2bad56d3154f55a907830061` (ID `10588052972`) and `v2-3-1-model-lab-shell-windows-latest-33d30747ebd915ab2bad56d3154f55a907830061` (ID `10588422645`).

Accepted V2.3.1 product truth is a dedicated structured **read-only Model Lab** over existing R15 evidence and model infrastructure: bounded project-scoped evidence discovery; accepted specialized-model registry integrity validation; dataset/training/evaluation/export/registry lineage projection; saved Ollama roles plus explicit read-only installed-model refresh; explicit Kaggle doctor/quota refresh; dependency capability introspection without installation; explicit missing/invalid/stale/tampered/unavailable state; raw JSON as diagnostics only; no dataset build, training, conversion/package, promotion or rollback mutation.

V2.3.2 implementation PR `#506` was qualified **28/28** on exact final head `f419e125fa28f72bbb11dce855047a64dc3be574` and merged with `expected_head_sha` protection as `cefcffbfa55fdd0de096ebe8f029a2123c735d08`. Its deterministic acceptance reported **16/16 PASS** on Ubuntu and Windows with identical evidence payload SHA-256 `fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`. Exact-head artifacts were `v2-3-2-governed-curation-ubuntu-latest-f419e125fa28f72bbb11dce855047a64dc3be574` (ID `10593690427`) and `v2-3-2-governed-curation-windows-latest-f419e125fa28f72bbb11dce855047a64dc3be574` (ID `10592989545`).

Accepted V2.3.2 product truth is a dedicated structured **Data Curation** workspace over accepted R15 Experience/dataset governance: metadata-only eligibility/provenance/license/privacy/sanitization/revocation/quarantine/integrity; safe dedup/contamination outcomes; immutable dataset identity/digest inspection without raw JSONL payload reads; non-mutating dataset preview; typed R15-only curation/dataset-build actions with dry-run/confirmation/configured-backend and project-scope gates; no automatic Project Knowledge/Research/context ingestion; no training/conversion/promotion/rollback mutation.

Normalized V2.3 authority:

`docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md`

It freezes six subdivisions and reuses accepted R15 backends rather than creating a parallel training stack. Project Knowledge/Research/context remain reference-only and do not become training data automatically; only the accepted R15 Experience governance -> dedup/contamination -> immutable dataset path can make examples training-eligible.

V2.3.1 through V2.3.6 are **COMPLETE + NORMALIZED**.

V2.3.3 implementation PR `#508` was qualified **32/32** on exact head `e24a7d88af0f05e75b45bb1c173b0ea0d78c2ed7`, passed deterministic **16/16 PASS** acceptance on Ubuntu and Windows with identical evidence SHA-256 `8c1b92bdee6e6236f653afb749a5ea29b464b22d63ef95bd078b739a7684d064`, and merged with `expected_head_sha` protection as `b2943239885b5fc4e3791d48dfacf5b6947851a2`. Accepted exact-head artifacts are Ubuntu ID `10595259236` and Windows ID `10596176144`.

V2.3.4 implementation PR `#510` was qualified **31/31** on exact head `4f25fb6331ba76dfe51cd13c8a1560f66142a862`, passed deterministic **18/18 PASS** acceptance on Ubuntu and Windows with identical evidence SHA-256 `f8be65eaffcc71080551c30c2fc7eff56b20509f7fed74b30ceeb0ccf29e8113`, and merged with `expected_head_sha` protection as `0e88eb5e5f4a2fc7f80038dc28e580c8e93332b2`. Accepted exact-head artifacts are Ubuntu ID `10598522634` and Windows ID `10597613394`.

Accepted V2.3.4 product truth is a structured governed **Training** workspace over existing R15 runtime contracts, with immutable plan/model/tokenizer/dataset/TRAIN/capability binding, explicit local/Kaggle backend truth, fail-closed preflight, dry-run/confirmation, typed run/status/cancel/resume actions and lineage-safe checkpoints/recovery, while candidate evaluation/export/conversion/package/promotion/rollback remain outside V2.3.4.

V2.3.5 implementation PR `#512` was qualified **31/31** on exact head `ed4197780828e54068f0f6893d5f6d4274c57d3d`, passed deterministic **18/18 PASS** acceptance on Ubuntu and Windows with identical evidence SHA-256 `bb2c17564a1efa5ef5b8011559c212f96a870ce5c311bfb439d6869dc42d2548`, and merged with `expected_head_sha` protection as `c13893edb82c350b623af4c0f486a525dce116f0`. Accepted exact-head artifacts are Ubuntu ID `10604315201` and Windows ID `10603926113`.

Accepted V2.3.5 product truth is a structured **Candidate lifecycle** workspace over accepted R15.10-R15.14 contracts: persisted paired base/candidate evidence and critical-regression vetoes remain authoritative; export, GGUF conversion/quantization, Ollama packaging and specialized-model registry lineage are projected without parallel engines; the typed R15 UX gap is limited to governed export/conversion/package actions plus exact registry role selection; mutations remain dry-run/explicit-confirmation guarded; promotion requires matching accepted evaluation/export/conversion/package/registry evidence and an exact role/artifact mapping; rollback requires the immutable prior mapping; Project Knowledge/Research/chat/memory/retrieved context remains reference/data only; public model-hub publishing and silent model/tokenizer/routing replacement remain unavailable.

V2.3.6 implementation PR `#514` was qualified **26/26** on exact final head `cf79702ca05fe56620fc7ce34b3f9803fa2b0b1e`, passed deterministic **21/21 PASS** acceptance on Ubuntu and Windows with identical evidence SHA-256 `935e35c549571a9ae578515bf2acd5cf9353b264b90da5fefb644a62a6d0e8cd`, and merged with `expected_head_sha` protection as `d511c1ef081ddc02c3071892862e2f83ed5ba8c0`. Accepted exact-head artifacts are Ubuntu ID `10609481837` and Windows ID `10610285166`.

Accepted V2.3.6 product truth is adversarial and degraded-state proof over the already accepted V2.3/R15 chain, not a new engine or product surface: untrusted Project Knowledge/Research/context cannot authorize training or promotion; privacy/license/revocation/contamination and tampered/stale evidence remain fail closed; capability/resource/backend and checkpoint lineage failures remain explicit; paired candidate evaluation preserves critical-regression vetoes; GGUF/Ollama quality gates and registry promotion/rollback integrity remain binding; unavailable Ollama/Kaggle/runtime states remain honest; deterministic empty/missing-evidence UI remains accessible; public model-hub publishing, silent routing/model/tokenizer mutation, V2.4 accelerator implementation and release/R20 mutation remain unavailable.

The two corrective commits after the initial hardening head aligned test assertions and ineligible-experience fixtures with the already accepted live contracts. No product code, gate, workflow criterion or trust boundary was weakened.

The V2.3.4 post-merge normalization historically made **V2.3.5 is now the only authorized implementation subdivision** while **V2.3.6+ remain unauthorized**. That historical boundary is retained for acceptance provenance and is superseded by the later V2.3 normalizations.

V2.3 is **COMPLETE + NORMALIZED** through V2.3.6. V2.4 planning, V2.4.1, V2.4.2, V2.4.3 and **V2.4.4 are COMPLETE + NORMALIZED**. V2.4.3 remains accepted from PR `#522`, exact head `81c5709ff457da375fd2f8f8ef13aad4b59aced0`, merge `975d46a071f52a27a48de15227432d9d4911e142`. V2.4.4 implementation PR `#524` was qualified **29/29** on exact final head `1abf4917566f065ac26b71a02e02d8fb3506fe1a`; deterministic acceptance passed **25/25 on Ubuntu** and **25/25 on Windows** with common evidence SHA-256 `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`, Ubuntu artifact `10654524114` and Windows artifact `10655573341`. It merged with `expected_head_sha` protection as `779a9c8282e153b7dba35fb22be89ec5c622e1d3`. Accepted V2.4.4 truth derives a rank-zero canonical checkpoint manifest only from a completed exact-lineage V2.4.3 report plus both rank evidences; independently binds checkpoint metadata and artifact digests; binds exact execution/TrainingPlan/strategy/benchmark/topology/world-size/device identity; permits resume only from a checkpoint strictly before max steps; reuses the fixed one-node/two-rank repository-owned launcher and R15.9 real resume semantics; requires both resumed ranks and recovery-specific evidence; and treats timeout/cancel/nonzero/missing/tampered/mismatched rank evidence as whole-group terminal. Historical V2.4.3 `resume_authorized=false` remains intact; no pooled VRAM, FSDP, DeepSpeed/ZeRO, tensor/pipeline parallelism, TPU or live-provider qualification was introduced. **This normalization authorizes V2.4.5 — Model Lab accelerator UX and live Kaggle qualification only.** V2.4.6+ remain unauthorized until V2.4.5 is implemented, exact-head qualified, merged and post-merge normalized. V2.5+, release/TUF/updater mutation and R20 reopening remain unauthorized.

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




Existing security authority remains unchanged: immutable Research Pack provenance, ResearchGuard, KodeSecrets, WorkspaceBoundary and R16.7 MemoryStore integrity/quarantine/project-scope rules remain binding. Indexed, retrieved or context-selected data never gains instruction authority merely by being selected or scored.

Post-rc8 source features on `main` remain development capabilities until a later release is explicitly qualified. Their presence in source does not mean they exist in the public rc8 installer.

Kaggle **T4×2** remains the primary V2 remote-training target for the current CUDA/PyTorch/PEFT/QLoRA path; the two devices remain separate 16 GiB GPUs. TPU v5e-8 remains deferred experimental capacity.

No post-rc8 release version or TUF transition is authorized solely by the V2 roadmap.

## Continuity hierarchy

Use the following documents in this order when interpreting current state:

1. `docs/continuity/STATE.md` for immediate operational authority;
2. `docs/continuity/NEXT.md` for the next authorized direction and resume prompt;
3. this file for the compact cross-phase/public-release/development summary;
4. `docs/roadmap/KODEPOIA_ROADMAP_V2.md` for the active V2 development ordering;
5. `docs/roadmap/V2_4_KAGGLE_T4X2_PRODUCTION_MULTIGPU.md` for normalized V2.4 planning/V2.4.1/V2.4.2/V2.4.3/V2.4.4 authority and the current V2.4.5 boundary;
6. `docs/roadmap/V2_3_MODEL_LAB_GOVERNED_IMPROVEMENT_UX.md` for completed normalized V2.3 authority through V2.3.6;
7. `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md` for completed V2.1 Research authority;
8. `docs/roadmap/V2_2_PROJECT_KNOWLEDGE_CONTEXT_MEMORY.md` for completed normalized V2.2 authority;
9. `docs/continuity/KODEPOIA_CONTINUITY_R20.md` for terminal R20 authority and historical post-R20 release operations;
10. `docs/continuity/KODEPOIA_CONTINUITY_R19.md` for frozen R19 authority;
11. `docs/continuity/KODEPOIA_CONTINUITY.md` for the large historical R1–R18 continuity archive;
11. phase plans and Git history for immutable phase-specific evidence.

The large legacy continuity archives intentionally remain historical. Stale “current” wording inside old frozen sections is superseded by `STATE.md`, `NEXT.md`, this file and the explicit current-distribution section of the R20 continuity rather than by retroactive rewriting of historical phase evidence.

## Terminal R20 boundary

R20 is **COMPLETE + NORMALIZED**. Post-R20 releases and updater/TUF operations are release operations built on the completed R20 machinery. They do **not** create R20.7 or reopen R20.

The rc7 corrective release, rc8 validation-only release, rc8 TUF authorization, public release verification, real Windows rc7 -> rc8 E2E and continuity closure are complete. No additional rc8 corrective release or TUF mutation is required by this incident. V2 work proceeds as a new roadmap while preserving all existing fail-closed trust invariants.
