# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 28 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.8 COMPLETE + NORMALIZED. R14.9 IN_PROGRESS. R14.10–R14.17 PLANNED.** R14.8 est définitivement normalisée sur `main` `433c86cc5d43bfea41adb529451367e10c75a30b` après PR #272. R14.9 démarre exactement de ce SHA sur `r14/09-progression-leaderboards`. Frozen scope : définitions achievement/stat/leaderboard immuables et versionnées, progression seulement depuis événements/commandes autoritatifs validés, unlock/progress idempotents, score ordering/tie/period/reset explicites, snapshots de classement déterministes, écritures directes de score client interdites, privacy/display controls et queries provider-neutral. Manual intervention : NONE.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R13 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest : `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 canonical integrated digest : `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`.
- R14 planning : **ACCEPTED + NORMALIZED**.
- R14.1–R14.8 : **COMPLETE + NORMALIZED**.
- R14.8 normalized `main` : **`433c86cc5d43bfea41adb529451367e10c75a30b`** après normalization PR #272.
- R14.9 : **IN_PROGRESS** sur `r14/09-progression-leaderboards`, base exacte `433c86cc5d43bfea41adb529451367e10c75a30b`.
- R14.10–R14.17 : **PLANNED**.
- Manual state actuel : **NONE**.

## Permanent R-phase execution rule

Pour chaque subdivision R :

1. branche dédiée depuis le `main` immédiatement précédent et normalisé ;
2. START-sync obligatoire avant implémentation : subdivisions précédentes `COMPLETE + NORMALIZED`, subdivision active `IN_PROGRESS`, suivantes `PLANNED` ;
3. implémentation + tests focused/adversarial ;
4. gates exact-head sur une source technique immuable ;
5. état manuel véridique ; si un gate manuel/conditionnel est déclenché, arrêt avant la subdivision suivante ;
6. END-sync plan + continuité + acceptance après acceptation technique ;
7. re-gates exact-head frais si les bytes documentaires/evidence changent ;
8. merge uniquement avec `expected_head_sha` ;
9. exactement une normalisation post-merge continuity-only avec R0 + full Python Core + KodeStudio UI Smoke frais ;
10. seul le `main` normalisé résultant autorise la subdivision suivante.

La normalisation post-merge ne doit jamais réécrire le plan de phase. Toute preuve provenant d’un autre SHA, d’un candidat rejeté, d’un état provider non démontré ou d’un PASS synthétique est invalide.

## Security / governance boundaries

- `WorkspaceBoundary` et R8 `VaultBoundary` gouvernent source, artefacts, schémas, migrations, fixtures, backend state et evidence.
- `ProcessSandbox` + KillSwitch gouvernent les processus/outils repository-owned.
- Guardian/`PermissionSet`, SafeChange, Backup/Recovery et Audit restent obligatoires.
- `KodeSecrets` est l’unique autorité de secret ; aucun password/token/private key/DSN secret/provider credential dans DNA, Git, evidence, logs ou argv model-visible.
- Network **off by default** ; endpoints externes allowlisted, permissioned, timeout-bounded.
- Environnements `local` / `test` / `staging` / `production` explicitement séparés.
- Client input = intention, jamais état autoritaire. Le serveur valide actor/session, function/object authorization, revision/sequence et idempotency.
- Provider/account/domain/TLS/credential/quota manquant = `UNAVAILABLE` ou `BLOCKED`, jamais PASS.
- R12 desktop et R13 mobile restent des clients typés des services R14.

## R14 status index

| ID | Status | Manual |
| --- | --- | --- |
| R14.1 | COMPLETE + NORMALIZED | NONE |
| R14.2 | COMPLETE + NORMALIZED | NONE |
| R14.3 | COMPLETE + NORMALIZED | NONE |
| R14.4 | COMPLETE + NORMALIZED | CONDITIONAL / NOT TRIGGERED |
| R14.5 | COMPLETE + NORMALIZED | NONE |
| R14.6 | COMPLETE + NORMALIZED | NONE |
| R14.7 | COMPLETE + NORMALIZED | NONE |
| R14.8 | COMPLETE + NORMALIZED | NONE |
| R14.9 | IN_PROGRESS | NONE |
| R14.10 | PLANNED | CONDITIONAL |
| R14.11 | PLANNED | NONE |
| R14.12 | PLANNED | CONDITIONAL |
| R14.13 | PLANNED | NONE |
| R14.14 | PLANNED | NONE |
| R14.15 | PLANNED | CONDITIONAL |
| R14.16 | PLANNED | NONE |
| R14.17 | PLANNED | CONDITIONAL |

## R14.1–R14.6 closure checkpoint

Les détails complets restent immuables dans `docs/roadmap/R14_PLAN.md` et dans l’historique Git. Dernier `main` normalisé avant R14.7 : `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`. R14.6 source technique : `a1425b53e1228f9c88ba373cdfabf1459393a7cf`; final END-head `cf5a14295fdc3ff92ca72384b061e3a2c844e725`; merge PR #267 `6033e5610a811a690a2998eb07183f19183fa557`; normalisation R14.6 `9dafc361e909157dedf5cb89d7a39cdbb6ffff14`; normalized main `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`.

## R14.7 closure authority

- Branche implementation : `r14/07-matchmaking-lobby-presence`.
- Base exacte : normalized R14.6 main `1ce9b5223d1dfe9e1cfe4aaff324c5cd810883a2`.
- START-sync plan : `8dc25375e40c045b8831278faa0f55ad74cf6df1`; continuité START : `63c41c51ad6fb4adb981d284c3753ea5a26c9eb6`.
- Candidat `12071ee561717ac436f4ffa0457361685214c989` : **REJECTED**, ne jamais réutiliser ses preuves. Matchmaking Acceptance #2 a détecté que `update_presence(IN_MATCH)` ne balayait pas l’expiration server-clock avant autorisation.
- Source technique immuable acceptée : `d04c841fcef9eb9f963085da68e579dbb58186da`.
- Gates techniques : R0 #1803 / `33203286519`, Python Core #1777 / `33203286537`, UI #1744 / `33203286514`, R14 Matchmaking Acceptance #4 / `33203286510` — tous SUCCESS.
- Full Ubuntu : **1543 passed / 13 skipped / 46 warnings**. Focused R14.7→R14.4 : **66 passed Ubuntu + 66 passed Windows**.
- Quatorze checks gelés PASS : lobby lifecycle, object authorization, duplicate join, recursive reserved-field rejection, duplicate ticket, deterministic matching, incompatible criteria isolation, no double assignment, cancellation terminality, reservation expiry, stale presence rejection, reconnect binding, reconnect expiry, bounded capacity.
- Digests cross-platform identiques : state `ae9ecc0893537e5c12cc8a78247197ed53d094b1a811c386c17161fac10c0c19`; lobby `27bcd90471e3775b859ce21e977c5ac534909a898deab0eb2c27cd44b86db0cf`; reservation `e8423de1a2d1a92873bbfa466111ab4a07168adeafca4bde4d62c64a70a9f690`; presence `5f2ca6c7402bba1a3b2d195d9f63d1c8b758c01d577d4581785559d92de24f0f`; trace `5f25c8f15da7e4f9dd45fbf072dd72101d3f32deef349c28069beeb83d954bd3`.
- Artifacts : Ubuntu `9698619713` / `sha256:f8bd9f43b431bb9a5f9b194da245a57381b000795a5c8ccacb51a866c371b1df`; Windows `9698629064` / `sha256:1e3b191e9d1de0844b49c62bcd36c79798a23315e93edf20393b862d1fb44c1c`.
- Final END-head : `a9376ad7aee4e4683fe9d7d98ef52d19ec2184e2`, dont le diff depuis la source technique est limité à `R14_PLAN.md`, `R14_7_ACCEPTANCE.md` et cette continuité.
- Final END gates : R0 #1808 / `33203970458`, Python Core #1782 / `33203970581`, UI #1749 / `33203970444`, R14 Matchmaking Acceptance #9 / `33203970381` — tous SUCCESS.
- PR #269 fusionnée avec `expected_head_sha=a9376ad7aee4e4683fe9d7d98ef52d19ec2184e2` comme merge `763ce96c4f82da2eaec167b56ffb62d9e548b300`.
- Provider posture : `provider_live_claim=false`, `secrets_exposed=false`, manual NONE.

## R14.8 closure authority

- Dedicated implementation branch: **`r14/08-cloud-saves`**.
- Exact branch point: normalized R14.7 `main` **`24e40db2781db8e42591c6ffa8fbdb8f0bf84108`**.
- Immutable technical source: **`8132c4029983f693a32e0d26903d05e347313bf6`**.
- Technical-source gates: R0 #1822 / `33206330276`, Python Core #1796 / `33206330171`, UI #1763 / `33206330345`, Cloud Save Acceptance #6 / `33206330291` — all SUCCESS.
- Python Core technical source Ubuntu: **1564 passed / 13 skipped / 46 warnings**; Windows Core SUCCESS; package builds Ubuntu/Windows SUCCESS.
- Focused technical-source R14.8→R14.5: **70 passed Ubuntu + 70 passed Windows**; fourteen cloud-save checks PASS cross-platform.
- Semantic digests: state `984bf5fc88d5ca537cd3a4d938c0aa6d890e8f1794f5485467726331331ce345`; trace `f071636d1c5c99614b91817d328bab43ec406daaf315621affecd45af42df5e8`; slot `24c423bfc661d2f8d207364c9d7058cb45413b7e15347beb78b50ca10c7345d1`; current revision `4603e4e2a7d7d708cf689eb6cd4502b9809993b7245fc3ac64bf05eee1f34d7e`; resolved conflict `be2d6808b13bd40aa4a04d003d8d47df315a4461a67647746b87b26d1e6c0eca`.
- Technical artifacts: Ubuntu `9699802370` / `sha256:bfd9d7cadb002a822f5c0f399f32dc7410b62318a1dee7a0c3d480bd1c8398d8`; Windows `9699818533` / `sha256:748f1b5572d679e619d82aeda314a1fa1f4c688d7edfe6f84e41fe54424c5a0d`.
- Rejected documentation END head `e9525d876a347c35336b34263eb33f5d0578f1b4`: **NON-AUTHORITATIVE** because an over-broad documentation replacement removed unrelated later R14 plan sections. Detected by exact-source compare before acceptance; plan restored from immutable source before targeted repair.
- Final accepted END-head: **`954991537fc8c076169993ea106303421b8edd60`**. Its final diff from technical source is restricted to `docs/roadmap/R14_PLAN.md`, `docs/roadmap/R14_8_ACCEPTANCE.md` and this continuity file.
- Fresh END gates on that exact head: R0 Repository Guard #1832 / `33208260744` SUCCESS; Python Core #1806 / `33208260746` SUCCESS; KodeStudio UI Smoke #1773 / `33208260611` SUCCESS; R14 Cloud Save Acceptance #16 / `33208260670` SUCCESS on Ubuntu and Windows.
- PR #271 merged only after verifying its exact head `954991537fc8c076169993ea106303421b8edd60`, with `expected_head_sha` protection, as implementation/evidence merge **`5b51967c63ad5ae5ccc2df89f76aa48831ee2762`**.
- Provider posture: `provider_live_claim=false`, `secrets_exposed=false`; RFC 9110 / Google Play Games / OWASP are informative evidence only.
- Single post-merge normalization head: **`0850580c78f2190199931129e9c1389f6c9977b1`**, changing only this continuity file. Fresh normalization gates: R0 #1834 / `33208563238`, Python Core #1808 / `33208563310`, UI #1775 / `33208563115` — all SUCCESS.
- Normalization PR #272 merged with `expected_head_sha=0850580c78f2190199931129e9c1389f6c9977b1` as normalized `main` **`433c86cc5d43bfea41adb529451367e10c75a30b`**.
- R14.8 final state: **COMPLETE + NORMALIZED**; R14.9 is authorized from that exact normalized `main`.
- Manual intervention: **NONE**.

## R14.9 START authority

- Dedicated branch: **`r14/09-progression-leaderboards`**.
- Exact branch point: normalized R14.8 `main` **`433c86cc5d43bfea41adb529451367e10c75a30b`**.
- START plan head: `5830d5d7fb75ac529c139c1f020e8dfc4423e580`; helper files self-removed before implementation.
- START state: R14.1–R14.8 **COMPLETE + NORMALIZED**; R14.9 **IN_PROGRESS**; R14.10–R14.17 **PLANNED**.
- Frozen scope: immutable/versioned achievement, stat and leaderboard definitions; server-authoritative validated progression events/commands; duplicate-safe idempotency; terminal/idempotent unlocks; explicit score ordering, tie, update and period/reset policies; deterministic ranking snapshots; privacy/display filtering; provider-neutral reads; direct client score writes forbidden.
- Acceptance focus: forged score rejection, duplicate/rebound event handling, duplicate unlock, definition immutability/versioning, deterministic higher/lower ranking and ties, period rollover/reset, privacy filtering, concurrency and bounded capacity.
- Provider posture: Steam/Game Center/Google Play are informative compatibility references only; no provider account, API key or live publication is required for core R14.9 acceptance.
- Manual intervention: **NONE**.

## External research baseline relevant to R14.9

- Steamworks distinguishes trusted backend Web API operations from client operations; its leaderboard API can require trusted writes so client score submission is disabled, and exposes explicit score update policy. R14.9 therefore keeps trusted progression writes server-side without making Steam the canonical model.
- Apple Game Center distinguishes classic leaderboards from recurring leaderboards that reset on configured schedules and exposes score sort order. R14.9 models periods/reset/order explicitly and deterministically rather than inheriting a platform implementation.
- Google Play Games exposes achievements and leaderboards as distinct client capabilities. R14.9 keeps those surfaces distinct while sharing one authoritative progression/event source internally.
- Provider documentation is versioned comparison evidence only; `provider_live_claim=false` remains mandatory unless a later explicit provider-live gate is executed.

## Next authorized action

Verify that the exact R14.9 START head differs from normalized R14.8 `main` `433c86cc5d43bfea41adb529451367e10c75a30b` by **only** `docs/roadmap/R14_PLAN.md` and `docs/continuity/KODEPOIA_CONTINUITY.md`. No implementation file may exist before that comparison passes. Once the START diff is clean, implement R14.9 on the same dedicated branch with immutable/versioned definitions, authoritative/idempotent progression events, deterministic ranking/period semantics, privacy filtering, bounded state and dedicated Ubuntu/Windows acceptance. Manual intervention remains **NONE**.
