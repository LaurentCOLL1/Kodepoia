# Kodepoia continuity state

Last synchronized: 2026-09-17 after V2.1.3 implementation PR `#480` merged and post-merge continuity normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; for V2.1 specifically, read `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## V2.0 — COMPLETE + NORMALIZED

Roadmap preparation PR `#472` remains the accepted V2 planning authority. V2.0 implementation was completed by PR `#474` on exact head `79749ab25d58faaca6421bcda4eb460194a3683c`; all **27/27** PR-triggered workflows succeeded and PR `#474` merged as `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

## V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 implementation PR `#476` was qualified with **27/27** PR-triggered workflows on exact head `c485083419f492e9c10989f6aadbda5bc436d5cc` and merged as `16ef244e9cad922421f2440ef8185e9e896a164d`.

Exact-head evidence:

- `v2-1-1-honest-research-ux-ubuntu-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `29bdb2bb193a3a2c7a397e3d2c1307f0d323d07ff5425081803ca28e133d4d26`;
- `v2-1-1-honest-research-ux-windows-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `215a5b7e1a931a04ecb957bb561c01695c8f6b992f3889aaa72026e8f8969aa6`.

## V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 implementation PR `#478` was qualified with **27/27** PR-triggered workflows on exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef` and merged as `347068de7f9be9275754bbda7c55f4e0d5e66bac`.

Its post-merge normalization PR `#479` was qualified on exact head `02f00beb070492c398858dcfa70ce0118872b55d` and merged as `39ceec560ff069d98530687f77e7ad1c41670d3a`.

Exact-head V2.1.2 evidence:

- `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

Accepted V2.1.2 product truth remains:

- general Web discovery uses the official Brave Search HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- GitHub public repository discovery uses the official GitHub REST Search API with optional authentication;
- discovery returns bounded descriptor-only candidates marked `candidate-only` / `unfetched` and never automatically fetches, persists or promotes them to evidence;
- provider failure, missing authentication, rate limiting and network restriction remain explicit and cannot masquerade as successful empty discovery;
- every later acquisition remains subject to guarded fetch and ResearchGuard/protected-action boundaries.

## V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

Implementation PR `#480` was qualified on exact head:

`c4cff95ea2309ea5482e6c24c61002b13becb48f`

All **27/27** PR-triggered workflows associated with that exact head completed with conclusion `success`, including `Python Core`, `KodeStudio UI Smoke`, `R0 Repository Guard`, `R17 Windows Installer`, `R18.11 Integrated Adversarial Release Update Acceptance`, Android, Apple and the remaining Windows gates. No failed or historical run was used in place of the exact-head qualification.

PR `#480` merged with `expected_head_sha=c4cff95ea2309ea5482e6c24c61002b13becb48f` as merge commit:

`0c3d365626df666f2a847b9320b0730dc0110afa`

V2.1.3 exact-head evidence emitted by `Python Core`:

- `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The acceptance reported **13/13 PASS** on the exact head. Accepted product truth after V2.1.3:

- discovered candidates and fetched evidence are structurally and visibly distinct;
- equivalent source locators normalize to a stable canonical source identity while provider provenance is retained;
- include/exclude state applies only to fetched artifact IDs and never promotes a descriptor-only candidate;
- fetched artifacts remain persisted when excluded;
- repeated retrievals create inspectable immutable lightweight revisions, including unchanged-content refetches;
- lineage exposes older/newer artifacts for the same canonical source instead of silently replacing history;
- conflicting source versions remain visible;
- KodeStudio exposes a dedicated structured Evidence workspace while preserving the historical seven-column Research results contract and bounded technical JSON detail;
- V2.1.4 cited synthesis, Research Pack persistence and Context Builder/RAG injection were not pulled forward.

## V2.1 authorization

With V2.1.3 COMPLETE + NORMALIZED, the only next authorized subdivision is **V2.1.4 — Cited synthesis and Research Packs**.

V2.1.4 must build on selected fetched evidence and implement claim-linked citations, explicit uncertainty, governed Research Pack persistence, and the approved project-knowledge/context handoff defined by `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`. It must not pull V2.1.5 media/community provider expansion or V2.1.6 adversarial hardening forward.

No V2.1.5 implementation may begin until V2.1.4 is qualified on its exact head, merged and continuity-normalized.

## Accepted V2 capability truth

The runtime truth model distinguishes:

- capability provenance/classification: `public-validated`, `source-available`, `acceptance-proven`, `experimental`, `unavailable`;
- provider/runtime state: `ready`, `unavailable`, `auth-required`, `network-restricted`, `not-implemented`;
- accelerator state: `priority`, `available`, `experimental`, `deferred`, `unsupported`.

Presence on live `main` does not imply presence in public rc8. Acceptance proof is separately bound to exact source evidence.

## Accelerator authority

Kaggle **T4×2** remains the primary remote-training target for the current CUDA/PyTorch/PEFT/QLoRA stack. The GPUs remain two separate 16 GiB devices; no component may present them as a single 32 GiB pool.

TPU v5e-8 remains **deferred**. Do not create or claim a distinct XLA/JAX or PyTorch/XLA backend unless a concrete benchmark demonstrates a material advantage that justifies its own implementation and acceptance surface.

## Release/updater boundary

Roadmap V2 does not reserve a new public release version and authorizes no release/TUF mutation. The rc8 source/tag/installer/TUF and real-machine E2E authority remain documented in `docs/continuity/KODEPOIA_CURRENT_AUTHORITY.md` and the release evidence. Post-rc8 source capabilities on `main` remain development capabilities until separately qualified for a future public release.

All accepted fail-closed invariants remain in force: exact source/artifact binding, TUF signature/threshold/rollback/version/expiry checks, exact target length/SHA-256, target-scoped Authenticode policy, installer identity verification, explicit user consent and no private signing material in Git/CI/public artifacts/chat.

## Resume rule

For future work:

1. re-fetch live `main` and read `STATE.md` + `NEXT.md`;
2. verify V2.1.3 remains COMPLETE + NORMALIZED before beginning V2.1.4;
3. the immediate next authorized implementation is **V2.1.4 — Cited synthesis and Research Packs**;
4. for every subdivision, branch from an exact live SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity;
5. if a genuine manual intervention is required, stop at that subdivision and describe exactly what the operator must do; never bypass a failed or missing gate;
6. never reopen R20 or invent R20.7.
