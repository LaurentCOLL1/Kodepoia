# Kodepoia — Roadmap V2

Status: **ACTIVE — V2.1.2 COMPLETE + NORMALIZED; V2.1.3 authorized**  
Created: 2026-09-15  
Public Windows distribution baseline: `v1.1.0-rc8`

## Authority checkpoints

- V2 roadmap preparation: PR `#472`, merge `87fc09e16531260d64cf3d5fb59f511295e2b703`, 25/25 exact-head PR workflows successful.
- V2.0: PR `#474`, accepted head `79749ab25d58faaca6421bcda4eb460194a3683c`, merge `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`, 27/27 successful.
- V2.1.1: PR `#476`, accepted head `c485083419f492e9c10989f6aadbda5bc436d5cc`, merge `16ef244e9cad922421f2440ef8185e9e896a164d`, 27/27 successful.
- V2.1.2: PR `#478`, accepted head `e1e209ebcf78265f04b30b0019d201d58dae76ef`, merge `347068de7f9be9275754bbda7c55f4e0d5e66bac`, 27/27 successful.

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

### V2.1.3 — Evidence workspace — NEXT

Implement only:

- source cards / structured inspectable source rows;
- canonical locator, source dates/version, trust and freshness metadata;
- explicit include/exclude state for fetched evidence;
- candidate-vs-fetched distinction preserved;
- cache/refetch lineage without silent historical replacement;
- duplicate source identities normalized without losing provider provenance;
- deterministic backend/UI tests and exact-head Ubuntu/Windows acceptance.

Do **not** pull V2.1.4 cited synthesis or Research Pack persistence into V2.1.3.

### Later V2.1 order

1. V2.1.4 — Cited synthesis and Research Packs.
2. V2.1.5 — Extended media/community sources.
3. V2.1.6 — ResearchGuard hardening.

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
