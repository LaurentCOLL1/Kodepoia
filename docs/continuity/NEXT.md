# Kodepoia next actions

Last synchronized: 2026-09-16 after V2.0 PR `#474` merged and continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0 implementation PR `#474` was qualified with **27/27** `completed/success` PR workflows on exact head `79749ab25d58faaca6421bcda4eb460194a3683c` and merged with an exact-head guard as `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

V2.0.3 emitted exact-head capability-truth acceptance evidence on Ubuntu and Windows. The capability truth, KodeStudio diagnostics and reusable acceptance contract are therefore accepted, and this continuity change completes the required post-merge normalization.

**V2.0 is COMPLETE + NORMALIZED. V2.1.1 is now authorized.**

## Immediate execution order

### V2.1.1 — Honest Research UX and diagnostics

Create a dedicated branch from re-fetched live `main` and implement only V2.1.1 from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Required product truth:

- keep **Search saved research** as the local query over already persisted project research reports;
- expose **Search sources** as a distinct external/local discovery operation, without pretending discovery exists where no provider is implemented;
- make the default empty state explain whether there are no saved reports, no discovery provider, network access is disabled/restricted, authentication is missing, or an available provider genuinely returned no matches;
- keep fetch-by-explicit-URL available as the existing guarded acquisition path;
- surface provider/network/authentication states using the accepted V2.0 capability truth contract;
- errors and unavailable states must be actionable, localized and test-covered;
- raw JSON may remain available for diagnostics/export but must not be the principal user experience.

V2.1.1 acceptance must prove saved-report query separately from external discovery semantics and must preserve all ResearchGuard/protected-action invariants. Re-fetch every required PR-triggered workflow on the exact final V2.1.1 head and merge only if every required gate is `completed/success`.

After V2.1.1 merge, normalize continuity before starting V2.1.2.

## Later V2.1 order

Only after V2.1.1 is COMPLETE + NORMALIZED, continue:

1. V2.1.2 — Discovery providers;
2. V2.1.3 — Evidence workspace;
3. V2.1.4 — Cited synthesis and Research Packs;
4. V2.1.5 — Extended media/community sources;
5. V2.1.6 — ResearchGuard hardening.

Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live. V2.0 est COMPLETE + NORMALIZED après PR #474 qualifiée 27/27 sur le head exact 79749ab25d58faaca6421bcda4eb460194a3683c et merge 043dba64111f763f0e9544ea8cde9a3cbf9b1dff. Commence ou continue V2.1.1 — Honest Research UX and diagnostics — sur branche dédiée, avec acceptance exact-head et normalisation avant V2.1.2. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
