# Kodepoia — Continuité / reprise par un autre LLM

**Dernière mise à jour : 22 août 2026**

## Prompt de reprise

> Kodepoia, architecture v1.0 gelée. **R1–R7 COMPLETE. R8 PLANNING ACCEPTED. R8.1 AUTHORIZED / NOT STARTED.** R7.11 est accepté sur le head exact `52330ca576fe294956a8fb601bdfda1d72dc3f92`; PR #80 merge `1cdf5b90cc6c3e829c13e63f753f47fb067ef14e`; manual R7.11 = CONDITIONAL NOT TRIGGERED. La normalisation finale R7 est acceptée sur le head exact `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4` avec R0 #1035 / `32599397013`, Python Core #1009 / `32599397057` cinq jobs SUCCESS, suite Ubuntu `515 passed / 5 skipped / 46 warnings`, validation `R7 integrated acceptance: PASS`, UI Smoke #976 / `32599397003` SUCCESS; PR #81 merge `24dc403b329fd748a8aadac9d6760a2fb73a9730`. La continuité finale R7 a ensuite été fusionnée par PR #82 sur `main` `b98832b339902527bce8a5ea95b5a08a19839a40`. **Le planning exhaustif R8 est ACCEPTED sur le head exact `08844fc09501ed8a4974909eca4595021bc73bf4` avec R0 Repository Guard #1039 / `32600268817` SUCCESS, Python Core #1013 / `32600268710` cinq jobs SUCCESS, KodeStudio UI Smoke #980 / `32600268680` SUCCESS; PR #83 merge `60412afac35678b2a25547a7f0c937891a8a1004`. `docs/roadmap/R8_PLAN.md` fige R8.1–R8.11. La prochaine action autorisée après cette normalisation est R8.1 — Asset/Vault contracts, identity, schemas + boundary — sur une branche dédiée issue du `main` normalisé. Ne pas sauter directement à R8.2 ni modifier la structure R8 sans synchroniser plan + continuité; toute modification de fondation exige un ADR.**

## Source de vérité et état

- Dépôt : `LaurentCOLL1/Kodepoia` — PUBLIC volontairement.
- Architecture v1.0 : gelée le 21 août 2026.
- `main` : source de vérité après chaque fusion acceptée.
- `main` au branch point R8 planning : `b98832b339902527bce8a5ea95b5a08a19839a40` (PR #82, final continuity R7).
- R1–R6 : COMPLETE.
- R7 : **COMPLETE**.
- R7 planning : ACCEPTED — head `f86825ffd84c1c814afb5865be95b278c4291314`; PR #58 merge `9315d801f3a2d13a5441bd87babd2abeb9305995`; normalization #59 `7279412ae751bce739317763462c4a48d7832122`.
- R7.1 : COMPLETE — `a6e9cf9f6db717155c311f4ded1ad5fb744b70ca`; manual NONE.
- R7.2 : COMPLETE — `9101e686a32b24bb33a23d7ac578bf25570e115e`; manual NONE.
- R7.3 : COMPLETE — `4efd2cb016e774fa3ef06590ffda377606d875e9`; manual NONE.
- R7.4 : COMPLETE — `be6f1d5d2f7d9a16c1c295a51905fcd22e9835be`; manual CONDITIONAL NOT TRIGGERED.
- R7.5 : COMPLETE — `12d5580ff3f8c6d9d0fb211e1688e3ba37dcdce5`; manual NONE.
- R7.6 : COMPLETE — `b623836b8f5bd39fce101eca7fe4653a996a9562`; manual CONDITIONAL NOT TRIGGERED.
- R7.7 : COMPLETE — `04cef94c82fdacafe7313d27c8cf516e8e765295`; manual REQUIRED SATISFIED.
- R7.8 : COMPLETE — `deb5de415541004fb07bfbc6d955e9d76d717533`; manual NONE.
- R7.9 : COMPLETE — `80390f95a11e5b3d4353b16eada26f10204bb4fa`; manual NONE.
- R7.10 : COMPLETE — `cfd0f7ba02af04b456993f686827f10810b3a61a`; manual NONE.
- R7.11 : COMPLETE — `52330ca576fe294956a8fb601bdfda1d72dc3f92`; manual CONDITIONAL NOT TRIGGERED.
- R7 integrated report : PASS, no blockers, digest `2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.
- R7 final normalization : COMPLETE — head `d2278b1ee31d7d4a7b8570836edc3082e9fe30c4`; R0 #1035 / `32599397013`; Python Core #1009 / `32599397057` 5/5 (`515 passed / 5 skipped / 46 warnings` Ubuntu, integrated check PASS); UI Smoke #976 / `32599397003`; PR #81 merge `24dc403b329fd748a8aadac9d6760a2fb73a9730`.
- R7 final continuity : PR #82 merged to `main` `b98832b339902527bce8a5ea95b5a08a19839a40`.
- R8 planning : **ACCEPTED** — head `08844fc09501ed8a4974909eca4595021bc73bf4`; R0 #1039 / `32600268817` SUCCESS (Ubuntu + Windows); Python Core #1013 / `32600268710` SUCCESS 5/5; UI Smoke #980 / `32600268680` SUCCESS; PR #83 merge `60412afac35678b2a25547a7f0c937891a8a1004`.
- R8 : AUTHORIZED / NOT IMPLEMENTED YET.
- R8.1 : **AUTHORIZED / NOT STARTED**.
- R8.2–R8.11 : PLANNED / NOT STARTED.
- R9–R16 : PENDING / NOT STARTED.

## R8 frozen structure — planning accepted

`docs/roadmap/R8_PLAN.md` est l'autorité exhaustive de planification. La PR #83 étant acceptée et fusionnée, la structure suivante est maintenant gelée et ne peut pas être réinterprétée silencieusement :

| ID | Title | Manual planned |
| --- | --- | --- |
| R8.1 | Asset/Vault contracts, identity, schemas + boundary | NONE |
| R8.2 | Inter-project Vault store, revisions, reuse + preservation | NONE |
| R8.3 | Source/derived lineage + reproducible transform cache/rebuild | NONE |
| R8.4 | Duplicate + near-duplicate detection | NONE |
| R8.5 | Semantic asset search + hybrid ranking | CONDITIONAL |
| R8.6 | Provenance, license/BOM + governed reuse/export | NONE |
| R8.7 | Asset-aware Git/VCS integration | NONE |
| R8.8 | Git LFS tracking, pointer/object integrity + diagnostics | CONDITIONAL |
| R8.9 | Godot 4.7 source/import bridge + rebuild verification | CONDITIONAL |
| R8.10 | CLI + KodeStudio Vault/Asset/VCS UX | NONE |
| R8.11 | Adversarial hardening + R8 integrated acceptance | CONDITIONAL |

R8.1 peut être commencé uniquement depuis le `main` contenant le planning accepté et cette normalisation de continuité. Toute modification ultérieure de subdivision, dépendance, état manuel ou gate d'acceptation doit modifier `R8_PLAN.md` et cette continuité dans le même work cycle. Toute modification de fondation gelée exige un ADR.

## R8 planning acceptance — source de vérité

- Planning head exact : `08844fc09501ed8a4974909eca4595021bc73bf4`.
- Branch point : `b98832b339902527bce8a5ea95b5a08a19839a40`.
- `docs/roadmap/R8_PLAN.md` + `docs/continuity/KODEPOIA_CONTINUITY.md` étaient les deux seuls fichiers modifiés sur le planning head.
- R0 Repository Guard #1039 / `32600268817` : SUCCESS, Ubuntu + Windows.
- Python Core #1013 / `32600268710` : SUCCESS, cinq jobs (`python-core` Ubuntu/Windows, package build Ubuntu/Windows, KodeStudio UI Windows).
- KodeStudio UI Smoke #980 / `32600268680` : SUCCESS.
- PR #83 : merged.
- Merge SHA : `60412afac35678b2a25547a7f0c937891a8a1004`.
- R8.1 implementation on the planning branch : **NONE**.

## R8 planning architecture summary

- Inter-project Vault is local-first and explicitly configured; there is no implicit scan of arbitrary drives/home/network shares.
- Project `WorkspaceBoundary` semantics remain unchanged. A Vault boundary may only compose equivalent confinement around the explicit Vault root; weakening the frozen boundary requires an ADR.
- Assets have logical identity + immutable revisions; exact bytes use SHA-256/content length; replacing bytes creates a new revision.
- Source and derived roles are explicit. Derived/cache outputs never silently overwrite or replace source.
- Vault objects are content-addressed; provenance records are not collapsed merely because bytes are identical.
- Reuse scope and preservation are separate from license/governance policy.
- Derived outputs require recorded lineage: exact inputs, recipe identity, tool/provider version, deterministic settings/environment as relevant, output digests and nondeterminism/seed when applicable.
- Cache hits verify recipe key and output digest; path existence alone never implies validity.
- Duplicate detection distinguishes exact byte identity from probabilistic near-duplicate evidence; no destructive auto-merge.
- Semantic search reuses accepted R3 EMBED/vector/retrieval boundaries and retains deterministic lexical fallback; no mandatory cloud embedding service.
- Provenance/license reuse integrates R6 License/BOM and R7 provenance; no new legal inference engine.
- R8 VCS extends the accepted R4 Git/Worktree pattern through fixed structured operations; no arbitrary Git command/refspec/config surface.
- Git LFS remains transport/storage, not Vault identity. Pointer validity, object availability and tracking policy are separate states; history rewriting is out of normal R8 automation.
- Godot bridge treats `.godot/` and `.import/` as generated/import state and preserves original source assets as Vault/VCS source revisions.
- Qt/CLI must use one typed Asset service; no direct Qt process/Git/socket/secret handling.
- R8.11 will create canonical exact-head integrated evidence analogous in rigor to R7, but with R8-specific identities and manual-state verification.

## R7 frozen structure — completed

| ID | Title | Manual final |
| --- | --- | --- |
| R7.1 | KodeResearch contracts + ResearchGuard hardening | NONE |
| R7.2 | Local + official documentation research | NONE |
| R7.3 | Governed Web fetch + extraction | NONE |
| R7.4 | GitHub research adapter | CONDITIONAL NOT TRIGGERED |
| R7.5 | Community/forums research normalization | NONE |
| R7.6 | YouTube metadata + transcript ingestion | CONDITIONAL NOT TRIGGERED |
| R7.7 | Local STT + frame extraction/analysis hooks | REQUIRED SATISFIED |
| R7.8 | Version-awareness + provenance/conflict model | NONE |
| R7.9 | Research cache + Context/Memory orchestration | NONE |
| R7.10 | CLI + KodeStudio Research UX | NONE |
| R7.11 | Adversarial hardening + R7 integrated acceptance | CONDITIONAL NOT TRIGGERED |

Aucune subdivision R7 ne peut être réinterprétée rétroactivement. Toute modification de fondation exige un ADR. Toute nouvelle phase R8+ doit suivre la règle permanente de planification exhaustive.

## R7 integrated acceptance — source de vérité

`docs/roadmap/R7_INTEGRATED_ACCEPTANCE.json` contient exactement R7.1–R7.11 et lie pour chaque subdivision :

- chemin canonique `docs/roadmap/R7_N_ACCEPTANCE.md`;
- SHA-256 du blob Git canonique;
- longueur exacte en octets;
- accepted implementation head;
- état manuel explicite et dérivé `manual_satisfied`.

Le rapport :

- `schema_version=1`;
- `source_sha=52330ca576fe294956a8fb601bdfda1d72dc3f92`;
- `status=pass`;
- `blockers=[]`;
- `evidence_sha256=2d6fc8e95d22891228a462d2731059683ed03ae51bb5fff6e2755b194198f437`.

`scripts/r7_integrated_acceptance.py` régénère cette preuve depuis `git show HEAD:path`. `validate_repository_evidence()` recalcule les tailles/SHA-256, vérifie les heads, les états manuels et l'identité R7.11; toute différence fail closed. Python Core #1009 a exécuté ce contrôle avant pytest et a retourné `R7 integrated acceptance: PASS`.

## R7.11 accepted evidence

- Accepted head : `52330ca576fe294956a8fb601bdfda1d72dc3f92`.
- R0 Repository Guard #1030 / `32598775535` — SUCCESS.
- Python Core #1004 / `32598775562` — SUCCESS 5/5.
- Ubuntu : `514 passed / 6 skipped / 46 warnings`.
- UI Smoke #971 / `32598775534` — SUCCESS.
- PR #80 merge : `1cdf5b90cc6c3e829c13e63f753f47fb067ef14e`.
- Manual : CONDITIONAL NOT TRIGGERED.
- Candidate rejeté `b35a6dcd330c7cc3cb582d775ce0275d7a9b2f87` : R0 #1029 a correctement détecté un faux token GitHub littéral dans un fixture. Le scanner n'a pas été affaibli; le fixture final construit la valeur factice à l'exécution.

## Accepted R7 trust/security baseline

- Toute donnée externe reste une donnée, jamais une instruction agentique; `ResearchGuard` reste l'unique frontière de confiance contenu.
- `WorkspaceBoundary` confine stockage Research, documents, cache/context/export et paths media; traversal/absolute/symlink escapes fail closed.
- Web : GET-only typé, validation de toutes les réponses DNS, IP publique épinglée, TLS sur hostname original, redirects revalidés, Guardian NETWORK, bornes MIME/octets/timeout/rate, pas de retry caché.
- GitHub : REST read-only typé sur origine fixe, pas de GraphQL arbitraire ni write endpoint, mutable ref -> SHA exact avant preuve fichier, pagination bornée, secrets optionnels via `KodeSecrets` seulement.
- Community : auteur/thread/parent/timestamps/quotes/états conservés; popularité, votes, réactions ou rôle vendor/moderator ne deviennent jamais automatiquement autorité officielle.
- YouTube : metadata/transcript/track/timestamps/auth states séparés et explicites; aucun login automation, DRM/restriction bypass ou média arbitraire.
- Local media : FFmpeg/whisper.cpp uniquement via ProcessSandbox + KillSwitch + Guardian PROCESS_EXECUTE; aucun argv/cwd/executable arbitraire fourni par le modèle; aucun install auto; vision reste UNAVAILABLE sans provider réel.
- Versioning : EXACT/RANGE/INFERRED/UNKNOWN distincts; freshness séparée; mutable/immutable explicite; contradictions et supersession restent visibles; ranking ne transforme pas popularité/source count en vérité.
- Cache/context/memory : cache hit ne fabrique pas CURRENT; provenance/trust/citations sont conservés; résumé et Memory ne deviennent jamais automatiquement Experience validée/globale; global/training promotion désactivée.
- CLI/KodeStudio : un seul `ResearchService`; Web BLOCKED par défaut; Qt ne manipule ni socket, secret ni process arbitraire; cancel avant persistence/READY; export cité/redacted/workspace-confined.
- R7.11 : tests adversariaux cross-source couvrent prompt injection, SSRF/private/redirect/mixed DNS, path escape, secret exfiltration, cancellation, process/tool surface et version conflicts.

Ces choix sont cohérents avec les recommandations OWASP actuelles : séparer clairement le contenu externe non fiable, appliquer le moindre privilège/validation des tool calls et tester les indirect prompt injections; pour SSRF, ne pas faire confiance aux redirects et se protéger contre DNS pinning/rebinding. Ces références externes sont du contexte de sécurité, pas une certification.

## R7.7 REQUIRED local-media accepted evidence

- Accepted head `04cef94c82fdacafe7313d27c8cf516e8e765295`.
- FFmpeg 4.2.3 SHA-256 `b6bd38a97c5f118f30c93a97b5739b5f33dd2616c735f841c2a56074a9f0a9f0`.
- whisper.cpp 1.9.1 SHA-256 `58245314fb73b30fbd0cf0542c5c172e23f02b6eb7cad7b51e792439cf5e1755`.
- STT model SHA-256 `a03779c86df3323075f5e796cb2ce5029f00ec8869eee3fdfb897afe36c6d002`.
- Fixture SHA-256 `8b3ed015526fd4584309a3c661b9e267ac464315e2d1c9aeed5bea19f28bdcf7`, 12,112 bytes.
- Doctor SHA-256 `463c0de4ad477baabc711a2b89fc1c7ad0b7735c6bdfc2ecfdde457a9f8f86e1`.
- Local acceptance SHA-256 `33e52eb43ed448dd02766b823c3b22bfb08301a9f4dc3f24f336269f1ab76283`.
- Authoritative local pytest : PASS, 1 passed et non skipped.

## Permanent architecture/security boundaries

Préserver sans réinterprétation : `WorkspaceBoundary`; ProcessSandbox + global KillSwitch; Guardian + PermissionSet; APIs outils structurées uniquement; SafeChange/Backup/Recovery/Audit lorsque requis; Secrets OS-backed + redaction; Health/Budget/DataGovernance + schémas versionnés; exact-head acceptance; états explicites UNKNOWN/N/A/UNAVAILABLE/BLOCKED/STALE; comportement platform-aware; ADR pour toute fondation gelée. Aucun arbitrary command/argv/cwd/host/network surface ne peut être fourni par le modèle.

## Accepted model roles

- KodeFast = `granite4.1:3b`.
- KodeCore = `gpt-oss:20b`.
- KodeCoder = `ornith:9b`.
- `north-mini-code-1.0:Q4_K_M` reste un candidat futur KodeDeepCoder.
- Les tâches non triviales Git/repository/software-engineering ne doivent pas être routées vers Granite.

## Permanent phase-start rule

Pour toute phase R8+ :

1. créer un `RX_PLAN.md` exhaustif avant RX.1;
2. y figer subdivisions, dépendances, architecture, implementation plan, deliverables, acceptance/evidence, rollback, risques et état manuel NONE/REQUIRED/CONDITIONAL;
3. synchroniser `docs/continuity/KODEPOIA_CONTINUITY.md` dans le même work cycle;
4. faire passer R0 Repository Guard, Python Core complet et KodeStudio UI Smoke sur le head exact du plan;
5. merger le plan avant toute implémentation RX.1;
6. toute modification ultérieure de structure doit synchroniser plan + continuité; tout changement de fondation nécessite un ADR.

## Next action

**R1–R7 COMPLETE. R8 PLANNING ACCEPTED. R8.1 AUTHORIZED / NOT STARTED.** La prochaine action autorisée, après fusion de cette normalisation de continuité, est **R8.1 — Asset/Vault contracts, identity, schemas + boundary** sur une nouvelle branche dédiée issue du `main` normalisé. Ne pas commencer R8.2 avant acceptation de R8.1 et ne pas modifier la structure R8 sans synchroniser `R8_PLAN.md` + continuité.