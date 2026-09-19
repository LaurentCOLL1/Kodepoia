# V2.3 — Model Lab governed improvement UX

Status: **PLANNING COMPLETE + NORMALIZED; V2.3.1 and V2.3.2 COMPLETE + NORMALIZED — V2.3.3 is the only authorized implementation subdivision**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Planning base: normalized `main` `b5ac64becc4b748aa77386121ba6a63e02cf88bd`  
Public distribution boundary: `v1.1.0-rc8`

## Planning qualification

Planning PR `#502` was qualified on exact final head:

`8a13bb5c7a334b500cebaedec8bf7988d10147c3`

All **25/25** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35447327711`;
- `KodeStudio UI Smoke` run `35447327644`;
- `Python Core` run `35447327756`;
- `R12 Tauri2 Acceptance` run `35447327773`;
- `R13 Integrated Release Readiness` run `35447327678`;
- `R17 Windows Installer` run `35447327730`.

PR `#502` merged from that unchanged exact head with `expected_head_sha` protection as:

`4744cc47827ca28c61395fc6c8e5064a18ae2b0c`

This post-merge normalization satisfies the planning definition of done and authorizes **V2.3.1 — Model Lab shell, inventory and lineage only**.

V2.3.2 through V2.3.6 remain planned and unauthorized until each prior subdivision is implemented, exact-head qualified, merged and post-merge normalized.

## 1. Authority and goal

V2.1 Research Workspace and V2.2 Project Knowledge / Context Builder / Memory integration are **COMPLETE + NORMALIZED**.

V2.3 exists to turn the already accepted R15 Experience / Bench / Fine-tuning machinery into a coherent, inspectable and fail-closed **Model Lab** inside KodeStudio.

The goal is not to invent a new training stack. The goal is to make the existing governed model-improvement chain understandable and deliberately operable by a user:

`eligible experience -> governed dataset -> benchmark/gap diagnosis -> TRAIN or NO_TRAIN -> capability probe -> immutable training plan -> bounded run -> base/candidate evaluation -> export/conversion/package -> explicit promotion or rollback`

The existing R15 backend remains authoritative for the underlying contracts and mutations.

V2.3 must make every transition visible, evidence-bound and reversible where the accepted backend already provides rollback semantics.

## 2. Existing accepted primitives that V2.3 must reuse

V2.3 planning is derived from live source and accepted R15 authority, including:

### Experience and dataset governance

- `src/kodepoia/experience/contracts.py` — typed experience contracts and training-data trust boundary;
- `src/kodepoia/experience/collector.py` — governed validated-experience capture;
- `src/kodepoia/experience/governance.py` — sanitization, privacy, license provenance and revocation;
- `src/kodepoia/experience/dedup.py` — deduplication, contamination firewall and quarantine;
- `src/kodepoia/experience/dataset.py` — immutable dataset builder, manifests, deterministic splits, export digests and dataset cards.

### Benchmark and decision authority

- `src/kodepoia/bench/kodebench.py` — KodeBench v2 registry and reproducible scoring;
- `src/kodepoia/bench/decision.py` — governed gap diagnosis and explicit `TRAIN` / `NO_TRAIN` decision;
- `src/kodepoia/bench/evaluation.py` — base-vs-candidate comparison and critical-regression veto.

### Training and runtime authority

- `src/kodepoia/tuning/contracts.py` — backend/resource/quantization/capability contracts;
- `src/kodepoia/tuning/runtime.py` — capability probes and fail-closed resource preflight;
- `src/kodepoia/tuning/training.py` — immutable `TrainingPlan`, exact model/tokenizer/dataset binding, bounded SFT/QLoRA run, checkpoint/recovery/cancel contracts;
- `src/kodepoia/tuning/kaggle_remote.py` — already accepted governed Kaggle remote-training bundle/doctor path;
- `src/kodepoia/tuning/local_qualification.py` — local hardware qualification evidence.

### Export, packaging and promotion authority

- `src/kodepoia/tuning/export.py` — accepted candidate export lineage;
- `src/kodepoia/tuning/gguf.py` — GGUF conversion and quantization quality gates;
- `src/kodepoia/tuning/ollama_packaging.py` — local Ollama packaging/import safety;
- `src/kodepoia/tuning/model_registry.py` — specialized-model registry, immutable lineage, promotion and rollback;
- `src/kodepoia/models/router.py` — role-aware runtime model registry/router;
- `src/kodepoia/kodestudio/model_manager.py` — installed Ollama models and user model-role preferences.

### Existing UX facade

- `src/kodepoia/tuning/r15_ux.py` already defines a typed action catalog over experience, dataset, bench, gap, training, conversion, Ollama and registry actions;
- `src/kodepoia/kodestudio/r15_tuning_panel.py` exposes that catalog in KodeStudio with explicit confirmation and dry-run support.

The current R15 UI is intentionally generic and JSON-heavy. V2.3 may improve presentation and workflow guidance, but it must not weaken or bypass the typed R15 backend contracts.

## 3. Permanent trust and data-eligibility invariants

The following remain binding across all V2.3 subdivisions:

1. **No automatic training capture.** Chats, project files, Research Packs, Project Knowledge, retrieved context, tool output and memory are not training examples merely because they exist or were useful.
2. **V2.2 Project Knowledge is reference/context data, not training authority.** It may inform diagnosis or display supporting context, but training eligibility must flow through the accepted R15 Experience governance path.
3. **Explicit eligibility is required.** A training example must have accepted source/provenance, scope, consent/eligibility, sanitization, license and revocation state.
4. **Secrets remain forbidden.** KodeSecrets/redaction rules and the R15 secret checks remain fail closed.
5. **Unknown license is not permission.** Ambiguous, missing or revoked license/provenance prevents training eligibility.
6. **Benchmark contamination is a hard blocker.** Holdouts and near-duplicates cannot enter training data.
7. **Datasets are immutable identities.** Training must bind to exact dataset/manifest/export digests.
8. **Model and tokenizer identities are exact.** A training plan must preserve base model revision/digest and tokenizer revision/digest.
9. **TRAIN is explicit evidence, not a UI convenience.** A model-gap diagnosis may validly conclude `NO_TRAIN`; V2.3 must present that outcome as first-class.
10. **Capability state is honest.** Missing CUDA, VRAM, dependencies, Kaggle auth/network/quota or conversion tools remain explicit unsupported/unavailable/blocked states.
11. **No arbitrary command surface.** Model text, dataset content or UI fields cannot construct raw shell/argv/env execution outside the accepted structured backend.
12. **Critical regressions veto promotion.** Aggregate improvement never overrides a critical-domain regression.
13. **Promotion is a separate explicit mutation.** Training or export success does not silently alter model routing or active-role mappings.
14. **Rollback remains available where the accepted registry contract supports it.**
15. **No public publishing by default.** V2.3 does not authorize uploading datasets, adapters or models to public hubs/registries.
16. **No authority promotion from AI-generated text.** Research/project/model output is evidence or data only unless an existing explicit governance contract grants a specific mutation.
17. **Exact-head evidence remains mandatory.** Every V2.3 implementation subdivision must be qualified on its final SHA.

## 4. Relationship with V2.2 Project Knowledge

V2.3 may read the active V2.2 project context for explainability and diagnostics, for example:

- showing which project facts motivated a benchmark/gap investigation;
- linking a benchmark gap to cited project requirements;
- helping a user understand why a training proposal exists.

This does **not** create a shortcut into training data.

Any content that is to become training material must enter through the R15 Experience contracts and pass:

`capture/eligibility -> governance/sanitization/license -> dedup/contamination -> immutable dataset build`

The existing `ProjectMemoryBridge` and Project Knowledge catalog must never be treated as implicit training dataset stores.

## 5. Model Lab UX direction

Model Lab should replace the current JSON-first mental model with a structured workspace while keeping raw JSON available for diagnostics.

The target KodeStudio experience should provide:

- a phase/status overview showing what is ready, blocked, missing or rejected;
- immutable identities/digests and lineage links where relevant;
- clear distinction between inspect, dry-run and mutation;
- explicit prerequisite explanations before a mutation can become enabled;
- structured source/license/quarantine/revocation state for data;
- benchmark and gap evidence rather than a single opaque score;
- visible `TRAIN` / `NO_TRAIN` decision and reasons;
- structured training-plan review before launch;
- visible runtime/backend capability and resource blockers;
- run progress/checkpoint/cancel/recovery state;
- base-vs-candidate regression tables, with critical regressions highlighted structurally;
- export/conversion/package lineage;
- explicit promotion and rollback with the exact model-role mapping affected;
- a history/lineage view that lets a user trace model -> dataset -> training plan -> run -> evaluation -> export -> packaged variant -> registry state.

Raw JSON may remain available behind diagnostics, but it must not be the primary UX.

## 6. V2.3 subdivisions

The subdivision list below is frozen by the accepted V2.3 planning authority. No subdivision may be silently added, removed, merged, split or renumbered.

### V2.3.1 — Model Lab shell, inventory and lineage — COMPLETE + NORMALIZED

Goal: create the structured Model Lab workspace and make current model-improvement state inspectable before enabling new mutations.

Required scope:

- dedicated Model Lab entry in KodeStudio;
- read-only overview of accepted R15 evidence stores;
- installed/local Ollama inventory plus saved role preferences;
- specialized-model registry candidates/active/retired/rejected state;
- dataset identities/cards/manifests and benchmark/training/evaluation/export evidence discovery;
- runtime capability summary without installing dependencies;
- Kaggle doctor/auth/network/quota state may be displayed when available, without changing accelerator behavior;
- lineage graph/table from dataset -> plan -> run -> evaluation -> export/conversion/package -> model-registry version;
- explicit missing/stale/tampered/unavailable states;
- raw JSON remains diagnostics-only.

Non-goals:

- no new training;
- no dataset build mutation;
- no promotion/rollback mutation;
- no V2.4 accelerator-production work.

Definition of done: the user can inspect what Model Lab knows, where each artifact came from, and which prerequisites block later operations without running a mutation.

Accepted implementation evidence:

The implementation was developed and qualified while the governing subdivision marker was exactly `V2.3.1 — Model Lab shell, inventory and lineage — CURRENT`. That historical marker is retained here as immutable acceptance context only; it is superseded by the `COMPLETE + NORMALIZED` status above and does not re-authorize V2.3.1.

- implementation PR `#504`;
- exact final head `33d30747ebd915ab2bad56d3154f55a907830061`;
- **28/28** pull-request workflows `completed/success`;
- merge `1a7454f52bcd78ac2b44c3db467f6faa39df3a62` with `expected_head_sha` protection;
- deterministic **14/14 PASS** exact-head acceptance on Ubuntu and Windows;
- identical evidence payload SHA-256 `5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`;
- Ubuntu artifact `v2-3-1-model-lab-shell-ubuntu-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588052972`;
- Windows artifact `v2-3-1-model-lab-shell-windows-latest-33d30747ebd915ab2bad56d3154f55a907830061` — ID `10588422645`.

Accepted product truth:

- the Model Lab is a dedicated structured KodeStudio surface over existing R15 evidence/model infrastructure rather than a parallel backend;
- R15 evidence discovery is bounded, project-scoped and read-only;
- accepted specialized-model registry digest/integrity validation is reused;
- dataset/training/evaluation/export/registry digests are exposed through read-only lineage;
- saved Ollama role preferences are visible before any runtime access and installed-model inventory is refreshed explicitly;
- Kaggle doctor/quota state is refreshed explicitly and does not alter accelerator behavior;
- dependency capability is introspected without dependency/driver installation;
- missing, invalid, stale, tampered and unavailable states are explicit;
- raw JSON remains secondary diagnostics;
- no dataset build, training, conversion/package, promotion or rollback mutation exists in V2.3.1;
- Project Knowledge/Research/context remains reference-only and is not training authority.

This normalization closes V2.3.1 and authorizes **V2.3.2 only**.

### V2.3.2 — Governed experience and dataset curation workspace — COMPLETE + NORMALIZED

Goal: expose the accepted R15 training-data trust boundary as a structured, deliberate UX.

Required scope:

- inspect experience eligibility and provenance;
- show source type/identity, project scope, consent/eligibility, privacy/sanitization, license assessment, revocation and quarantine state;
- expose dedup/near-duplicate and holdout-contamination outcomes;
- explicit curation transitions only through accepted handlers;
- dataset-build preview/dry-run with row/split/license/domain/task summaries;
- immutable dataset identity, manifest/export digests and dataset card after build;
- revoked/quarantined/ineligible examples remain excluded;
- Project Knowledge/context may be linked for explanation but never auto-ingested.

Definition of done: a user can understand exactly why an example is or is not training-eligible and can deliberately build an immutable dataset without bypassing governance.

Accepted implementation evidence:

The implementation was developed and qualified while the governing subdivision marker was exactly `V2.3.2 — Governed experience and dataset curation workspace — CURRENT`. That historical marker is retained here as immutable acceptance context only; it is superseded by the `COMPLETE + NORMALIZED` status above and does not re-authorize V2.3.2.

- implementation PR `#506`;
- exact final head `f419e125fa28f72bbb11dce855047a64dc3be574`;
- **28/28** pull-request workflows `completed/success`;
- merge `cefcffbfa55fdd0de096ebe8f029a2123c735d08` with `expected_head_sha` protection;
- deterministic **16/16 PASS** exact-head V2.3.2 acceptance on Ubuntu and Windows;
- identical evidence payload SHA-256 `fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`;
- Ubuntu artifact `v2-3-2-governed-curation-ubuntu-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10593690427`;
- Windows artifact `v2-3-2-governed-curation-windows-latest-f419e125fa28f72bbb11dce855047a64dc3be574` — ID `10592989545`.

Accepted V2.3.2 product truth:

- KodeStudio now has a dedicated structured **Data Curation** workspace while the accepted V2.3.1 Model Lab and R15 Experience / Tune surfaces remain available;
- governed experience inspection exposes metadata, provenance, project scope, authorization/consent, license, privacy, sanitization, benchmark protection, revocation/quarantine and integrity without displaying or reading raw experience payloads;
- deduplication and benchmark-holdout contamination evidence is presented as safe group/finding metadata, including exact/near match state, while contaminated groups remain dataset-ineligible;
- immutable dataset manifests/cards are inspected through deterministic dataset identity/digest checks without reading exported JSONL rows;
- non-mutating dataset preview summarizes candidate/excluded rows, exclusion reasons, licenses, domains, tasks and honest split-policy availability;
- experience curation and dataset build mutations delegate exclusively to accepted typed `R15UXService` handlers; preview remains dry-run and apply remains explicit-confirmation/configured-backend gated;
- the curation facade rejects cross-project R15 service binding and exposes no training, conversion/package, promotion or rollback control;
- Project Knowledge, Research Packs, chat, memory and retrieved context are not scanned or auto-ingested as training examples;
- FR/EN/pseudo-localization and central KodeStudio accessibility contracts include the new curation controls.

Two qualification-only defects were corrected before the final accepted head: the historical V2.3.1 pseudo-localization acceptance was made forward-compatible without weakening its Model Lab assertion, and the V2.3.2 tamper fixture was corrected so its test mutation actually changes the governed record. No gate was weakened; only the exact final head above is accepted.

This normalization closes V2.3.2 and authorizes **V2.3.3 only**.

### V2.3.3 — Bench, gap diagnosis and TRAIN/NO_TRAIN decision UX — CURRENT

Goal: make model-improvement decisions evidence-driven before training is offered.

Required scope:

- structured KodeBench suite/task/domain results;
- base-model identity and reproducible run/config digests;
- gap diagnosis that distinguishes model capability from tool, retrieval, routing, context, prompt and product defects;
- explicit `TRAIN`, `NO_TRAIN`, `NOT_NEEDED`, blocked or inconclusive state as provided by accepted decision contracts;
- evidence/reason presentation for the decision;
- project/context references may support diagnosis but remain data-only;
- training controls remain disabled unless an accepted `TRAIN` authorization can be bound to a valid immutable dataset and exact base model.

Definition of done: the user can see why training is or is not justified and cannot launch training from an unsupported or inconclusive diagnosis.

### V2.3.4 — Governed training plan, execution and recovery UX

Goal: expose the accepted R15 training runtime safely and transparently.

Required scope:

- structured immutable training-plan preview over existing `TrainingPlan`;
- exact base model/tokenizer identity and dataset binding;
- SFT/QLoRA mode, LoRA and SFT parameters only within accepted backend validation bounds;
- runtime capability probe and resource preflight before launch;
- local backend states plus the already accepted governed Kaggle remote path may be selectable when available;
- Kaggle remains an auth/network/quota-dependent backend and no V2.4 production/multi-GPU claim is made;
- explicit dry-run and explicit user confirmation before launch;
- run ID, plan digest, state, progress evidence, checkpoints and losses where available;
- cancel through accepted KillSwitch/ProcessSandbox path;
- resume/recovery only from matching checkpoint/plan lineage;
- no arbitrary command, env or dependency-install surface;
- fixture-driven deterministic acceptance must not require a live GPU or Kaggle account.

Definition of done: a user can review, launch, monitor, cancel and recover an authorized bounded training run without bypassing capability, resource or lineage gates.

### V2.3.5 — Candidate evaluation, export, promotion and rollback UX

Goal: make candidate acceptance and activation an evidence-bound deliberate decision.

Required scope:

- paired base-vs-candidate benchmark comparison on matching suite/config/holdout evidence;
- task/domain deltas and explicit critical-regression veto;
- training-loss/overfit/resource evidence where available;
- clear candidate disposition: reject, inconclusive or promotable/exportable;
- export lineage over accepted R15.11 contract;
- GGUF conversion/quantization quality state over accepted R15.12 contract;
- local Ollama packaging/import state over accepted R15.13 contract;
- specialized-model registry lineage/variants/role eligibility over accepted R15.14 contract;
- explicit promotion mutation with exact role mapping shown before confirmation;
- explicit rollback to prior immutable mapping;
- no public model-hub publishing;
- no silent replacement of base model, tokenizer or routing preferences.

Definition of done: a user cannot promote a model without accepted comparison/export/package evidence and can trace or roll back the resulting role mapping.

### V2.3.6 — Model Lab hardening and integrated acceptance

Goal: adversarially prove the complete V2.3 UX and governance chain without weakening R15, V2.1 or V2.2.

Required acceptance coverage includes:

- untrusted/project/research text attempting to authorize training or promotion;
- secret-bearing or privacy-ineligible experience;
- missing/ambiguous/revoked license;
- exact and near-duplicate contamination against benchmark holdouts;
- tampered dataset manifest/export digest;
- stale or mismatched base model/tokenizer identity;
- invalid capability report or insufficient RAM/VRAM/storage;
- unsupported quantization/backend;
- mismatched checkpoint/plan lineage;
- cancellation and recovery;
- tampered run/evaluation/export/conversion/package evidence;
- base/candidate report mismatch;
- critical-domain regression despite aggregate gain;
- quantization/package quality regression;
- invalid promotion evidence;
- registry rollback integrity;
- unavailable Ollama/Kaggle/runtime capability;
- deterministic empty/missing-evidence UI states;
- Project Knowledge remaining reference-only rather than training authority;
- exact-head Ubuntu and Windows backend acceptance;
- KodeStudio UI smoke/structured-state acceptance.

Definition of done: Model Lab makes the accepted model-improvement chain usable without allowing ungoverned data ingestion, unsupported training, hidden authority promotion or unsafe model activation.

## 7. Backend reuse map

V2.3 implementation should prefer adapters/facades over backend rewrites.

Expected reuse:

- Experience page -> `experience.contracts/collector/governance/dedup/dataset`;
- Bench/Decision page -> `bench.kodebench/decision/evaluation`;
- Training page -> `tuning.contracts/runtime/training/kaggle_remote/local_qualification`;
- Candidate page -> `tuning.export/gguf/ollama_packaging/model_registry`;
- Local installed model inventory -> `kodestudio.model_manager` / `brain.ollama`;
- role/runtime semantics -> `models.router`;
- structured mutation policy -> existing `R15UXService` action contracts, extended only where a typed gap is proven;
- Project Knowledge references -> V2.2 shared governed context, reference-only.

A new backend primitive requires evidence that no accepted R15/V2.2 primitive satisfies the need.

## 8. Accelerator boundary

Kaggle `GPU T4 x2` remains the priority remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack.

V2.3 may:

- display the existing Kaggle doctor/auth/network/quota state;
- use the already accepted governed remote-training bundle path when explicitly selected and available;
- preserve exact training-plan/dataset/model binding across remote execution.

V2.3 must not:

- claim that two T4 devices form one 32 GiB pool;
- add or claim new multi-GPU training semantics;
- claim production accelerator qualification;
- create a new TPU/XLA/JAX/PyTorch-XLA backend;
- move V2.4 acceptance into V2.3.

TPU v5e-8 remains deferred. V2.4 owns accelerator production qualification and explicit multi-GPU work.

## 9. Failure and degraded-state UX

At minimum Model Lab must distinguish:

- no governed experiences;
- experiences exist but none are training-eligible;
- privacy/license/revocation blocked;
- contamination/quarantine blocked;
- no immutable dataset;
- no benchmark evidence;
- `NO_TRAIN` / `NOT_NEEDED`;
- decision inconclusive;
- runtime dependency unavailable;
- backend unsupported;
- resource budget blocked;
- Kaggle auth/network/quota unavailable;
- run cancelled/timed out/failed;
- checkpoint unavailable or incompatible;
- evaluation inconclusive;
- candidate rejected for critical regression;
- export/conversion/package unavailable or rejected;
- promotion blocked;
- rollback unavailable;
- active candidate/role mapping missing or stale.

No degraded state may be represented as a successful empty result when the backend contract distinguishes the condition.

## 10. Security and mutation boundaries

Model Lab remains local-first and fail closed.

Protected mutations include:

- experience curation;
- dataset build;
- benchmark execution;
- training launch/cancel/recovery;
- conversion/package operations;
- model promotion/rollback;
- local model installation/deletion where existing Model Manager exposes it.

Every mutation must use an accepted typed API, explicit policy state and user confirmation where the current backend requires confirmation.

Prompt/source/model text cannot become an argv, shell command, environment variable, filesystem escape, package-install request, permission grant or registry promotion instruction.

WorkspaceBoundary, ProcessSandbox, KillSwitch, KodeSecrets and existing digest/lineage validation remain in force.

## 11. Acceptance discipline

Every V2.3 implementation subdivision must follow:

1. re-fetch live `main` and the normalized V2.3 authority;
2. create a dedicated branch from the exact current `main` SHA;
3. implement only the authorized subdivision;
4. add deterministic backend/UI tests and exact-head acceptance;
5. use fixture/mocked capability evidence for mandatory CI where real GPU/Kaggle/Ollama is unavailable;
6. never fabricate a live accelerator/provider success;
7. re-fetch every `pull_request` workflow for the exact final head;
8. merge only when all required workflows on that exact head are `completed/success`;
9. post-merge normalize continuity before authorizing the next subdivision.

Any new commit invalidates all previous CI evidence for that branch head.

A real manual intervention stops the sequence rather than being bypassed.

## 12. Explicit non-goals

V2.3 does not authorize:

- V2.4 accelerator production qualification or new multi-GPU behavior;
- TPU v5e-8 implementation;
- V2.5 cross-workspace orchestration/handoff automation;
- V2.6 release hardening/public release work;
- release/TUF/updater mutation;
- R20 reopening or `R20.7`;
- RLHF, DPO, PPO, RLAIF, autonomous self-reward or online-learning architecture;
- full-parameter large-model fine-tuning as the default path;
- automatic training from Project Knowledge, memory, chats or Research Packs;
- automatic public publishing to Hugging Face/Ollama/model hubs;
- arbitrary-shell training configuration;
- silent dependency/GPU-driver installation;
- silent role/routing changes after a successful training run.

## 13. Planning definition of done

The V2.3 planning phase is complete because:

- this document is present as the dedicated V2.3 normative authority;
- the six subdivisions above are recorded in current continuity and Roadmap V2;
- R15/V2.2 reuse and trust boundaries are explicit;
- V2.4/V2.5/V2.6 and release/R20 boundaries are explicit;
- planning PR `#502` was qualified **25/25** on exact head `8a13bb5c7a334b500cebaedec8bf7988d10147c3`;
- planning PR `#502` was merged with `expected_head_sha` protection as `4744cc47827ca28c61395fc6c8e5064a18ae2b0c`;
- the planning post-merge normalization authorized **V2.3.1 only**;
- V2.3.1 implementation PR `#504` was qualified **28/28** on exact head `33d30747ebd915ab2bad56d3154f55a907830061`, passed deterministic **14/14** acceptance on Ubuntu and Windows with evidence SHA-256 `5063e101b899d2e7a409ab14d4e2ab684cb98b67f963980fdc8e9f990061b6cc`, and merged as `1a7454f52bcd78ac2b44c3db467f6faa39df3a62`;
- the V2.3.1 post-merge normalization recorded V2.3.1 as **COMPLETE + NORMALIZED** and authorized **V2.3.2 only**;
- V2.3.2 implementation PR `#506` was qualified **28/28** on exact head `f419e125fa28f72bbb11dce855047a64dc3be574`, passed deterministic **16/16** acceptance on Ubuntu and Windows with evidence SHA-256 `fdbd30700e56db014bbf8ac35c33ce783bfc3444a4d06a33a6637dce04fb19af`, and merged as `cefcffbfa55fdd0de096ebe8f029a2123c735d08`;
- this post-merge continuity normalization records V2.3.2 as **COMPLETE + NORMALIZED** and authorizes **V2.3.3 only**.

**V2.3.3 is now the only authorized implementation subdivision. V2.3.4+ remain unauthorized.**
