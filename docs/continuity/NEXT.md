# Kodepoia next actions

Last synchronized: 2026-09-17 after V2.1.3 implementation PR `#480` merged and continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0, V2.1.1, V2.1.2 and V2.1.3 are **COMPLETE + NORMALIZED**.

## V2.1.3 accepted implementation

V2.1.3 implementation PR `#480` was qualified with **27/27** `completed/success` PR workflows on exact head:

`c4cff95ea2309ea5482e6c24c61002b13becb48f`

It merged with an exact-head guard as:

`0c3d365626df666f2a847b9320b0730dc0110afa`

Exact-head acceptance evidence:

- `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The exact-head V2.1.3 acceptance reported **13/13 PASS**. Accepted scope is evidence inspection and selection only:

- canonical source identity and canonical locator;
- explicit candidate-only versus fetched lifecycle;
- fetched-evidence include/exclude state without deleting artifacts;
- immutable retrieval revisions and inspectable refetch lineage, including unchanged-content refetches;
- duplicate normalization while retaining provider provenance;
- visible source dates/version/trust/freshness and version conflicts;
- dedicated structured Evidence workspace in KodeStudio while preserving the seven-column historical Research result contract;
- no cited synthesis, Research Pack persistence, Context Builder/RAG injection or provider expansion pulled forward.

## Immediate execution order

### V2.1.4 — Cited synthesis and Research Packs — NEXT AUTHORIZED

Branch only from re-fetched live `main` containing this V2.1.3 normalization, then implement only V2.1.4 from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Required product/architecture truth:

- synthesis consumes only explicitly selected **fetched evidence**; descriptor-only discovery candidates cannot be cited as if fetched;
- every source-backed claim must have inspectable claim-to-evidence citation linkage using stable artifact/source identity;
- citations must remain bound to the evidence revision actually used, so later refetches cannot silently rewrite an earlier answer's provenance;
- uncertainty and conflicting/stale evidence must remain visible instead of being collapsed into false certainty;
- generated synthesis must remain source-data-driven and must not grant permissions or execute source instructions;
- save a governed Research Pack containing the scoped question, selected evidence/revisions, citations, synthesis, uncertainty/provenance metadata and a stable digest;
- Research Pack persistence must be project-scoped under `.kodepoia/`, deterministic enough for acceptance, and must preserve ResearchGuard/secret-redaction/protected-action boundaries;
- expose a clear KodeStudio synthesis/save workflow without making raw JSON the primary UX;
- add deterministic backend/UI tests plus exact-head Ubuntu/Windows acceptance evidence.

Do **not** pull forward:

- V2.1.5 forum/YouTube/media provider expansion;
- V2.1.6 adversarial ResearchGuard hardening corpus beyond what is required to preserve existing boundaries;
- any new public release, installer publication or TUF transition.

After V2.1.4 merges, normalize continuity before V2.1.5 begins.

## Later V2.1 order

Only after each previous subdivision is COMPLETE + NORMALIZED, continue:

1. V2.1.5 — Extended media/community sources;
2. V2.1.6 — ResearchGuard hardening.

Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live et toute PR de normalisation ouverte. V2.1.3 a été qualifiée 27/27 sur le head exact c4cff95ea2309ea5482e6c24c61002b13becb48f puis fusionnée comme 0c3d365626df666f2a847b9320b0730dc0110afa. V2.1.4 — Cited synthesis and Research Packs — est la prochaine subdivision autorisée seulement depuis un main contenant la normalisation V2.1.3. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
