# Kodepoia next actions

Last synchronized: 2026-09-17 after V2.1.2 implementation PR `#478` merged; post-merge normalization is being qualified on this branch  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0 and V2.1.1 remain **COMPLETE + NORMALIZED**.

## V2.1.2 accepted implementation

V2.1.2 implementation PR `#478` was qualified with **27/27** `completed/success` PR workflows on exact head:

`e1e209ebcf78265f04b30b0019d201d58dae76ef`

It merged with an exact-head guard as:

`347068de7f9be9275754bbda7c55f4e0d5e66bac`

Exact-head acceptance evidence:

- `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

The accepted V2.1.2 boundary is real discovery only: Brave Search for general Web discovery, GitHub REST repository Search for public GitHub discovery, explicit provider/auth/network/rate-limit diagnostics, bounded candidate descriptors, and strict separation from guarded fetch/persistence/evidence.

This documentation branch is the required post-merge normalization. **Do not begin V2.1.3 until the normalization PR itself has passed all required workflows on its exact head and has merged.**

## Immediate execution order

### V2.1.3 — Evidence workspace — authorized only after normalization merge

Once V2.1.2 is formally **COMPLETE + NORMALIZED**, create a dedicated branch from re-fetched live `main` and implement only V2.1.3 from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Required product/architecture truth:

- present discovered/fetched sources as inspectable source cards or equivalent structured rows rather than relying on raw JSON;
- display canonical locator plus available publication/update/version metadata, source trust and freshness;
- expose explicit include/exclude state for evidence selection without silently promoting discovery candidates;
- preserve the distinction between descriptor-only candidates and fetched evidence;
- add cache/refetch lineage so refreshing a source creates an inspectable newer evidence state rather than silently replacing historical evidence;
- normalize duplicate source identities while retaining provider provenance;
- do not implement cited synthesis or Research Pack persistence yet; those remain V2.1.4;
- add deterministic backend/UI tests and exact-head acceptance proving these invariants on Ubuntu and Windows.

After V2.1.3 merge, normalize continuity before starting V2.1.4.

## Later V2.1 order

Only after each previous subdivision is COMPLETE + NORMALIZED, continue:

1. V2.1.4 — Cited synthesis and Research Packs;
2. V2.1.5 — Extended media/community sources;
3. V2.1.6 — ResearchGuard hardening.

Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live et toute PR de normalisation ouverte. V2.1.2 a été qualifiée 27/27 sur le head exact e1e209ebcf78265f04b30b0019d201d58dae76ef puis fusionnée comme 347068de7f9be9275754bbda7c55f4e0d5e66bac. Ne commence V2.1.3 qu'après la fusion de la normalisation post-V2.1.2. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
