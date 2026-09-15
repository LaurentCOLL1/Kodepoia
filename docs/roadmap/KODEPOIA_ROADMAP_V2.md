# Kodepoia — Roadmap V2

Status: **ACTIVE DIRECTION — planning authority, implementation not yet accepted**  
Created: 2026-09-15  
Baseline repository head when this roadmap was opened: `6b7ec8d4504da83579af98d8235326ea4268d63f`  
Public Windows distribution baseline: `v1.1.0-rc8`

## 1. Purpose

Roadmap V1 remains frozen historical architecture and acceptance evidence. V2 does not reopen R20, does not create `R20.7`, and does not retroactively rewrite the R1–R20 history.

V2 shifts the emphasis from proving isolated capabilities to making the existing capabilities genuinely usable together in KodeStudio. Every V2 milestone must preserve the protected-core, least-privilege, provenance, rollback and fail-closed invariants already accepted in V1.

The first V2 priority is the Research Workspace because the current Research page exposes low-level query/fetch primitives but does not yet provide the user workflow expected from a research assistant: natural-language discovery of sources, inspection, cited synthesis and governed reuse in the active project.

## 2. V2 ordering

### V2.0 — Baseline, capability truth and usability audit

Goal: establish an exact distinction between what is public in rc8, what exists only on `main`, what is acceptance-proven and what is merely implemented.

Deliverables:

- capability matrix: public rc8 / current `main` / experimental / unavailable;
- KodeStudio diagnostics that never present an unavailable provider as silently functional;
- source-only post-rc8 features documented as such until a later release is qualified;
- reusable V2 acceptance template with exact-head binding;
- no release or TUF mutation merely for planning.

DoD: a user can tell, from KodeStudio and documentation, what is expected to work and why a blocked capability is blocked.

### V2.1 — Research Workspace: real discovery, evidence and cited synthesis

Goal: replace the current low-level research UX with a complete question-to-evidence workflow.

The normative design and acceptance contract are in `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Required outcome:

`question -> provider discovery -> source cards -> guarded fetch -> inspect/include/exclude -> cited synthesis -> governed Research Pack -> project context/RAG`

This phase has priority over adding more source types. A small number of sources that work end to end is preferable to many adapters that cannot be used from KodeStudio.

Subdivisions:

- **V2.1.1 — Honest UX and diagnostics:** separate “search saved research” from “search external sources”, expose network/provider state, actionable errors and empty-state explanations.
- **V2.1.2 — Discovery providers:** real discovery for official documentation/general Web and GitHub; provider interface, ranking, deduplication and bounded retrieval.
- **V2.1.3 — Evidence workspace:** source cards, metadata, trust/freshness/version indicators, preview, include/exclude, cache/refetch and provenance.
- **V2.1.4 — Cited synthesis and Research Packs:** claim-level citations, uncertainty, export to project-scoped governed knowledge and Context Builder/RAG integration.
- **V2.1.5 — Extended media/community sources:** forums and YouTube discovery, transcript when available, STT/frames only through explicit governed media paths.
- **V2.1.6 — ResearchGuard hardening:** prompt-injection corpus, malicious pages, redirects, network denial, timeouts, duplicate content, stale/version-conflicting sources and cancellation.

DoD: entering an ordinary research question in KodeStudio either returns inspectable real sources and a cited answer, or returns a visible diagnostic explaining exactly why discovery cannot run. Raw external content never becomes an agentic instruction and cannot directly authorize a tool action.

### V2.2 — Project Knowledge, Context Builder and Memory integration

Goal: make accepted research useful without repeatedly copying text into prompts.

Deliverables:

- project-scoped Research Packs with immutable provenance/digests;
- semantic retrieval over accepted research, project files and relevant memory scopes;
- Context Builder showing why each context item was selected;
- version-aware invalidation when engine/tool versions change;
- user controls to include, exclude, refresh or delete derived knowledge;
- no silent conversion of untrusted Web text into durable instructions.

DoD: Chat, code and specialist workspaces can consume cited, scoped project knowledge while retaining source traceability.

### V2.3 — Model Lab: governed improvement UX

Goal: turn the already existing R15 backend into an understandable end-to-end KodeStudio workflow.

Deliverables:

- select base model and role (`FAST`, `CORE`, `CODE`, `HEAVY`);
- choose/construct only validated datasets;
- estimate RAM, VRAM, disk and remote quota;
- choose local or qualified remote backend;
- dry-run before mutation;
- SFT/LoRA/QLoRA training with progress/checkpoints;
- before/after KodeBench comparison;
- explicit promote/reject action with regression gates;
- Ollama candidate packaging only after qualification.

DoD: a model candidate cannot be promoted merely because training completed or loss decreased; comparative quality evidence is mandatory.

### V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU

Goal: make the existing Kaggle backend useful for real governed training and qualify deliberate use of both T4 GPUs.

Policy:

- `GPU T4 x2` remains the primary Kaggle accelerator target for the current CUDA/PyTorch/PEFT/QLoRA stack;
- two T4 devices remain two separate 16 GiB VRAM devices, never represented as one fictitious 32 GiB device;
- first perform a real account E2E on the existing conservative path;
- then qualify a two-process/multi-GPU strategy such as Hugging Face Accelerate/DDP or a separately justified sharding strategy;
- record per-device memory, throughput, failure and resume evidence;
- never alter a `TrainingPlan` silently because remote hardware differs.

DoD: a two-GPU run proves that both devices are intentionally used, produces artifacts bound to the exact plan and passes the same post-fetch R15 integrity and benchmark gates as local training.

### V2.5 — Cross-workspace orchestration

Goal: let Research, Chat/Vision, KodeCode, Vault, Godot/Blender/ComfyUI and QA cooperate around the same active project without bypassing their guards.

Deliverables:

- explicit handoff contracts between workspaces;
- project-root identity propagated everywhere;
- human confirmation for sensitive mutations;
- resumable task/evidence trail;
- no direct model access to unrestricted filesystem/network/process APIs.

DoD: a multi-step task can move from research to implementation to tests while preserving provenance, permissions and rollback boundaries.

### V2.6 — V2 hardening and next public Windows release

Goal: publish a post-rc8 build only after V2 functionality selected for that release is acceptance-proven.

Deliverables:

- real Windows E2E for project opening, Research Workspace, Ollama model management and selected Model Lab paths;
- regression/red-team suite;
- installer and update path qualification on exact source;
- draft-first publication and TUF mutation only after normal release gates pass;
- update public documentation to match exactly what the released binary contains.

No release number is reserved by this roadmap. A future rc/stable version must be chosen explicitly when the release boundary is known.

## 3. TPU v5e-8 policy

TPU v5e-8 is **deferred experimental capacity**, not a V2 critical path and not a release blocker.

The current R15 path is centered on PyTorch/CUDA plus PEFT/bitsandbytes-style 4-bit QLoRA. Supporting TPU correctly would require a separately qualified XLA/JAX or PyTorch/XLA execution path, dependency/capability detection, training semantics, checkpoint compatibility, resource accounting and acceptance evidence.

V2 will add TPU work only if a benchmark proposal demonstrates a material advantage for a concrete Kodepoia workload that cannot be met adequately by the qualified GPU path. Until then, Kaggle T4×2 receives engineering priority.

## 4. V2 acceptance discipline

Each subdivision follows the existing repository discipline:

1. re-fetch live `main` and continuity authority;
2. create a dedicated branch from an exact SHA;
3. implement only the authorized subdivision;
4. add/update deterministic tests and acceptance evidence;
5. re-fetch every required workflow for the exact branch head;
6. merge only after all required gates for that exact head are successful;
7. normalize continuity after merge before starting the next subdivision;
8. stop for required manual intervention rather than bypassing a gate.

External outages, quota exhaustion and unavailable optional providers are not reasons to weaken fail-closed behavior. They must surface as explicit diagnostics.

## 5. Immediate V2 start

The first implementation target after this roadmap is accepted is **V2.1.1 — Honest Research UX and diagnostics**, followed by **V2.1.2 — real discovery providers**. V2.3/V2.4 can proceed only after the Research Workspace has a usable end-to-end path, unless a separately approved dependency requires otherwise.
