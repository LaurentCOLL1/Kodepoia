# Kodepoia — Roadmap V2

Status: **ACTIVE — roadmap preparation accepted; V2.0 execution gate pending**  
Created: 2026-09-15  
Roadmap preparation merged by PR `#472` as `87fc09e16531260d64cf3d5fb59f511295e2b703` after 25/25 exact-head PR workflows succeeded  
Public Windows distribution baseline: `v1.1.0-rc8`

## 1. Purpose

Roadmap V1 remains frozen historical architecture and acceptance evidence. V2 does not reopen R20, does not create `R20.7`, and does not retroactively rewrite R1–R20 history.

V2 shifts the emphasis from isolated capabilities to truthful, usable, end-to-end KodeStudio workflows while preserving protected-core, least-privilege, provenance, rollback and fail-closed invariants.

A critical distinction governs all V2 work: the public rc8 distribution, live `main` source, explicit acceptance evidence, experimental work and unavailable paths are different states and must never be collapsed into one claim of support.

## 2. Mandatory V2 ordering

### V2.0 — Baseline, capability truth and usability audit

**Status: NOT COMPLETE. V2.1 is blocked until V2.0 is COMPLETE + NORMALIZED.**

Goal: establish one exact, testable truth model for what is public, source-available, acceptance-proven, experimental or unavailable, and make that truth visible in KodeStudio.

#### V2.0.1 — Capability matrix/runtime truth

Deliverables:

- machine-readable capability classification: `public-validated`, `source-available`, `acceptance-proven`, `experimental`, `unavailable`;
- provider/runtime state: `ready`, `unavailable`, `auth-required`, `network-restricted`, `not-implemented`;
- accelerator state: `priority`, `available`, `experimental`, `deferred`, `unsupported`;
- explicit distinction between public `v1.1.0-rc8` and post-rc8 live-source capabilities;
- no claim that an implementation is acceptance-proven without bound evidence.

#### V2.0.2 — KodeStudio diagnostics

Deliverables:

- visible and actionable capability/provider/network/authentication diagnostics;
- a genuine successful zero-result query is distinct from provider absence, missing authentication, denied network access and an unimplemented path;
- no unavailable provider can look like a successful empty search;
- the current Research behavior is labeled truthfully: saved-research query is local persisted-report search, while external acquisition is a separate guarded explicit-locator operation.

#### V2.0.3 — Reusable V2 exact-head acceptance

Deliverables:

- reusable exact-head-bound acceptance contract/template;
- deterministic tests for capability/provider/accelerator states;
- acceptance evidence proving zero-result-success separately from unavailable/auth/network/not-implemented states;
- parity check proving KodeStudio and current documentation expose the same capability truth;
- evidence reusable by later V2 subdivisions.

V2.0 DoD: implementation tests pass, acceptance is bound to the exact head, every required PR workflow on that head is `completed/success`, the branch is merged, and continuity is normalized. Only then is V2.0 **COMPLETE + NORMALIZED**.

### V2.1 — Research Workspace: real discovery, evidence and cited synthesis

**Start condition: V2.0 COMPLETE + NORMALIZED.**

Goal: replace the current low-level Research UX with a complete question-to-evidence workflow. Normative details are in `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Target flow:

`question -> provider discovery -> source cards -> guarded fetch -> inspect/include/exclude -> cited synthesis -> governed Research Pack -> project context/RAG`

Subdivisions:

- **V2.1.1 — Honest Research UX and diagnostics:** separate saved-research search from external discovery; surface provider/network/auth states and actionable empty/error states using the V2.0 truth contract.
- **V2.1.2 — Discovery providers:** bounded official/general Web and GitHub discovery, provider interfaces, ranking/deduplication and guarded selected-source fetch.
- **V2.1.3 — Evidence workspace:** source cards, preview, metadata, trust/freshness/version, include/exclude and cache/refetch lineage.
- **V2.1.4 — Cited synthesis and Research Packs:** claim-linked citations, uncertainty and governed project knowledge/Context Builder/RAG integration.
- **V2.1.5 — Extended media/community sources:** forums and YouTube/transcript paths; STT/frames only through separately governed media operations.
- **V2.1.6 — ResearchGuard hardening:** prompt-injection corpus, malicious redirects, SSRF, timeouts, stale/version conflicts, outages, cancellation and offline behavior.

V2.1 DoD: from KodeStudio, an ordinary research question either produces inspectable sources, selected evidence and a cited answer, or a visible diagnostic explaining exactly why discovery cannot run. External content remains data, never privileged instruction.

### V2.2 — Project Knowledge, Context Builder and Memory integration

Goal: make accepted research reusable without copying text manually.

Deliverables include project-scoped Research Packs with immutable provenance/digests, semantic retrieval over accepted sources and project files, inspectable Context Builder selection, version-aware invalidation and explicit include/exclude/refresh/delete controls. Untrusted Web text never silently becomes durable instruction.

### V2.3 — Model Lab: governed improvement UX

Goal: expose the accepted R15 training backend as an understandable end-to-end workflow: base-model/role selection, validated datasets, resource estimates, local/qualified remote backend, dry-run, SFT/LoRA/QLoRA, progress/checkpoints, before/after KodeBench and explicit promote/reject gates. Training completion or lower loss alone never authorizes promotion.

### V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU

Kaggle `GPU T4 x2` remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. Two T4 devices remain two separate 16 GiB devices, never one fictitious 32 GiB pool. First qualify the conservative real-account path, then explicitly qualify deliberate two-process/multi-GPU execution with per-device evidence and the normal R15 integrity/benchmark gates.

### V2.5 — Cross-workspace orchestration

Goal: enable Research, Chat/Vision, KodeCode, Vault, Godot/Blender/ComfyUI and QA to cooperate around the same project through explicit handoff contracts, shared project-root identity, protected mutations and resumable evidence, never unrestricted model access to filesystem/network/process APIs.

### V2.6 — V2 hardening and next public Windows release

A post-rc8 release is authorized only after the selected V2 boundary is acceptance-proven and exact-source release gates pass. No release number is reserved by this roadmap. Publication remains draft-first and any TUF mutation occurs only after normal qualification.

## 3. TPU v5e-8 policy

TPU v5e-8 is **deferred experimental capacity**, not a V2 critical path or release blocker. Supporting it correctly requires a separately qualified XLA/JAX or PyTorch/XLA execution path, dependencies/capability detection, training semantics, checkpoint compatibility, resource accounting and acceptance evidence.

Schedule TPU work only if a benchmark proposal demonstrates a material advantage for a concrete Kodepoia workload not adequately served by the qualified GPU path. Until then, Kaggle T4×2 receives engineering priority.

## 4. V2 acceptance discipline

Every subdivision follows the same discipline:

1. re-fetch live `main` and continuity authority;
2. create a dedicated branch from an exact SHA;
3. implement only the authorized scope;
4. add/update deterministic tests and acceptance evidence;
5. re-fetch every required workflow for the exact branch head;
6. merge only after all required gates for that exact head are successful;
7. normalize continuity after merge before the next subdivision;
8. stop for genuine manual intervention rather than bypassing a gate.

External outages, quota exhaustion and unavailable optional providers never justify weakening fail-closed behavior; they surface as explicit diagnostics.

## 5. Immediate V2 start

The first implementation target after Roadmap V2 preparation and its post-merge normalization is **V2.0.1 — capability matrix/runtime truth**, followed by **V2.0.2 — KodeStudio diagnostics** and **V2.0.3 — reusable exact-head V2 acceptance**.

**V2.1.1 must not start until V2.0 is COMPLETE + NORMALIZED.**
