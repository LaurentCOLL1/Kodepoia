# V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU

Status: **PLANNING + V2.4.1 + V2.4.2 + V2.4.3 + V2.4.4 COMPLETE + NORMALIZED — V2.4.5 is the only authorized implementation subdivision; V2.4.6+ remain unauthorized**  
Roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`  
Planning base: normalized `main` `586d55a3cbccaadbb2a868c5fd5e0ed0123bf8b0`  
Public distribution boundary: `v1.1.0-rc8`

## Planning qualification

Planning PR `#516` was qualified on exact final head:

`8c78ff19cf05b3009a05e2e5337ce31303e9d8b7`

All **25/25** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35535395734`;
- `KodeStudio UI Smoke` run `35535395763`;
- `Python Core` run `35535395830`;
- `R13 Integrated Release Readiness` run `35535395854`;
- `R17 Windows Installer` run `35535395721`.

PR `#516` merged from that unchanged exact head with `expected_head_sha` protection as:

`a14190f529a465e8e42ee0dd90a0248bc38e1b9c`

The initial planning head `7142659d00cea3ae6faf427ed100fb84ce28668e` exposed only two historical V2.3.5 authority-compatibility assertions after the repository advanced to V2.4 planning. Corrective commit `8c78ff19cf05b3009a05e2e5337ce31303e9d8b7` made the V2.3.5/V2.3.6 acceptance contracts forward-compatible with the new planning state and fixed a duplicated `NEXT.md` heading. It changed no V2.4 runtime/product code and weakened no product, security or trust gate.

This post-merge normalization satisfies the planning definition of done and authorizes **V2.4.1 — Accelerator topology and provider truth only**. V2.4.2+ remain unauthorized until V2.4.1 is implemented, exact-head qualified, merged and post-merge normalized.

## V2.4.1 qualification

V2.4.1 implementation PR:

`#518 — feat: implement V2.4.1 accelerator topology truth`

Exact final accepted head:

`544b7d172499594f32c464c46753bfc5fb378fe0`

All **30/30** pull-request workflows associated with that exact final head completed with conclusion `success`.

Deterministic exact-head acceptance:

- Ubuntu: **22/22 PASS**;
- Windows: **22/22 PASS**;
- common evidence SHA-256: `3049f1d4fb07d8edb4d8722ffaf1a1d8e503186972eec2dfb000a5057f519c6d`;
- Ubuntu artifact ID: `10614179278`;
- Windows artifact ID: `10614546908`.

Selected successful workflow runs include:

- `R0 Repository Guard` — `35540624489`;
- `R15.8 Training Runtime Acceptance` — `35540624402`;
- `R15 Kaggle Remote Training Acceptance` — `35540624433`;
- `R15.9 QLoRA SFT Acceptance` — `35540624448`;
- `Python Core` — `35540624471`;
- `R15 Integrated Acceptance` — `35540624649`;
- `R13 Integrated Release Readiness` — `35540624507`;
- `R17 Windows Installer` — `35540624572`.

PR `#518` merged from the unchanged exact final head with `expected_head_sha` protection as:

`3ebed48b8aa113635ddc9516827d867ce346fe0f`

Accepted V2.4.1 truth:

- historical R15.8 capability schema v1 remains intact;
- topology evidence is separate and versioned;
- actual CUDA/ROCm devices are enumerated with independent per-device VRAM;
- legacy scalar device/VRAM evidence remains device-zero evidence;
- provider request and observed topology have separate digests;
- Kaggle `NvidiaTeslaT4` requests two T4-class CUDA devices but never proves runtime topology;
- topology/provider mismatch, ambiguous identity and unknown selected-device VRAM fail closed;
- `single_gpu` resource admission uses one selected device only and never pools VRAM;
- no distributed training launch or replicated execution path exists yet.

This normalization marks **V2.4.1 COMPLETE + NORMALIZED** and authorizes **V2.4.2 only**.

## V2.4.2 qualification

V2.4.2 implementation PR:

`#520 — feat: implement V2.4.2 strategy planning contract`

Exact final accepted head:

`abf9d396ef4f2800c5e9de9bd62a9b680a2be758`

All **29/29** pull-request workflows associated with that exact final head completed with conclusion `success`.

Deterministic exact-head acceptance:

- Ubuntu: **23/23 PASS**;
- Windows: **23/23 PASS**;
- common evidence SHA-256: `f10a620c34ea3928ce6de4e44002485120654c031d6073bbf00f5f3bddf68ffa`;
- Ubuntu artifact ID: `10620663114`;
- Windows artifact ID: `10620827996`.

Selected successful workflow runs include:

- `R0 Repository Guard` — `35557259551`;
- `R15.8 Training Runtime Acceptance` — `35557259491`;
- `R15.9 QLoRA SFT Acceptance` — `35557259534`;
- `Python Core` — `35557259581`;
- `R15 Integrated Acceptance` — `35557259570`;
- `R13 Integrated Release Readiness` — `35557259591`;
- `R17 Windows Installer` — `35557259506`.

PR `#520` merged from the unchanged exact final head with `expected_head_sha` protection as:

`4d411df6b0923b1443017ff25f06b1c04453a7f6`

Accepted V2.4.2 truth:

- immutable strategy plans bind exact TrainingPlan, topology report and topology digests;
- only `single_gpu` and `replicated_data_parallel` strategy intents exist;
- world size and selected device ordinals are exact and digest-bound;
- VRAM is budgeted independently per selected device and is never pooled;
- host RAM/storage remain independent host budgets;
- per-device batch, gradient accumulation and effective global batch are explicit;
- paired strategies preserve effective global batch exactly or fail closed;
- rank/data seeds use deterministic `offset_by_rank_v1` semantics;
- paired benchmark evidence binds same plan/topology/config/work/effective batch and per-device resource/integrity evidence;
- normative threshold is **>=1.25x throughput** with **0.0 allowed eval-loss regression**;
- missing quality evidence is inconclusive;
- V2.4.2 evidence always has `launch_authorized=false`;
- no distributed execution path exists in V2.4.2.

This normalization marks **V2.4.2 COMPLETE + NORMALIZED** and authorizes **V2.4.3 only**.

## V2.4.3 qualification

V2.4.3 implementation PR:

`#522 — feat: implement V2.4.3 governed two-GPU execution`

Exact final accepted head:

`81c5709ff457da375fd2f8f8ef13aad4b59aced0`

All **30/30** pull-request workflows associated with that exact final head completed with conclusion `success`.

Deterministic exact-head acceptance:

- Ubuntu: **22/22 PASS**;
- Windows: **22/22 PASS**;
- common evidence SHA-256: `fbcad387a86924c1ed7384b4408e2910c63c550f6dd9283e7c020b03b8ffbbc7`;
- Ubuntu artifact ID: `10646496287`;
- Windows artifact ID: `10646575915`.

Selected successful workflow runs include:

- `R0 Repository Guard` — `35614891252`;
- `R15.8 Training Runtime Acceptance` — `35614891434`;
- `R15.9 QLoRA SFT Acceptance` — `35614891273`;
- `Python Core` — `35614891412`;
- `R15 Integrated Acceptance` — `35614891265`;
- `R13 Integrated Release Readiness` — `35614891015`;
- `R13 Android Signing Acceptance` — `35614891044`;
- `R17 Windows Installer` — `35614891251`.

The Android Signing Windows job required one failed-job rerun on the unchanged exact SHA; Ubuntu remained successful and no source/workflow/acceptance criterion changed.

PR `#522` merged from the unchanged exact final head with `expected_head_sha` protection as:

`975d46a071f52a27a48de15227432d9d4911e142`

Accepted V2.4.3 truth:

- only governed TRAIN-authorized SFT/QLoRA plus exact qualified V2.4.2 strategy/benchmark evidence may enter distributed execution;
- launch is fixed to one node, two ranks, zero restarts and the repository-owned distributed worker;
- only accepted device visibility is injected; raw launcher argv/env/rendezvous are not exposed;
- rank/local-rank/world-size/restart identity is trusted-launcher-derived and validated;
- seed/sampler semantics are strategy-bound;
- rank zero is the sole canonical output authority and subordinate rank evidence is integrity-bound;
- rank failure, timeout, cancellation or missing/mismatched rank evidence fails the whole run;
- ProcessSandbox/KillSwitch covers the complete managed process group;
- the accepted R15.9 worker is reused;
- distributed resume remains unauthorized in V2.4.3;
- no pooled VRAM, sharded-memory strategy or TPU path was introduced.

This normalization marks **V2.4.3 COMPLETE + NORMALIZED** and authorizes **V2.4.4 only**.

## V2.4.4 qualification

V2.4.4 implementation PR:

`#524 — feat: implement V2.4.4 distributed checkpoint recovery`

Exact final accepted head:

`1abf4917566f065ac26b71a02e02d8fb3506fe1a`

All **29/29** pull-request workflows associated with that exact final head completed with conclusion `success`.

Deterministic exact-head acceptance:

- Ubuntu: **25/25 PASS**;
- Windows: **25/25 PASS**;
- common evidence SHA-256: `09820473e95e03672b89c6d9d086b6a9aa8fada394be2e661a4085f1989410ed`;
- Ubuntu artifact ID: `10654524114`;
- Windows artifact ID: `10655573341`.

Selected successful workflow runs include:

- `R0 Repository Guard` — `35633506877`;
- `R15.8 Training Runtime Acceptance` — `35633506917`;
- `R15.9 QLoRA SFT Acceptance` — `35633506716`;
- `Python Core` — `35633506815`;
- `R15 Integrated Acceptance` — `35633506982`;
- `R13 Integrated Release Readiness` — `35633506771`;
- `R17 Windows Installer` — `35633506891`.

PR `#524` merged from the unchanged exact final head with `expected_head_sha` protection as:

`779a9c8282e153b7dba35fb22be89ec5c622e1d3`

Accepted V2.4.4 truth:

- exact rank-zero canonical checkpoint lineage plus both rank evidences;
- independent checkpoint metadata/artifact digest validation;
- immutable execution/TrainingPlan/strategy/benchmark/topology/world-size/device binding;
- fixed one-node/two-rank recovery boundary and accepted R15.9 resume semantics;
- both ranks required for successful recovery;
- timeout/cancel/nonzero/missing/tampered/mismatched evidence is whole-group terminal;
- historical V2.4.3 resume remains false; V2.4.4 recovery authority is separate and explicit;
- no live-provider/Model Lab qualification is part of V2.4.4.

This normalization marks **V2.4.4 COMPLETE + NORMALIZED** and authorizes **V2.4.5 only**.

## 1. Authority and goal

V2.1, V2.2 and V2.3 are **COMPLETE + NORMALIZED**. V2.3 closed the governed Model Lab UX without claiming accelerator production qualification.

V2.4 exists to make the existing R15 Kaggle training path honest and production-qualifiable on Kaggle **GPU T4 ×2**, with explicit multi-GPU semantics and exact evidence.

The goal is not to invent another training engine. It is to evolve the accepted R15.8/R15.9/Kaggle path from a single-device-oriented capability/run contract into a versioned topology-aware path that can deliberately use both T4 devices when an accepted strategy says so.

The target chain is:

`provider request -> observed accelerator topology -> explicit execution strategy -> immutable strategy-bound training plan -> governed distributed launch -> per-device evidence -> checkpoint/recovery -> candidate evaluation -> production qualification`

Official Kaggle CLI documentation checked on 2026-09-20 documents `NvidiaTeslaT4` as **GPU T4 ×2**. That provider metadata is request/configuration evidence only. Kodepoia must still probe the actual runtime topology before it can claim that two CUDA devices are present or usable.

## 2. Live accepted primitives and demonstrated gaps

V2.4 planning is derived from live source and accepted authority.

### Existing Kaggle governance to preserve

- `src/kodepoia/tuning/kaggle_remote.py` already owns private bundle creation, exact plan/dataset digests, private dataset/kernel metadata, Kaggle CLI doctor/run/status/fetch and R15.9 output revalidation.
- `KaggleRemoteConfig.accelerator` currently maps `NvidiaTeslaT4` and `NvidiaL4`; V2.4 production scope is **T4 ×2 only**.
- the Kaggle kernel remains private and may read `HF_TOKEN` only from Kaggle Secrets at runtime; no Kaggle/Hugging Face credential may enter the bundle, Git, CI artifact, report or UI.
- `src/kodepoia/kodestudio/kaggle_quota.py` keeps quota reads explicit and observational through the official Kaggle CLI.

### Existing runtime/training authority to preserve

- `src/kodepoia/tuning/contracts.py` owns R15.8 backend/resource/capability contracts.
- `src/kodepoia/tuning/runtime.py` owns fail-closed capability/resource preflight.
- `src/kodepoia/tuning/probe_worker.py` performs actual bounded PyTorch/dtype/NF4 operations.
- `src/kodepoia/tuning/training.py` owns immutable `TrainingPlan`, exact model/tokenizer/dataset/capability binding, bounded run/cancel/checkpoint/recovery and report validation.
- `src/kodepoia/tuning/train_worker.py` owns actual SFT/QLoRA execution through the accepted PyTorch/Transformers/PEFT/TRL stack.
- `accelerate>=1.10,<2` is already an optional tuning dependency; V2.4 may reuse accepted dependencies but must not add arbitrary package-install behavior.
- `ProcessSandbox`, `KillSwitch`, `KodeSecrets` and `WorkspaceBoundary` remain runtime/trust authorities.

### Gaps demonstrated by live source

1. R15.8 capability evidence is currently single-device-oriented: the worker probes `cuda:0`, emits one `device`, and one free/total VRAM pair.
2. `NvidiaTeslaT4` in kernel metadata requests Kaggle GPU T4 ×2, but the Kodepoia report does not prove the actual device count or per-device resources.
3. the Kaggle kernel invokes one `python -m kodepoia.tuning.train_worker`; no explicit world size, rank topology or Kodepoia-owned multi-GPU strategy is bound to the training plan.
4. R15.9 resource evidence has one scalar `peak_vram_bytes`; it cannot prove per-device maxima or distinguish two devices from one pooled value.
5. checkpoint/recovery evidence binds plan identity but not a distributed strategy/topology identity.
6. KodeStudio can select `local` or `kaggle`, but does not currently present a verified device topology or explicit multi-GPU strategy contract.
7. current deterministic CI proves Kaggle bundle/control-plane safety without requiring live Kaggle/GPU; V2.4 must preserve that property while separating it from later live provider qualification.

## 3. Permanent V2.4 invariants

1. **Two T4s are two devices.** They are never represented as one 32 GiB accelerator and their free/total VRAM is never summed to authorize a model that does not fit the per-device strategy budget.
2. **Provider metadata is not runtime truth.** `machine_shape=NvidiaTeslaT4` may request GPU T4 ×2, but only a bounded runtime probe can establish observed device count, ordinals and per-device resources.
3. **No silent multi-GPU.** Every run binds an explicit typed strategy. No implicit `auto`, hidden DataParallel, environment-driven launch or trainer-side surprise may change world size.
4. **Single-GPU remains a first-class baseline.** V2.4 must preserve a deliberate one-device execution mode for paired qualification and fallback.
5. **Initial multi-GPU semantics are replicated data parallel, not memory pooling.** A replicated strategy may improve throughput but does not increase per-device model-fit VRAM.
6. **No sharded-memory claim without separate authority.** FSDP, DeepSpeed, tensor parallelism, pipeline parallelism, ZeRO or any strategy that changes model-placement/memory semantics is outside V2.4 unless the planning authority is explicitly amended and requalified.
7. **Exact topology/strategy lineage.** A training plan/run/checkpoint must bind the exact topology evidence digest, strategy, world size, selected device ordinals and relevant effective-batch semantics.
8. **Per-device preflight is fail closed.** Unknown or insufficient VRAM on any required device blocks launch.
9. **Host budgets remain independent.** RAM/storage are host resources and are not multiplied or guessed from device count.
10. **Effective batch is explicit.** Per-device batch, gradient accumulation, world size and derived global batch must be visible and digest-bound.
11. **Distributed seeds/sampling are explicit.** Rank/world-size seed and sampler behavior must be deterministic enough to reproduce the declared strategy and must be recorded in evidence.
12. **Rank failures are terminal.** A single worker failure, lost rank, timeout or cancellation cannot be relabeled as a successful partial run.
13. **No orphan workers.** Cancellation/timeout must terminate the complete accepted process group through repository-owned launch semantics and existing KillSwitch/Sandbox boundaries.
14. **Canonical output is single-authority.** Only the accepted coordinator/rank-zero path may emit canonical run/checkpoint metadata; per-rank evidence is subordinate and integrity-bound.
15. **Resume is topology-aware.** Checkpoint recovery must fail closed on incompatible plan/strategy/world-size/topology evidence unless an explicitly accepted compatibility rule exists.
16. **No arbitrary launch surface.** User/model/project text cannot become `torchrun`/Accelerate flags, argv, shell, environment, rendezvous configuration or package installs.
17. **No secret propagation.** Kaggle/HF credentials remain outside bundles/reports; distributed launch must not broaden environment passthrough.
18. **Quality gates remain authoritative.** Faster throughput never overrides training integrity, paired evaluation, critical-regression veto, export/package integrity or promotion evidence.
19. **CI and live proof are distinct.** Required PR CI must remain deterministic and need no live Kaggle account, network, GPU or provider quota. Live Kaggle evidence is a separate later production-qualification artifact.
20. **No TPU pull-forward.** `TpuV5E8` and any XLA/JAX/PyTorch-XLA backend remain outside V2.4.
21. **No V2.5 pull-forward.** Cross-workspace orchestration remains unauthorized.
22. **No release pull-forward.** V2.4 does not authorize installer/release/TUF/updater mutation; public distribution remains `v1.1.0-rc8`.

## 4. Strategy model

V2.4 freezes two user-visible execution intents:

- `single_gpu` — exactly one explicitly selected CUDA device. This is the production baseline and must remain usable on a T4 ×2 session without silently consuming the second device.
- `replicated_data_parallel` — exactly two explicitly selected CUDA devices for the V2.4 Kaggle target. Model/adapter state is replicated according to the accepted PyTorch/Accelerate path; batches are distributed across ranks. This strategy **does not pool VRAM** and may be accepted only for models that satisfy the per-device memory budget.

The implementation may use repository-owned PyTorch/Accelerate distributed launch primitives because those dependencies are already in the accepted optional tuning stack. The public Kodepoia API must remain typed; callers must not supply raw launcher argv/env/rendezvous settings.

No third strategy is reserved in V2.4. Adding sharding/tensor/pipeline parallelism requires an explicit plan amendment, exact-head qualification, protected merge and normalization before implementation.

## 5. Production-qualification evidence model

Deterministic CI and live provider qualification must not be conflated.

### Deterministic CI evidence

All implementation subdivisions must be testable without live GPU/Kaggle using bounded fixtures/fakes that prove:

- two-device topology serialization and per-device budgets;
- rejection of pooled/ambiguous/duplicate device identities;
- explicit world-size/rank/strategy binding;
- fixed repository-owned launch construction with no caller argv/env escape;
- rank-zero canonical output and per-rank subordinate evidence;
- rank failure, timeout, cancellation and orphan-process rejection;
- strategy/topology-bound checkpoint and resume rejection;
- exact dataset/model/tokenizer/plan/evidence digests;
- deterministic KodeStudio unavailable/blocked/ready states.

### Live Kaggle production evidence

V2.4 cannot be marked production-qualified solely from fixtures. A dedicated later subdivision must produce exact-source live Kaggle evidence showing, at minimum:

- authenticated private Kaggle execution on requested `NvidiaTeslaT4`;
- observed two-device CUDA topology from inside the kernel;
- separate per-device names and free/total VRAM;
- one governed `single_gpu` baseline and one governed `replicated_data_parallel` run using the same accepted model/tokenizer/dataset/evaluation configuration where comparison is meaningful;
- exact source SHA, plan/strategy/topology digests, kernel/run identity, package/framework versions and provider state;
- no secret leakage;
- completed output and checkpoints revalidated after download by Kodepoia;
- paired candidate evaluation with no critical regression;
- measured throughput/resource evidence sufficient to justify the production claim.

If live provider access/auth/quota is unavailable, Kodepoia must report qualification as unavailable/blocked. It must never convert deterministic fixture success into a live provider claim.

## 6. Benchmark/acceptance policy for the multi-GPU strategy

V2.4.2 must establish paired benchmark evidence before V2.4.3 can make `replicated_data_parallel` a launchable production strategy.

The comparison must keep constant or explicitly account for:

- exact model/tokenizer revision and digests;
- exact immutable dataset and split digests;
- optimizer/scheduler/learning-rate policy;
- max steps and evaluation cadence;
- precision/quantization;
- effective global batch semantics;
- seed/data-seed policy;
- benchmark/evaluation suite and critical-regression policy.

Required evidence includes:

- wall time;
- steady training throughput using a stable declared unit;
- per-device peak/free/total VRAM evidence;
- host RAM/storage evidence where available;
- train/eval loss;
- run/checkpoint integrity;
- paired post-training evaluation.

The implementation PR must define the normative performance threshold from measured evidence before a later subdivision is authorized. If no material operational gain is demonstrated without quality/integrity regression, V2.4 must keep the replicated strategy experimental/unavailable rather than fabricate production value.

Bit-identical adapter bytes across independent GPU executions are not assumed. Each run's artifact digest remains exact; reproducibility is assessed through declared configuration/topology identity, checkpoint/run integrity and paired evaluation/metric evidence.

## 7. V2.4 subdivisions

The list below is frozen by the accepted V2.4 planning authority. No subdivision may be silently added, removed, merged, split or renumbered.

### V2.4.1 — Accelerator topology and provider truth — COMPLETE + NORMALIZED

Goal: replace single-device assumptions with versioned topology evidence while preserving historical R15.8 contracts.

Required scope:

- versioned topology/capability contract, not an in-place reinterpretation of historical single-device evidence;
- actual CUDA device count;
- stable bounded per-device descriptors including ordinal, backend/name and per-device free/total VRAM;
- exact distinction between requested provider shape and observed runtime topology;
- explicit topology digest;
- fail-closed duplicate/missing/ambiguous device handling;
- `single_gpu` may select one device only after topology verification;
- no distributed training launch yet.

Definition of done: Kodepoia can prove whether the runtime actually exposes the expected two T4-class CUDA devices and can reason about each device's budget independently, without claiming pooled VRAM.

### V2.4.2 — Strategy, effective-batch and resource planning contract — COMPLETE + NORMALIZED

Goal: make execution semantics immutable before any multi-process launch.

Required scope:

- typed `single_gpu` and `replicated_data_parallel` strategies only;
- world size and selected device ordinals bound to plan identity;
- per-device VRAM requirements and host RAM/storage requirements;
- per-device batch, gradient accumulation and derived global batch;
- rank/data seed policy;
- topology evidence digest bound to strategy/plan;
- deterministic strategy benchmark harness/fixtures;
- paired baseline-versus-replicated qualification evidence and a normative measured performance threshold;
- no arbitrary launcher args/env;
- no live Kaggle requirement in PR CI;
- no actual production multi-GPU launch until this subdivision is normalized.

Definition of done: a user or backend cannot request an ambiguous multi-GPU run; the exact strategy and resource semantics are digest-bound and benchmark-justified.

### V2.4.3 — Governed explicit two-GPU execution — COMPLETE + NORMALIZED

Goal: execute the accepted replicated strategy through a repository-owned multi-process boundary.

Required scope:

- reuse the accepted R15.9 SFT/QLoRA worker semantics;
- repository-owned fixed PyTorch/Accelerate launch construction;
- exact world size two for the Kaggle T4 ×2 replicated target;
- rank/local-rank assignment from trusted launcher state only;
- no user/project/model-controlled argv/env/rendezvous;
- distributed sampler/seed semantics bound to strategy evidence;
- canonical rank-zero output plus integrity-bound per-rank evidence;
- rank failure/timeout/cancellation fails the whole run;
- ProcessSandbox/KillSwitch coverage extends to the complete process group;
- no new sharded-memory semantics.

Definition of done: both devices can be deliberately used under one accepted plan without hidden strategy changes, orphan processes or weakened R15 lineage.

### V2.4.4 — Distributed checkpoint, cancellation and recovery — COMPLETE + NORMALIZED

Goal: preserve exact recovery semantics under a two-rank run.

Required scope:

- strategy/topology/world-size bound checkpoint metadata;
- rank-zero canonical checkpoint lineage;
- explicit subordinate per-rank state when needed;
- cancel/timeout/partial-rank failure evidence;
- no successful result from an incomplete process group;
- resume only from a compatible exact plan/strategy/topology lineage;
- fail closed on missing/tampered/mismatched rank/checkpoint evidence;
- preserve existing dataset/model/tokenizer/capability bindings.

Definition of done: recovery cannot silently change topology/strategy or accept a partial/tampered distributed checkpoint.

### V2.4.5 — Model Lab accelerator UX and live Kaggle qualification — CURRENT

Goal: make accelerator truth inspectable and perform the real provider proof.

Required scope:

- structured Model Lab display of requested provider shape versus observed topology;
- separate device rows and per-device VRAM, never a summed 32 GiB pool;
- explicit strategy selector/status with `single_gpu` vs `replicated_data_parallel`;
- effective batch/world size/device mapping visible before launch;
- honest auth/network/quota/unavailable states;
- no automatic provider calls at application startup;
- exact-source live Kaggle qualification workflow with private bundle/kernel and downloaded evidence revalidation;
- paired single-vs-replicated live run evidence;
- FR/EN/qps-ploc and accessibility;
- live qualification may require operator credentials/quota; if so, stop at this subdivision and request only the exact bounded operator action.


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



Definition of done: the user can see what Kaggle actually provided, what strategy will run, and whether live production qualification exists for the exact source.

### V2.4.6 — Production hardening and integrated acceptance

Goal: adversarially prove the entire V2.4 topology/strategy/execution/recovery/live-evidence chain.

Required coverage includes:

- provider says T4 ×2 but runtime exposes zero/one/unexpected devices;
- duplicate ordinals/device identities;
- unknown/free-VRAM telemetry;
- one device insufficient while aggregate VRAM would appear sufficient;
- strategy/world-size/device mismatch;
- malicious text attempting to inject launcher args/env/rendezvous/package installs;
- rank crash/hang/timeout/cancellation;
- orphan-process detection;
- rank-zero/per-rank evidence disagreement;
- tampered topology/strategy/run/checkpoint evidence;
- resume with changed world size/device set/strategy;
- provider auth/network/quota unavailable;
- deterministic CI with no live provider;
- exact-head Ubuntu/Windows acceptance for non-provider-dependent logic;
- KodeStudio degraded/empty/missing-live-evidence states;
- live production evidence remains exact-source and separate from fixture claims.

Definition of done: V2.4 may claim Kaggle T4 ×2 production qualification only when deterministic adversarial acceptance and the required exact-source live provider evidence are both accepted.

## 8. Versioning and historical acceptance

Historical R15.8/R15.9 schemas and acceptances must remain reproducible.

Topology-aware capability/run/checkpoint structures must use explicit versioning or forward-compatible additive contracts. Do not reinterpret a historical scalar `vram_total_bytes` or `peak_vram_bytes` as aggregate multi-GPU memory.

If an old acceptance contains a literal later-scope assertion, it may only be made forward-compatible while preserving the historical pre-normalization state explicitly.

## 9. Security and trust boundaries

V2.4 must preserve:

- ResearchGuard;
- KodeSecrets;
- WorkspaceBoundary;
- ProcessSandbox;
- KillSwitch;
- R15 Experience/dataset governance;
- immutable model/tokenizer/dataset/TRAIN/capability lineage;
- V2.3 candidate evaluation/export/package/promotion/rollback evidence;
- no authority promotion from Project Knowledge, Research Packs, chat, memory, retrieved context or model text.

Prompt/source/model text can never become distributed launcher argv, shell command, arbitrary environment variable, rendezvous endpoint, package-install request, permission grant or provider credential.

## 10. CI and merge discipline

Every implementation subdivision must:

1. re-fetch live `main` and authority;
2. branch from the exact live SHA;
3. modify only the authorized subdivision;
4. provide deterministic tests that require no live Kaggle/GPU unless the subdivision explicitly owns separate live qualification;
5. emit exact-head evidence on Ubuntu and Windows where applicable;
6. invalidate every prior-SHA result after a commit;
7. read the exact failing log before correction or rerun;
8. never weaken a gate to obtain green CI;
9. merge only after anti-race verification and `expected_head_sha`;
10. post-merge normalize before authorizing the next subdivision.

A live-provider rerun is not a substitute for a deterministic product/test defect. A deterministic CI rerun is allowed only on the same SHA for a clearly transient/environmental incident.

## 11. Manual-intervention boundary

Planning itself requires no manual Kaggle intervention.

If a later live qualification subdivision requires account authentication, GPU quota or another operator-owned Kaggle action that connected tooling cannot perform, stop at that subdivision. State exactly:

- why the action is necessary;
- the bounded commands/actions to perform;
- the expected output/evidence;
- what must be returned before work can continue.

Do not skip the live requirement and do not proceed to a later subdivision while it is unresolved.

## 12. Explicit non-goals

V2.4 does not authorize:

- TPU v5e-8;
- XLA/JAX or PyTorch-XLA;
- FSDP;
- DeepSpeed/ZeRO;
- tensor parallelism;
- pipeline parallelism;
- implicit Trainer/DataParallel behavior as production authority;
- pooled 32 GiB VRAM claims;
- arbitrary `torchrun`/Accelerate arguments or environment passthrough;
- automatic package/dependency installation outside the accepted bundle dependency profile;
- public Kaggle datasets/kernels;
- public model-hub publishing;
- V2.5 cross-workspace orchestration;
- V2.6 release work;
- release/TUF/updater mutation;
- R20 reopening or R20.7.

## 13. Planning definition of done

V2.4 planning is complete only when:

- this document is exact-head qualified;
- the six subdivisions and their boundaries are frozen;
- live-source gaps and reuse points are explicit;
- provider-request versus observed-topology truth is explicit;
- single-GPU and replicated two-GPU semantics are explicit;
- per-device resource and no-pooling invariants are explicit;
- distributed launch/recovery/trust boundaries are explicit;
- deterministic CI versus live Kaggle qualification is explicit;
- manual-intervention handling is explicit;
- V2.5/release/R20 boundaries are explicit;
- the planning PR is merged with `expected_head_sha`;
- this post-merge normalization records planning as COMPLETE + NORMALIZED and authorizes **V2.4.1 only**.

**V2.4.5 is now the only authorized implementation subdivision. V2.4.6+ remain unauthorized** until V2.4.5 is implemented, exact-head qualified, merged and post-merge normalized.
