# Kodepoia next actions

Last synchronized: 2026-09-15 after Roadmap V2 preparation PR `#472` merged  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

Roadmap preparation PR `#472` was qualified with **25/25** `completed/success` PR workflows on exact head `eac1a9bc1c8ad0e99de13e46c5048354ec932311` and merged as `87fc09e16531260d64cf3d5fb59f511295e2b703`.

This closes roadmap preparation only. **V2.0 is not COMPLETE. V2.1.1 is blocked until V2.0 is COMPLETE + NORMALIZED.**

## Immediate execution order

### V2.0.1 — Capability matrix/runtime truth

Create the dedicated V2.0 implementation branch from re-fetched live `main` and establish one machine-readable/runtime truth model that distinguishes:

- public rc8 (`public-validated`);
- live `main`/source (`source-available`);
- explicitly `acceptance-proven` capabilities;
- `experimental` capabilities;
- `unavailable` capabilities.

Represent provider/runtime state explicitly as `ready`, `unavailable`, `auth-required`, `network-restricted` or `not-implemented`. Represent accelerator state explicitly as `priority`, `available`, `experimental`, `deferred` or `unsupported`.

The public/source distinction is mandatory: presence on `main` must never imply presence in `v1.1.0-rc8`.

### V2.0.2 — KodeStudio diagnostics

Make the capability truth visible and actionable in KodeStudio. At minimum, distinguish:

- a provider/query that really ran successfully but returned zero matches;
- provider unavailable/not configured;
- authentication required;
- network access restricted/disabled;
- not implemented;
- other actionable transport/policy failure where applicable.

No unavailable path may appear as a successful empty search.

The current baseline must remain honest: `ResearchService.query()` searches persisted project research reports; it does not perform Internet discovery. External Web acquisition remains a separate guarded explicit-locator operation until V2.1 adds real discovery providers.

### V2.0.3 — Reusable exact-head V2 acceptance

Add deterministic tests and a reusable acceptance template/runner that:

- binds evidence to an expected exact head SHA and fails on mismatch;
- proves capability/provider/accelerator state vocabulary and invariants;
- proves the real zero-result success case separately from unavailable/auth/network/not-implemented cases;
- proves KodeStudio and current documentation expose the same capability truth;
- emits inspectable acceptance evidence suitable for future V2 subdivisions.

Then re-fetch **all required PR-triggered workflows on the exact final V2.0 head**. Merge only if every required workflow is `completed/success`. After merge, normalize `STATE.md`, `NEXT.md` and any other current authority affected by V2.0. Only then mark V2.0 **COMPLETE + NORMALIZED**.

## Only after V2.0 COMPLETE + NORMALIZED

Begin **V2.1.1 — Honest Research UX and diagnostics**, then continue V2.1 subdivision by subdivision according to `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`. Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live. La distribution publique de référence reste v1.1.0-rc8 et l'incident updater est clos. Ne rouvre pas R20 et n'invente pas R20.7. Si V2.0 n'est pas COMPLETE + NORMALIZED, poursuis d'abord V2.0.1 capability truth, V2.0.2 KodeStudio diagnostics puis V2.0.3 exact-head acceptance, avec qualification complète et normalisation. Ne commence V2.1.1 qu'ensuite. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
