# Kodepoia next actions

Last synchronized: 2026-09-17 after V2.1.5 implementation PR `#484` merged and post-merge continuity normalization  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

Public Windows **`v1.1.0-rc8`** remains the last fully real-machine updater-E2E-qualified distribution baseline. The updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete. R20 is terminal and remains **COMPLETE + NORMALIZED**; do not reopen it or invent `R20.7`.

V2.0, V2.1.1, V2.1.2, V2.1.3, V2.1.4 and V2.1.5 are **COMPLETE + NORMALIZED**.

## V2.1.5 accepted implementation

V2.1.5 implementation PR `#484` was qualified with **27/27** `completed/success` pull-request workflows on exact head:

`f46068a410e7e0ea3f32f8decc77eed6aa105355`

It merged from that unchanged head as:

`bfe7fa6b4def1a291d97bd2b9365bda321bcde52`

The final exact-head qualification included:

- `R0 Repository Guard` run `35265257329` = `completed/success`;
- `Python Core` run `35265257418` = `completed/success`;
- `KodeStudio UI Smoke` run `35265257290` = `completed/success`;
- `R17 Windows Installer` run `35265257386` = `completed/success`;
- `R18.11 Integrated Adversarial Release Update Acceptance` run `35265257328` = `completed/success`.

V2.1.5 exact-head evidence:

- Ubuntu artifact `v2-1-5-extended-sources-ubuntu-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `6275abca3e380e118120718834fd34e68e819822860220b4f79a2f63ff69c2e7`;
- Windows artifact `v2-1-5-extended-sources-windows-latest-f46068a410e7e0ea3f32f8decc77eed6aa105355` — SHA-256 `68373539d62e0e348ce6ab7ff5f23c567b0f0e287a98901f31895d34986a4b0b`.

The deterministic V2.1.5 acceptance reported **12/12 PASS** on Ubuntu and Windows. Accepted product truth includes:

- YouTube and community discovery items remain descriptor-only `candidate-only` / `unfetched` candidates until an explicit guarded acquisition succeeds;
- official YouTube `search.list` payloads are normalized into bounded video descriptors without implicit fetch or persistence;
- YouTube metadata/transcript acquisition uses the existing guarded provider path and keeps network, credential, provider and transcript-unavailable states explicit;
- community acquisition remains guarded and preserves semantic thread relationships such as parent/quote linkage without treating popularity as authority;
- acquired community/media content enters the canonical `ResearchStore` / `EvidenceWorkspace` / selection lifecycle with existing provenance, revision, citation and Research Pack contracts;
- speech-to-text and frame extraction remain explicitly non-authoritative and cannot silently become trusted evidence;
- KodeStudio exposes typed Community/YouTube fetch choices, provider state and candidate-to-explicit-fetch handoff without collapsing discovery into acquisition;
- source content remains untrusted data and cannot grant permissions or invoke protected actions;
- V2.1.6 adversarial hardening and all release/TUF/updater work remained out of scope.

## Immediate execution order

### V2.1.6 — ResearchGuard hardening — NEXT AUTHORIZED

Branch only from re-fetched live `main` containing this V2.1.5 normalization, then implement only the V2.1.6 scope defined in `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

Current authorized scope:

- adversarial prompt-injection coverage for discovered and fetched source data;
- malicious redirect and SSRF boundary hardening around external acquisition;
- explicit timeout, outage and cancellation behavior that cannot masquerade as successful empty research;
- stale/version-conflict and offline/cache adversarial coverage while preserving immutable evidence/citation lineage;
- deterministic backend/UI tests plus exact-head Ubuntu/Windows acceptance evidence for the implemented V2.1.6 boundary.

Do **not** pull forward:

- V2.2 Project Knowledge / Context Builder / Memory integration;
- any new public release, installer publication or TUF transition;
- unrelated Model Lab, accelerator or cross-workspace work.

After V2.1.6 merges, normalize continuity before V2.2 begins.

## Later V2 order

Only after V2.1.6 is COMPLETE + NORMALIZED, continue with V2.2 — Project Knowledge, Context Builder and Memory integration. Do not skip subdivision acceptance or continuity normalization.

## Accelerator policy

Kaggle **T4×2** remains the priority remote accelerator for the current CUDA/PyTorch/PEFT/QLoRA training path. Treat the two T4s as two separate 16 GiB devices. TPU v5e-8 remains deferred unless a concrete benchmark justifies the engineering and acceptance cost of a distinct XLA/JAX or PyTorch/XLA backend.

## Release boundary

No V2 planning or implementation step by itself authorizes a new release, installer publication or TUF mutation. Keep `v1.1.0-rc8` as the public reference until a future release is explicitly scoped and qualified.

## Per-subdivision discipline

For every subdivision: re-fetch live `main`, branch from the exact SHA, implement only the authorized scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only when all required gates succeed, and normalize continuity before starting the next subdivision. If and only if a genuine manual intervention is required, stop and state exactly what the operator must do.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md, docs/roadmap/KODEPOIA_ROADMAP_V2.md et docs/roadmap/V2_1_RESEARCH_WORKSPACE.md. Revalide d'abord le main live et toute PR ouverte. V2.1.5 a été qualifiée 27/27 sur le head exact f46068a410e7e0ea3f32f8decc77eed6aa105355 puis fusionnée comme bfe7fa6b4def1a291d97bd2b9365bda321bcde52. V2.1.5 est COMPLETE + NORMALIZED et V2.1.6 — ResearchGuard hardening — est la prochaine subdivision autorisée seulement depuis un main contenant cette normalisation. La distribution publique reste v1.1.0-rc8; l'incident updater reste clos; ne rouvre pas R20 et n'invente pas R20.7. Kaggle T4×2 reste prioritaire; TPU v5e-8 reste différé sauf benchmark justifiant réellement un backend XLA distinct.`
