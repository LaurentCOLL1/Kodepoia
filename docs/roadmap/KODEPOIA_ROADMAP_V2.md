# Kodepoia — Roadmap V2

Status: **ACTIVE — V2.1.3 COMPLETE + NORMALIZED; V2.1.4 authorized**  
Created: 2026-09-15  
Public Windows distribution baseline: `v1.1.0-rc8`

## Authority checkpoints

- V2 roadmap preparation: PR `#472`, merge `87fc09e16531260d64cf3d5fb59f511295e2b703`, 25/25 exact-head PR workflows successful.
- V2.0: PR `#474`, accepted head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`, 27/27 successful.
- V2.1.1: PR `#476`, accepted head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful.
- V2.1.2: PR `#478`, accepted head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful; normalization PR `#479`, head `02f00beb070492c398858dcfa70ce0118872b55d`, merge `39ceec560ff069d98530687f77e7ad1c41670d3a`.
- V2.1.3: PR `#480`, accepted head `c4cff95ea2309ea5482e6c24c61002b13becb48f`, merge `0c3d365626df666f2a847b9320b0730dc0110afa`, 27/27 successful.

V2 does not reopen R20, does not create `R20.7`, and does not turn post-rc8 source capabilities into public rc8 capabilities.

## V2.1 — Research Workspace

Target flow:

`question -> provider discovery -> source cards -> guarded fetch -> inspect/include/exclude -> cited synthesis -> governed Research Pack -> project context/RAG`

### V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

Saved research, external discovery and explicit-locator fetch are distinct operations. Provider/network/auth failures are explicit rather than empty-success states.

### V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

Accepted scope:

- Brave Search general-Web discovery through its official HTTPS API when NETWORK is explicitly allowed and credentials are referenced through KodeSecrets;
- public GitHub repository discovery through the official REST Search API with optional authentication;
- bounded descriptor-only candidates marked `candidate-only` / `unfetched`;
- discovery never automatically fetches, persists or promotes candidates to evidence;
- provider/auth/network/rate-limit failures remain explicit;
- KodeStudio `Search sources` performs real discovery only under NETWORK permission;
- discovery remains separate from guarded `ResearchService.fetch()`.

Exact-head evidence:

- Ubuntu `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- Windows `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

### V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

Accepted scope:

- structured source/evidence rows rather than raw-JSON-only inspection;
- stable canonical source identity and visible canonical locator;
- visible publication/update/version, trust, freshness and suspicious indicators;
- explicit candidate-only versus fetched lifecycle;
- include/exclude state only for fetched artifact IDs;
- immutable lightweight retrieval revisions and inspectable refetch lineage, including unchanged-content refetches;
- duplicate source identities normalized while provider provenance is retained;
- stale/conflicting versions remain inspectable;
- dedicated KodeStudio Evidence workspace preserving the historical seven-column Research results contract.

Exact-head acceptance on `c4cff95ea2309ea5482e6c24c61002b13becb48f` reported **13/13 PASS**.

Exact-head evidence:

- Ubuntu `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

### V2.1.4 — Cited synthesis and Research Packs — NEXT

Implement only:

- synthesis from explicitly selected fetched evidence;
- claim-linked, inspectable citations bound to the evidence revision actually used;
- visible uncertainty and unresolved stale/conflicting evidence;
- governed Research Pack persistence with scoped question, selected evidence/revisions, citations, synthesis and provenance metadata;
- stable Research Pack digest and project-scoped persistence under `.kodepoia/`;
- clear KodeStudio synthesis/save workflow;
- deterministic backend/UI tests and exact-head Ubuntu/Windows acceptance.

Preserve ResearchGuard, secret redaction and protected-action boundaries. Discovery candidates must never be cited as fetched evidence merely because they were discovered.

Do **not** pull V2.1.5 forum/YouTube/media provider expansion or V2.1.6 adversarial hardening forward.

### Later V2.1 order

1. V2.1.5 — Extended media/community sources.
2. V2.1.6 — ResearchGuard hardening.

Each subdivision requires its own branch, exact-head acceptance, all required workflows successful, protected merge, and post-merge continuity normalization before the next subdivision.

## Remaining V2 sequence

- V2.2 — Project Knowledge, Context Builder and Memory integration.
- V2.3 — Model Lab governed improvement UX.
- V2.4 — Kaggle T4×2 production qualification and explicit multi-GPU.
- V2.5 — Cross-workspace orchestration.
- V2.6 — V2 hardening and next public Windows release.

## Accelerator authority

Kaggle `GPU T4 x2` remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. Treat the two T4 devices as two separate 16 GiB GPUs, never a fictitious single 32 GiB pool.

TPU v5e-8 remains deferred. A distinct XLA/JAX or PyTorch/XLA backend is authorized only if a concrete benchmark demonstrates a material Kodepoia advantage that justifies its own implementation and acceptance surface.

## Acceptance discipline

For every subdivision:

1. re-fetch live `main` and continuity authority;
2. branch from an exact SHA;
3. implement only the authorized scope;
4. add deterministic tests and exact-head acceptance evidence;
5. re-fetch every required workflow for the exact head;
6. merge only after every required workflow succeeds on that same head;
7. normalize continuity after merge before the next subdivision;
8. stop only for a genuine manual intervention that cannot be performed through connected tooling.

No V2 step by itself authorizes release/TUF/updater mutation. The public reference remains `v1.1.0-rc8` until a future release is separately scoped and qualified.
