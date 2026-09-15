# Kodepoia continuity state

Last synchronized: 2026-09-15 after merge of Roadmap V2 preparation PR `#472`  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; for V2.1 specifically, read `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## Roadmap V2 preparation — COMPLETE, implementation gate still pending

Roadmap preparation PR `#472` was qualified on exact head:

`eac1a9bc1c8ad0e99de13e46c5048354ec932311`

All **25/25** PR-triggered workflows for that exact SHA completed with conclusion `success`, including `R17 Windows Installer`. PR `#472` was then merged with an exact-head guard as merge commit:

`87fc09e16531260d64cf3d5fb59f511295e2b703`

That merge prepares and authorizes Roadmap V2. It **does not complete V2.0** and it does not authorize V2.1.1 to start early.

Current execution state:

- Roadmap V2 preparation / PR `#472`: **COMPLETE**;
- post-`#472` authority normalization: performed by the dedicated normalization change that contains this state;
- **V2.0 — Baseline, capability truth and usability audit: NOT STARTED**;
- **V2.1 — Research Workspace: NOT STARTED and BLOCKED on V2.0 COMPLETE + NORMALIZED**.

## Mandatory V2.0 execution order

V2.0 must be completed on a dedicated implementation branch before any V2.1.1 implementation:

1. **V2.0.1 — capability matrix/runtime truth**: distinguish precisely public rc8, live `main`/source, acceptance-proven, experimental and unavailable capability truth; include provider, network, authentication and accelerator states.
2. **V2.0.2 — KodeStudio diagnostics**: expose those states visibly and actionably. An unavailable, unauthenticated, network-restricted or not-implemented provider must never look like a successful empty search.
3. **V2.0.3 — reusable V2 acceptance contract**: exact-head-bound tests/acceptance proving that KodeStudio and current documentation expose the same capability truth.
4. Re-fetch every required workflow on the exact final V2.0 head; merge only when all required checks are `completed/success`.
5. Normalize continuity after V2.0 merge. Only after V2.0 is **COMPLETE + NORMALIZED** may V2.1.1 begin.

## Capability truth vocabulary authorized for V2.0

Capability provenance/classification must distinguish at least:

- `public-validated` — present in the qualified public rc8 baseline;
- `source-available` — present on live `main`/source but not thereby public;
- `acceptance-proven` — explicitly demonstrated by bound acceptance evidence;
- `experimental` — implemented or investigatory but not accepted as a normal supported path;
- `unavailable` — not currently usable in the relevant runtime/context.

Provider/runtime states must distinguish at least:

- `ready`;
- `unavailable`;
- `auth-required`;
- `network-restricted`;
- `not-implemented`.

Accelerator states must distinguish at least:

- `priority`;
- `available`;
- `experimental`;
- `deferred`;
- `unsupported`.

A successful query with zero matches is a real success state only when the relevant provider/query actually ran successfully. It must never be used to mask provider absence, missing authentication, denied network access or an unimplemented path.

## Research truth at the V2.0 baseline

The current KodeStudio Research `Search` action queries already persisted project research reports through `ResearchService.query()`. It is not external Internet discovery. Web acquisition is a separate guarded fetch operation for an explicit locator/URL and remains subject to network permission and ResearchGuard.

This baseline truth must be exposed accurately during V2.0. V2.1 later evolves it into a full `question -> discovery -> guarded fetch -> evidence -> cited synthesis -> Research Pack` workflow.

## Accelerator authority

Kaggle **T4×2** remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. The GPUs remain two separate 16 GiB devices; no component may present them as a single 32 GiB pool.

TPU v5e-8 remains **deferred**. Do not create or claim a distinct XLA/JAX or PyTorch/XLA backend unless a concrete benchmark demonstrates a material advantage that justifies its own implementation and acceptance surface.

## Release/updater boundary

Roadmap V2 does not reserve a new public release version and authorizes no release/TUF mutation. The rc8 source/tag/installer/TUF and real-machine E2E authority remain documented in `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` and the release evidence. Post-rc8 source capabilities on `main` are development capabilities until separately qualified for a future public release.

All accepted fail-closed invariants remain in force: exact source/artifact binding, TUF signature/threshold/rollback/version/expiry checks, exact target length/SHA-256, target-scoped Authenticode policy, installer identity verification, explicit user consent and no private signing material in Git/CI/public artifacts/chat.

## Resume rule

For future work:

1. re-fetch live `main` and read `STATE.md` + `NEXT.md`;
2. if V2.0 is not yet COMPLETE + NORMALIZED, continue the next unfinished V2.0 subdivision and do **not** start V2.1.1;
3. for every subdivision, branch from an exact live SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity;
4. if a genuine manual intervention is required, stop at that subdivision and describe exactly what the operator must do; never bypass a failed or missing gate;
5. never reopen R20 or invent R20.7.
