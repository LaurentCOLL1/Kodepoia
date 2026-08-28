# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 28 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R13 COMPLETE + NORMALIZED. R14 planning ACCEPTED + NORMALIZED. R14.1–R14.7 COMPLETE + NORMALIZED. R14.8–R14.17 PLANNED.** R14.7 a été fusionnée par PR #269 depuis le HEAD exact `a9376ad7aee4e4683fe9d7d98ef52d19ec2184e2` après R0 #1808, Python Core #1782, KodeStudio UI Smoke #1749 et R14 Matchmaking Acceptance #9, tous SUCCESS. Merge R14.7 : `763ce96c4f82da2eaec167b56ffb62d9e548b300`. Cette branche `r14/07-continuity-normalization` est l’unique normalisation post-merge et ne modifie que ce fichier. R14.8 n’est autorisée qu’après R0 + Python Core + UI Smoke SUCCESS sur le HEAD exact de cette normalisation puis merge avec expected-head protection. Manual intervention : NONE.

## État global

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : **frozen**.
- R1–R13 : **COMPLETE + NORMALIZED**.
- R12 canonical integrated digest : `daa54b643259a3b940d66db855bf5013bf2f4bfd877c0e82d222616ded624e50`.
- R13 canonical integrated digest : `831b155fce200eae6b9fbe91c8eb44e992ea036c0922e508171644b497a4c3c7`.
- R14 planning : **ACCEPTED + NORMALIZED**.
- R14.1–R14.7 : **COMPLETE + NORMALIZED**, sous réserve du merge de cette unique normalisation R14.7 après ses trois gates frais.
- R14.8–R14.17 : **PLANNED**.
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
| R14.8 | PLANNED | NONE |
| R14.9 | PLANNED | NONE |
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

## External research baseline relevant to R14.8

- RFC 9110 §13 définit les requêtes conditionnelles ; `If-Match` permet de faire échouer une mutation lorsque la représentation courante ne correspond plus à la version observée, afin d’éviter le problème de “lost update”. Cette sémantique est un bon repère pour le compare-and-swap/base-revision de R14.8, sans imposer HTTP comme architecture interne.
- OWASP API1:2023 exige une autorisation objet sur chaque endpoint qui reçoit un identifiant d’objet. Les `CloudSaveSlotId` / `SaveRevisionId` devront donc être autorisés server-side et ne jamais être considérés comme sûrs parce qu’ils viennent d’un client.

## Next authorized action

Cette branche est l’unique normalisation `r14/07-continuity-normalization` depuis le merge `763ce96c4f82da2eaec167b56ffb62d9e548b300` et ne doit modifier que `docs/continuity/KODEPOIA_CONTINUITY.md`. Exiger R0 Repository Guard + full Python Core + KodeStudio UI Smoke SUCCESS sur son HEAD exact, puis merger la PR de normalisation uniquement avec `expected_head_sha`. Le `main` résultant devient alors l’unique base autorisée de R14.8. Pour R14.8 : créer une branche dédiée depuis ce `main`, START-sync `R14_PLAN.md` + continuité avant toute implémentation, puis implémenter immutable save revisions, base-revision/CAS, explicit conflicts, idempotency, quota/integrity checks et rollback/recovery. Manual intervention : **NONE**.
