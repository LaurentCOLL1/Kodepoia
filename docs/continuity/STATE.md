# Kodepoia continuity state

Last synchronized: 2026-09-17 after V2.1.2 implementation PR `#478` merged; this branch performs the required post-merge normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; for V2.1 specifically, read `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## V2.0 — COMPLETE + NORMALIZED

Roadmap preparation PR `#472` remains the accepted V2 planning authority. V2.0 implementation was completed by PR `#474` on exact head `79749ab25d58faaca6421bcda4eb460194a3683c`; all **27/27** PR-triggered workflows succeeded and PR `#474` merged as `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

V2.0 remains **COMPLETE + NORMALIZED**.

## V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 implementation PR `#476` was qualified with **27/27** PR-triggered workflows on exact head `c485083419f492e9c10989f6aadbda5bc436d5cc` and merged as `16ef244e9cad922421f2440ef8185e9e896a164d`.

Exact-head evidence:

- `v2-1-1-honest-research-ux-ubuntu-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `29bdb2bb193a3a2c7a397e3d2c1307f0d323d07ff5425081803ca28e133d4d26`;
- `v2-1-1-honest-research-ux-windows-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `215a5b7e1a931a04ecb957bb561c01695c8f6b992f3889aaa72026e8f8969aa6`.

## V2.1.2 — Discovery providers — COMPLETE; normalization in progress on this branch

Implementation PR `#478` was qualified on exact head:

`e1e209ebcf78265f04b30b0019d201d58dae76ef`

All **27/27** PR-triggered workflows associated with that exact head completed with conclusion `success`. This included `Python Core`, `KodeStudio UI Smoke`, `R13 Apple Xcode Acceptance`, `R17 Windows Installer`, `R18.11 Integrated Adversarial Release Update Acceptance`, Android and the remaining Windows/Apple gates. No failed job was bypassed or recycled from a previous head. The earlier Apple Xcode timeout on historical head `03fc1eee68c3750c6ae6a6b1f0b5c842582e44fd` was not rerun after the product fixes; Apple Xcode passed normally on the final qualified head.

PR `#478` was merged with `expected_head_sha=e1e209ebcf78265f04b30b0019d201d58dae76ef` as merge commit:

`347068de7f9be9275754bbda7c55f4e0d5e66bac`

V2.1.2 exact-head evidence emitted by `Python Core`:

- `v2-1-2-discovery-providers-ubuntu-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `e9c0d999b28d38c6319229354f19156b6b19e14d35ff567a9f0fcab25ebcd164`;
- `v2-1-2-discovery-providers-windows-latest-e1e209ebcf78265f04b30b0019d201d58dae76ef` — SHA-256 `8ff58d6ea0f4590654387b5b2c405df265aa36b91044c023e10f0c9ea304df8a`.

Accepted product truth after V2.1.2:

- general Web discovery uses the official Brave Search HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- GitHub public repository discovery uses the official GitHub REST Search API, with authentication optional and rate-limit/auth/network failures surfaced explicitly;
- discovery returns bounded descriptor-only candidates marked `candidate-only` / `unfetched` and does not automatically fetch, persist or promote them to evidence;
- KodeStudio `Search sources` calls real discovery only when NETWORK permission is enabled;
- selected candidate details expose lifecycle metadata including `candidate_only`, `fetched: false` and `persisted: false`;
- discovery remains strictly separate from `ResearchService.fetch()` and every later acquisition remains subject to the existing guarded fetch and ResearchGuard/protected-action boundaries;
- provider failure, missing authentication, rate limiting and network restriction cannot masquerade as successful empty discovery.

This branch is the required post-merge normalization. Once its exact head passes every required PR workflow and the normalization PR is merged, **V2.1.2 is COMPLETE + NORMALIZED** and V2.1.3 becomes authorized.

## V2.1 authorization

No V2.1.3 implementation may begin until this normalization PR itself is qualified on its exact head and merged.

After that merge, the only next authorized subdivision is **V2.1.3 — Evidence workspace**. Its scope is source cards and inspect/include/exclude flow; canonical locator/date/version/trust/freshness display; cache/refetch lineage; and duplicate normalization without losing provider provenance. Do not pull V2.1.4 synthesis/Research Pack work forward into V2.1.3.

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
2. verify that the V2.1.2 normalization PR is merged before starting V2.1.3;
3. the next authorized implementation after that normalization is **V2.1.3 — Evidence workspace**;
4. for every subdivision, branch from an exact live SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity;
5. if a genuine manual intervention is required, stop at that subdivision and describe exactly what the operator must do; never bypass a failed or missing gate;
6. never reopen R20 or invent R20.7.
