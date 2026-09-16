# Kodepoia continuity state

Last synchronized: 2026-09-16 after V2.1.1 implementation PR `#476` merged and post-merge normalization  
Repository: `LaurentCOLL1/Kodepoia`  
Canonical branch: `main`

## Immediate authority

Read this file together with `docs/continuity/NEXT.md` and re-fetch live GitHub state before acting. For V2 work, also read `docs/roadmap/KODEPOIA_ROADMAP_V2.md`; for V2.1 specifically, read `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

The public Windows distribution authority remains **`v1.1.0-rc8`**. The real installed Windows updater E2E `rc7 -> rc8` passed and the exercised updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 remains **COMPLETE + NORMALIZED**, terminal, and must not be reopened or extended as `R20.7`.

## V2.0 — COMPLETE + NORMALIZED

Roadmap preparation PR `#472` remains the accepted V2 planning authority. V2.0 implementation was completed by PR `#474` on exact head:

`79749ab25d58faaca6421bcda4eb460194a3683c`

All **27/27** PR-triggered workflows on that exact SHA completed with conclusion `success`, including `Python Core`, both KodeStudio UI smoke paths, `R17 Windows Installer`, `R18.11 Integrated Adversarial Release Update Acceptance`, R20.6 and all required Android/Apple/Windows gates. PR `#474` was merged with an exact-head guard as merge commit:

`043dba64111f763f0e9544ea8cde9a3cbf9b1dff`

V2.0.3 exact-head evidence was emitted inside `Python Core` for both operating systems:

- `v2-0-capability-truth-ubuntu-latest-79749ab25d58faaca6421bcda4eb460194a3683c` — SHA-256 `a5dd36a7f0b758c577879c71b34ec65c0b0c24848c7962337d3fe5a8e66e3c2d`;
- `v2-0-capability-truth-windows-latest-79749ab25d58faaca6421bcda4eb460194a3683c` — SHA-256 `8dad43c801f848883bba4e86f249ca8a035a0a37739bcde2645f0ccaf0d79e8d`.

V2.0 remains **COMPLETE + NORMALIZED**.

## V2.1.1 — Honest Research UX and diagnostics — COMPLETE + NORMALIZED

V2.1.1 implementation PR `#476` was qualified on exact head:

`c485083419f492e9c10989f6aadbda5bc436d5cc`

All **27/27** PR-triggered workflows on that exact SHA completed with conclusion `success`. `Python Core`, `KodeStudio UI Smoke`, `R17 Windows Installer`, `R18.11 Integrated Adversarial Release Update Acceptance`, Android and Apple acceptance all passed. `R13 Apple Xcode Acceptance` initially hit a hosted-runner `xcrun simctl` timeout; the single failed job was rerun on the same `GITHUB_SHA`/`GITHUB_REF` and the rerun completed successfully without any code change or head movement.

PR `#476` was then merged with exact-head guard as merge commit:

`16ef244e9cad922421f2440ef8185e9e896a164d`

V2.1.1 exact-head evidence emitted by `Python Core`:

- `v2-1-1-honest-research-ux-ubuntu-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `29bdb2bb193a3a2c7a397e3d2c1307f0d323d07ff5425081803ca28e133d4d26`;
- `v2-1-1-honest-research-ux-windows-latest-c485083419f492e9c10989f6aadbda5bc436d5cc` — SHA-256 `215a5b7e1a931a04ecb957bb561c01695c8f6b992f3889aaa72026e8f8969aa6`.

Accepted product truth after V2.1.1:

- **Search saved research** queries already persisted project research only;
- **Search sources** is a separate operation and was deliberately exposed as unavailable/not implemented until V2.1.2 provides real discovery providers;
- **Open/fetch source** remains the existing guarded locator acquisition path;
- provider/network/authentication failures are visible and actionable instead of being rendered as successful empty searches;
- raw JSON is secondary diagnostic detail, not the primary UX;
- ResearchGuard and protected-action boundaries remain unchanged.

This authority update is the required post-merge normalization. Therefore **V2.1.1 is COMPLETE + NORMALIZED**.

## V2.1 authorization

The only next authorized subdivision is **V2.1.2 — Discovery providers**.

V2.1.2 must implement only the discovery-provider scope from `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`: deterministic provider interfaces/fixtures, at least official/general Web plus GitHub discovery, bounded results, cancellation, deduplication, no hidden retries, no protected mutation from discovery alone, and continued guarded fetch for every selected/discovered locator.

No later V2.1 subdivision may be started before V2.1.2 is qualified on its exact head, merged and continuity-normalized.

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
2. begin or continue the current V2.1 subdivision only if the previous subdivision is COMPLETE + NORMALIZED;
3. the immediate next subdivision is **V2.1.2 — Discovery providers**;
4. for every subdivision, branch from an exact live SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity;
5. if a genuine manual intervention is required, stop at that subdivision and describe exactly what the operator must do; never bypass a failed or missing gate;
6. never reopen R20 or invent R20.7.
