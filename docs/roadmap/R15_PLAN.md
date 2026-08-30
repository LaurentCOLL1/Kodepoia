# Kodepoia — R15 detailed phase plan

**Phase:** R15  
**Roadmap title:** Experience / Bench / Fine-tuning  
**Status:** ACTIVE
**Phase planning started:** 2026-08-29  
**Architecture:** v1.0 frozen  
**Source of truth at planning branch point:** normalized `main` `3f10bc62059e120d5ff467d00e39a0a7f9219cb9`  
**Execution checkpoint:** R1–R14 are COMPLETE + NORMALIZED; R15 planning is ACCEPTED + NORMALIZED. R15.1–R15.10 are COMPLETE + NORMALIZED. R15.11 is COMPLETE with immutable technical source `6f49a72918d4ddb4ae4d779e85513ae721688c49`; its final documented END-head requires fresh exact-head R15.11/R0/Python/UI gates before protected merge. R15.12–R15.17 remain PLANNED.

## Purpose and authority

R15 implements the frozen-roadmap capability **“Collecte des expériences validées → nettoyage/déduplication/licence/governance → benchmark des lacunes → QLoRA si utile → conversion/GGUF/Ollama → KodeBench avant/après. Rejeter tout fine-tuning qui régresse les domaines critiques.”**

The phase specializes Kodepoia only after the system around the model is already implemented and measurable. It does not assume that fine-tuning is always beneficial. A governed `NO_TRAIN` / `NOT_NEEDED` decision is a valid outcome when benchmark evidence shows that a gap is better solved by tools, retrieval, routing, prompts, context, product logic or existing models, or when data/licensing/hardware evidence is insufficient.

This file is the exhaustive execution and recovery authority for R15. The subdivision list R15.1–R15.17 is frozen when the planning PR and its single planning continuity normalization are accepted. No subdivision may be silently added, removed, merged, split or renumbered. Scope/status/manual-state changes must update this plan and continuity in the same work cycle; architecture changes require an ADR when they cross the frozen v1.0 boundary.

## Permanent subdivision status synchronization rule

For every R15 subdivision:

1. **Start, before implementation:** prior normalized subdivisions are `COMPLETE + NORMALIZED`, the active subdivision becomes `IN_PROGRESS`, later subdivisions remain `PLANNED`; phase status/checkpoint and continuity are synchronized in the same work cycle.
2. **End, before final documentation/evidence re-gates:** the accepted active subdivision becomes `COMPLETE`; later subdivisions stay `PLANNED`; continuity is synchronized in the same work cycle.
3. A triggered manual gate uses truthful `BLOCKED` / `MANUAL_REQUIRED`, never synthetic `COMPLETE`.
4. Post-merge normalization is continuity-only and MUST NOT rewrite phase-plan status.
5. A stale subdivision index, stale phase status, mixed-SHA evidence, benchmark leakage or reuse of rejected-candidate evidence is an acceptance blocker.
6. Every model/dataset promotion decision is fail-closed. Unknown provenance, unknown license, benchmark contamination, missing base-model identity, unsupported conversion, missing critical-domain evidence or unbounded regression means `REJECTED` / `QUARANTINED`, never PASS.

## Phase objective

Deliver a deterministic, auditable, local-first Experience / KodeBench / specialization capability that lets Kodepoia:

- collect only explicitly eligible, validated experiences rather than indiscriminately logging conversations or project data;
- preserve source, project scope, consent/eligibility, license, transformation, schema and lineage metadata for every training-eligible example;
- redact secrets and disallowed/private data before any example can enter a training corpus;
- deduplicate exact and near-duplicate content while preserving deterministic cluster and provenance records;
- prevent training/evaluation contamination by enforcing a hard firewall between training material and benchmark holdouts;
- build immutable, versioned datasets with deterministic splits, manifests, hashes and dataset cards;
- evolve the existing R3 KodeBench baseline into a role/domain-aware, reproducible before/after benchmark authority;
- diagnose model gaps and distinguish model-capability deficits from tool, retrieval, routing, context, prompt or product defects;
- make an explicit evidence-backed `TRAIN` / `NO_TRAIN` decision instead of automatically fine-tuning;
- provide a capability-probed, reproducible QLoRA/SFT runtime when training is justified;
- checkpoint, resume, cancel and recover training through ProcessSandbox/KillSwitch and governed artifact boundaries;
- compare base, adapter, merged, GGUF and Ollama variants on the same uncontaminated benchmark contract;
- reject any candidate that regresses a critical domain even if its aggregate score improves;
- convert accepted candidates through a controlled Safetensors/adapter → merged model when supported → GGUF → quantized GGUF pipeline while measuring conversion/quantization loss;
- import and validate compatible GGUF models/adapters in local Ollama without silently replacing the wrong base model;
- maintain an immutable model/dataset registry with promotion, rollback, lineage and compatibility state;
- expose Experience, Bench and Tune workflows through structured CLI and KodeStudio without allowing model-supplied arbitrary commands;
- close the phase with adversarial integrated exact-head acceptance that proves provenance, contamination isolation, reproducibility and regression rejection without circular evidence.

## Explicitly out of scope

R15 does **not** implement R16 final red-team/beta/v1.0 hardening. It also does not authorize:

- indiscriminate recording of all chats, code, files, prompts, tool outputs or user content for training;
- training on secrets, credentials, access tokens, private keys, passwords, personal/private data lacking explicit eligibility, or content outside allowed project/data scope;
- automatic web scraping or automatic ingestion of third-party datasets merely because they are publicly reachable;
- treating an absent/ambiguous license as permission to train or redistribute;
- full-parameter fine-tuning of large models as the default path;
- RLHF, online reinforcement learning, DPO/PPO/RLAIF or autonomous self-reward training unless separately accepted by scope decision/ADR;
- distributed multi-node training, mandatory cloud GPU, mandatory paid model-training service or mandatory external experiment tracker for core acceptance;
- silent installation of GPU drivers, ROCm/CUDA, PyTorch, training frameworks or external model tooling;
- publishing datasets, adapters or models to Hugging Face, Ollama registry or any public model hub without an explicit separately authorized action;
- changing base-model licenses, redistributing models contrary to their terms or claiming ownership of third-party weights/data;
- promoting a model solely on aggregate score, subjective preference or one successful example;
- training on any benchmark holdout or near-duplicate of benchmark holdout content;
- assuming that QLoRA adapters are portable across a different base model, tokenizer, architecture or revision;
- silently requantizing an already quantized GGUF as an accepted production path when a high-precision source is available;
- replacing R3 ModelRouter/Brain, R6 quality budgets, R7 ResearchGuard, R8 Vault/lineage, R9 VRAM scheduling or R1 security/governance boundaries.

## Current external compatibility baseline — 2026-08-29

External library behavior is **dated capability evidence**, never a permanent architecture constant. R15 must record exact package/tool/model versions and capability-probe results in each training/conversion acceptance report.

### Dataset documentation, licensing and governance

- Hugging Face Dataset Cards are an interoperability/documentation reference for recording dataset contents, intended use, limitations/biases and metadata such as license, language and size. R15 keeps its canonical manifest repository-owned and may export card-compatible metadata.
- Hugging Face Model Cards are an interoperability/documentation reference for model identity, intended use/limitations, training parameters, datasets and evaluation results.
- SPDX 3.0.1 license expressions provide a machine-parseable representation of simple and compound license expressions. R15 accepts only explicit allowed expressions/policies; missing or unrecognized licensing remains quarantined.
- NIST AI RMF Generative AI Profile (NIST AI 600-1, updated 2026) is an informative risk/governance reference, not an architecture mandate.

Official references:

- https://huggingface.co/docs/hub/datasets-cards
- https://huggingface.co/docs/hub/model-cards
- https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/
- https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

### QLoRA / PEFT / SFT baseline

- QLoRA combines a 4-bit quantized base model with trainable LoRA parameters. Hugging Face bitsandbytes/PEFT guidance supports 4-bit training and recommends NF4 for 4-bit training; PEFT documents QLoRA-style targeting with `target_modules="all-linear"` where architecture compatibility permits.
- TRL `SFTTrainer` supports language-modeling, prompt-completion and conversational datasets. Completion-only/assistant-only loss behavior is configuration- and chat-template-dependent, so R15 must probe/model this explicitly rather than assume one template works for every family.
- Transformers Trainer exposes deterministic seeds and stricter full-determinism behavior; R15 records seeds, data split digests, package versions and checkpoint identity and tests resume semantics.
- Training frameworks are optional R15 tooling and MUST NOT become unconditional base-package dependencies.

Official references:

- https://huggingface.co/docs/bitsandbytes/main/en/reference/nn/linear4bit
- https://huggingface.co/docs/transformers/main/quantization/bitsandbytes
- https://huggingface.co/docs/peft/developer_guides/quantization
- https://huggingface.co/docs/peft/main/package_reference/lora
- https://huggingface.co/docs/trl/sft_trainer
- https://huggingface.co/docs/transformers/main_classes/trainer

### AMD / hardware capability baseline

- Current bitsandbytes documentation exposes AMD ROCm support, but the exact Windows/Linux wheel targets and AMD ROCm/HIP SDK device support are version- and hardware-specific. R15 must capability-probe actual Torch/ROCm/bitsandbytes/model operations and may not infer training support merely from GPU family or VRAM size.
- AMD’s own Windows Radeon/Ryzen compatibility matrices distinguish runtime support from full HIP SDK/library support for individual GPUs. A successful Ollama inference path does not prove QLoRA training support.
- Therefore no particular consumer GPU, Windows ROCm state, CUDA state or cloud accelerator is a frozen global prerequisite. Real local-GPU qualification is CONDITIONAL evidence.

Official references:

- https://huggingface.co/docs/bitsandbytes/installation
- https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/shared/hipsdk/reference/system-requirements.html

### GGUF / llama.cpp baseline

- `llama.cpp` requires GGUF for its native model path and documents conversion of Hugging Face models to GGUF followed by optional quantization.
- Quantization reduces model size and can improve inference resource use but may reduce quality; llama.cpp explicitly describes measuring degradation with metrics such as perplexity/KL divergence and supports importance-matrix-assisted quantization.
- Requantizing already-quantized tensors can severely reduce quality; R15 preserves high-precision lineage and treats requantization as non-authoritative unless explicitly justified and separately evaluated.
- GGUF/tool versions are recorded in conversion evidence; R15 never assumes a model architecture is supported merely because a file extension is `.gguf`.

Official references:

- https://github.com/ggml-org/llama.cpp/blob/master/docs/models.md
- https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md
- https://github.com/ggml-org/llama.cpp/blob/master/convert_hf_to_gguf.py

### Ollama import baseline

- Ollama documents import of compatible Safetensors models/adapters and GGUF models/adapters through `Modelfile`, `FROM`, `ADAPTER` and `ollama create`.
- The adapter must use the same base model it was tuned from; mismatch can produce erratic results and is a hard R15 rejection.
- Ollama can quantize supported FP16/FP32 models and exposes model details including format/family/parameter size/quantization. R15 records the exact resulting model digest and validates runtime behavior through the existing loopback-only Ollama boundary.
- Registry upload/sharing is not part of core R15 acceptance.

Official references:

- https://docs.ollama.com/import
- https://docs.ollama.com/modelfile
- https://docs.ollama.com/api-reference/show-model-details

### Benchmark contamination and reproducibility baseline

- Recent benchmark research continues to identify train/test contamination as a material threat to trustworthy LLM evaluation. R15 therefore treats benchmark isolation as a first-class security/provenance boundary rather than a post-hoc metric correction.
- Benchmark methodology prioritizes reproducibility, fixed task definitions, immutable inputs, explicit scoring rules, exact model/config identity and comparable execution conditions.

References:

- https://aclanthology.org/2025.emnlp-main.511/
- https://aclanthology.org/2026.acl-long.2071/
- https://mlcommons.org/benchmarks/

## Phase-wide architecture and governance boundaries

All accepted R1–R14 controls remain mandatory:

- `WorkspaceBoundary` and R8 `VaultBoundary` govern raw/quarantined/curated experiences, dataset versions, benchmark fixtures, model/adapters, checkpoints, GGUF files, conversion outputs and evidence.
- `ProcessSandbox` + global KillSwitch govern training, dataset tooling, converters, quantizers, Ollama create/import operations and repository-owned subprocesses.
- Guardian/`PermissionSet` authorizes data promotion, training, external model/data download, converter execution, model import/promotion and destructive cleanup.
- SafeChange snapshots wrap mutable registry/config/model-routing changes; rollback is defined before promotion.
- AuditLog records data promotion/rejection, dedup decisions, benchmark runs, train/no-train decisions, training execution, conversion, quantization and model promotion/rollback without leaking raw secrets/private content.
- `KodeSecrets` remains the sole secret authority. Secrets are redacted before persistence and no secret may enter training text, manifests, reports, stdout/stderr, command-line arguments visible to the model, checkpoints or public artifacts.
- R6 Health/Budget constrains disk, RAM, VRAM, CPU/GPU time, process counts and wall-clock execution. Budget exceedance is `BUDGET_EXCEEDED`, never PASS.
- R6 DataGovernance/Privacy/License/BOM controls apply to datasets, model inputs/outputs, external weights, adapters, transformation tools and distributable artifacts.
- R7 ResearchGuard keeps external documentation/model cards/dataset cards as untrusted evidence, never agent instructions.
- R8 immutable lineage and source-vs-derived distinction apply to every dataset/model artifact; derived model files never replace their source identity.
- R9 VRAM scheduling/unload semantics are reused for model/training resource coordination where technically applicable.
- R3 Brain/ModelRouter remains the runtime abstraction. R15 may register/promote compatible specialized models but may not bypass the router or silently rewrite role selection.
- R3 Ollama access remains loopback-only for authoritative local acceptance unless a later accepted architecture decision explicitly expands it.
- Structured Tool APIs are mandatory. Dataset text, model output, config text or prompt content may never become raw shell commands.

## Experience eligibility and data firewall

An experience is **not training data by default**. R15 defines explicit states:

`OBSERVED` → `ELIGIBLE` → `SANITIZED` → `CURATED` → `DATASET_INCLUDED`

with terminal alternatives `REJECTED`, `QUARANTINED`, `REVOKED` and `EXPIRED` where policy requires.

Promotion requires all applicable facts to be known and policy-allowed:

- source/project scope and stable origin identity;
- task/domain label;
- validated outcome or explicit quality label;
- training eligibility/consent or repository-owned fixture status;
- explicit license/provenance policy;
- secret/private-data scan result;
- benchmark-holdout contamination result;
- transformation lineage and content digest;
- duplicate/near-duplicate cluster identity;
- schema version and curator/policy decision.

Unknown values fail closed. Revocation must prevent future dataset builds and invalidate affected derived dataset versions/candidates through lineage.

### Hard train/evaluation firewall

- Benchmark holdout IDs/content digests/near-duplicate signatures are registered before dataset inclusion.
- Any exact or policy-threshold near match to a protected holdout is excluded/quarantined from training material.
- Benchmark outputs may be stored as evaluation evidence but not automatically recycled into training examples.
- A candidate trained on a contaminated dataset cannot be rehabilitated by good benchmark scores; the candidate and its derived artifacts are rejected.
- Dataset split assignment is deterministic from stable content/group identity, not row order, preventing duplicate clusters from crossing train/validation/test boundaries.

## KodeBench R15 critical-domain policy

R15 extends the R3 baseline rather than discarding it. At minimum the benchmark authority covers:

- exact instruction following;
- Python/software-engineering correctness;
- Godot/GDScript/current-engine awareness;
- debugging/repair;
- structured output/schema compliance;
- tool-call correctness and refusal to invent unavailable tool results;
- governance/security boundaries (secrets, permissions, path/network/process constraints);
- context/retrieval use and source grounding where applicable;
- code patch quality/regression constraints;
- multilingual behavior required by accepted project/product requirements;
- latency/load/tokens-per-second/resource metrics as non-quality dimensions.

`critical=true` tasks/domains are hard vetoes. An accepted candidate MUST NOT decrease the critical-domain acceptance result relative to its declared base under the same benchmark version/config. Aggregate improvements cannot compensate for a critical regression.

The exact statistical/score thresholds are versioned benchmark policy artifacts implemented in R15.6/R15.10. They must include minimum sample/repeat requirements, deterministic seeds/configuration, per-domain comparisons, error counts, resource budgets and an explicit reasoned disposition (`PROMOTE`, `REJECT`, `INCONCLUSIVE`).

## Training decision policy

Fine-tuning is permitted only if R15.7 produces `TRAIN` with evidence that:

1. the gap is reproducible on an uncontaminated benchmark;
2. the gap is plausibly model-trainable rather than primarily a tool/retrieval/router/context/product defect;
3. enough eligible curated data exists for the affected domain;
4. dataset license/provenance and base-model license permit the intended use/output;
5. a supported training path is capability-probed;
6. required disk/RAM/VRAM/time budgets are declared and acceptable;
7. an immutable before-benchmark exists;
8. rollback to the base model is available.

Otherwise the decision is `NO_TRAIN`, `INSUFFICIENT_DATA`, `FIX_SYSTEM_FIRST`, `UNSUPPORTED`, `LICENSE_BLOCKED`, `BUDGET_BLOCKED` or `INCONCLUSIVE` as appropriate. These are truthful outcomes, not failures to follow the roadmap.

## Phase-wide deterministic evidence contract

Every R15 decision artifact must bind to exact identities rather than mutable names alone. Depending on stage, evidence records:

- repository source SHA and tree/diff scope;
- dataset manifest digest and split digests;
- benchmark suite/version/task digests and scorer policy digest;
- protected holdout digest set / contamination-policy digest;
- base model identifier, immutable model/blob digest/revision, architecture, tokenizer identity and license;
- adapter config digest, seed/data seed, training framework versions and hardware/backend capability snapshot;
- checkpoint identity and resume lineage;
- conversion tool revision/version and GGUF metadata digest;
- quantization type/config/importance-matrix digest when used;
- Ollama version, Modelfile digest, created model digest/details;
- per-domain before/after metrics and critical-domain disposition;
- manual state and any exact user-side evidence when triggered;
- blockers/warnings and final `status`.

Reports with mixed source/model/dataset/benchmark SHAs are invalid.

## Global prerequisites

Before R15.1 implementation:

- R1–R14 are `COMPLETE + NORMALIZED` on `main`.
- R14 canonical integrated report remains `status=pass`, `blockers=[]`, semantic digest `06dbdc830b20fd4b2966b11cbacfd4b010f93101b071d827766c8b9cbfd45189`.
- R15 exhaustive planning PR is merged and exactly one continuity-only planning normalization is merged after fresh exact-head R0 + full Python Core + KodeStudio UI Smoke.
- Python remains >=3.12 according to repository packaging policy unless an accepted later decision changes it.
- The existing R3 `BaselineBench`, `OllamaClient`, ModelRouter and loopback restrictions remain operational.
- External model/training dependencies are optional and capability-probed; the base Kodepoia install must remain usable without PyTorch/Transformers/PEFT/TRL/bitsandbytes/llama.cpp.
- Internet access, external datasets, model-hub accounts, paid cloud GPU, CUDA/ROCm drivers and public publishing accounts are **not** global prerequisites.
- Large model weights, checkpoints and derived binaries must remain outside ordinary Git blobs and obey R8 Vault/LFS/derived-artifact policies.

## Complete subdivision index

| ID | Title | Status | Manual intervention | Depends on |
| --- | --- | --- | --- | --- |
| R15.1 | Experience contracts, eligibility state machine + training-data trust boundary | COMPLETE | NONE | R14 COMPLETE + normalized R15 planning |
| R15.2 | Governed validated-experience capture, outcome labeling + opt-in/source scope | COMPLETE | NONE | R15.1 + R1/R6/R8 |
| R15.3 | Sanitization, secret/privacy filtering, license/provenance policy + revocation | COMPLETE | NONE | R15.1–R15.2 + R6/R7/R8 |
| R15.4 | Exact/near deduplication, benchmark-contamination firewall + quarantine | COMPLETE | NONE | R15.1–R15.3 |
| R15.5 | Immutable dataset builder, group-safe deterministic splits, manifests + dataset cards | COMPLETE | NONE | R15.1–R15.4 |
| R15.6 | KodeBench v2 registry, domain/critical scoring, reproducibility + resource metrics | COMPLETE + NORMALIZED | NONE | R15.1/R15.4–R15.5 + R3/R6 |
| R15.7 | Gap diagnosis + governed TRAIN/NO_TRAIN decision engine | COMPLETE + NORMALIZED | NONE | R15.5–R15.6 + R3/R4/R7 |
| R15.8 | Optional training runtime, backend capability probes, dependency isolation + reproducibility | COMPLETE + NORMALIZED | CONDITIONAL | R15.7 + R1/R6/R9 |
| R15.9 | QLoRA/SFT adapter training, checkpoints, resume/cancel/recovery + budget controls | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED | R15.5/R15.7–R15.8 |
| R15.10 | Base-vs-adapter evaluation, critical-regression veto + candidate disposition | COMPLETE + NORMALIZED | NONE | R15.6/R15.9 |
| R15.11 | Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage | COMPLETE | NONE | R15.9–R15.10 + R8 |
| R15.12 | GGUF conversion + quantization matrix, quality-loss measurement + artifact validation | PLANNED | CONDITIONAL | R15.10–R15.11 + R6/R8/R9 |
| R15.13 | Ollama import/Modelfile packaging, base-binding + local runtime verification | PLANNED | CONDITIONAL | R15.10–R15.12 + R3 |
| R15.14 | Specialized-model registry, promotion/rollback + ModelRouter compatibility | PLANNED | NONE | R15.10–R15.13 + R3/R8 |
| R15.15 | CLI + KodeStudio Experience/Bench/Tune UX, dry-run/status/evidence workflows | PLANNED | NONE | R15.1–R15.14 |
| R15.16 | Hardware-local end-to-end qualification + reproducibility/resource acceptance | PLANNED | CONDITIONAL | R15.1–R15.15 |
| R15.17 | Adversarial integrated Experience/Bench/Fine-tuning acceptance | PLANNED | CONDITIONAL | R15.1–R15.16 |

---

# R15.1 — Experience contracts, eligibility state machine + training-data trust boundary

## Objective and rationale

Create the canonical data contracts and state machine that prevent ordinary logs, conversations, project files or model outputs from silently becoming training data. All later R15 data, benchmark and training operations depend on these identities and fail-closed eligibility rules.

## In scope

Typed experience IDs; source/project/task/domain identities; outcome/quality labels; eligibility states; content references/digests; provenance/license/consent descriptors; transformation lineage; benchmark-protection flags; redacted serialization; registry/storage interfaces; schema versions; permission/audit hooks; structured error/status vocabulary.

## Out of scope

Actual collection, sanitization, deduplication, dataset construction, benchmarking or training.

## Dependencies and prerequisites

Normalized R14 main and normalized R15 planning; existing WorkspaceBoundary, VaultBoundary, Guardian, Audit, KodeSecrets, DataGovernance and schema/versioning patterns.

## Detailed implementation plan

Add `src/kodepoia/experience/` foundations with immutable `ExperienceId`, `ExperienceState`, source scope, task/domain labels, evidence refs and a transition validator. Raw payload bytes remain referenced through governed storage rather than duplicated into audit records. Unknown training eligibility defaults to false. State transitions require explicit policy reasons and audit events. Serialization uses canonical ordering/hashing and strips sensitive raw content from summary/status objects.

Add JSON schema(s) under repository schema conventions and deterministic round-trip tests. Reject invalid transitions, mutable identifiers, missing provenance, cross-workspace references and any attempt to mark benchmark-protected content as training-includable.

## Deliverables

Experience package foundations; schemas; storage/protocol interfaces; focused unit/adversarial tests; R15.1 DESIGN/ACCEPTANCE documentation; any required package exports and R0 manifest updates.

## Acceptance gates / Definition of Done

Focused transition/schema/provenance/path-boundary tests; canonical serialization/digest stability on Ubuntu+Windows; full Python Core; R0; KodeStudio UI Smoke; exact-head evidence; protected PR merge; exactly one post-merge continuity-only normalization.

## Validation and evidence

Exact source SHA, schema digests, state-transition matrix, adversarial rejected fixtures, focused/full test counts and CI run IDs.

## Rollback / recovery

Remove new contracts/schemas and restore manifests/exports. No eligible corpus or model state exists yet.

## Risks and regression traps

Implicit opt-in; raw-content leakage into logs; workspace identity confusion; mutable content without digest update; permissive unknown-license defaults; benchmark flag bypass.

## Manual intervention

**NONE.**

## Completion record

**COMPLETE — technical acceptance recorded.**

- clean START-head: `a474d0c85d27ca7113a8044b2c29a5e664ebd352`;
- immutable technical source: `2da5e5d5aa712462c898270c41c5cafb42e6aeaa`;
- R15.1 Acceptance #6 / `33271323481`: SUCCESS Ubuntu + Windows, 18 focused tests + Ruff + compileall on both;
- R0 #2057 / `33271323508`: SUCCESS;
- Python Core #2032 / `33271323458`: SUCCESS 5/5; Ubuntu 1778 passed / 14 skipped / 46 warnings;
- KodeStudio UI Smoke #1997 / `33271323468`: SUCCESS;
- manual state: `NONE`;
- redaction/sanitization cannot convert a denied/unknown/review source authorization into training eligibility;
- rejected evidence candidates: `77f3ce9a935ea6c1816f3f6095d0d2b62db527aa` (synthetic PR-merge checkout) and `ea57df89e172d97f91498d758373e13048d7e707` (Ruff E501 failure).

Implementation merge and the unique continuity-only normalization remain required before R15.2 is authorized.

---

# R15.2 — Governed validated-experience capture, outcome labeling + opt-in/source scope

## Objective and rationale

Capture only high-value, policy-eligible experiences with evidence of what happened and whether the result was validated. R15 must learn from accepted outcomes, not from arbitrary model chatter or failed/unreviewed actions.

## In scope

Structured capture hooks around accepted Brain/tool/workflow outcomes; explicit opt-in/project policy; outcome labels (`accepted`, `rejected`, `corrected`, `failed`, etc.); source/action/result references; before/after or correction pairs where valid; capture quotas; replay-safe IDs; disabled-by-default training eligibility; user/project scope and audit trail.

## Out of scope

Automatic promotion to curated data, third-party web/dataset ingestion, training, free-form telemetry harvesting.

## Dependencies and prerequisites

R15.1; R1 permissions/audit/secrets; R6 privacy/budget; R8 Vault; accepted workflow outcome/evidence patterns from earlier phases.

## Detailed implementation plan

Introduce an `ExperienceCollector` and repository-owned capture policy. Integrations write normalized records only after an operation has a validated terminal outcome and the source policy allows capture. Content references are stored in a quarantined/raw Vault area with size/type limits; audit/status surfaces contain digests and redacted summaries only. Duplicate event delivery is idempotent.

Support explicit correction provenance: original response/action, validated correction or accepted patch, evaluator/source of validation and result linkage. Never infer “good training example” merely because a command exited zero or a user did not complain.

## Deliverables

Collector/policy implementation, raw Vault layout, schemas/config, focused tests/fixtures, CLI inspection capability where appropriate, R15.2 docs/evidence.

## Acceptance gates / Definition of Done

Capture-disabled-by-default tests; explicit eligibility tests; failed/rejected outcome behavior; idempotency; quota/budget; path/scope isolation; secret-like fixture non-leakage; full R0/Python/UI and exact-head acceptance.

## Validation and evidence

Deterministic record IDs/digests, accepted/rejected capture matrix, storage paths relative to governed root, audit redaction evidence and CI runs.

## Rollback / recovery

Disable collector, preserve raw records as quarantined/non-training or safely delete derived records through Vault lineage policy; no automatic dataset inclusion exists.

## Risks and regression traps

Feedback loops from model-generated labels; capturing private source accidentally; duplicate event inflation; equating build success with semantic correctness; hidden project-scope mixing.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R15.3 — Sanitization, secret/privacy filtering, license/provenance policy + revocation

## Objective and rationale

Make training eligibility dependent on deterministic sanitization and legal/governance evidence. Data that cannot be safely and permissibly used stays quarantined.

## In scope

Secret scanning/redaction; configured private-data patterns; path/metadata scrub; provenance normalization; SPDX-compatible license expression handling and repository policy; source-type allow/deny rules; model/dataset base terms metadata; revocation/tombstone propagation; human-readable rejection reasons; dataset/model-card-ready provenance summaries.

## Out of scope

Legal advice, automatic assertion that an unknown public source is trainable, external dataset scraping.

## Dependencies and prerequisites

R15.1–R15.2; KodeSecrets; R6 privacy/license/BOM; R7 ResearchGuard; R8 lineage.

## Detailed implementation plan

Create staged sanitizers whose transformations are versioned and digest-bound. Secret detectors must reuse accepted redaction primitives and include entropy/pattern fixtures without preserving detected values in reports. License policy parses explicit known expressions/refs but treats unknown/ambiguous/custom terms as `LICENSE_REVIEW`/quarantine unless an accepted policy maps them.

Revocation is lineage-aware: a revoked source marks dependent curated rows/dataset versions/candidates non-promotable and emits a rebuild requirement. Reports record category/count/digest, never secret value.

## Deliverables

Sanitization pipeline, license/provenance policy, revocation index, schemas, tests, fixtures, design/acceptance evidence.

## Acceptance gates / Definition of Done

Adversarial secret/private/path leakage tests; license allow/deny/unknown compound-expression tests; transformation determinism; revocation cascade tests; zero raw secret in generated reports; full R0/Python/UI.

## Validation and evidence

Sanitizer/policy digests, redaction counts/categories, provenance examples with synthetic data, revocation lineage checks and CI IDs.

## Rollback / recovery

Revert sanitizer/policy version and invalidate/rebuild affected derived data rather than silently reusing it under different rules.

## Risks and regression traps

False confidence from pattern-only redaction; custom license misclassification; reports echoing matched secrets; revocation not reaching already-built derived data.

## Manual intervention

**NONE.** Legal ambiguity remains `LICENSE_REVIEW`/blocked rather than requesting sensitive credentials or silently guessing.

## Completion record

**COMPLETE + NORMALIZED.**

- clean START-head: `ba719dd9d556909b08606d6c7ebb4d4ef18dbd37`;
- immutable technical source: `e049a8f5c8155accb1d64ca4028deec5f85c4aa8`;
- final END-head: `3a41e703bdedaf613e88dc672bee1b8ca01b62ff`;
- exact-END R15.3 #19 / `33283462348`: SUCCESS Ubuntu + Windows;
- R0 #2088 / `33283462344`: SUCCESS Ubuntu + Windows;
- Python Core #2063 / `33283462455`: SUCCESS 5/5;
- KodeStudio UI Smoke #2028 / `33283462377`: SUCCESS;
- PR #300 merged with protected exact head as `4b37d7735194e9b4b21899d44ad4224c418979ed`;
- post-merge normalization head `db823f11fbc04007b304810fb94aa300fc8ddc48`: R0 #2090 / `33283698522`, Python #2065 / `33283698570`, UI #2030 / `33283698532` SUCCESS; normalization PR #301 -> normalized `main` `ffb5a830cce35334b3f62e69fae2e2c02c717080`;
- manual state: `NONE`.


---

# R15.4 — Exact/near deduplication, benchmark-contamination firewall + quarantine

## Objective and rationale

Prevent repeated examples from dominating training and prevent benchmark leakage from invalidating before/after comparisons.

## In scope

Canonical text/code normalization for comparison only; exact hashes; near-duplicate fingerprints/similarity policy; group/cluster identity; cross-split grouping; benchmark protected-signature registry; contamination scanner; quarantine reason/index; deterministic representative selection; false-positive review metadata.

## Out of scope

Semantic rewriting of examples, benchmark generation by the candidate model, training.

## Dependencies and prerequisites

R15.1–R15.3.

## Detailed implementation plan

Implement deterministic exact and near-duplicate clustering with algorithm/version/config digest. Preserve original sanitized content; normalization/fingerprints are derived metadata. Register benchmark holdouts before dataset building and scan both exact and near matches. Entire duplicate groups share one split group ID so variants cannot leak across train/validation/test.

Contamination scans run incrementally and as a complete pre-build gate. Any protected match above the accepted threshold is quarantined with source/fingerprint evidence. Benchmark results never become training inputs automatically.

## Deliverables

Dedup/contamination modules, protected-holdout registry schema, fixtures for exact/near/cross-language-or-code variants where applicable, reports/tests/docs.

## Acceptance gates / Definition of Done

Deterministic clustering across row order/platform; no cluster crosses dataset groups; exact/near benchmark leakage rejected; threshold-boundary tests; no benchmark raw protected content leaked in reports; full R0/Python/UI.

## Validation and evidence

Algorithm/config digest, cluster counts, contamination summary, synthetic match IDs, deterministic dataset-group assignments and CI IDs.

## Rollback / recovery

Changing dedup/contamination policy creates a new policy version and forces rebuild; old derived datasets remain immutable but lose promotion eligibility if policy is superseded.

## Risks and regression traps

Over-dedup destroying useful diversity; under-dedup leakage; normalization collision; changing threshold without lineage invalidation; benchmark content copied into diagnostic reports.

## Manual intervention

**NONE.**

## Completion record

**COMPLETE.**

- clean START-head: `68a6d1a5d35430128db8fa450bd9afa4e0c7c36e`;
- immutable technical source: `b82c7595f69f94e173a6e7893073585c9f8c1aae`;
- technical R15.4 #7 / `33284070954`: SUCCESS Ubuntu + Windows, 68 cumulative tests per OS + Ruff + compile;
- R0 #2092 / `33284070915`: SUCCESS Ubuntu + Windows;
- Python Core #2067 / `33284070930`: SUCCESS 5/5;
- KodeStudio UI Smoke #2032 / `33284070882`: SUCCESS;
- manual state: `NONE`;
- final END-head: `e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d`; exact-END R15.4 #16 / `33284334173`, R0 #2097 / `33284334475`, Python Core #2072 / `33284334142`, and KodeStudio UI Smoke #2037 / `33284334250` all SUCCESS;
- PR #302 merged with `expected_head_sha=e91a2f18ef79f66672e42bdf04ad4d731ec7bf8d` as `195920e06fb6487fe58be4247ba9b90a75b96dad`;
- unique continuity-only normalization head `8aee5b6f69c61c513e0c3dcd56cba1035c365d18` passed R0 #2099 / `33287315588`, Python Core #2074 / `33287315591`, and UI #2039 / `33287315606`; normalization PR #303 merged with exact expected head as normalized `main` `8744df5f3a408595693c67819a29f95b3a82f1d7`.


---

# R15.5 — Immutable dataset builder, group-safe deterministic splits, manifests + dataset cards

## Objective and rationale

Turn curated eligible experiences into reproducible training/validation datasets without losing lineage or allowing duplicate groups to cross splits.

## In scope

Dataset selection query/policy; immutable dataset version; deterministic group-aware train/validation split and optional internal test split distinct from KodeBench protected holdouts; task/domain balancing; prompt-completion/conversational canonical forms; tokenizer-independent source representation; manifests; per-split hashes/stats; dataset card; export adapters for supported training frameworks.

## Out of scope

Training, public dataset upload, benchmark holdout inclusion.

## Dependencies and prerequisites

R15.1–R15.4.

## Detailed implementation plan

Add `DatasetBuilder` over curated records. Selection policy includes required sanitizer/dedup/license versions and domain constraints. Split assignment derives from stable group identity plus explicit seed/policy digest so row order cannot alter membership. Dataset manifests list source record IDs/digests and transformations but avoid embedding secrets/private rejected content.

Generate repository/Vault-owned JSONL or Arrow-compatible export as appropriate plus a Markdown/YAML dataset-card record describing origin, license policy, intended use, limitations, language/domain distributions, filters and known gaps. Exports are derived artifacts and reproducible from manifest + source Vault state.

## Deliverables

Dataset builder, manifest/card schemas, exporters, fixtures, deterministic split tests, R15.5 acceptance report.

## Acceptance gates / Definition of Done

Rebuild byte/semantic determinism where format permits; no duplicate group cross-split; no protected holdout; manifest-to-row reconciliation; license/provenance completeness; size/domain stats; full R0/Python/UI.

## Validation and evidence

Dataset version/digest, split digests/counts/domain distribution, source policy digest, card digest and exact-head CI.

## Rollback / recovery

Datasets are immutable; rollback changes the active dataset pointer to a prior eligible version. Invalidated source lineage prevents new use but preserves audit evidence.

## Risks and regression traps

Data ordering changing splits; source revocation ignored; chat-template-specific formatting baked too early; train/validation duplicates; derived exports treated as source authority.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

## R15.5 implementation and END-sync recovery evidence

- Clean START: `4c9bee744e4c43ef130e50c4867ca3d467878c51` from normalized R15.4 `main` `8744df5f3a408595693c67819a29f95b3a82f1d7`.
- Immutable technical source: `1ecdfda67a23d8659e48e4c76f805a45a1560ec5`.
- Exact-source qualification: R15.5 #4 / `33288632868` SUCCESS Ubuntu + Windows; R0 #2102 / `33288632870` SUCCESS; Python Core #2077 / `33288632943` SUCCESS 5/5; KodeStudio UI Smoke #2042 / `33288632867` SUCCESS.
- Technical scope accepted: policy-bound immutable dataset construction, authoritative R15.4 group-safe splits, contamination exclusion, deterministic domain and `(domain, task)` balancing, tokenizer-independent text/prompt-completion/conversational JSONL, safe provenance, strict manifest/card schemas and fail-closed manifest↔JSONL reconciliation.
- Pre-recovery PR head `9cc528a3be1dba2f915b6383c1817191f78060d1` passed R15.5 #6 / `33288867382` SUCCESS Ubuntu + Windows, R0 #2103 / `33288867356` SUCCESS, Python Core #2078 / `33288867418` SUCCESS 5/5 and KodeStudio UI Smoke #2043 / `33288867394` SUCCESS, then PR #304 merged with exact expected head as `ceba5be8875e5eb9af62db202c050015be00e09a`.
- Recovery reason: `.github/workflows/r15-5-end-sync-helper.yml` did not execute its intended documentary synchronization before PR #304 merged. The merge therefore left this phase plan, design, acceptance and continuity stale. No stale status or prior rejected evidence is laundered into normalization.
- This END-sync recovery candidate changes documentary authority only. Its final exact head MUST receive fresh R15.5 acceptance + R0 + full Python Core + KodeStudio UI Smoke before the recovery PR may merge with `expected_head_sha`.
- After recovery merge, exactly one continuity-only post-merge normalization remains mandatory before R15.6 START-sync.
- Manual state: **NONE**.

---

# R15.6 — KodeBench v2 registry, domain/critical scoring, reproducibility + resource metrics

## Objective and rationale

Promote the R3 baseline benchmark into an immutable, extensible authority capable of deciding whether specialization actually improves Kodepoia without hiding regressions.

## In scope

Versioned benchmark suite/task registry; domain/critical labels; deterministic task IDs and prompt/scorer digests; exact/regex/schema/tool-call/custom repository-owned scorers; repeated seeds; model/config/runtime identity; per-domain and aggregate scores; error categories; latency/load/tokens-per-second/resource measures; comparative reports; protected holdout export to R15.4.

## Out of scope

Training, model promotion, external leaderboard claims.

## Dependencies and prerequisites

R15.1, R15.4–R15.5; existing `src/kodepoia/bench/baseline.py`; R3 Brain/Ollama; R6 Quality/Budget.

## Detailed implementation plan

Refactor/extend rather than break `BaselineBench`. Add explicit suite definitions and stable scorer versions while preserving R3 command compatibility. Bench tasks can be static protected fixtures or deterministic repository-owned generators whose seed/config is part of suite identity. Store only appropriate prompts/expected values; holdout access is read-only to the runner and prohibited to dataset builders.

Comparisons bind base and candidate runs to the same suite/config/repeats. Reports include per-task outcomes, per-domain summaries, variance, runtime metrics, unavailable capabilities and scorer errors separately from model failures.

## Deliverables

KodeBench v2 modules/schemas, compatibility layer, expanded governed fixture suite, compare CLI/library API, tests, benchmark policy docs/evidence.

## Acceptance gates / Definition of Done

R3 baseline compatibility; deterministic suite digest; same-run reproducibility within defined nondeterminism policy; scorer failure isolation; critical-domain labels; contamination registry integration; metrics schema validation; full R0/Python/UI.

## Validation and evidence

Suite/scorer digests, task inventory, repeated fixture results on fake/local test clients, backward-compat report checks and CI IDs.

## Rollback / recovery

Benchmark versions are immutable. Router/model promotion may pin an older accepted suite until a new suite is separately accepted; never rewrite historical scores under a new scorer.

## Risks and regression traps

Benchmark overfitting; brittle string matching; hidden test leakage; aggregate score masking critical failure; comparing runs with different options/context/templates.

## Manual intervention

**NONE.** Core acceptance uses deterministic fakes/fixtures; real local models are handled later.

## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.5 branch point: `097e99db28508cd1c53eadfe00b2b33576a445af`;
- continuity START-sync preceded implementation; `R15_PLAN.md` START checkpoint/table was stale and is repaired truthfully here rather than retroactively claimed;
- immutable technical source: `ae856396faa964fee19ee39e461bc7de4e775cd9`;
- R15.6 #2 / `33295649414`: SUCCESS Ubuntu + Windows, 17 combined R3/R15.6 tests per OS plus schema/Ruff/import/compile/CLI checks;
- R0 #2124 / `33295649494`: SUCCESS Ubuntu + Windows;
- Python Core #2099 / `33295649527`: SUCCESS 5/5;
- KodeStudio UI Smoke #2064 / `33295649458`: SUCCESS;
- manual state: `NONE`;
- the exact final documented END-head must receive fresh R15.6/R0/Python/UI evidence before protected merge; technical-source evidence is not reused for that decision.


---

# R15.7 — Gap diagnosis + governed TRAIN/NO_TRAIN decision engine

## Objective and rationale

Determine whether a measured weakness should be solved by model training at all. This preserves the frozen roadmap principle “build around the model, measure, then specialize.”

## In scope

Gap records; domain/task clustering; system-vs-model diagnostic probes; data sufficiency; license/base-model eligibility; hardware/backend feasibility snapshot; expected impact/risk/budget; candidate base-model selection from accepted registry; explicit decision vocabulary; decision report/audit.

## Out of scope

Executing training, silently changing prompts/tools/router to manufacture a passing benchmark.

## Dependencies and prerequisites

R15.5–R15.6 plus R3/R4/R7 diagnostic/tooling boundaries.

## Detailed implementation plan

Create a deterministic decision engine with ordered gates: benchmark reproducibility → contamination validity → system diagnostic → eligible data sufficiency → model/base license → backend capability/budget → rollback readiness. Diagnostic variants can test tool availability, retrieval/context assembly and router selection without modifying benchmark authority. If a tool/context defect explains the gap, result is `FIX_SYSTEM_FIRST`.

A `TRAIN` decision records target domains, immutable base model identity, dataset version, benchmark before-run, permitted adapter method and explicit acceptance targets. There is no implicit train trigger from a low score.

## Deliverables

Gap/decision models, rule engine, diagnostic probes, schemas, tests, CLI inspection, R15.7 evidence.

## Acceptance gates / Definition of Done

All decision terminal states tested; unknown license/data/backend fails closed; base benchmark required; critical targets explicit; same evidence yields same decision; full R0/Python/UI.

## Validation and evidence

Decision-policy digest, synthetic `TRAIN` and each `NO_TRAIN` family fixture, input evidence digests and CI IDs.

## Rollback / recovery

Decisions are immutable records; a superseding decision cites prior record and changed evidence. No training occurs in this subdivision.

## Risks and regression traps

Training used to paper over tool bugs; circular data sufficiency; mutable base tag without digest; decision thresholds tuned after seeing candidate outcome.

## Manual intervention

**NONE.**

## Completion record

- Post-merge normalization head `d07ca7b2ab550e0fcaf09897d51d72b2dd94d590`: R0 #2140 / `33300956787`, Python Core #2115 / `33300956780` (5/5), UI #2080 / `33300956762` SUCCESS; PR #310 merged with exact expected head as normalized `main` `5de1cabd3e861e75204595de1819564c782a217d`. R15.7 is COMPLETE + NORMALIZED; manual NONE.
**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.6 main: `9ef6f704d54332203e820cd2bd85e3b4ac86910a`;
- START synchronization before implementation: `07593e95380df6fb43bda299b7de7295c614d17f`;
- immutable technical source: `a9a967289bbede1ffd155567f3caaa201d1af772`;
- R15.7 Acceptance #2 / `33299136312`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2134 / `33299136336`: SUCCESS Ubuntu + Windows;
- Python Core #2109 / `33299136316`: SUCCESS 5/5;
- KodeStudio UI Smoke #2074 / `33299136461`: SUCCESS;
- deterministic ordered gates cover benchmark reproducibility, contamination validity, system diagnostics, data sufficiency, dataset/base licence, backend/budget and rollback readiness;
- `FIX_SYSTEM_FIRST` precedes training/data/licence gates when a relevant system defect explains the measured gap;
- R15.7 executes no training and mutates no model/router/tool state;
- manual state: `NONE`;
- the exact final documented END-head must receive fresh R15.7/R0/Python/UI evidence before protected merge; technical-source evidence is not reused for that decision.


---

# R15.8 — Optional training runtime, backend capability probes, dependency isolation + reproducibility

## Objective and rationale

Provide a safe optional training environment without making heavy ML stacks part of the core Kodepoia installation and without assuming a GPU/backend works from its name alone.

## In scope

Optional training dependency profile; Python/framework version probe; Torch device/backend probe; bitsandbytes/quantization capability probe; CPU/CUDA/ROCm capability vocabulary; available dtype/4-bit operations; disk/RAM/VRAM estimate; model/tokenizer load dry-run; deterministic seeds/config; ProcessSandbox/KillSwitch runner; stdout/stderr redaction; environment report.

## Out of scope

Driver installation, QLoRA training itself, mandatory cloud accelerator.

## Dependencies and prerequisites

R15.7; R1 sandbox/secrets; R6 health/budget; R9 VRAM coordination.

## Detailed implementation plan

Add `src/kodepoia/tuning/` runtime contracts and a repository-owned training launcher that accepts structured configuration only. Heavy dependencies live behind optional imports/extras or an explicitly managed environment. Probe actual operations needed for QLoRA, not just package imports. Record backend/device capability and fail with `UNSUPPORTED` when a requested quantization/training path is unavailable.

Process launch is bounded, cancellable and kill-switch-aware. No command string comes from dataset/model text. Environment evidence records package/tool versions and device descriptors without serializing unrelated machine/user information.

## Deliverables

Training runtime/probe package, optional dependency strategy, dry-run CLI/API, fixtures/fakes, tests and capability report schema.

## Acceptance gates / Definition of Done

Core install works without ML extras; fake CPU/supported/unsupported backend tests; subprocess cancellation/timeout; budget preflight; import/error handling; no secret in argv/report; full R0/Python/UI.

## Validation and evidence

Capability report/digest, optional dependency matrix, synthetic backend fixtures, CI IDs and any real local probe if explicitly triggered.

## Rollback / recovery

Remove optional environment and derived caches safely; no model registry change. Core Kodepoia remains unaffected.

## Risks and regression traps

Assuming Windows ROCm/CUDA from device name; importing unavailable heavy packages at CLI startup; driver mutation; subprocess orphaning; huge model download before budget approval.

## Manual intervention

**CONDITIONAL.** Core acceptance uses isolated/fake/CI-capability paths. If authoritative acceptance of a specific local GPU/backend is required, the user must run the bounded R15 capability command on the exact accepted head and return the generated JSON with secrets/private paths redacted. No driver installation or system mutation is to be requested automatically.

## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.7 main: `5de1cabd3e861e75204595de1819564c782a217d`;
- immutable technical source: `fa932e4a436004045074f417005b2edc038cfc87`;
- R15.8 #5 / 33306096508: SUCCESS Ubuntu + Windows, 13 focused tests per OS, Ruff, compileall, CLI help and capability-schema validation;
- core acceptance installs only `.[dev]`; PyTorch/Transformers/Accelerate/PEFT/TRL/bitsandbytes remain optional and are not imported by `kodepoia.tuning`;
- CPU/CUDA/ROCm and requested dtype/NF4 support are decided by bounded real-operation probes rather than device-name or backend-name assumptions; CPU NF4 is not pre-rejected;
- nonzero disk/RAM requirements with unavailable host measurements fail closed before subprocess launch; accelerator VRAM admission remains fail-closed before model load;
- model/tokenizer identifiers stay out of subprocess argv and reports; model/tokenizer load is a distinct local-only second phase after admission;
- timeout/KillSwitch cancellation and bounded redacted failure evidence are terminal non-success paths;
- real local GPU/backend qualification was not required for core R15.8 and manual state remains `CONDITIONAL / NOT TRIGGERED`;
- the exact final documented END-head must receive fresh R15.8 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke evidence before protected merge; technical-source evidence is not reused for that decision.


---

# R15.9 — QLoRA/SFT adapter training, checkpoints, resume/cancel/recovery + budget controls

## Objective and rationale

Implement the roadmap’s “QLoRA si utile” as a reproducible adapter-training capability gated by R15.7, with checkpoint/recovery and bounded resource use.

## In scope

Model/tokenizer/base revision binding; 4-bit quantized base where supported; PEFT LoRA config; QLoRA-style target selection policy; TRL/Trainer SFT configuration; prompt-completion/conversation format adapters; assistant/completion-only loss capability checks; gradient checkpointing/config; deterministic seeds; checkpoint schedule; resume; cancellation/KillSwitch; training/eval loss; resource telemetry; adapter Safetensors output.

## Out of scope

Full-weight default training, RLHF/DPO, auto-promotion, public upload.

## Dependencies and prerequisites

R15.5 dataset, R15.7 `TRAIN` or fixture-training authorization, R15.8 supported capability.

## Detailed implementation plan

Create a typed `TrainingPlan` that binds exact base model, tokenizer, dataset version/splits, LoRA config, quantization config, seed/data seed, batch/accumulation/context limits, optimizer/scheduler and budgets. QLoRA defaults follow capability-probed PEFT/bitsandbytes guidance (e.g. NF4/all-linear where appropriate) but are not blindly applied to unsupported architectures.

The trainer emits immutable run/checkpoint metadata. Resume verifies the same base/dataset/config lineage. Cancellation leaves a terminal run state and recoverable last-good checkpoint. A tiny repository-owned fixture model/dataset path must exercise orchestration without downloading large weights in CI.

## Deliverables

Training plan/schema, QLoRA/SFT runner, checkpoint registry, tiny fixture training path, tests, R15.9 acceptance report.

## Acceptance gates / Definition of Done

Deterministic config; tiny train run produces adapter; resume/cancel/recovery; mismatched resume rejected; budget/timeout; base/tokenizer mismatch rejected; train split only; validation split not optimized as training data; full R0/Python/UI plus optional focused runtime workflow.

## Validation and evidence

Training-plan digest, base/dataset/config identities, seed, framework versions, step/loss summary, checkpoint/adaptor digests, resource maxima and CI/manual state.

## Rollback / recovery

Training creates derived artifacts only. Reject/delete temporary checkpoints through Vault policy and restore active candidate pointer; base model is immutable.

## Risks and regression traps

OOM; optimizer/checkpoint incompatibility; template loss mask wrong; base model drift; accidental validation/benchmark training; unsupported 4-bit backend; non-reproducible resume.

## Manual intervention

**CONDITIONAL.** Large/real-model training may require user-side local hardware or explicitly authorized external compute. Core orchestration acceptance uses bounded fixtures. If the gate triggers, exact commands, expected report fields, failure recovery and evidence are supplied at that subdivision and execution stops before later subdivisions until reviewed.

## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- clean START / normalized R15.8 `main`: `4c1c726301b5a5f798944632336e130ccfb0cbbe`;
- START synchronization preceded implementation and kept R15.10–R15.17 PLANNED;
- immutable technical source: `a964bff54886cafe640fb583610e81055fbe3907`;
- R15.9 QLoRA SFT Acceptance #4 / `33310588740`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2146 / `33310588679`: SUCCESS Ubuntu + Windows;
- Python Core #2121 / `33310588722`: SUCCESS 5/5;
- KodeStudio UI Smoke #2086 / `33310588691`: SUCCESS;
- core acceptance installs only `.[dev]`; heavy ML dependencies remain optional and real target-GPU/backend qualification is not claimed;
- deterministic repository-owned fixture training produces canonical cross-platform Safetensors adapter/checkpoint evidence, validates train-only optimization, resume lineage/integrity, mismatch rejection, cancellation/timeout and fail-closed RAM/disk budgets;
- model and tokenizer revisions/digests are separately bound; dataset/manifest/train+validation export lineage is immutable; assistant-only/completion-only loss modes fail closed when their declared dataset/template capability is incompatible;
- manual state: `CONDITIONAL / NOT TRIGGERED`;
- PR #313 carries this technical source; the exact final documented END-head produced by this synchronization must receive fresh R15.9 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke evidence before protected merge. Technical-source evidence above is not reused for that final merge decision.

---

# R15.10 — Base-vs-adapter evaluation, critical-regression veto + candidate disposition

## Objective and rationale

Prove whether the trained adapter is actually better for its declared gaps without sacrificing critical behavior.

## In scope

Immutable base before-run; adapter candidate after-run; same KodeBench suite/config/repeats; per-task/domain paired comparison; critical veto; target-domain gain; aggregate score; errors; latency/resource deltas; overfit indicators; validation-loss context; `PROMOTE_TO_EXPORT`, `REJECT`, `INCONCLUSIVE` disposition.

## Out of scope

GGUF/Ollama conversion, router promotion.

## Dependencies and prerequisites

R15.6, R15.9; uncontaminated protected benchmark; exact base/adapter identities.

## Detailed implementation plan

Comparison runner asserts suite/config identity before calculating deltas. Critical-domain regression is a hard reject. Candidate must satisfy declared target-domain acceptance and must not exceed accepted resource/error budgets. Repeated-run variance is surfaced; high instability can yield `INCONCLUSIVE`. A rejected candidate is immutable evidence but cannot feed training automatically.

## Deliverables

Comparison policy/runner/schema, candidate-disposition record, tests covering critical regression despite aggregate gain, target improvement, tie/inconclusive and runtime regressions.

## Acceptance gates / Definition of Done

Mixed-suite/base/config comparison rejected; critical veto proven; target improvement policy deterministic; rejected candidate blocked downstream; full R0/Python/UI.

## Validation and evidence

Before/after run digests, per-domain deltas, critical matrix, resource deltas, disposition-policy digest and CI IDs.

## Rollback / recovery

No active model changes. Rejected adapter remains non-promotable and can be garbage-collected according to retention policy after evidence is preserved.

## Risks and regression traps

Cherry-picking tasks; changing generation config between runs; aggregate score masking critical regression; benchmark contamination; candidate-generated evaluation labels.

## Manual intervention

**NONE.**

## Completion record

**COMPLETE — technical acceptance recorded; fresh final-END gates required before merge.**

- normalized R15.9 base: `ba37dbc46393ca64d565ee1122fe545cc1b48c2d`;
- clean R15.10 START head: `f539e0f340f780222dfd4c6a690c4cfb22f961f6`;
- immutable technical source: `a4770042509dbba9397c974f2f5f153513f97b24`;
- R15.10 Base Adapter Evaluation Acceptance #4 / `33314874217`: SUCCESS Ubuntu + Windows;
- R0 Repository Guard #2157 / `33314874266`: SUCCESS Ubuntu + Windows;
- Python Core #2132 / `33314874246`: SUCCESS 5/5;
- KodeStudio UI Smoke #2097 / `33314874243`: SUCCESS;
- comparison is digest-bound to identical KodeBench suite/config/protection evidence, exact base/candidate identities and exact `(task_id, repeat, seed)` pairing; duplicate/missing pairs and mixed evidence fail closed;
- any critical-task regression is a hard rejection even when aggregate score improves; target-domain gain, error/latency/VRAM budgets, repeat instability and train/validation loss context produce deterministic `PROMOTE_TO_EXPORT`, `REJECT` or `INCONCLUSIVE`;
- `REJECT` and `INCONCLUSIVE` candidates cannot feed R15.11 through the exportability guard; serialized disposition evidence is Draft 2020-12 schema validated;
- manual state: `NONE`;
- PR #315 carries this technical source; the exact final documented END-head produced by this synchronization must receive fresh R15.10 + R0 Repository Guard + full Python Core + KodeStudio UI Smoke evidence before protected merge. Technical-source evidence above is not reused for that final merge decision.

---

# R15.11 — Accepted adapter/model export, merge compatibility, Safetensors/model card + lineage

## Objective and rationale

Package an accepted adapter and, where supported/needed, a merged high-precision model as immutable derived artifacts with complete base/dataset/training/evaluation lineage.

## In scope

Adapter Safetensors validation; adapter config; tokenizer/template artifacts; optional safe merge into the exact base model when framework/license/architecture allow; high-precision export; model card; license/provenance manifest; checksums; artifact sizes; derived/source relationships.

## Out of scope

GGUF quantization, Ollama import, public upload.

## Dependencies and prerequisites

R15.9–R15.10 accepted disposition; R8 Vault/lineage.

## Detailed implementation plan

Validate adapter tensors/config and bind them to immutable base identity. Merge, if selected, occurs from a supported high-precision base and is validated by load/inference smoke and benchmark spot-check; unsupported merge remains adapter-only rather than being forced. Generate model-card metadata describing base, dataset version, training config, intended use/limits and accepted eval results. Preserve third-party license notices without rewriting them.

## Deliverables

Exporter/validator, artifact manifest/model card, schemas, tests with tiny model fixture, R15.11 evidence.

## Acceptance gates / Definition of Done

Adapter/base mismatch rejected; deterministic manifest; load smoke; no missing provenance/license; no secret/private source contents in card; source weights not overwritten; full R0/Python/UI.

## Validation and evidence

Artifact hashes/sizes, base/adaptor/merged identities, export tool versions, card/manifest digest and CI IDs.

## Rollback / recovery

Derived export is immutable and removable without affecting source model/adapter evidence. Active registry remains unchanged until R15.14.

## Risks and regression traps

Merging into wrong base revision; tokenizer/template omitted; license metadata loss; huge artifacts placed in Git; candidate identity confused with base.

## Manual intervention

**NONE** for fixture/core exporter. Large external model availability remains a capability state rather than an inferred PASS.

## Completion record

To be appended when accepted.

---

# R15.12 — GGUF conversion + quantization matrix, quality-loss measurement + artifact validation

## Objective and rationale

Create deployable GGUF variants without assuming conversion or quantization preserves quality.

## In scope

llama.cpp tool capability/revision probe; model/adaptor conversion path where supported; high-precision GGUF source; selected quantization matrix (policy-driven, not hard-coded forever); optional importance matrix; metadata validation; file hashes/sizes; load/inference smoke; KodeBench comparison against accepted pre-quant candidate; quantization-loss report; rejection thresholds.

## Out of scope

Requantization as default, Ollama promotion, public distribution.

## Dependencies and prerequisites

R15.10–R15.11, R6 budgets, R8 artifact lineage, R9 resource scheduling.

## Detailed implementation plan

Run repository-owned converter/quantizer wrappers via ProcessSandbox with structured args. Probe whether the exact architecture is supported. Convert from the highest-quality accepted source available. Each output records converter revision, input hash, quant type, command-argument structure, metadata and output hash. Evaluate candidate quantizations on a defined KodeBench subset/full suite as policy requires; any critical regression or unacceptable target degradation rejects that quant.

Never silently use `--allow-requantize`. If only an already quantized source exists, mark the authoritative high-quality conversion path `UNAVAILABLE` unless a separately accepted exception documents the quality risk.

## Deliverables

GGUF tool wrapper/capability probe, conversion/quantization plan schema, validators, tiny fixture/tool fakes, quality matrix report, tests/docs.

## Acceptance gates / Definition of Done

Unsupported architecture fails cleanly; input/output lineage; quant type recorded; malformed GGUF rejected; quantization quality comparison; critical veto preserved; disk budget/cleanup; full R0/Python/UI plus focused conversion workflow if tool available.

## Validation and evidence

Tool revision/version, input/output hashes, metadata, quant matrix sizes/scores/resource metrics, accepted/rejected variants and CI/manual state.

## Rollback / recovery

Remove rejected/temporary derived GGUFs, retain accepted high-precision source and evidence, restore prior registry pointers.

## Risks and regression traps

Architecture unsupported by converter; quant quality collapse; tokenizer/template metadata mismatch; disk exhaustion; requantization; model file extension accepted without semantic validation.

## Manual intervention

**CONDITIONAL.** Core wrappers/fixtures are automated. A real large-model conversion may require locally installed llama.cpp and disk/resources not available in hosted CI. If triggered, execution stops and requests only bounded user-side commands/evidence on the exact head.

## Completion record

To be appended when accepted.

---

# R15.13 — Ollama import/Modelfile packaging, base-binding + local runtime verification

## Objective and rationale

Make accepted specialized models usable through Kodepoia’s existing local Ollama abstraction while preventing adapter/base mismatch and mutable-tag ambiguity.

## In scope

Modelfile generator/validator; `FROM`/`ADAPTER` identity binding; LICENSE/model metadata; deterministic runtime parameters/templates where needed; `ollama create`; show/details/digest capture; loopback-only smoke; structured output/tool-call capability probes; KodeBench comparison of Ollama-packaged candidate against pre-import accepted candidate/base.

## Out of scope

Public `ollama push`, remote Ollama service, silent replacement of installed model tags.

## Dependencies and prerequisites

R15.10–R15.12; R3 OllamaClient/loopback policy.

## Detailed implementation plan

Generate a Modelfile from structured repository-owned configuration and immutable artifact refs. Adapter path requires the exact base model identity used for training; mismatch is rejected before `ollama create`. Create under a namespaced candidate tag, never overwrite an active role tag. Query Ollama model details/digest after creation and run representative KodeBench tasks under fixed settings.

If direct Safetensors adapter import is unreliable/unsupported for an architecture or QLoRA artifact, prefer the validated merged/GGUF path established in R15.11–R15.12 rather than claiming compatibility.

## Deliverables

Ollama packaging/import module, Modelfile schema/template, candidate naming policy, tests/fakes, local smoke/evidence report.

## Acceptance gates / Definition of Done

Wrong base rejected; non-loopback authoritative endpoint rejected; model digest captured; create/show/run lifecycle; structured/tool capability preserved where claimed; no public push; full R0/Python/UI.

## Validation and evidence

Ollama version, Modelfile digest, base/artifact identity, created model digest/details, smoke/KodeBench deltas and CI/manual state.

## Rollback / recovery

Remove candidate tag via governed cleanup and restore previous active model pointer. Source artifacts remain immutable.

## Risks and regression traps

Mutable base tag drift; adapter/base mismatch; template changes benchmark behavior; candidate name collides with production/active model; Ollama import succeeds but behavior regresses.

## Manual intervention

**CONDITIONAL.** Hosted/core tests use fakes/fixtures. If authoritative real-model Ollama packaging is required, the user runs the exact loopback command set on the accepted head and returns JSON evidence; no registry upload or credentials are required.

## Completion record

To be appended when accepted.

---

# R15.14 — Specialized-model registry, promotion/rollback + ModelRouter compatibility

## Objective and rationale

Promote only fully accepted specialized candidates and make rollback deterministic without destabilizing R3 routing.

## In scope

Immutable model version record; base/dataset/train/eval/export/GGUF/Ollama lineage; capability/domain tags; role eligibility; active/candidate/rejected/retired states; promotion policy; router mapping update through SafeChange; health probe; rollback pointer; audit; compatibility with existing R3 roles.

## Out of scope

Automatic model training loop, deleting historical evidence, changing router architecture.

## Dependencies and prerequisites

R15.10–R15.13 and R3 ModelRouter/R8 lineage.

## Detailed implementation plan

Create registry records keyed by immutable candidate/version ID rather than mutable Ollama tag. Promotion requires accepted disposition and all required conversion/runtime evidence for the intended deployment form. Update role mapping atomically through SafeChange, run post-promotion smoke, and rollback on failure. `REJECTED` candidates cannot be activated.

Support `base`, `adapter`, `gguf`, `ollama` artifact variants under one lineage with capability differences explicit. A model can be accepted for one role/domain without becoming the universal default.

## Deliverables

Registry/promotion service, schema/storage, router adapter, rollback logic, tests, R15.14 acceptance report.

## Acceptance gates / Definition of Done

Rejected candidate activation blocked; atomic promotion; crash/restart state; rollback restores exact prior mapping; audit chain; mutable external tag cannot change immutable identity silently; full R0/Python/UI.

## Validation and evidence

Registry record digest, before/after router mapping, candidate/base IDs, promotion/rollback audit and CI IDs.

## Rollback / recovery

SafeChange snapshot and prior immutable active version are mandatory before activation; rollback is tested in acceptance.

## Risks and regression traps

Global default changed from a role-specific win; mutable tag drift; stale registry path; active model removed externally; promotion evidence references different benchmark/model digest.

## Manual intervention

**NONE.** Promotion in core acceptance uses repository/local candidate state, not external public registries.

## Completion record

To be appended when accepted.

---

# R15.15 — CLI + KodeStudio Experience/Bench/Tune UX, dry-run/status/evidence workflows

## Objective and rationale

Expose the R15 pipeline through safe structured workflows so users can understand eligibility, gaps, decisions and model status without editing internal files or invoking arbitrary training commands.

## In scope

CLI families for experience status/curation, dataset build/inspect, KodeBench run/compare, gap diagnosis, training doctor/plan/run/status/cancel, conversion/quantization doctor, Ollama package status, registry candidate/promote/rollback; KodeStudio pages/panels; dry-run; permission prompts; progress; redacted evidence export; accessibility/localization patterns.

## Out of scope

Raw shell console, secret editor, cloud training marketplace, public model upload.

## Dependencies and prerequisites

R15.1–R15.14 and existing KodeStudio/CLI patterns.

## Detailed implementation plan

Register `r15`/domain commands through structured argparse/service APIs and reuse backend-independent service objects. KodeStudio invokes typed commands/services, displays immutable IDs/digests and makes train/no-train/rejected states visible. Destructive cleanup, training start and promotion use explicit permission/dry-run flows. UI never displays raw secrets/quarantined private content by default.

## Deliverables

CLI registration/module, KodeStudio UI, view models, localization/accessibility labels, smoke fixtures/tests, docs.

## Acceptance gates / Definition of Done

CLI help/argument validation; dry-run non-mutation; cancel/promotion permission flows; UI smoke on Windows; redaction; status reflects exact registry/evidence state; full R0/Python/UI.

## Validation and evidence

CLI output schemas, UI smoke run, screenshots only if already supported/governed, command matrix and CI IDs.

## Rollback / recovery

UI/CLI removal leaves underlying R15 data/artifacts intact and accessible to repository services; router promotion state is not coupled to UI process lifetime.

## Risks and regression traps

UI starts training without explicit action; mutable tag shown instead of immutable candidate; long blocking work on UI thread; evidence panel leaks paths/content/secrets.

## Manual intervention

**NONE.**

## Completion record

To be appended when accepted.

---

# R15.16 — Hardware-local end-to-end qualification + reproducibility/resource acceptance

## Objective and rationale

Qualify the real local path that hosted CI cannot authoritatively prove: actual model runtime/training backend, memory/resource behavior, optional QLoRA candidate execution and Ollama packaging on the target workstation when the phase needs a real-model promotion claim.

## In scope

Hardware/software doctor; exact accepted-head assertion; disk/RAM/VRAM/backend snapshot; bounded real-model preflight; optional short/representative QLoRA run when R15.7 says training is useful and capability exists; resume/cancel; base/adapter benchmark; GGUF conversion/quant where selected; Ollama import; final local report with hashes, timings/resources and no secret values.

## Out of scope

Driver installation, BIOS changes, destructive system tuning, paid cloud account, public model publishing, unbounded overnight training without explicit approved plan/budget.

## Dependencies and prerequisites

R15.1–R15.15; all prior normalized; exact local model/data availability and permissions if the conditional gate triggers.

## Detailed implementation plan

Provide one repository-owned acceptance runner that first performs a non-mutating doctor. It records only necessary hardware/backend facts. If real QLoRA is supported and required, execute an explicitly bounded plan from R15.7/R15.9; otherwise record truthful `TRAINING_BACKEND_UNAVAILABLE` or `NO_TRAIN_REQUIRED` and test the remaining relevant local path. The report binds every stage to exact dataset/model/benchmark/tool digests.

A system where Ollama inference works but the selected QLoRA backend is unsupported must not be mislabeled as training-capable. Alternate supported backend/OS may be documented but never silently installed.

## Deliverables

Local doctor/acceptance runner, PowerShell-compatible invocation where appropriate, report schema, recovery instructions, fixture validation and R15.16 acceptance document.

## Acceptance gates / Definition of Done

Exact-head assertion; doctor; bounded resource controls; truthful backend state; deterministic repeated benchmark configuration; no critical regression for any promoted real candidate; report schema/hash; full standard CI still green on the exact evidence head.

## Validation and evidence

Exact source SHA; host OS/Python/Ollama/training-tool versions; non-sensitive CPU/GPU/RAM/VRAM summary; model/dataset/benchmark digests; durations/resource maxima; local result; command exit code; report SHA-256.

## Rollback / recovery

Cancel/kill runner, remove only derived candidate/cache artifacts through governed cleanup, restore prior Ollama/router model mapping, preserve base models and evidence. Never advise deleting unrelated user model stores.

## Risks and regression traps

Hardware support changing between ROCm/PyTorch/bitsandbytes versions; Windows-vs-Linux capability mismatch; insufficient VRAM/disk; thermals/long run; report path leaks; assuming local success transfers to other hardware.

## Manual intervention

**CONDITIONAL.** It triggers only if a real target-workstation training/conversion/promotion capability claim is required. When triggered, execution MUST stop before R15.17 and provide: exact accepted SHA; prerequisites; copy-paste commands; expected JSON/exit codes; recovery; precise evidence files; actions not to perform; and privacy guidance. Passwords, tokens, private keys and unrelated machine data must never be requested.

## Completion record

To be appended when accepted.

---

# R15.17 — Adversarial integrated Experience/Bench/Fine-tuning acceptance

## Objective and rationale

Close R15 with a non-circular end-to-end acceptance proving that experience governance, dataset lineage, KodeBench, training decisions, optional QLoRA, conversion, Ollama packaging and promotion/rollback compose safely.

## In scope

Repository-owned integrated scenario and negative/adversarial matrix; exact-source CI authority; canonical R15 integrated acceptance report/digest; cross-platform deterministic core checks; optional real local evidence linkage without turning missing optional hardware/provider evidence into synthetic PASS.

## Out of scope

R16 red-team/beta work, public model publication, provider/cloud claims not demonstrated by R15.

## Dependencies and prerequisites

R15.1–R15.16 all COMPLETE + NORMALIZED or a documented conditional real-training state that is valid under the frozen `QLoRA if useful` policy; all authoritative prior evidence available.

## Detailed implementation plan

Build an integrated scenario from synthetic/repository-owned eligible experiences through sanitization, dedup, protected-holdout isolation, dataset build, KodeBench before, gap decision, tiny QLoRA fixture when `TRAIN`, after-evaluation, export, simulated/available GGUF/Ollama stages, registry promotion and rollback. The scenario must include failure-closed cases and must recompute its own semantic digest from source data rather than trusting an earlier PASS field.

At minimum prove these adversarial invariants:

1. unvalidated/unopted experience cannot enter training;
2. secret/private fixture is redacted/quarantined and never emitted in reports;
3. unknown/disallowed license blocks inclusion;
4. revoked source invalidates dependent dataset/candidate promotion;
5. exact and near duplicate groups cannot cross splits;
6. benchmark holdout/near-duplicate cannot enter training;
7. mixed dataset/benchmark/model SHA evidence is rejected;
8. low score caused by missing tool/context can yield `FIX_SYSTEM_FIRST`, not automatic training;
9. QLoRA run is bound to exact base/tokenizer/dataset/config and mismatched resume is rejected;
10. aggregate candidate improvement with one critical-domain regression is rejected;
11. wrong-base adapter export/Ollama import is rejected;
12. quantized candidate with excessive/critical quality loss is rejected;
13. rejected candidate cannot be promoted and rollback restores exact previous router mapping;
14. missing optional GPU/llama.cpp/Ollama capability is truthful `UNAVAILABLE`/conditional, never fabricated PASS.

Generate `docs/roadmap/R15_INTEGRATED_ACCEPTANCE.json` or equivalent canonical authority only from exact-source scenario output and validate semantic digest, `status`, `blockers`, source SHA, suite/data/model identities and expected check inventory.

## Deliverables

Integrated scenario runner/tests, dedicated CI workflow if needed, canonical integrated report/schema, adversarial fixtures, R15.17 ACCEPTANCE documentation and final phase END synchronization.

## Acceptance gates / Definition of Done

Focused integrated/adversarial tests; Ubuntu+Windows core scenario where applicable; R0; full Python Core; KodeStudio UI Smoke; any dedicated R15 Integrated workflow; exact immutable technical source; canonical report digest; final END-sync of plan + continuity + acceptance; fresh exact-END re-gates after documentation/evidence byte changes; PR required checks; merge with exact expected-head; exactly one post-merge R15 phase continuity-only normalization with fresh R0/Python/UI before R16 planning is authorized.

No circular acceptance: checked-in report status cannot be the sole reason the scenario passes. No evidence from rejected/mixed candidates may be reused.

## Validation and evidence

Immutable technical source SHA; exact END-head; all CI run IDs/job conclusions; test counts; canonical integrated digest; scenario/check inventory; dataset/benchmark/model fixture digests; artifact IDs/hashes where produced; manual/conditional state; PR and merge SHA.

## Rollback / recovery

Reject failing candidate/source head, preserve prior normalized `main`, remove temporary integrated artifacts, and rerun from a new immutable source. Never patch a failed report into PASS without rerunning its producing scenario on the exact new source.

## Risks and regression traps

Circular evidence; contamination hidden by synthetic scores; optional external tooling mistaken for mandatory; critical regression masked by aggregate gain; source-vs-END drift; helper files surviving final tree; plan rewritten during post-merge normalization.

## Manual intervention

**CONDITIONAL.** Normally core integrated acceptance is repository/CI-owned. If R15.16 has a triggered real-hardware gate or the final claim explicitly depends on a real local large-model training/conversion result, R15.17 must stop until the exact user-side evidence is reviewed. No secret or public-model upload is required for core closure.

## Completion record

To be appended when accepted.

---

## Phase completion rule

R15 can be marked `COMPLETE` only when every subdivision R15.1–R15.17 is `COMPLETE` with required exact-head evidence and its one post-merge continuity normalization, or is explicitly removed from scope by a recorded accepted architecture/roadmap decision.

Because the frozen roadmap says **“QLoRA si utile”**, a truthful evidence-backed `NO_TRAIN` result does not remove R15.8–R15.14 from implementation scope: those subdivisions still implement and fixture-test the governed capability. It only means no real project/base-model candidate is promoted as a fine-tuned production model without evidence that training is useful.

After R15.17 implementation/evidence merge, exactly one continuity-only **R15 phase normalization** must pass fresh exact-head R0 + full Python Core + KodeStudio UI Smoke and merge with expected-head protection. Only that normalized `main` may mark R15 `COMPLETE + NORMALIZED` and authorize R16 planning.

## Ongoing maintenance rule

Update `R15_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md` in the same work cycle whenever subdivision scope/status, manual prerequisites, acceptance requirements, important recovered defects or phase ordering changes.

External library/tool versions and hardware compatibility matrices remain dated evidence, not frozen architecture. Capability probes and immutable evidence control what Kodepoia may claim on a particular head/environment.
