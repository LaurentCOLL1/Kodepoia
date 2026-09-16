# Kodepoia next actions

Last synchronized: 2026-09-16 after V2.1.1 PR `#476` merged and continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0 remains **COMPLETE + NORMALIZED**.

V2.1.1 implementation PR `#476` was qualified with **27/27** `completed/success` PR workflows on exact head `c485083419f492e9c10989f6aadbda5bc436d5cc` and merged with an exact-head guard as `16ef244e9cad922421f2440ef8185e9e896a164d`.

V2.1.1 exact-head acceptance evidence was emitted on Ubuntu and Windows:

- `v2-1-1-honest-research-ux-ubuntu-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `29bdb2bb193a3a2c7a397e3d2c1307f0d323d07ff5425081803ca28e133d4d26`;
- `v2-1-1-honest-research-ux-windows-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `215a5b7e1a931a04ecb957bb561c01695c8f6b992f3889aaa72026e8f8969aa6`.

This continuity change completes the required post-merge normalization.

**V2.1.1 is COMPLETE + NORMALIZED. V2.1.2 is now authorized.**

## Immediate execution order

### V2.1.2 — Discovery providers

Create a dedicated branch from re-fetched live `main` and implement only V2.1.2 from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Required product/architecture truth:

- define a deterministic discovery-provider contract whose output is bounded candidate descriptors, not trusted fetched content;
- provide at least an official/general Web discovery path plus a GitHub discovery path;
- make result bounds, cancellation and deduplication explicit and deterministic;
- perform no hidden retries and no protected mutation merely because a candidate was discovered;
- keep candidate discovery separate from acquisition;
- every selected/discovered locator must still pass the existing guarded fetch path and ResearchGuard/protected-action policies before content is accepted;
- provider/network/authentication/rate-limit failures must remain explicit states, not empty-success results;
- add deterministic fixtures/tests and exact-head acceptance proving the provider contract, bounded results, cancellation, dedupe and guarded-fetch separation.

After V2.1.2 merge, normalize continuity before starting V2.1.3.

## Later V2.1 order

Only after V2.1.2 is COMPLETE + NORMALIZED, continue:

1. V2.1.3 — Evidence workspace;
2. V2.1.4 — Cited synthesis and Research Packs;
3. V2.1.5 — Extended media/community sources;
4. V2.1.6 — ResearchGuard hardening.

Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live. V2.0 est COMPLETE + NORMALIZED. V2.1.1 est COMPLETE + NORMALIZED après PR #476 qualifiée 27/27 sur le head exact c485083419f492e9c10989f6aadbda5bc436d5cc et merge 16ef244e9cad922421f2440ef8185e9e896a164d. Commence ou continue V2.1.2 — Discovery providers — sur branche dédiée, avec acceptance exact-head et normalisation avant V2.1.3. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
