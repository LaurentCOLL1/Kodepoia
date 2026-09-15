# Kodepoia next actions

Last synchronized: 2026-09-15 for Roadmap V2 planning from live `main` `6b7ec8d4504da83579af98d8235326ea4268d63f`  
Companion state: `docs/continuity/STATE.md`  
Active roadmap: `docs/roadmap/KODEPOIA_ROADMAP_V2.md`

## Stable public boundary

The updater corrective/validation sequence is complete:

`rc7 corrective release -> healthy installed rc7 -> validation-only rc8 -> exact-source qualification -> draft-first publication -> qualified TUF authorization -> real Windows updater E2E rc7 -> rc8`

The real-machine E2E succeeded and the updater incident is **CLOSED**. The historical `rc5 -> rc6` attempt remains failed/incomplete and must never be relabeled successful.

Public Windows `v1.1.0-rc8` remains the last fully real-machine updater-E2E-qualified distribution baseline. Do not reopen R20, invent `R20.7`, or create another release candidate merely to repeat the successful rc7 -> rc8 proof.

## New authorized development direction

The user authorized preparation of Roadmap V2. This is a new development track layered on the completed V1/R1–R20 foundation, not a rewrite of historical acceptance.

The immediate priority is **V2.1 — Research Workspace**, because the current KodeStudio Research page is technically functional at the primitive level but does not yet provide a usable research-assistant workflow.

On the planning baseline:

- **Search** calls `ResearchService.query()` and searches already persisted project research reports/findings;
- it does **not** discover new Internet results;
- **Fetch** is a separate operation for a known local path or explicit Web URL;
- Web fetch remains governed by network permission, URL/SSRF safety, bounded response policies and ResearchGuard;
- therefore a user who enters a new question in a fresh project can legitimately receive no useful result even though the UI appears to offer “search”.

This semantic mismatch is the first V2 usability defect to correct.

## Execution order

1. **V2.0 baseline/capability truth** — preserve the distinction between public rc8, live `main`, experimental features and unavailable providers.
2. **V2.1.1 honest Research UX and diagnostics** — visibly distinguish saved-research search from external source discovery; expose provider/network state and actionable empty/error states.
3. **V2.1.2 real discovery providers** — implement bounded discovery for official/general Web plus GitHub, followed by guarded fetch of selected candidates.
4. **V2.1.3 evidence workspace** — source cards, preview, metadata, version/freshness/trust, include/exclude, deduplication and cache/refetch lineage.
5. **V2.1.4 cited synthesis + Research Packs** — claim-linked citations and governed project knowledge/Context Builder integration.
6. **V2.1.5 community/media providers** — forums and YouTube/transcript paths, with STT/frames only through separately governed media operations.
7. **V2.1.6 ResearchGuard hardening** — prompt injection, malicious redirects, SSRF attempts, timeouts, stale/version-conflicting evidence, provider outages and cancellation.
8. **V2.2 project knowledge/context integration**.
9. **V2.3 Model Lab** for end-to-end governed SFT/LoRA/QLoRA UX.
10. **V2.4 real Kaggle T4×2 E2E and explicit multi-GPU qualification**.
11. **V2.5 cross-workspace orchestration**.
12. **V2.6 hardening and a future post-rc8 public release**, only when its exact functional boundary is known and qualified.

The detailed Research contract is `docs/roadmap/V2_1_RESEARCH_WORKSPACE.md`.

## Accelerator decision

For the current R15 training architecture, **Kaggle GPU T4×2 is the primary remote-training target**.

The two T4s remain separate 16 GiB devices. V2.4 must first prove the existing conservative Kaggle path on a real account, then qualify explicit two-process/multi-GPU execution with per-device evidence. No component may pretend that 2 × 16 GiB is a single 32 GiB VRAM pool.

**TPU v5e-8 is deferred.** It is not useless in general, but using it correctly would create a separate XLA/JAX or PyTorch/XLA backend and acceptance surface. Do not spend V2 engineering effort on TPU unless a concrete benchmark proposal shows a material advantage for a Kodepoia workload that is not adequately served by the qualified GPU path.

## Release boundary

Roadmap V2 planning does not reserve `rc9`, `1.1.0`, `1.2.0` or any other version. Do not mutate release tags, installer artifacts or TUF metadata merely because the roadmap is merged.

Before any future updater/release/TUF mutation:

1. re-fetch live `main`;
2. re-fetch latest public release/tag/asset;
3. re-read live Root/Targets/Snapshot/Timestamp metadata;
4. preserve exact-source qualification and draft-first release discipline;
5. preserve TUF exact length/SHA binding, signature/threshold/rollback/version/expiry checks and installer identity verification;
6. keep Authenticode exceptions target-scoped only;
7. require explicit user consent before installer launch;
8. stop on any failed verification rather than bypassing it;
9. never expose private signing keys, seeds, passphrases or custody paths.

## Per-subdivision discipline

For each V2 subdivision: re-fetch live state, branch from an exact SHA, implement only that scope, add deterministic tests/acceptance, re-fetch all required workflows on the exact head, merge only after successful gates, then normalize continuity before the next subdivision. If a manual intervention is genuinely required, stop and state exactly what the operator must do instead of bypassing the gate.

## Resume prompt

`@Recherche sur le Web Reprends Kodepoia depuis docs/continuity/STATE.md, docs/continuity/NEXT.md et docs/roadmap/KODEPOIA_ROADMAP_V2.md. Revalide d'abord le main live. La distribution publique de référence reste rc8 et l'incident updater est clos. Continue la prochaine subdivision V2 non terminée, en priorité V2.1 Research Workspace : le Search actuel ne découvre pas Internet, il cherche les rapports de recherche déjà persistés. Implémente un vrai flux question -> découverte de sources -> fetch gardé -> inspection -> synthèse citée -> Research Pack, sans affaiblir ResearchGuard. Kaggle T4×2 est prioritaire pour le training; TPU v5e-8 reste différé sauf benchmark justifiant un backend XLA distinct. Ne crée aucune release/TUF mutation sans demande et qualification explicites.`
