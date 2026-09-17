# Kodepoia continuity state

Last synchronized: 2026-09-17 after V2.1.4 implementation PR `#482` merged and post-merge continuity normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; for V2.1 specifically, read `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## V2.0 — COMPLETE + NORMALIZED

Roadmap preparation PR `#472` remains the accepted V2 planning authority. V2.0 implementation was completed by PR `#474` on exact head `79749ab25d58faaca6421bcda4eb460194a3683c`; all **27/27** PR-triggered workflows succeeded and PR `#474` merged as `043dba64111f763f0e9544ea8cde9a3cbf9b1dff`.

## V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 implementation PR `#476` was qualified with **27/27** PR-triggered workflows on exact head `c485083419f492e9c10989f6aadbda5bc436d5cc` and merged as `16ef244e9cad922421f2440ef8185e9e896a164d`.

## V2.1.2 — Discovery providers — COMPLETE + NORMALIZED

V2.1.2 implementation PR `#478` was qualified with **27/27** PR-triggered workflows on exact head `e1e209ebcf78265f04b30b0019d201d58dae76ef` and merged as `347068de7f9be9275754bbda7c55f4e0d5e66bac`. Its normalization PR `#479` merged as `39ceec560ff069d98530687f77e7ad1c41670d3a`.

Accepted V2.1.2 product truth remains:

- general Web discovery uses the official Brave Search HTTPS API when NETWORK is explicitly allowed and the API key is referenced through KodeSecrets;
- GitHub public repository discovery uses the official GitHub REST Search API with optional authentication;
- discovery returns bounded descriptor-only candidates marked `candidate-only` / `unfetched` and never automatically fetches, persists or promotes them to evidence;
- provider failure, missing authentication, rate limiting and network restriction remain explicit and cannot masquerade as successful empty discovery;
- every later acquisition remains subject to guarded fetch and ResearchGuard/protected-action boundaries.

## V2.1.3 — Evidence workspace — COMPLETE + NORMALIZED

Implementation PR `#480` was qualified with **27/27** PR-triggered workflows on exact head `c4cff95ea2309ea5482e6c24c61002b13becb48f` and merged as `0c3d365626df666f2a847b9320b0730dc0110afa`.

Exact-head evidence:

- Ubuntu `v2-1-3-evidence-workspace-ubuntu-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `753436509fc379e5bfc93426d5be0b5605083c5959679c8b61abb79feac54d27`;
- Windows `v2-1-3-evidence-workspace-windows-latest-c4cff95ea2309ea5482e6c24c61002b13becb48f` — SHA-256 `043a626b059277bd4dbcb8cf0f7b32ed1b5e2fd1ac71c993c31c3802e049dd2c`.

The deterministic exact-head acceptance reported **13/13 PASS**.

## V2.1.4 — Cited synthesis and Research Packs — COMPLETE + NORMALIZED

Implementation PR `#482` was qualified on exact head:

`7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921`

All **27/27** pull-request workflows associated with that exact head completed with conclusion `success`, including:

- `R0 Repository Guard` run `35241928748`;
- `Python Core` run `35241928338`, final workflow state `completed/success` after the targeted Ubuntu rerun, attempt 2;
- `KodeStudio UI Smoke` run `35241928376`;
- `R17 Windows Installer` run `35241928065`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35241928032`.

The first Ubuntu Python Core attempt had failed only in historical R16.16 resource-soak measurement due to runner resource noise. The targeted rerun job `105285922212` completed successfully, including the full pytest suite. R16.16 was not modified because no reproducible product defect was established.

PR `#482` merged from the unchanged exact head as merge commit:

`a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda`

The V2.1.4 deterministic acceptance reported **13/13 PASS** on Ubuntu and Windows. Accepted exact-head evidence from the successful Python Core qualification is:

- Ubuntu rerun artifact `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows artifact `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

Accepted V2.1.4 product truth:

- synthesis consumes only explicitly persisted INCLUDED fetched evidence; descriptor-only candidates cannot become citations;
- source-backed claims expose citations bound to immutable artifact ID, evidence revision ID, canonical source identity and content digest;
- later refetches cannot silently retarget historical citation provenance;
- stale/conflicting evidence remains visible as uncertainty/conflict state;
- source facts and synthesis inferences remain explicitly distinguishable;
- source content is treated as guarded data and cannot grant permissions or invoke protected actions;
- Research Packs are deterministic, schema-versioned, digest-bound, reopenable and project-scoped below `.kodepoia/research/packs/`;
- secret redaction and WorkspaceBoundary constraints remain effective;
- KodeStudio exposes structured `Synthesize included evidence` and `Save Research Pack` workflows plus claim/citation state;
- V2.1.5 media/community provider expansion and V2.1.6 adversarial hardening were not pulled forward.

## V2.1 authorization

With V2.1.4 **COMPLETE + NORMALIZED**, the only next authorized subdivision is **V2.1.5 — Extended media/community sources**.

Its exact scope must be taken from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md` after this normalization is live. The current roadmap boundary authorizes forum and YouTube/transcript discovery paths, with STT/frame extraction only when separately governed and accepted. V2.1.5 must preserve the existing candidate/fetch/evidence/synthesis separation and ResearchGuard boundaries. It must not pull V2.1.6 adversarial hardening or release/TUF work forward.

No V2.1.6 implementation may begin until V2.1.5 is qualified on its exact head, merged and continuity-normalized.

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
2. verify V2.1.4 remains COMPLETE + NORMALIZED before beginning V2.1.5;
3. the immediate next authorized implementation is **V2.1.5 — Extended media/community sources**;
4. for every subdivision, branch from an exact live SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity;
5. if a genuine manual intervention is required, stop at that subdivision and describe exactly what the operator must do; never bypass a failed or missing gate;
6. never reopen R20 or invent R20.7.
