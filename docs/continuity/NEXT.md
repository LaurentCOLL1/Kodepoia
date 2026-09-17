# Kodepoia next actions

Last synchronized: 2026-09-17 after V2.1.4 implementation PR `#482` merged and post-merge continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0, V2.1.1, V2.1.2, V2.1.3 and V2.1.4 are **COMPLETE + NORMALIZED**.

## V2.1.4 accepted implementation

V2.1.4 implementation PR `#482` was qualified with **27/27** `completed/success` pull-request workflows on exact head:

`7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921`

It merged from that unchanged head as:

`a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda`

The final exact-head qualification included:

- `R0 Repository Guard` run `35241928748` = `completed/success`;
- `Python Core` run `35241928338` = `completed/success`, attempt 2 after a targeted rerun of the Ubuntu job;
- `KodeStudio UI Smoke` run `35241928376` = `completed/success`;
- `R17 Windows Installer` run `35241928065` = `completed/success`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35241928032` = `completed/success`.

The first Ubuntu Python Core attempt had failed only in the historical R16.16 bounded resource-soak test because the runner resource measurement returned `resource_claim == False`. The targeted Ubuntu rerun job `105285922212` then completed successfully, including the full pytest suite. No R16.16 product change was made.

V2.1.4 exact-head evidence:

- Ubuntu rerun artifact `v2-1-4-cited-synthesis-ubuntu-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `ef883894e5833d7d6cf4f6e6cb76360d701b5b66142d5de7e92ea29fa7e38490`;
- Windows artifact `v2-1-4-cited-synthesis-windows-latest-7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921` — SHA-256 `c83fee4ffb3326ef2a409f7cf8e0ed3907ccc7f9cbee1aa79b5a10cfa790ae1f`.

The deterministic V2.1.4 acceptance reported **13/13 PASS** on Ubuntu and Windows. Accepted product truth includes:

- synthesis only from explicitly persisted INCLUDED fetched evidence;
- immutable claim-to-citation provenance bound to artifact, evidence revision, canonical source identity and content digest;
- later refetches cannot silently rewrite historical citation provenance;
- visible stale/conflict uncertainty and explicit source-fact versus inference distinction;
- source content remains guarded data and cannot grant permissions or invoke protected actions;
- deterministic, schema-versioned, digest-bound, reopenable Research Packs under `.kodepoia/research/packs/`;
- secret redaction and WorkspaceBoundary preservation;
- structured KodeStudio synthesis/save/citation UI;
- no V2.1.5 provider expansion, V2.1.6 hardening corpus or release/TUF mutation pulled forward.

## Immediate execution order

### V2.1.5 — Extended media/community sources — NEXT AUTHORIZED

Branch only from re-fetched live `main` containing this V2.1.4 normalization, then implement only the V2.1.5 scope defined in `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Current authorized scope:

- add forum/community source discovery paths;
- add YouTube/video discovery and transcript-oriented source paths;
- keep discovery candidates descriptor-only until an explicit guarded fetch/acquisition step succeeds;
- keep provider/network/authentication/rate-limit failures visible rather than converting them into empty-success results;
- preserve canonical source identity, provider provenance, evidence selection, immutable revision lineage and cited synthesis contracts already accepted in V2.1.2–V2.1.4;
- any speech-to-text or frame extraction must be separately governed and accepted before it can become trusted fetched evidence;
- add deterministic backend/UI tests and exact-head acceptance evidence for the implemented V2.1.5 boundary.

Do **not** pull forward:

- V2.1.6 full adversarial ResearchGuard hardening for prompt injection, malicious redirects, SSRF, outage/timeout/cancellation and related corpus coverage beyond what is necessary to preserve existing fail-closed boundaries;
- any new public release, installer publication or TUF transition;
- unrelated Model Lab, accelerator or cross-workspace work.

After V2.1.5 merges, normalize continuity before V2.1.6 begins.

## Later V2.1 order

Only after V2.1.5 is COMPLETE + NORMALIZED, continue with:

1. V2.1.6 — ResearchGuard hardening.

Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live et toute PR ouverte. V2.1.4 a été qualifiée 27/27 sur le head exact 7d7fbcb6d7f4bfcf64b0d9e6ecdc2573673d3921 puis fusionnée comme a5efbe44c0ed8c42c251cf0462ef7d8c24d7ecda. V2.1.4 est COMPLETE + NORMALIZED et V2.1.5 — Extended media/community sources — est la prochaine subdivision autorisée seulement depuis un main contenant cette normalisation. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
